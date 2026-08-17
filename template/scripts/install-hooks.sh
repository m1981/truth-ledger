#!/usr/bin/env bash
# Wires local git hooks. Local hooks don't survive clones -- if your team
# can't rely on that, use the CI equivalents instead (one of the two MUST
# exist): a job running scripts/check-truth.sh on PRs touching the ledger
# (which also covers merge commits server-side), and a job running
# `python3 scripts/truth reproduce` on PRs, which blocks on exit 7 (a live
# capsule no longer reproduces) and on exit 8 (it examined nothing).
# Four hooks: pre-commit and pre-merge-commit carry the SAME gate --
# git runs pre-merge-commit, never pre-commit, when a merge auto-commits
# (the commit class a union-merge sync produces; ADR-045); post-merge is
# deliberately inert; and pre-push runs `truth reproduce`.
#
# THE PUSH HOOK IS NEW IN refactor step 2.6, and it is what makes
# the Reproduce-on-Read story true for a consumer rather than only for
# this template's own repo. Step 2.4 emptied post-merge -- the invalidation
# scan was a syntactic proxy with a 3.6% positive predictive value -- and
# said reproduce runs at pre-push instead. It did, here. In a generated
# consumer repo nothing wrote that hook, so the sentence was a promise
# with no mechanism behind it: exactly the "detection that runs on
# nobody's schedule" this project refuses. Push is the right boundary for
# the same reason the meta-repo puts its battery there -- it is where
# staleness starts leaving the machine, and unlike pre-commit it does not
# tax every edit and train `--no-verify`.
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
  echo "  $HOOKS_PATH/pre-push:           python3 scripts/truth reproduce" >&2
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
cat > "$HOOK_DIR/pre-push" <<'HOOK'
#!/usr/bin/env bash
# Reproduce-on-Read at the push boundary: re-run every LIVE claim's
# evidence capsule here and now. Blocks on exit 7 (a recorded capsule no
# longer reproduces -- judge it, do not re-file blind) and on exit 8 (the
# sweep examined ZERO live claims, which is a failure and never a pass;
# ADR-042 rule 2). Emergency exit is `git push --no-verify`, which is
# honest and loud in the reflog.
#
# A PUSH HOOK MUST NEVER BLOCK ON INPUT: it runs with a terminal attached,
# and anything downstream consulting isatty() would wait forever.
exec </dev/null
exec python3 scripts/truth reproduce
HOOK
chmod +x "$HOOK_DIR/pre-commit" "$HOOK_DIR/pre-merge-commit" \
         "$HOOK_DIR/post-merge" "$HOOK_DIR/pre-push"
echo "hooks installed: pre-commit, pre-merge-commit, post-merge, pre-push"
