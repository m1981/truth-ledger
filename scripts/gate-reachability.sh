#!/usr/bin/env bash
# gate-reachability: does a schedule actually REACH each of our checks?
# META-REPO ONLY (ADR-003 rule 2): the CHECK enumeration and the ROOT set
# below encode THIS repository's wiring, not the machinery consumers get.
#
# WHY THIS EXISTS. release-battery.sh already carries the law -- "Detection
# that runs on nobody's schedule runs after the incident" -- and on
# 2026-08-02 three independent audits found the repo breaking it again, in
# the same commit series that claimed to strengthen coverage: three test
# suites (fact-health 10 arms, session-digest 3, instruments 16) had been
# written and committed with NOTHING invoking them, and six proven canary
# assertions had been MOVED into one of them. Automated coverage went down
# while the log said it went up. The law was prose; nothing measured it.
# This is the measurement, and it is itself one of the checks it measures.
#
# --- THE REACHABILITY RULE ---------------------------------------------
# A CHECK is reachable when some ROOT invokes it, directly or through
# other files. Everything else is a dark gate and FAILS.
#
# ROOTS are the things that fire without anyone remembering to fire them:
#   - .githooks/*  -- this repo's ACTIVE hooks (core.hooksPath=.githooks),
#     so what they invoke runs on commit, merge and push here;
#   - .claude/settings.json hook commands -- the harness lane (PreToolUse,
#     SessionStart);
#   - template/scripts/install-hooks.sh -- a TEMPLATE root. It writes the
#     consumer's pre-commit/pre-merge-commit/post-merge bodies, so a
#     template-side check named in one of those bodies runs on a schedule
#     in every consumer repo. That is the honest reachability story for
#     template/: a template check is reachable if a TEMPLATE root would
#     invoke it, or if a meta root does (the battery runs the canary and
#     the two python suites; the canary in turn drives spec-health,
#     doc-health and session-close inside its sandbox).
#
# EDGES are textual and grep-shaped, and that is stated plainly rather
# than implied: file A invokes file B when a non-comment line of A names
# B (by path tail, or by bare basename) AND carries an invoker token
# (bash/sh/zsh/python3/exec/source/./). Consequences, both recorded:
#   - a check dispatched through a variable-built path is INVISIBLE here
#     and reads as unreachable -- the fail-safe direction, a loud false
#     alarm rather than a quiet blessing;
#   - matching by path TAIL means two mirrored files (scripts/x.sh and
#     template/scripts/x.sh) are reached together. That is the one
#     direction that can over-report, and it is confined to files this
#     repo deliberately mirrors.
# Reachability is the TRANSITIVE closure from the roots (fixpoint, not a
# fixed hop count: pre-push -> release-battery -> truth-canary ->
# doc-health is three hops and entirely real).
#
# A SCOPED invocation still counts. The battery runs the canary only when
# the CLI or the suite moved; that is a policy about WHEN a check fires,
# not whether it is wired. An unwired check fires never.
#
# --- OPT-OUT POLICY (.truth/reachability-opt-out) -----------------------
# Fail-mode semantics copied from .truth/generated-paths, deliberately:
#   ABSENT       -- no policy on record. The sweep cannot tell a deliberate
#                   exemption from an oversight, so it excuses NOTHING and
#                   says so loudly (advisory, the dark-gate voice).
#   COMMITTED EMPTY -- a conscious "everything here must be reachable".
#                   Armed and silent; empty is a statement, not an omission.
#   POPULATED    -- armed. One entry per line: `<path> -- <one-line reason>`.
# An entry that names a path which is not a check, or a check that IS
# reachable, is itself a FAILURE: a stale excuse is a gate that looks
# considered and covers nothing. Pathspec magic is refused (SI-1
# precedent, as in .truth/citation-scope): a line starting ':', '-' or '!'
# is rejected, so exemptions are enumerated positively and never as
# exclusions.
#
# SELF-APPLICATION. This sweep enumerates itself (scripts/gate-*.sh is one
# of the CHECK patterns) and reports its own reachability by name; if it
# ever drops out of its own enumeration, or examines zero checks, it
# FAILS. A sweep that examined nothing is never a pass.
#
# Exit codes follow check-truth.sh: 0 ok / 1 governance / 2 environment.
set -u
cd "$(dirname "$0")/.."

