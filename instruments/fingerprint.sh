#!/usr/bin/env bash
# Behavioural fingerprint — the acceptance instrument for behaviour-preserving
# refactors (A1 sys.exit, A2 advisory split, A4 verb table).
#
# WHY THIS EXISTS. For a refactor, "the tests pass" is not a proof: the tests
# are the thing an agent can bend to make them pass. ADR-044 got this right —
# its acceptance was the OLD corpus unchanged, and any arm-count delta meant
# the phase had exceeded its licence. This script generalises that: it drives
# the REAL CLI through every refusal path and records (exit code, stderr,
# stdout shape) as one canonical file. A behaviour-preserving refactor must
# reproduce it byte for byte.
#
#   ./fingerprint.sh > before.txt     # on the base commit
#   ./fingerprint.sh > after.txt      # on the refactor
#   diff before.txt after.txt         # MUST be empty
#
# A non-empty diff is not a merge conflict to resolve. It is the refactor
# changing behaviour, and the agent's licence says it may not.
set -u
# the TEMPLATE is the artifact under test, unambiguously -- the meta-repo
# root also carries a scripts/truth (it eats its own cooking), and testing
# that one silently tests a symlink instead of the shipped surface.
TL="$(cd "$(dirname "$0")/../template" && pwd)"
D="$(mktemp -d)"; trap 'cd /; rm -rf "$D"' EXIT
cd "$D" || exit 1

# The claim id hashes the payload, and the payload carries anchor_commit --
# so a varying commit hash makes every VERIFIED id vary, and any id-ordered
# listing (impact) reorders between runs. Pin git's clock too.
export GIT_AUTHOR_DATE="2026-01-01T00:00:00+00:00"
export GIT_COMMITTER_DATE="2026-01-01T00:00:00+00:00"
git init -q .; git config user.email a@b; git config user.name a
mkdir -p .truth/schema docs/specs
cp "$TL/.truth/schema/claims.schema.json" .truth/schema/
printf 'grep\ncat\nwc\nls\necho\ntest\n' > .truth/evidence-allow
cp "$TL/.truth/evidence-deny" .truth/ 2>/dev/null || :
: > .truth/generated-paths
: > .truth/accept-allow
printf 'x\nx\n' > f.txt
echo "anchor" > docs/specs/anchor.md
echo "scripts/truth" > AGENTS.md
printf '.truth/claims.jsonl merge=union\n' > .gitattributes
git add -A >/dev/null; git commit -qm init

T="python3 $TL/scripts/truth"
export TRUTH_ACTOR=fp TRUTH_SESSION=s-fp

# Deterministic normalisation: ids, hashes, timestamps and paths vary per run
# and are NOT behaviour. Everything else is.
norm() {
  sed -E -e "s#$D#<SANDBOX>#g" \
         -e 's/tr-[0-9a-f]{8}/<TR>/g' -e 's/wk-[0-9a-f]{8}/<WK>/g' \
         -e 's/sha256:[0-9a-f]{64}/<SHA>/g' \
         -e 's/[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.+]+/<TS>/g' \
         -e 's/\b[0-9a-f]{40}\b/<COMMIT>/g' \
         -e 's/[0-9]+\.[0-9]+ms|[0-9]+ms/<MS>/g'
}

# Ids are sha256(payload, ts, actor), so a moving clock makes every id --
# and therefore every id-ordered listing -- vary between runs. Pinning the
# clock per probe makes the id a pure function of the payload, which is what
# a fingerprint needs. TRUTH_NOW also disables the ADR-015 clock-push; that
# is fine here and is the hook's documented purpose.
FP_N=0
probe() {  # probe "<label>" <argv...>
  local label="$1"; shift
  local out err rc
  FP_N=$((FP_N + 1))
  export TRUTH_NOW="$(printf '2026-01-01T00:%02d:%02d.000000+00:00' \
                      $((FP_N / 60)) $((FP_N % 60)))"
  out="$("$@" 2>/tmp/fp.err)"; rc=$?
  err="$(cat /tmp/fp.err)"
  printf '=== %s\n' "$label"
  printf '    exit=%s\n' "$rc"
  printf '%s\n' "$err" | norm | sed 's/^/    E| /'
  printf '%s\n' "$out" | norm | sed 's/^/    O| /'
}

