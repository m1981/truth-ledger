#!/usr/bin/env bash
# Wires local git hooks. Local hooks don't survive clones -- if your team
# can't rely on that, use the CI equivalents instead (one of the two MUST
# exist): a job running scripts/check-truth.sh on PRs touching the ledger
# (which also covers merge commits server-side), and a job running
# `python3 scripts/truth reproduce` on PRs, which blocks on exit 7 (a live
# capsule no longer reproduces) and on exit 8 (it examined nothing).
# Three hooks: pre-commit and pre-merge-commit carry the SAME gate --
# git runs pre-merge-commit, never pre-commit, when a merge auto-commits
# (the commit class a union-merge sync produces; ADR-045) -- and
# post-merge runs the invalidation scan.
set -euo pipefail
# If core.hooksPath points elsewhere (husky, lefthook, .githooks), hooks
# written to .git/hooks are DEAD FILES -- refuse to pretend otherwise.
HOOKS_PATH="$(git config core.hooksPath || true)"
if [ -n "$HOOKS_PATH" ]; then
  echo "install-hooks: core.hooksPath=$HOOKS_PATH is set; .git/hooks would never run." >&2
  echo "  Wire the truth hooks into your hook manager instead, e.g. add to" >&2
  echo "  $HOOKS_PATH/pre-commit:         bash scripts/check-truth.sh" >&2
  echo "  $HOOKS_PATH/pre-merge-commit:   bash scripts/check-truth.sh" >&2
  echo "  $HOOKS_PATH/post-merge:         (nothing -- reproduce runs at pre-push)" >&2
  exit 1
fi
HOOK_DIR="$(git rev-parse --git-dir)/hooks"
cat > "$HOOK_DIR/pre-commit" <<'HOOK'
#!/usr/bin/env bash
exec bash scripts/check-truth.sh
HOOK
cat > "$HOOK_DIR/pre-merge-commit" <<'HOOK'
#!/usr/bin/env bash
exec bash scripts/check-truth.sh
HOOK
cat > "$HOOK_DIR/post-merge" <<'HOOK'
#!/usr/bin/env bash
# Reproduce-on-Read: this hook does not write to the ledger. `truth
# reproduce` is the authority and runs at pre-push; see docs/ARCHITECTURE.md
# section 4.
exit 0
HOOK
chmod +x "$HOOK_DIR/pre-commit" "$HOOK_DIR/pre-merge-commit" "$HOOK_DIR/post-merge"
echo "hooks installed: pre-commit, pre-merge-commit, post-merge"