command -v git >/dev/null 2>&1 || { echo "gate-reachability: no git" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "gate-reachability: no python3" >&2; exit 2; }
git rev-parse --git-dir >/dev/null 2>&1 || {
  echo "gate-reachability: not inside a git repository" >&2; exit 2; }

# --- enumerate, never hardcode -----------------------------------------
# Derived from git ls-files so a check added tomorrow is examined tomorrow.
# A hardcoded roster is the same defect one level up: it falls behind in
# silence, and the sweep reports "all reachable" over a list that stopped
# growing. `--others --exclude-standard` puts the WORKTREE in scope too:
# an orphaned suite is a defect the hour it is written, not the day after
# it is committed -- which is precisely when the 2026-08-02 audits caught
# this one. Ignored files stay out.
LS="git ls-files --cached --others --exclude-standard"
CHECKS="$($LS \
  'scripts/test-*.sh' 'scripts/*-health.sh' 'scripts/gate-*.sh' \
  'template/scripts/*-health.sh' 'template/scripts/truth-canary.sh' \
  'template/scripts/test-*.py' 'template/scripts/session-close.sh' \
  'instruments/field-consumers.py' 'instruments/label-coupling.py' \
  'instruments/arm-index.py' | sort -u)"
ROOTS="$($LS '.githooks/*' | sort -u)
$($LS '.claude/settings.json')
$($LS 'template/scripts/install-hooks.sh')"
# Every tracked file that could sit BETWEEN a root and a check.
NODES="$($LS 'scripts/*' 'template/scripts/*' 'instruments/*' \
  '.githooks/*' '.claude/settings.json' | sort -u)"
OPTOUT=".truth/reachability-opt-out"
OPTOUT_STATE=absent
[ -f "$OPTOUT" ] && OPTOUT_STATE=present

export CHECKS ROOTS NODES OPTOUT OPTOUT_STATE
python3 - <<'PY'
import os, re, sys

def lines(s):
    return [x.strip() for x in s.splitlines() if x.strip()]

checks = lines(os.environ["CHECKS"])
roots  = lines(os.environ["ROOTS"])
nodes  = sorted(set(lines(os.environ["NODES"])) | set(checks) | set(roots))
optout_path  = os.environ["OPTOUT"]
optout_state = os.environ["OPTOUT_STATE"]
SELF = "scripts/gate-reachability.sh"

fail = 0
def bad(label, why):
    global fail
    print(f"  FAIL  {label} -- {why}")
    fail = 1

if not roots:
    print("gate-reachability: no roots found -- .githooks/ and "
          ".claude/settings.json are both absent from the index; there is "
          "nothing to be reachable FROM (exit 2: environment)", file=sys.stderr)
    sys.exit(2)

def text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""

# An invoker token, anchored so that the ".sh" ENDING of a path can never
# masquerade as the `sh` command (it did, in the first cut: every line
# naming a shell script looked like an invocation).
INVOKER = re.compile(r"""(?:^|[\s;&|(`='"])(?:bash|sh|zsh|python3?|exec|source|\.)\s"""
                     r"""|(?<![\w.])\./""")

def token_paths(line, base):
    """Path-ish tokens on `line` that end in `base`."""
    pat = re.compile(r"(?<![\w./-])([\w./${}\"'-]*" + re.escape(base) + r")(?![\w.-])")
    out = []
    for m in pat.finditer(line):
        segs = m.group(1).split("/")
        # Drop leading variable-ish segments: "$HERE/x.sh" -> "x.sh".
        while segs and any(c in segs[0] for c in "$\"'{"):
            segs.pop(0)
        tok = "/".join(segs).strip("\"'")
        if tok:
            out.append(tok)
    return out

