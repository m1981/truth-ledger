#!/usr/bin/env bash
# Behavioural fingerprint — the acceptance instrument for behaviour-preserving
# refactors (A1 sys.exit, A2 advisory split, A4 verb table).
#
# WHY THIS EXISTS. For a refactor, "the tests pass" is not a proof: the tests
# are the thing an agent can bend to make them pass. ADR-044 got this right —
# its acceptance was the OLD corpus unchanged, and any arm-count delta meant
# the phase had exceeded its licence. This script generalises that: it drives
# the REAL CLI through a NAMED SET of refusal paths and records (exit code,
# stderr, stdout shape) as one canonical file. A behaviour-preserving refactor
# must reproduce it byte for byte.
#
# WHAT IT DOES NOT COVER. This header used to read "every refusal path … every
# intake gate … every non-trivial exit code", and that was false: eight of the
# twenty-three verbs had no probe at all, and a mutation of the tracker refusal
# in shellio.tracker_issues -- converted by a refactor whose own commit message
# certified "the refusal strings are unchanged" AGAINST THIS FILE -- produced
# an empty diff. The instrument now probes all twenty-three verbs, and its
# remaining blind spots are written down, not implied: see "Declared coverage
# limits" in docs/reviews/architecture-repairs-2026-08-13.md. Read that
# section before certifying anything against this file. A limit you can read
# is worth more than a claim of completeness you cannot check.
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
         -e 's/[0-9]+\.[0-9]+ms|[0-9]+ms/<MS>/g' \
         -e 's/(-- )fatal:.*( \(exit 2: usage\))/\1<GIT-ERR>\2/' \
         -e 's/(baseline [^ ]+ )\([0-9a-f]{7,40}\)/\1(<SHORT>)/' \
         -e 's/("commit": ")[0-9a-f]{7,40}(")/\1<SHORT>\2/' \
         -e 's/("anchor_commit": ")[0-9a-f]{40}(")/\1<COMMIT>\2/'
}
# `baseline` prints the ref's ABBREVIATED sha, in the text arm and as
# "commit" in --json; the dispatch envelope prints the claim's full
# anchor_commit. Neither is behaviour.
#
# The rule above them -- s/\b[0-9a-f]{40}\b/<COMMIT>/ -- IS A NO-OP ON THIS
# PLATFORM. BSD sed (macOS) has no \b, so it matches nothing, and the
# committed baseline already carries two RAW 40-hex commit shas (the "head"
# field of `reproduce --json`). It is not a determinism fault: the sandbox
# pins both git dates, so its commit shas are a pure function of its tree.
# But it is a portability trap -- the same instrument normalises those lines
# under GNU sed and does not here, so a baseline generated on Linux and one
# generated on macOS disagree for a reason that has nothing to do with
# truthlib. Repairing it means REWRITING two existing baseline lines, which
# the append-only acceptance for wk-24db9abe forbids; the new rules above
# are therefore keyed to their own fields, so this file adds no third leak.
# Reported, not silently chosen: see the declared coverage limits.
# The last rule collapses GIT's own wording inside the events_at_ref refusal
# (`truth: cannot read <ledger> at <ref> -- fatal: … (exit 2: usage)`). git
# has reworded "invalid object name" and "exists on disk, but not in" across
# releases, so leaving it raw would make the committed baseline a fingerprint
# of the reviewer's git version, and every reprove on a different machine
# would read DIFFERS for a reason that is not the code under test. The COST
# is declared: a change to how truthlib interpolates git's stderr into that
# line is invisible here. The prefix, the ref, and exit 2 are still pinned.