echo "# behavioural fingerprint — refusal messages, exit codes, advisory block"
echo "# any diff against this file is a BEHAVIOUR CHANGE, not a refactor"
echo

# ---- intake gates, in table order (ADR-034) -----------------------------
probe "G:text-empty"            $T claim "" --class UNVERIFIED
probe "G:dup-baseline"          $T claim "the alpha fact holds here" --class UNVERIFIED
probe "G:near-duplicate-G8"     $T claim "the alpha fact holds here too" --class UNVERIFIED
probe "G:quantifier-ADR007"     $T claim "no calls to foo anywhere in the repo" \
                                  --class VERIFIED --evidence-cmd "grep -c x --include=*.txt f.txt" --paths f.txt
# ORDER-SENSITIVE. Trips G8 (Jaccard 0.833 against the alpha baseline --
# above the 0.6 threshold, which the first draft of this probe missed at
# 0.556) AND ADR-007 (quantifier `anywhere` over an --include-scoped
# command) at once, so the message that returns names whichever gate the
# TABLE put first. Without this pair, swapping two rows in INTAKE_GATES is
# invisible to the fingerprint -- a blind spot only mutation testing found.
probe "G:order-G8-vs-ADR007"    $T claim "the alpha fact holds here anywhere" \
                                  --class VERIFIED --evidence-cmd "grep -c x --include=*.txt f.txt" --paths f.txt
probe "G:inv-m-whitespace"      $T claim "watch shape probe one" --class UNVERIFIED --paths "a.txt b.txt"
probe "G:inv-m-dead-literal"    $T claim "watch shape probe two" --class UNVERIFIED --paths "nope.txt"
probe "G:inv-m-dead-glob"       $T claim "watch shape probe three" --class UNVERIFIED --paths ".git/*"
probe "G:verified-no-cmd"       $T claim "verified shape probe" --class VERIFIED --paths f.txt
probe "G:verified-no-paths"     $T claim "verified shape probe two" --class VERIFIED --evidence-cmd "cat f.txt"
probe "G:inferred-no-basis"     $T claim "inferred shape probe" --class INFERRED
probe "G:screen-unlisted"       $T claim "screen probe one" --class VERIFIED \
                                  --evidence-cmd "curl http://x" --paths f.txt
probe "G:screen-newline"        $T claim "screen probe two" --class VERIFIED \
                                  --evidence-cmd "$(printf 'cat f.txt\ntouch P')" --paths f.txt
probe "G:screen-substitution"   $T claim "screen probe three" --class VERIFIED \
                                  --evidence-cmd 'cat $(echo f.txt)' --paths f.txt
probe "G:screen-redirect"       $T claim "screen probe four" --class VERIFIED \
                                  --evidence-cmd "cat f.txt > out.txt" --paths f.txt
probe "G:exit-gate-ADR035"      $T claim "the marker string is present in f.txt" --class VERIFIED \
                                  --evidence-cmd "grep -c zzz f.txt" --paths f.txt

# ---- the happy path, and the CC-1 advisory block ------------------------
probe "OK:clean-filing"         $T claim "f.txt carries exactly two x lines" --class VERIFIED \
                                  --evidence-cmd "grep -c x f.txt" --paths f.txt
probe "OK:advisory-block"       $T claim "f.txt line numbering probe" --class VERIFIED \
                                  --evidence-cmd "grep -n x f.txt" --paths f.txt --ttl-days 5

# ---- verdict surface ----------------------------------------------------
CID="$($T list --json 2>/dev/null | python3 -c 'import json,sys;d=json.load(sys.stdin);print([r["id"] for r in d if "two x lines" in (r["text"] or "")][0])' 2>/dev/null)"
probe "V:unknown-claim"         $T verdict tr-deadbeef agree --basis b
probe "V:no-basis"              $T verdict "$CID" agree
probe "V:self-agree-ADR010"     $T verdict "$CID" agree --basis "self"
probe "V:mechanical-misuse"     $T verdict "$CID" agree --basis b --mechanical
probe "V:cause-on-agree"        $T verdict "$CID" agree --basis b --cause wrong
probe "V:retract-no-cause"      env TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID" $T verdict "$CID" retracted --basis b
probe "V:retract-no-human"      $T verdict "$CID" retracted --basis b --cause wrong
probe "V:restated-no-successor" env TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID" \
                                  $T verdict "$CID" retracted --basis b --cause restated
