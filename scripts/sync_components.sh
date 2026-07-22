#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
if [[ "$MODE" != "import" && "$MODE" != "pull" && "$MODE" != "plan" && "$MODE" != "plan-json" ]]; then
  echo "Usage: $0 import|pull|plan|plan-json" >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  echo "Run this script inside a Git repository." >&2
  exit 1
fi
cd "$ROOT"

subtree_probe="$(git subtree 2>&1 || true)"
if echo "$subtree_probe" | grep -q "is not a git command"; then
  echo "git subtree is required but was not found." >&2
  exit 1
fi

if [[ "$MODE" != "plan" && "$MODE" != "plan-json" && -n "$(git status --porcelain)" ]]; then
  echo "Working tree must be clean before subtree operations." >&2
  exit 1
fi

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "python3 or python is required." >&2
  exit 1
fi

git_name="$(git config --local --get user.name || true)"
git_email="$(git config --local --get user.email || true)"
if [[ "$MODE" != "plan" && "$MODE" != "plan-json" && ( -z "$git_name" || -z "$git_email" ) ]]; then
  echo "Repository-local Git user.name and user.email are required before subtree operations." >&2
  echo "Set them with: git config --local user.name \"Your Name\" && git config --local user.email \"you@example.com\"" >&2
  exit 1
fi

mkdir -p packages provenance provenance/import-receipts
MANIFEST="provenance/imported-sources.tsv"
MANIFEST_TMP="${MANIFEST}.tmp"
TMP_RECEIPT_DIR="provenance/.import-receipts.tmp"
mkdir -p "$TMP_RECEIPT_DIR"
printf "name\tprefix\tbranch\tcommit\ttree\turl\timported_at_utc\n" > "$MANIFEST_TMP"

current_component=""
cleanup() {
  rm -f "$MANIFEST_TMP"
  rm -rf "$TMP_RECEIPT_DIR"
}

on_error() {
  status=$?
  cleanup
  if [[ -n "$current_component" ]]; then
    echo "Component $MODE failed while processing: $current_component" >&2
  fi
  exit "$status"
}

trap on_error ERR
trap cleanup EXIT

# name|prefix|branch|url
COMPONENTS=(
  "TrustedRuntime|packages/trusted-runtime|main|https://github.com/LadyElinor/TrustedRuntime.git"
  "AConstellation|packages/aconstellation|main|https://github.com/LadyElinor/AConstellation.git"
  "AttestAgentConlang|packages/attest-agent-conlang|main|https://github.com/LadyElinor/AttestAgentConlang.git"
  "meaning-assay|packages/meaning-assay|master|https://github.com/LadyElinor/meaning-assay.git"
  "SOPHRON-CER|packages/sophron-cer|main|https://github.com/LadyElinor/SOPHRON-CER.git"
  "CER-Telemetry|packages/cer-telemetry|main|https://github.com/LadyElinor/CER-Telemetry.git"
  "TrustworthyAgentStack|packages/trustworthy-agent-stack|main|https://github.com/LadyElinor/TrustworthyAgentStack.git"
  "EthicsCouncil|packages/ethics-council|master|https://github.com/LadyElinor/EthicsCouncil.git"
)

PLAN_JSON_ITEMS=()

previous_receipt_digest=""
for item in "${COMPONENTS[@]}"; do
  IFS='|' read -r name prefix branch url <<< "$item"
  current_component="$name"
  remote="source-$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-')"
  remote="${remote%-}"
  receipt_path="provenance/import-receipts/${prefix//\//--}.json"
  receipt_tmp_path="$TMP_RECEIPT_DIR/${prefix//\//--}.json"
  if [[ -f "$receipt_path" ]]; then
    previous_receipt_digest="$("$PYTHON_BIN" - "$receipt_path" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding='utf-8'))
