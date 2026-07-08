#!/usr/bin/env bash
# Wires local git hooks. Local hooks don't survive clones -- if your team
# can't rely on that, use the CI equivalents instead (one of the two MUST
# exist): a job running scripts/check-truth.sh on PRs touching the ledger,
# and a job running `scripts/truth invalidate-scan --quiet` after merges.
set -euo pipefail
HOOK_DIR="$(git rev-parse --git-dir)/hooks"
cat > "$HOOK_DIR/pre-commit" <<'HOOK'
#!/usr/bin/env bash
exec bash scripts/check-truth.sh
HOOK
cat > "$HOOK_DIR/post-merge" <<'HOOK'
#!/usr/bin/env bash
python3 scripts/truth invalidate-scan --quiet
HOOK
chmod +x "$HOOK_DIR/pre-commit" "$HOOK_DIR/post-merge"
echo "hooks installed: pre-commit, post-merge"