probe "V:refresh-on-recheck"    $T verdict "$CID" agree --basis b --refresh-evidence s --recheck

# ---- work kernel --------------------------------------------------------
probe "W:issue-unknown-dep"     $T issue "probe" --deps wk-deadbeef
probe "W:accept-kind-no-cmd"    $T issue "probe two" --accept-kind validation
probe "W:start-unknown"         $T start wk-deadbeef
probe "W:done-no-basis"         $T done wk-deadbeef
probe "W:premise-bad-id"        $T premise wk-x notanid
probe "W:contradicts-self"      $T contradicts "$CID" "$CID" --basis b

# ---- read surface (exit-code contract) ----------------------------------
probe "R:impact-watched"        $T impact f.txt
probe "R:impact-unwatched"      $T impact AGENTS.md
probe "R:impact-inverse-empty"  $T impact --inverse --under nosuchdir
probe "R:citations-bad-id"      $T citations '#'
probe "R:citations-clean"       $T citations "$CID"
# EXIT-CODE branch: the id must actually be cited inside the scope, or only
# the `else 0` arm is ever reached and CITATIONS_EXIT_CITED is untested --
# the second blind spot mutation testing found in this instrument.
echo "cites $CID as ground truth" > docs/specs/cited.md
git add docs/specs/cited.md >/dev/null 2>&1
git commit -qm cite >/dev/null 2>&1
probe "R:citations-cited-exit6"  $T citations "$CID"
probe "V:retract-while-cited"    env TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID" \
                                  $T verdict "$CID" retracted --basis b --cause wrong
probe "R:validate"              $T validate
probe "R:vocab"                 $T vocab
probe "R:staling-empty"         $T staling
# doctor is the installation check and its refusals are a user-facing
# surface like any other. Deterministic here because the sandbox is built
# fresh with no hooks, and the one time-varying field (fold latency, "Nms")
# is collapsed by norm(). Added after a reviewer asked whether its absence
# was scope or oversight -- it was oversight.
probe "R:doctor"                $T doctor
probe "R:doctor-json"           $T doctor --json

# ---- F1.1 reproduction sweep --------------------------------------------
# Added when this series landed on a tree that carries `truth reproduce`.
# This verb needs probing MORE than most, not less: A4 rewrites main() as a
# table including this parser, and A2 splits advisory, from which
# cmd_reproduce takes dirty_watch and parse_porcelain_z. It is the newest
# code in the tree and therefore the code a behaviour-preserving refactor
# is most likely to break without anyone noticing.
#
# The empty sweep goes FIRST, and it is not a filler arm: every verdict
# probe above is a refusal, so nothing in this sandbox has ever been live,
# and exit 8 is ADR-042 rule 2 -- an instrument that examined nothing has
# not passed. That arm is only reachable while the population is empty.
probe "R:reproduce-empty"       $T reproduce
probe "R:reproduce-empty-json"  $T reproduce --json
# Now make exactly one claim live so the arms and exit 0 are reachable too.
# A different session id, because ADR-010's self-agree guard compares
# session strings; the capsule (`grep -c x f.txt` over an unchanged f.txt)
# still reproduces, so ADR-051's coherence gate passes silently. This runs
# AFTER every other probe, so no existing block can move.
TRUTH_SESSION=s-fp-verifier $T verdict "$CID" agree \
  --basis "re-ran the capsule" >/dev/null 2>&1
probe "R:reproduce"             $T reproduce
probe "R:reproduce-json"        $T reproduce --json
probe "R:reproduce-arm"         $T reproduce --arm capsule-stale

echo
echo "# end of fingerprint"