print(payload.get('receipt_digest', ''))
PY
)"
  else
    previous_receipt_digest=""
  fi

  path_state="missing"
  if [[ -e "$prefix" ]]; then
    path_state="present"
  fi
  receipt_state="missing"
  if [[ -f "$receipt_path" ]]; then
    receipt_state="present"
  fi

  if [[ "$MODE" == "plan" || "$MODE" == "plan-json" ]]; then
    action="import"
    if [[ -d "$prefix" ]]; then
      action="pull"
    fi
    if [[ "$MODE" == "plan" ]]; then
      printf "PLAN     %-22s action=%-6s prefix=%-34s branch=%-8s path=%-7s receipt=%s\n" \
        "$name" "$action" "$prefix" "$branch" "$path_state" "$receipt_state"
    else
      PLAN_JSON_ITEMS+=("$("$PYTHON_BIN" - <<'PY' "$name" "$prefix" "$branch" "$url" "$action" "$path_state" "$receipt_state" "$receipt_path"
import json
import sys
name, prefix, branch, url, action, path_state, receipt_state, receipt_path = sys.argv[1:]
print(json.dumps({
    "name": name,
    "prefix": prefix,
    "branch": branch,
    "url": url,
    "action": action,
    "path_state": path_state,
    "receipt_state": receipt_state,
    "receipt_path": receipt_path,
}))
PY
)")
    fi
    continue
  fi

  if ! git remote get-url "$remote" >/dev/null 2>&1; then
    git remote add "$remote" "$url"
  fi
  git fetch "$remote" "$branch" --tags
  commit="$(git rev-parse "$remote/$branch")"

  if [[ "$MODE" == "import" ]]; then
    if [[ -e "$prefix" ]]; then
      echo "Refusing to import $name: $prefix already exists." >&2
      exit 1
    fi
    git subtree add --prefix="$prefix" "$remote" "$branch" \
      -m "Import $name at $commit"
  else
    if [[ ! -d "$prefix" ]]; then
      echo "Refusing to pull $name: $prefix is absent. Run import first." >&2
      exit 1
    fi
    git subtree pull --prefix="$prefix" "$remote" "$branch" \
      -m "Update $name to $commit"
  fi

  tree="$(git rev-parse HEAD:"$prefix")"
  imported_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$name" "$prefix" "$branch" "$commit" "$tree" "$url" "$imported_at" \
    >> "$MANIFEST_TMP"

  "$PYTHON_BIN" - "$name" "$prefix" "$branch" "$commit" "$tree" "$url" "$MODE" "$imported_at" "$previous_receipt_digest" "$receipt_tmp_path" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path('scripts').resolve()))
from provenance_utils import canonical_json_bytes, sha256_hex_bytes

name, prefix, branch, commit, tree, url, mode, imported_at, previous_digest, receipt_path = sys.argv[1:]
fidelis_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
row = {
    'name': name,
    'prefix': prefix,
    'branch': branch,
    'commit': commit,
    'tree': tree,
    'url': url,
    'imported_at_utc': imported_at,
}
payload = {
    'schema_version': '1.0',
    'receipt_type': 'component-import',
    'component': prefix.split('/', 1)[1],
    'name': name,
    'prefix': prefix,
    'mode': mode,
    'upstream_url': url,
    'upstream_branch': branch,
    'upstream_commit': commit,
    'imported_tree': tree,
    'manifest_row_digest': sha256_hex_bytes(canonical_json_bytes(row)),
    'fidelis_commit': fidelis_commit,
    'imported_at_utc': imported_at,
    'previous_receipt_digest': previous_digest or None,
}
payload['receipt_digest'] = sha256_hex_bytes(canonical_json_bytes(payload))
Path(receipt_path).write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
PY
done
current_component=""

if [[ "$MODE" == "plan" ]]; then
  echo "Component plan complete."
  exit 0
fi

if [[ "$MODE" == "plan-json" ]]; then
  "$PYTHON_BIN" - <<'PY' "${PLAN_JSON_ITEMS[@]}"
import json
import sys
items = [json.loads(arg) for arg in sys.argv[1:]]
payload = {
    "schema_version": "1.0",
    "mode": "plan-json",
    "components": items,
}
print(json.dumps(payload, indent=2))
PY
  exit 0
fi

mv "$MANIFEST_TMP" "$MANIFEST"
rm -rf provenance/import-receipts
mkdir -p provenance/import-receipts
cp "$TMP_RECEIPT_DIR"/*.json provenance/import-receipts/

# Commit the refreshed manifest and receipts separately because subtree commands commit as they run.
git add "$MANIFEST" provenance/import-receipts
if ! git diff --cached --quiet; then
  git commit -m "Record component source revisions"
fi

echo "Component $MODE complete."
