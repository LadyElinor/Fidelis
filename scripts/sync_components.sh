#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
if [[ "$MODE" != "import" && "$MODE" != "pull" ]]; then
  echo "Usage: $0 import|pull" >&2
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

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree must be clean before subtree operations." >&2
  exit 1
fi

mkdir -p packages provenance provenance/import-receipts
MANIFEST="provenance/imported-sources.tsv"
MANIFEST_TMP="${MANIFEST}.tmp"
printf "name\tprefix\tbranch\tcommit\ttree\turl\timported_at_utc\n" > "$MANIFEST_TMP"

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

previous_receipt_digest=""
for item in "${COMPONENTS[@]}"; do
  IFS='|' read -r name prefix branch url <<< "$item"
  remote="source-$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-')"
  remote="${remote%-}"
  receipt_path="provenance/import-receipts/${prefix//\//--}.json"
  if [[ -f "$receipt_path" ]]; then
    previous_receipt_digest="$(python - <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding='utf-8'))
print(payload.get('receipt_digest', ''))
PY
"$receipt_path")"
  else
    previous_receipt_digest=""
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

  python - <<'PY' "$name" "$prefix" "$branch" "$commit" "$tree" "$url" "$MODE" "$imported_at" "$previous_receipt_digest" "$receipt_path"
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

mv "$MANIFEST_TMP" "$MANIFEST"

# Commit the refreshed manifest and receipts separately because subtree commands commit as they run.
git add "$MANIFEST" provenance/import-receipts
if ! git diff --cached --quiet; then
  git commit -m "Record component source revisions"
fi

echo "Component $MODE complete."