def invokes(src):
    """Files that `src` textually invokes."""
    hit = set()
    body = text(src)
    if not body:
        return hit
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("#") or not INVOKER.search(line):
            continue
        for tgt in nodes:
            if tgt == src:
                continue
            base = os.path.basename(tgt)
            if base not in line:
                continue
            for tok in token_paths(line, base):
                if ("/" in tok and (tgt == tok or tgt.endswith("/" + tok))) \
                   or ("/" not in tok and base == tok):
                    hit.add(tgt)
                    break
    return hit

# Transitive closure from the roots, carrying a path so each ok line can
# name HOW the check is reached (an arm that cannot show its work is the
# thing this sweep exists to catch).
via = {r: [r] for r in roots}
frontier = list(roots)
while frontier:
    nxt = []
    for src in frontier:
        for tgt in invokes(src):
            if tgt not in via:
                via[tgt] = via[src] + [tgt]
                nxt.append(tgt)
    frontier = nxt

# --- opt-out policy ------------------------------------------------------
excused, advisory = {}, []
if optout_state == "absent":
    advisory.append(
        f"ADVISORY: {optout_path} is ABSENT, so no exemption can be honoured "
        "and none is assumed. Commit it EMPTY to state that everything here "
        "must be reachable, or populate it with `<path> -- <reason>` lines.")
else:
    for n, raw in enumerate(text(optout_path).splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line[0] in ":-!":
            bad(f"{optout_path}:{n}", f"pathspec magic refused (SI-1): {line!r}. "
                "Exemptions are enumerated positively, never as exclusions")
            continue
        if " -- " not in line:
            bad(f"{optout_path}:{n}", f"no reason given: {line!r}. An exemption "
                "without a one-line reason is an unexplained dark gate")
            continue
        path, reason = line.split(" -- ", 1)
        path, reason = path.strip(), reason.strip()
        if not reason:
            bad(f"{optout_path}:{n}", f"empty reason for {path}")
            continue
        excused[path] = reason

# --- verdict -------------------------------------------------------------
print(f"gate-reachability: {len(checks)} check(s) against {len(roots)} root(s)")
for r in roots:
    print(f"  root  {r}")

if not checks:
    print("  FAIL  enumeration -- the CHECK patterns matched 0 tracked files; "
          "this sweep examined nothing, which is a failure and never a pass")
    sys.exit(1)

reachable = unreachable = waived = 0
for c in checks:
    if c in via:
        reachable += 1
        hop = " -> ".join(via[c])
        print(f"  ok    {c} -- reached by {hop}")
    elif c in excused:
        waived += 1
        print(f"  waive {c} -- opted out: {excused[c]}")
    else:
        unreachable += 1
        bad(c, "NO root reaches it. It runs on nobody's schedule, so it runs "
               f"after the incident. Wire it, or list it in {optout_path} "
               "with a one-line reason")

for path, reason in sorted(excused.items()):
    if path not in checks:
        bad(f"{optout_path}", f"{path} is exempted but is not a check this "
                              "sweep enumerates -- a stale excuse")
    elif path in via:
        bad(f"{optout_path}", f"{path} is exempted ({reason}) but IS reachable "
                              "now -- delete the entry rather than keep a "
                              "standing excuse nobody rechecks")

# Self-application: the sweep must be in its own enumeration and must
# itself be reached by a root.
if SELF not in checks:
    bad("self", f"{SELF} is not in its own CHECK enumeration -- the sweep "
                "exempted itself from the rule it enforces")
elif SELF in via:
    print(f"  self  {SELF} is reachable: {' -> '.join(via[SELF])}")
else:
    bad("self", f"{SELF} is not reachable -- a reachability sweep nothing "
                "runs is the defect it exists to find")

for a in advisory:
    print(f"  {a}")

print(f"\ngate-reachability: examined {len(checks)} check(s), "
      f"{reachable} reachable, {unreachable} unreachable, {waived} opted out")
sys.exit(1 if fail else 0)
PY
