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

if ! git subtree >/dev/null 2>&1; then
  echo "git subtree is required but was not found." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree must be clean before subtree operations." >&2
  exit 1
fi

mkdir -p packages provenance
MANIFEST="provenance/imported-sources.tsv"
if [[ "$MODE" == "import" ]]; then
  printf "name\tprefix\tbranch\tcommit\turl\timported_at_utc\n" > "$MANIFEST"
fi

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

for item in "${COMPONENTS[@]}"; do
  IFS='|' read -r name prefix branch url <<< "$item"
  remote="source-$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-')"
  remote="${remote%-}"

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

  printf "%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$name" "$prefix" "$branch" "$commit" "$url" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    >> "$MANIFEST"
done

# Commit the refreshed manifest separately because subtree commands commit as they run.
git add "$MANIFEST"
if ! git diff --cached --quiet; then
  git commit -m "Record component source revisions"
fi

echo "Component $MODE complete."