# Ids are sha256(payload, ts, actor), so a moving clock makes every id --
# and therefore every id-ordered listing -- vary between runs. Pinning the
# clock per probe makes the id a pure function of the payload, which is what
# a fingerprint needs. TRUTH_NOW also disables the ADR-015 clock-push; that
# is fine here and is the hook's documented purpose.
FP_N=0
# Per-RUN stderr spool, not a fixed /tmp/fp.err. Two fingerprints running at
# once -- the ordinary shape of "diff before.txt after.txt", and of any agent
# fleet -- both wrote that one path, so each probe could read back the OTHER
# run's stderr. The failure is silent and looks like a behaviour change: a
# verifier who ran the two sides in parallel got a diff full of refusals
# attached to the wrong labels and started hunting a bug in truthlib. $D is
# already a per-run mktemp -d, but it is the sandbox git repo, and a stray
# file there would show up in `git status`, tracked_files() and the --inverse
# probe. So the spool gets its own mktemp OUTSIDE the sandbox, cleaned by the
# same trap.
ERR="$(mktemp)"; trap 'cd /; rm -rf "$D"; rm -f "$ERR"' EXIT
probe() {  # probe "<label>" <argv...>
  local label="$1"; shift
  local out err rc
  FP_N=$((FP_N + 1))
  export TRUTH_NOW="$(printf '2026-01-01T00:%02d:%02d.000000+00:00' \
                      $((FP_N / 60)) $((FP_N % 60)))"
  out="$("$@" 2>"$ERR")"; rc=$?
  err="$(cat "$ERR")"
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

# =========================================================================
# The nine verbs that had no probe (wk-24db9abe)
# =========================================================================
# An adversary pass counted the subparsers in cli.main() against the labels
# above and found NINE verbs driven by nothing: ready, baseline, dispatch,
# stats, queue, issues, invalidate-scan, reaffirm -- and `list`, which the
# CID extraction above merely USES (a break in it empties $CID and garbles
# the verdict block, but its own output was never recorded). Everything from
# here down closes that, refusals and exit codes first.
#
# EVERYTHING IS APPENDED. Several of these verbs need ledger or git state
# that does not exist above -- a stale claim for `reaffirm`, a commit
# touching a watched path for `invalidate-scan`, a committed ledger for
# `baseline`. Building that state earlier would move every probe below it
# and turn the acceptance diff into noise, so the state is built HERE, after
# the last pre-existing probe, and each block says what it changed.

# ---- ready: the tracker adapter seam (E1) -------------------------------
# TRUTH_TRACKER_CMD is set EXPLICITLY on every arm. The default source is
# `bd ready --json`, and on a machine that has Beads installed this verb
# would report that machine's tracker -- the instrument would fingerprint
# the reviewer's laptop, not the code. (Observed: the default path exits 1
# here and 127 on a clean machine.)
#
# The first row is the one this whole brief was written for. A refactor
# moved this refusal into shellio.tracker_issues and its commit certified
# "the refusal strings are unchanged" against this instrument -- which at
# that moment did not execute the line at all.
probe "RD:tracker-failed"       env TRUTH_TRACKER_CMD='exit 7' $T ready
probe "RD:tracker-not-json"     env TRUTH_TRACKER_CMD='printf not-json' $T ready
probe "RD:tracker-not-array"    env TRUTH_TRACKER_CMD='printf {}' $T ready
# --stdin renames the source in the same two refusals ('stdin', not the
# command repr): the branch a tracker-agnostic contract must keep.
probe "RD:stdin-not-json"       bash -c "printf nope | $T ready --stdin"
probe "RD:stdin-not-array"      bash -c "printf '{}' | $T ready --stdin"

# ---- dispatch: the G11 verifier envelope --------------------------------
probe "D:unknown-claim"         $T dispatch tr-deadbeef
# The sandbox has no prompts/truth-verifier.md yet, so this is the
# missing-prompt refusal, not the envelope.
probe "D:prompt-missing"        $T dispatch "$CID"
# Now install a prompt and take the envelope itself. Its integrity header
# counts the numbered rules and pins the prompt hash -- a guard against
# lossy context trimming, and therefore a contract, not decoration. Three
# rules on purpose: the count is in the header, so a rule silently dropped
# in transit is a visible number here.
mkdir -p prompts
cat > prompts/truth-verifier.md <<'PROMPT'
---
title: fingerprint sandbox verifier prompt
---
Verify the claim below.

1. Re-run the evidence command yourself.
2. Compare its output against the claim's sentence.
3. File agree, diverge, or cannot_verify with a basis.
PROMPT
probe "D:envelope"              $T dispatch "$CID"

# ---- list: the fold's own tabular surface -------------------------------
probe "L:list"                  $T list
probe "L:list-json"             $T list --json
probe "L:list-filtered"         $T list --live

# ---- issues / ready: the work kernel and the E1 join --------------------
# One real issue, premised on the live claim, so `issues` has a row and
# `ready` can reach its native source (ADR-002 precedence: no
# TRUTH_TRACKER_CMD, issue records exist -> native).
probe "I:issue-filed"           $T issue "carry a premised work item" --premise "$CID"
probe "I:issues"                $T issues
probe "I:issues-json"           $T issues --json
probe "I:issues-ready-json"     $T issues --ready-json
probe "RD:ready-native"         $T ready
probe "RD:ready-json"           $T ready --json
# The E1 contract as its own docstring states it: the kernel's --ready-json
# piped into --stdin must join to the same answer as the native path.
probe "RD:ready-stdin-join"     bash -c "$T issues --ready-json | $T ready --stdin"

# ---- ADR-037: the generated-artifact refusal, made REACHABLE ------------
# Until now .truth/generated-paths was committed EMPTY, and SI-4 reads a
# committed-empty list as the consumer consciously saying "nothing here is
# generated" -- so load_generated_globs returns source='empty',
# _gate_generated returns None before it ever builds `hits`, and the whole
# gate was dead code from this instrument's point of view. A one-word
# mutation of its refusal produced an EMPTY diff. The list gets real
# content from here on; every probe below picks paths accordingly.
mkdir -p gen
printf 'built artifact\n' > gen/out.txt
printf 'gen/**\n' > .truth/generated-paths
git add -A >/dev/null; git commit -qm "generated list, armed" >/dev/null
probe "G:generated-ADR037"      $T claim "the built file under gen is watched" \
                                  --class UNVERIFIED --paths "gen/out.txt"
probe "G:generated-ok"          $T claim "regeneration output stands as its own fact" \
                                  --class UNVERIFIED --paths "gen/out.txt" \
                                  --generated-ok "the artifact itself is what this sentence is about"
# R14a: the loader RETURNS its pathspec-magic refusal and this gate hands it
# on unchanged -- a different refusal from the same row, and the only one
# that fires before `hits` is computed.
printf ':(glob)gen/**\n' > .truth/generated-paths
probe "G:generated-magic-SI1"   $T claim "pathspec syntax has no place in that list" \
                                  --class UNVERIFIED --paths "gen/out.txt"
printf 'gen/**\n' > .truth/generated-paths

# ---- invalidate-scan and reaffirm: the staling round --------------------
# Touch the watched file WITHOUT changing what the evidence command reports
# (`grep -c x f.txt` counts x-lines; a y-line moves the commit, not the
# count). That is precisely ADR-030's case: the path-touched rule stales the
# claim, and the re-run says the fact never moved.
printf 'x\nx\ny\n' > f.txt
git add -A >/dev/null; git commit -qm "touch a watched path" >/dev/null
probe "S:invalidate-scan"       $T invalidate-scan
# Idempotence is the property that matters here: a stale claim is out of
# ACTIVE_STATUSES, so a second scan must mark nothing and file nothing.
probe "S:invalidate-scan-again" $T invalidate-scan
probe "S:invalidate-scan-quiet" $T invalidate-scan --quiet
# Default session = the authoring session, so ADR-010 must refuse the whole
# sweep: a batch verb may not self-agree either.
probe "RA:reaffirm-same-session" $T reaffirm
probe "RA:reaffirm-dry-json"    env TRUTH_SESSION=s-fp-verifier $T reaffirm --dry-run --json
probe "RA:reaffirm-dry"         env TRUTH_SESSION=s-fp-verifier $T reaffirm --dry-run
# F4: one env var turns the per-claim independence seam off for a whole
# sweep, and the count it let through is the loudness.
probe "RA:reaffirm-self-verdict" env TRUTH_SELF_VERDICT=1 $T reaffirm --dry-run
# For real this time: the hash-match arm is the only one that FILES.
probe "RA:reaffirm-match"       env TRUTH_SESSION=s-fp-verifier $T reaffirm

# ---- the mismatch arm, and a P0 in the queue ----------------------------
# A second claim, tier P0, over a file whose CONTENT the evidence reads --
# so touching it changes the digest and reaffirm must file NOTHING and hand
# the claim to dispatch (ADR-012: a batch verb has no judgment).
printf 'a\nb\nc\n' > g.txt
git add -A >/dev/null; git commit -qm "add the second watched file" >/dev/null
# BOTH of these are probes, not silent setup, and the reason is a trap worth
# writing down. TRUTH_NOW only advances inside probe(), so two ledger writes
# issued as plain setup share one timestamp -- and the fold orders by
# (ts, id, canon), so an agree can sort BEFORE the claim it agrees with and
# be dropped as a verdict on a claim that does not exist yet. Written the
# silent way first, this claim stayed `unverified` for the rest of the run,
# `reproduce` saw one live claim instead of two, and the exit-7 probe below
# reported exit 0 -- a green arm that was measuring nothing. As probes they
# get distinct timestamps, and the successful `claim` and `agree` echoes get
# pinned into the bargain: everything else in this file files a refusal.
probe "OK:claim-P0"             $T claim "g.txt holds the first three letters" \
                                  --class VERIFIED --tier P0 \
                                  --evidence-cmd "cat g.txt" --paths g.txt
CID2="$($T list --json 2>/dev/null | python3 -c 'import json,sys;d=json.load(sys.stdin);print([r["id"] for r in d if "first three letters" in (r["text"] or "")][0])' 2>/dev/null)"
probe "V:agree-goes-live"       env TRUTH_SESSION=s-fp-verifier $T verdict "$CID2" agree \
                                  --basis "re-read the file myself"
printf 'a\nb\nc\nd\n' > g.txt
git add -A >/dev/null; git commit -qm "change what the evidence reads" >/dev/null
# ---- the two exit codes nothing above reached --------------------------
# Counted from the baseline: exits 0,1,2,3,5,6,8 appeared; 4 and 7 did not,
# while §0 of the review claimed "every non-trivial exit code". Both are
# reachable only in a window this sweep happens to open, and only here.
#
# 7 = a LIVE claim whose capsule no longer reproduces. The P0 claim is still
# live for exactly one more probe -- the scan below stales it, and `reproduce`
# examines live claims only, so after that line this arm is out of reach.
probe "R:reproduce-exit7"       $T reproduce
# 4 = tracked files no active claim watches. docs/specs/* is watched by
# nothing in this sandbox and never has been.
probe "R:impact-inverse-dark"   $T impact --inverse --under docs
probe "S:invalidate-scan-P0"    $T invalidate-scan
probe "RA:reaffirm-mismatch"    env TRUTH_SESSION=s-fp-verifier $T reaffirm --dry-run
# queue is the human-review surface: a stale P0 belongs in it, and until now
# only its empty arm existed anywhere.
probe "Q:queue"                 $T queue
probe "Q:queue-json"            $T queue --json
# A stale premise breaks readiness: the HELD arm of the ready join (ADR-001).
# It needs its own issue -- the first one's premise was reaffirmed back to
# live two blocks up, which is the whole point of that verb.
probe "I:issue-on-stale-premise" $T issue "stand a second item on the stale premise" \
                                  --premise "$CID2"
probe "RD:ready-held"           $T ready
probe "RD:ready-held-json"      $T ready --json

# ---- stats: the FS-1 metric surface -------------------------------------
probe "T:stats"                 $T stats
probe "T:stats-json"            $T stats --json
# The --since window over a range containing NOTHING. Deliberately a future
# timestamp rather than one that splits this run's events: a mid-run cut
# would depend on how many probes ran before it, so appending a probe later
# would silently rewrite these lines and destroy the append-only property
# the next brief needs. The cost is declared: the partially-filtered window
# is not pinned.
probe "T:stats-since-empty"     $T stats --since 2027-01-01T00:00:00+00:00

# ---- baseline: fold at a ref, and the rewritten-history exit ------------
# Unreadable ref -> exit 2. git's own wording is collapsed by norm(); the
# prefix, the ref and the exit code are what this row pins.
probe "B:unreadable-ref"        $T baseline nosuchref
probe "B:unreadable-ref-diff"   $T baseline HEAD --diff nosuchref
# The ledger has been tracked since the first `git add -A` above, so these
# two tags differ by exactly one claim.
git tag fp-a
$T claim "a late note lands after the snapshot" --class UNVERIFIED >/dev/null 2>&1
git add -A >/dev/null; git commit -qm "one more record" >/dev/null
git tag fp-b
probe "B:baseline"              $T baseline fp-a
probe "B:baseline-json"         $T baseline fp-a --json
probe "B:baseline-diff"         $T baseline fp-a --diff fp-b
# Exit 5, the 10007 omission: a record PRESENT at the older ref is gone at
# the newer one. The only way to produce it is to rewrite the append-only
# file, which is what this does -- deliberately, in the sandbox, in the last
# block of the run, so nothing downstream reads the mutilated ledger.
python3 - <<'REWRITE'
p = ".truth/claims.jsonl"
lines = [l for l in open(p).read().splitlines()
         if "a late note lands after the snapshot" not in l]
open(p, "w").write("\n".join(lines) + "\n")
REWRITE
git add -A >/dev/null; git commit -qm "rewrite history (10007 omission)" >/dev/null
git tag fp-c
probe "B:baseline-disappeared"  $T baseline fp-b --diff fp-c

echo
echo "# end of fingerprint"
