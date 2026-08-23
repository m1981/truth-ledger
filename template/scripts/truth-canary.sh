#!/usr/bin/env bash
# truth-canary.sh v0.9.0 -- seeded-fault acceptance suite (v0.9.0 issue #4 C1-C5 contradicts/DISPUTED + SC session-close survival gate + v0.7.1 issue #5 W5-W8 impact --inverse + v0.7.0 ADR-014 AC1-AC7 acceptance oracles + v0.6.4 ADR-013 R10 premise supersede +seeded faults + TL hardening + adapter seam + bd normalization + ADR-002 work kernel + ADR-006 issue-fold hardening + INV-M dead-tripwire intake checks + ADR-005 impact verb + spec-health/doc-health incl. degradation paths + v0.6 solo-regime hardening: ADR-007 Q-faults, ADR-008 B-faults, ADR-009 E-faults, ADR-010 V-faults, ADR-011 H-faults, ADR-012 M1 + v0.6.2 review-finding faults: F1 arg-deny E5, F2 ts-evasion B3/B4, F3 scope-signal Q5/Q6 + v0.6.3 TL-2 work-kernel discovery warn + ADR-023 H5 FAULT T dormant-glob-materializes arm + ADR-024 FAULT T unreachable-glob-refused arm + ADR-025 FAULT DG doctor-decides-hook-or-CI + ADR-027 FAULT AN1-AN5 anchor_commit/commit git-SHA-prefix floor + ADR-028 FAULT IF future-dated-issue transition coherence + ADR-009/M4 FAULT SD screen-gates-execution ordering + v0.9.12 R3/ADR-030 FAULT RA reaffirm-mismatch-never-auto-filed + v0.9.13 R6/ADR-031 unified duplicate-id rule: B1/B3-B5 expect the one message, FAULT K2 later-ts distinct duplicate flips to refused + v0.9.14 R12/ADR-032 FAULT SD-decay --scope-ok default-expiry (4 arms incl. negative control) + R13/ADR-033 FAULT OV override-velocity verbatim-repeat advisory (2 arms incl. negative control) + v0.9.20/ADR-034 FAULT GS staged gate table + CC-1 advisory block (5 arms incl. negative control) + v0.9.21/ADR-035 FAULT X positive-claim exit gate (8 arms incl. negative control + validate mirror) + v0.9.22/ADR-036 FAULT TG tombstone citation gate (11 arms incl. scope policy, fail-closed, preflight, unicode quotepath) + v0.9.23/ADR-037 FAULT RC recipe lints + generated-paths (10 arms incl. per-segment, carve-outs, decay, quote-split, dropped-override) + v0.9.24/ADR-038 FAULT DW dirty-watch advisory (7 arms incl. untracked-under-glob, rename, unicode, UU-conflict) + v0.9.25/ADR-039 FAULT BF blast forecast + churn report (7 arms incl. window boundary, shallow, unborn-HEAD) + ADR-010 FAULT SEP separation instrument (3 arms incl. negative control) + P1 review R1 FAULT S2D disputed-citer spec fails + R3 SC dead-sensor scream and claimed-count false-match immunity + L3-F7 FAULT GE check-truth environment lane (2 arms incl. negative control) + v0.9.27 P2 contract layer: FAULT VC vocab-verb contract (2 arms) + GS6 done --claim --json advisory echo + v0.9.29/ADR-045 FAULT LK ledger-lock two-process serialization (2 arms) + FAULT UM5-UM7 pre-merge-commit merge gate (installer-driven; honest sync passes, tampered merge refused) + doctor pre-merge-commit WARN/quiet/CI-exempt arms (3) + v0.9.30/ADR-046 tiering (D4): FAULT SEP (3 arms) and FAULT OV's two stats arms RETIRED -- the separation and override-velocity stats sections left the template CLI for Tier C instruments, and the arms moved to the meta-repo gate scripts/test-instruments.sh; BF5 RETIRED there too (stats blast section render); BF4 FLIPPED to assert blast_forecast is NOT stored while the BF1 advisory still voices from the live computation (BF 7->6 arms); the concerns surface had no canary arms -- its retired core-suite arms are named in ADR-046).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PASS=0; FAIL=0
say()  { printf '%s\n' "$*"; }
ok()   { PASS=$((PASS+1)); say "  CAUGHT: $*"; }
miss() { FAIL=$((FAIL+1)); say "  MISSED: $*"; }

TMP1="$(mktemp -d)"; TMP2="$(mktemp -d)"; TMP3="$(mktemp -d)"; TMP4="$(mktemp -d)"; TMP5="$(mktemp -d)"
# Every later per-arm mktemp -d appends itself to TDIRS so the EXIT trap
# is the backstop when an arm dies before its own rm -rf line (which each
# arm keeps -- belt and braces). ${TDIRS+...} keeps set -u happy on an
# empty array under macOS bash 3.2.
TDIRS=()
cleanup() { rm -rf "$TMP1" "$TMP2" "$TMP3" "$TMP4" "$TMP5" ${TDIRS+"${TDIRS[@]}"}; }
trap cleanup EXIT

mkrepo() {
  # The ADR-005 lesson, applied to the canary itself. On 2026-08-20 21:48 a
  # battery run whose cwd was a LINKED WORKTREE escaped this sandbox: the
  # bare `cd` below failed, and under `set -u` with NO `set -e` the `git
  # init` ran wherever the shell happened to be standing -- writing fixture
  # commits onto the shared repository's main, six fixture branches, a
  # repointed branch ref and core.bare=true. AGENTS.md answered with a NORM
  # ("never run the canary from a linked worktree"), and this project's own
  # trial (RUNBOOK, S2-ext) is the evidence that norms alone do not hold.
  # So the guard is mechanical: enter the sandbox or die, and refuse
  # outright to `git init` inside a repository the canary does not own.
  cd "$1" || { echo "canary: cannot enter sandbox '$1' -- refusing to run" >&2; exit 1; }
  if owner=$(git rev-parse --show-toplevel 2>/dev/null); then
    echo "canary: sandbox '$PWD' is INSIDE an existing git repository ($owner)." >&2
    echo "  Refusing: this suite writes commits, branches, refs and git config," >&2
    echo "  and from here every one of those would land on a repository it does" >&2
    echo "  not own (measured incident: 2026-08-20 21:48, see AGENTS.md)." >&2
    exit 1
  fi
  git init -q -b main .
  git config user.email canary@truth.local
  git config user.name  truth-canary
  mkdir -p scripts .truth prompts
  touch .truth/claims.jsonl
  cp "$HERE/truth" scripts/truth
  cp -R "$HERE/../truthlib" truthlib  # ADR-044: the entry resolves ../truthlib from its own real path
  cp "$HERE/../.truth/evidence-allow" .truth/evidence-allow
  cp "$HERE/../.truth/evidence-deny" .truth/evidence-deny  # ADR-022 baseline
  cp "$HERE/../.truth/generated-paths" .truth/generated-paths  # ADR-037 (empty=silent)
  # F3.1: the sandbox is a CONSUMER, and a consumer with an empty policy
  # file must attest it or doctor fails. The template ships the file
  # unattested on purpose (an inherited attestation records nothing), so
  # every sandbox makes the statement itself -- which is also what keeps
  # the FAULT PA arms below honest: they mutate this line, not a default.
  printf '# attested 2026-01-01: the canary sandbox generates nothing\n' \
    >> .truth/generated-paths
  cp "$HERE/check-truth.sh" scripts/check-truth.sh
  cp "$HERE/spec-health.sh" scripts/spec-health.sh
  cp "$HERE/doc-health.sh" scripts/doc-health.sh
  cp "$HERE/session-close.sh" scripts/session-close.sh
  chmod +x scripts/truth scripts/check-truth.sh scripts/spec-health.sh scripts/doc-health.sh scripts/session-close.sh
}
T="python3 scripts/truth"
export TRUTH_ACTOR=canary TRUTH_SESSION=s-canary

# ======================================================= sandbox 1 (main)
mkrepo "$TMP1"
echo "hello" > watched.txt
echo "v1"    > fabricated.txt
printf 'verifier header\n---\nVERIFIER BODY\n\n1. RULE ONE.\n2. RULE TWO.\n' > prompts/truth-verifier.md
git add -A && git commit -qm "canary: init"

say "DOCTOR (G4): must FAIL on an unwired repo, PASS after wiring"
if $T doctor >/dev/null 2>&1; then
  miss "doctor passed a repo with no hooks, no gitattributes, no discovery"
else
  ok "doctor failed the unwired repo"
fi
echo ".truth/claims.jsonl merge=union" >> .gitattributes
printf '#!/usr/bin/env bash\nexec bash scripts/check-truth.sh\n' > .git/hooks/pre-commit
# Step 2.6: doctor's second row is reproduce-on-read at pre-push, not the
# retired invalidate-scan at post-merge. post-merge stays, deliberately
# inert, exactly as install-hooks.sh writes it.
printf '#!/usr/bin/env bash\nexit 0\n' > .git/hooks/post-merge
printf '#!/usr/bin/env bash\nexec python3 scripts/truth reproduce\n' > .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/post-merge .git/hooks/pre-push
printf '# Agents\nTruth ledger: use scripts/truth (see .truth/README.md)\n' > AGENTS.md
git add -A && git commit -qm "canary: wire installation" --no-verify
if $T doctor >/dev/null 2>&1; then
  ok "doctor passed the wired repo"
else
  miss "doctor failed a correctly wired repo"; $T doctor || true
fi
# ADR-045 (D3): git runs pre-merge-commit, never pre-commit, when a merge
# auto-commits -- so a locally gated repo without the third hook lands
# union-merged ledgers ungated. Doctor must WARN (adoption-gated, never
# FAIL: pre-v0.9.29 installs lack it blamelessly) and go quiet once the
# hook is installed.
DOC_PMC="$($T doctor 2>&1)"
if printf '%s\n' "$DOC_PMC" | grep -q "WARN  pre-merge-commit hook gates merge commits"; then
  ok "doctor WARNs: pre-commit wired but pre-merge-commit absent (merge commits ungated, ADR-045)"
else
  miss "doctor stayed silent on a locally gated repo missing pre-merge-commit (ADR-045)"
fi
printf '#!/usr/bin/env bash\nexec bash scripts/check-truth.sh\n' > .git/hooks/pre-merge-commit
chmod +x .git/hooks/pre-merge-commit
DOC_PMC="$($T doctor 2>&1)"
if printf '%s\n' "$DOC_PMC" | grep -q "OK    pre-merge-commit hook gates merge commits" \
   && ! printf '%s\n' "$DOC_PMC" | grep -q "WARN  pre-merge-commit"; then
  ok "doctor quiet (OK line) once pre-merge-commit is installed"
else
  miss "doctor still warns, or reports no OK, after pre-merge-commit was installed"
fi
# TL-1: hooks live where core.hooksPath says; .git/hooks wiring must not count
git config core.hooksPath .hookmgr/_
mkdir -p .hookmgr/_
if $T doctor >/dev/null 2>&1; then
  miss "doctor trusted .git/hooks while core.hooksPath points elsewhere"
else
  ok "doctor failed when core.hooksPath bypasses the wired hooks"
fi
# husky-style delegation: user hooks one level above the `_` shim dir, no +x
printf '#!/usr/bin/env sh\nbash scripts/check-truth.sh || exit 1\n' > .hookmgr/pre-commit
printf '#!/usr/bin/env sh\nexit 0\n' > .hookmgr/post-merge
printf '#!/usr/bin/env sh\npython3 scripts/truth reproduce\n' > .hookmgr/pre-push
if $T doctor >/dev/null 2>&1; then
  ok "doctor passed hook-manager wiring (hooksPath + _ delegation)"
else
  miss "doctor failed a correctly wired hook-manager repo"; $T doctor || true
fi
git config --unset core.hooksPath

# ADR-025 (H6): doctor decides BOTH arms of the "a hook OR CI MUST exist"
# gate. A CI config that names the gate script passes; neither hook nor CI
# fails. Isolated sub-repo so the main sandbox's wiring is untouched.
say "FAULT DG (ADR-025): doctor decides the commit gate via CI when no hook exists"
DG="$(mktemp -d)"; TDIRS+=("$DG")
mkrepo "$DG"   # NB: mkrepo cd's into $DG. No subshell -- ok/miss mutate the
               # PASS/FAIL counters and a subshell would discard them (a
               # miss here would be invisible). Restore cwd with cd below.
echo ".truth/claims.jsonl merge=union" >> .gitattributes
printf '# Agents\nUse scripts/truth (see .truth/README.md)\n' > AGENTS.md
git add -A && git commit -qm "dg: minimal repo, no hooks, no CI" --no-verify -q
DGOUT="$($T doctor 2>&1)"; DGRC=$?
if [ "$DGRC" -ne 0 ] \
   && printf '%s\n' "$DGOUT" | grep -q "FAIL  pre-commit hook enforces INV-A/INV-B"; then
  ok "doctor FAILs the gate (exit 1) with neither hook nor CI"
else
  miss "doctor did not fail the gate on a repo with no hook and no CI"
fi
# `doctor --json` is the SAME run rendered as one object (the contract
# layer's machine surface): the exit contract is unchanged, the missing
# gate is named in fail[], and the counts are the lists' lengths.
DGJ="$($T doctor --json 2>&1)"; DGJRC=$?
if [ "$DGJRC" -eq 1 ] && printf '%s' "$DGJ" | python3 -c '
import json, sys
d = json.load(sys.stdin)
assert set(d) == {"ok", "warn", "fail", "failures", "warnings"}, sorted(d)
assert all(set(e) == {"check", "detail"}
           for lvl in ("ok", "warn", "fail") for e in d[lvl]), d
assert d["failures"] == len(d["fail"]), d
assert d["warnings"] == len(d["warn"]), d
assert "pre-commit hook enforces INV-A/INV-B" in [e["check"] for e in d["fail"]], d["fail"]
'; then
  ok "doctor --json emits the structured report (fail[] names the missing gate) at the unchanged exit 1"
else
  miss "doctor --json did not parse as the contract object, or lost the exit-1 contract"
fi
# and the flag changes REPORTING only: with --json ABSENT the render is
# the pre-existing text, pinned literally (NOT by re-running doctor and
# comparing it to itself -- that compares one binary to the same binary
# and would pass any leak present in both runs). Every line is an
# OK/FAIL/WARN line, a blank, or the summary; the summary agrees with
# the JSON counts; no JSON leaks in.
DGTXT="$($T doctor 2>&1)"; DGTRC=$?
DGSUM="$(printf '%s' "$DGJ" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("doctor: %d failure(s), %d warning(s)" % (d["failures"], d["warnings"]))')"
if [ "$DGTRC" -eq 1 ] \
   && [ "$(printf '%s\n' "$DGTXT" | tail -1)" = "$DGSUM" ] \
   && printf '%s\n' "$DGTXT" | grep -q '^FAIL  pre-commit hook enforces INV-A/INV-B -- ' \
   && ! printf '%s\n' "$DGTXT" | grep -q '"check"' \
   && [ "$(printf '%s\n' "$DGTXT" | grep -cvE '^(OK    |FAIL  |WARN  |doctor: |$)')" -eq 0 ]; then
  ok "plain doctor renders the unchanged text (OK/FAIL/WARN + summary agreeing with the JSON counts), no JSON leak"
else
  miss "plain doctor output changed when the --json surface was added"
fi
# a workflow in a SUBDIR must NOT satisfy the gate (GitHub never runs it)
mkdir -p .github/workflows/disabled
printf 'jobs:\n  g:\n    steps: [{run: bash scripts/check-truth.sh}]\n' > .github/workflows/disabled/x.yml
git add -A && git commit -qm "dg: workflow in a subdir (not run by CI)" --no-verify -q
DGOUT="$($T doctor 2>&1)"; DGRC=$?
if [ "$DGRC" -ne 0 ] && printf '%s\n' "$DGOUT" | grep -q "FAIL  pre-commit hook"; then
  ok "doctor still FAILs -- a subdir workflow is not the gate (ADR-025 top-level only)"
else
  miss "doctor accepted a workflow CI never runs (subdir false pass, ADR-025 regression)"
fi
rm -rf .github/workflows/disabled
# a TOP-LEVEL workflow naming BOTH gate scripts must pass BOTH arms, exit 0
printf 'jobs:\n  gate:\n    steps:\n      - run: bash scripts/check-truth.sh\n      - run: python scripts/truth reproduce\n' > .github/workflows/truth.yml
git add -A && git commit -qm "dg: top-level CI names both gate scripts" --no-verify -q
DGOUT="$($T doctor 2>&1)"; DGRC=$?
if [ "$DGRC" -eq 0 ] \
   && printf '%s\n' "$DGOUT" | grep -q "enforces INV-A/INV-B via CI" \
   && printf '%s\n' "$DGOUT" | grep -q "enforces reproduce-on-read (INV-C successor) via CI"; then
  ok "doctor PASSes BOTH gate arms via a CI config naming check-truth and reproduce"
else
  miss "doctor did not accept the CI-named gate on both arms at exit 0 (ADR-025 regression)"
fi
# ADR-045: a CI-arm repo (no LOCAL pre-commit hook) is exempt from the
# pre-merge-commit warn -- its gate runs server-side on push/PR, where a
# merge commit arrives like any other.
if printf '%s\n' "$DGOUT" | grep -q "pre-merge-commit"; then
  miss "CI-arm repo got the pre-merge-commit line -- the exemption regressed (ADR-045)"
else
  ok "CI-arm repo exempt from the pre-merge-commit warn (gate runs server-side)"
fi
# a directory named after a hook must not crash doctor (it must report)
rm -f .github/workflows/truth.yml; mkdir -p .git/hooks/pre-commit
if $T doctor >/dev/null 2>&1; then :; else :; fi   # must not traceback
if $T doctor 2>&1 | grep -q "Traceback"; then
  miss "doctor tracebacked on a directory named pre-commit (ADR-025 hardening regression)"
else
  ok "doctor reports (no traceback) when a hook path is a directory"
fi
rmdir .git/hooks/pre-commit
cd "$TMP1" || { echo "canary: cannot cd into $TMP1 -- refusing to continue" >&2; exit 1; }
rm -rf "$DG"

# FAULT B FLIPPED (refactor step 2.5). Its subject -- "a commit touching a
# watched path stales the claim" -- was retired with the path invalidator:
# measured on this ledger, the proxy fired 1997 times for 71 judged
# divergences (PPV 3.6%). The arm is kept and INVERTED rather than deleted,
# because the removal needs a pin as much as the behaviour did: the same
# fixture, the opposite expectation. `truth reproduce` now answers the
# question this used to guess at, and FAULT C / the RP family cover it.
say "FAULT B (step 2.5): a commit touching evidence paths must NOT stale the claim"
CID_B=$($T claim "watched.txt says hello" --class VERIFIED \
        --evidence-cmd "cat watched.txt" --paths "watched.txt" --tier P0)
# ADR-010: agree verdicts come from a verifier session, never the author's
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_B" agree --basis "canary: verified at filing" >/dev/null
git add .truth/claims.jsonl && git commit -qm "canary: claim B" --no-verify
echo "changed" >> watched.txt
git add watched.txt && git commit -qm "canary: mutate evidence" --no-verify
$T ttl-scan --quiet
if $T list --stale --json | grep -q "$CID_B"; then
  miss "claim $CID_B was staled by a mere path touch -- the retired path invalidator is back"
elif $T list --live --json | grep -q "$CID_B"; then
  ok "claim $CID_B stays live after a watched path moved (the proxy is gone)"
else
  miss "claim $CID_B left live for a reason that is neither stale nor live"
fi
# CID_B used to be this sandbox's DEAD claim -- four later arms (S2
# spec-health, FAULT J, FAULT R3, the duplicate-id premise-strip check)
# borrowed its staleness. It stays live now, so the sandbox gets one
# deliberately dead claim instead. `diverged` is the ungated dead state
# (ADR-017 gates only retraction) and the ADR-001 premise matrix treats it
# exactly as it treated `stale`. Note it is also ACTIVE-set relevant: a
# live CID_B now participates in the ADR-018 near-duplicate gate, which is
# why the fixtures below carry deliberately distinct sentences.
CID_DEAD=$($T claim "the canary corpus records a superseded measurement" \
           --class UNVERIFIED --tier P1)
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_DEAD" agree --basis "canary: verified at filing" >/dev/null
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_DEAD" diverge --basis "canary: the measurement moved" >/dev/null

say "FAULT C (T1): recheck must diverge when reality no longer matches"
CID_C=$($T claim "fabricated.txt says v1" --class VERIFIED \
        --evidence-cmd "cat fabricated.txt" --paths "fabricated.txt" --tier P1)
echo "v2" > fabricated.txt
if $T verdict "$CID_C" --recheck | grep -q diverge; then
  ok "recheck flagged hash mismatch on $CID_C"
else
  miss "recheck accepted stale evidence on $CID_C"
fi

say "FAULT O (TL-4): recheck with matching hash must report, not file"
echo hello > intact.txt
git add intact.txt   # INV-M (v0.5.4): a literal --paths entry must be tracked at filing time
CID_O=$($T claim "the intact fixture file carries an unchanged greeting" \
        --class VERIFIED \
        --evidence-cmd "cat intact.txt" --paths "intact.txt" --tier P1)
N_BEFORE=$(grep -c "" .truth/claims.jsonl)
$T verdict "$CID_O" --recheck >/dev/null
N_AFTER=$(grep -c "" .truth/claims.jsonl)
if [ "$N_AFTER" -eq "$N_BEFORE" ] && $T list --unverified | grep -q "$CID_O"; then
  ok "matching recheck filed nothing; $CID_O still awaits a judged verdict"
else
  miss "recheck auto-filed a verdict on matching evidence (verifier pre-committed)"
fi

say "FAULT P (TL-3): dispatch must self-describe integrity (rule count + prompt hash)"
DISPATCH=$($T dispatch "$CID_O")
STATED=$(printf '%s\n' "$DISPATCH" | sed -n 's/.*contains \([0-9][0-9]*\) numbered rules.*/\1/p' | head -1)
ACTUAL=$(printf '%s\n' "$DISPATCH" | grep -Ec '^[0-9]+\. ')
TERM_HASH=$(printf '%s\n' "$DISPATCH" | sed -n 's/^END-OF-DISPATCH sha256:\(.*\)$/\1/p')
FILE_HASH=$(python3 -c "import hashlib;print(hashlib.sha256(open('prompts/truth-verifier.md','rb').read()).hexdigest())")
if [ -n "$STATED" ] && [ "$STATED" -eq "$ACTUAL" ] && [ "$TERM_HASH" = "$FILE_HASH" ]; then
  ok "dispatch states $STATED rules (matches actual) and terminator hash matches prompt file"
else
  miss "dispatch self-description broken: stated=$STATED actual=$ACTUAL termhash=${TERM_HASH:-absent}"
fi

say "FAULT Q (TL-5): records must carry a real session id, never s-unknown"
CID_QS=$(TRUTH_SESSION="" $T claim "session fallback probe" --class UNVERIFIED --tier P2)
if [ -z "$CID_QS" ] || ! grep -q "$CID_QS" .truth/claims.jsonl; then
  miss "fault injection failed: session-fallback claim was never filed (tail -1 would read the PREVIOUS record)"
else
  LAST_SESSION=$(tail -1 .truth/claims.jsonl | python3 -c "import json,sys;print(json.load(sys.stdin)['session'])")
  if [ "$LAST_SESSION" != "s-unknown" ] && [ -n "$LAST_SESSION" ]; then
    ok "unset TRUTH_SESSION falls back to a derived id ($LAST_SESSION)"
  else
    miss "record filed with session '$LAST_SESSION'"
  fi
fi
TRUTH_SESSION=s-custom-probe $T claim "session override probe" --class UNVERIFIED --tier P2 --duplicate-ok >/dev/null
if tail -1 .truth/claims.jsonl | grep -q '"session": "s-custom-probe"'; then
  ok "explicit TRUTH_SESSION is honored verbatim"
else
  miss "TRUTH_SESSION override not recorded"
fi

say "FAULT D (G10): claim past its ttl_days must expire to stale"
CID_D=$(TRUTH_NOW="2026-06-01T00:00:00+00:00" $T claim \
        "external API allows 100 req/min" --class INFERRED \
        --basis "vendor docs read 2026-06-01" --ttl-days 7 --tier P1)
if [ -z "$CID_D" ] || ! grep -q "$CID_D" .truth/claims.jsonl; then
  miss "fault injection failed: the ttl claim was never filed (an empty id makes grep -q match anything)"
else
  $T ttl-scan --quiet
  if $T list --stale --json | grep -q "$CID_D"; then
    ok "claim $CID_D expired after ttl elapsed"
  else
    miss "ttl_days is still a dead field: $CID_D outlived its ttl"
  fi
fi
# ADR-019 (H2): the fold reads no clock -- a TTL'd claim is NOT stale
# until a scan writes the invalidation record. File one already long past
# its ttl and do NOT scan: it must stay non-stale. An implementer whose
# fold expired from wall-time would wrongly show it stale here.
CID_DF=$(TRUTH_NOW="2026-01-01T00:00:00+00:00" $T claim \
         "external rate limit was 50 req per min" --class INFERRED \
         --basis "vendor docs read 2026-01-01" --ttl-days 7 --tier P2)
if $T list --stale --json | grep -q "$CID_DF"; then
  miss "fold synthesized TTL expiry with no scan record (clock leaked into the fold)"
else
  ok "TTL'd claim stays non-stale until a scan emits the record (fold clock-free, ADR-019)"
fi

say "FAULT G (G6): nondeterministic evidence command must be refused"
# ADR-040 removed `date` from the shipped allowlist (it sets the clock via
# GNU -s/--set and a bare BSD positional). Put it back HERE, in sandbox 1
# only: this arm and FAULT R7 must reach the DETERMINISM gate, and an
# unlisted program would refuse one step earlier -- the arm would still
# say CAUGHT while testing nothing. The entry persists for the rest of the
# sandbox and now earns a doctor grey-zone WARN, so FAULT AL (the only
# later arm that runs doctor here) deliberately re-installs a pristine
# shipped allowlist before asserting on that warning.
echo "date" >> .truth/evidence-allow
if $T claim "the clock ticks" --class VERIFIED \
     --evidence-cmd "date +%s%N" --paths "watched.txt" --tier P2 2>/dev/null; then
  miss "intake accepted nondeterministic evidence"
else
  ok "intake refused nondeterministic evidence"
fi

say "FAULT SD (ADR-009/M4): the screen GATES execution -- a screen-failed command is not double-run unless the author overrides"
# python3 is not on the evidence allowlist (a generic executor, ADR-021/022)
# and time_ns() is nondeterministic. Same command, two flags: without the
# override the SCREEN refuses first and the command never runs (determinism
# is unreachable); WITH --evidence-unsafe-ok the screen is bypassed, the
# command runs twice, and the determinism gate (G6) fires. The contrast
# proves the ordering: the screen decides IF a command runs; determinism
# only judges what ran (M4).
SD_CMD='python3 -c "import time; print(time.time_ns())"'
SD1=$($T claim "screen precedes the double-run" --class VERIFIED \
      --evidence-cmd "$SD_CMD" --paths "watched.txt" --tier P2 2>&1)
if echo "$SD1" | grep -q "ADR-009" && ! echo "$SD1" | grep -q "G6"; then
  ok "unscreened command reports the SCREEN refusal, not determinism (never run)"
else
  miss "screen did not precede the double-run: [$SD1]"
fi
SD2=$($T claim "override reaches the double-run" --class VERIFIED \
      --evidence-cmd "$SD_CMD" --paths "watched.txt" --tier P2 \
      --evidence-unsafe-ok --duplicate-ok 2>&1)
if echo "$SD2" | grep -q "G6"; then
  ok "--evidence-unsafe-ok bypasses the screen; the command runs twice and determinism (G6) fires"
else
  miss "override did not reach the determinism double-run: [$SD2]"
fi

say "FAULT Q1 (ADR-007): universal claim text over a scoped command must be refused"
if $T claim "no occurrences remain anywhere in the codebase" --class VERIFIED \
     --evidence-cmd "grep -rc hello --include=watched.txt ." --paths "watched.txt" \
     --tier P1 2>/dev/null; then
  miss "intake accepted a universal quantifier over an --include-scoped command"
else
  ok "quantifier-scope mismatch refused (the pilot's dominant failure shape)"
fi
say "FAULT Q2 (ADR-007): --scope-ok with a sentence must file and store scope_basis"
if CID_Q2=$($T claim "no occurrences remain anywhere in the codebase" --class VERIFIED \
     --evidence-cmd "grep -rc hello --include=watched.txt ." --paths "watched.txt" \
     --tier P1 --scope-ok "the quantifier is deliberately checked via the include filter" 2>/dev/null) \
   && tail -1 .truth/claims.jsonl | grep -q '"scope_basis"'; then
  ok "override filed with an auditable scope_basis ($CID_Q2)"
else
  miss "--scope-ok override failed or scope_basis absent from the record"
fi
say "FAULT Q3 (ADR-007): scoped text with no quantifier must pass silently"
if $T claim "watched.txt mentions hello at least once" --class VERIFIED \
     --evidence-cmd "grep -c hello --include=watched.txt -r ." --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  ok "non-universal claim over a scoped command passed"
else
  miss "gate misfired on a claim with no universal quantifier"
fi
say "FAULT Q4 (ADR-007): universal text over an unscoped command must pass silently"
if $T claim "watched.txt never went missing" --class VERIFIED \
     --evidence-cmd "cat watched.txt" --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  ok "universal claim over an unscoped command passed (no S signal)"
else
  miss "gate misfired with no scoping signal in the command"
fi
say "FAULT Q5 (ADR-007, F3): a ripgrep -t type filter is a scope signal (no slash)"
# The sentence must NOT collide with any claim already filed in this
# sandbox: Q5's original text was byte-identical to the claim Q2 filed,
# so G8 refused BEFORE the ADR-007 gate ever saw the -t flag (gate table
# order) -- the arm was vacuous. A distinct sentence plus asserting the
# refusal NAMES ADR-007 (the GS1/GS2 pattern) pins the right gate.
Q5ERR=$($T claim "zero stray hello markers survive across the tracked corpus" \
        --class VERIFIED --evidence-cmd "grep -t txt -rc hello ." \
        --paths "watched.txt" --tier P1 2>&1); Q5RC=$?
if [ "$Q5RC" -ne 0 ] && printf '%s\n' "$Q5ERR" | grep -q "ADR-007"; then
  ok "-t type-filter scope signal refused, and the refusal names ADR-007"
else
  miss "-t scope signal not refused by the ADR-007 gate (rc=$Q5RC, F3 evasion or wrong gate)"
fi
say "FAULT Q6 (ADR-007, F3): a glob-metacharacter positional is a scope signal"
Q6ERR=$($T claim "X appears everywhere in the code" --class VERIFIED \
        --evidence-cmd "grep -c hello watched.*" --paths "watched.txt" \
        --tier P1 2>&1); Q6RC=$?
if [ "$Q6RC" -ne 0 ] && printf '%s\n' "$Q6ERR" | grep -q "ADR-007"; then
  ok "glob-metacharacter positional scope signal refused, and the refusal names ADR-007"
else
  miss "glob positional not refused by the ADR-007 gate (rc=$Q6RC, F3 evasion or wrong gate)"
fi

say "FAULT E1 (ADR-009): a non-allowlisted program in the evidence command must be refused"
if $T claim "the network is reachable" --class VERIFIED \
     --evidence-cmd "curl -s https://example.com" --ttl-days 7 --tier P1 2>/dev/null; then
  miss "intake accepted an unscreened program (deferred execution channel open)"
else
  ok "unlisted program refused at intake"
fi
say "FAULT E2 (ADR-009): a pipeline of allowlisted programs must pass"
if CID_E2=$($T claim "watched.txt is a multi-word file" --class VERIFIED \
     --evidence-cmd "cat watched.txt | wc -w" --paths "watched.txt" \
     --tier P2 --duplicate-ok 2>/dev/null); then
  ok "allowlisted pipeline accepted ($CID_E2)"
else
  miss "screen wrongly refused a read-only allowlisted pipeline"
fi
say "FAULT E3 (ADR-009): recheck must refuse to execute an unscreened command"
CID_E3=$($T claim "unsafe evidence probe" --class VERIFIED \
     --evidence-cmd "python3 -c 'print(1)'" --paths "watched.txt" \
     --tier P2 --evidence-unsafe-ok --duplicate-ok 2>/dev/null)
N_E3=$(grep -c "" .truth/claims.jsonl)
if [ -z "$CID_E3" ]; then
  miss "fault injection failed: --evidence-unsafe-ok claim was never filed"
elif $T verdict "$CID_E3" --recheck >/dev/null 2>&1; then
  miss "recheck EXECUTED an unscreened evidence command (the ADR-009 channel)"
else
  N_E3_AFTER=$(grep -c "" .truth/claims.jsonl)
  if [ "$N_E3_AFTER" -eq "$N_E3" ]; then
    ok "recheck declined the unscreened command and filed nothing"
  else
    miss "recheck declined but still filed $((N_E3_AFTER-N_E3)) record(s)"
  fi
fi
say "FAULT E4 (ADR-009): a missing allowlist must fail VERIFIED intake closed"
mv .truth/evidence-allow evidence-allow.e4.bak
if $T claim "screen machinery absent" --class VERIFIED \
     --evidence-cmd "cat watched.txt" --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  miss "VERIFIED intake proceeded with no allowlist (screen failed open)"
else
  ok "missing allowlist failed closed with guidance"
fi
mv evidence-allow.e4.bak .truth/evidence-allow
say "FAULT E5 (ADR-009, F1): an allowlisted program's exec/write flag must be refused"
echo "sort" >> .truth/evidence-allow  # ensure the program is allowlisted
if $T claim "the log is sorted into place" --class VERIFIED \
     --evidence-cmd "sort -o /tmp/pwn watched.txt" --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  miss "screen accepted 'sort -o' -- an allowlisted program's file-write flag (F1 channel)"
else
  ok "allowlisted program's exec/write flag refused (sort -o)"
fi

say "FAULT ES (ADR-021, H4): a newline-smuggled command must be refused (screen/executor tokenizer parity)"
# shlex treats the newline as whitespace so 'touch' lands in argument
# position (approved), but /bin/sh runs it as a second statement at
# recheck. The screen must refuse the control character.
if $T claim "widget cache newline probe" --class VERIFIED \
     --evidence-cmd $'grep -q x watched.txt\ntouch PWNED_ES' --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  miss "screen accepted a newline-smuggled command (ADR-021 bypass open)"
else
  ok "screen refused the newline-smuggled command (ADR-021 tokenizer parity)"
fi

# ---- FAULT SF (ADR-041): shell-free evidence execution ------------------
# The screen used to model what /bin/sh would do with a string the
# executor then handed to /bin/sh. It lost that race three times: `cat
# <>F` created a file the '<' branch read as input, `>1` wrote a file
# named '1' behind the fd-dup carve-out, and a '&' separator backgrounded
# a job the screen had already counted as a segment. The runner executes
# argv now, so these are not patched refusals -- they are constructs with
# no expression. Each arm asserts BOTH the refusal and the absence of the
# file the old channel would have created.
say "FAULT SF1 (ADR-040 R4b): a read-write open ('<>') must be refused and create nothing"
if $T claim "the widget cache is warm" --class VERIFIED \
     --evidence-cmd "cat <>PWNED_SF1" --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  miss "intake accepted 'cat <>FILE' -- the read-write open channel is open"
elif [ -e PWNED_SF1 ]; then
  miss "'cat <>FILE' was refused but the file was created anyway"
else
  ok "read-write open refused, nothing created (ADR-041)"
fi

say "FAULT SF2 (ADR-040 R4c): a digit redirect target must be refused and create nothing"
if $T claim "the widget count is pinned" --class VERIFIED \
     --evidence-cmd "cat watched.txt >1" --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  miss "intake accepted 'cat f >1' -- a write to a file literally named 1"
elif [ -e 1 ]; then
  miss "'cat f >1' was refused but the file '1' was created anyway"
else
  ok "digit redirect target refused, nothing created (ADR-041)"
fi

say "FAULT SF3 (ADR-041): '&' is not a separator -- backgrounding must be refused"
if $T claim "the widget probe backgrounds" --class VERIFIED \
     --evidence-cmd "grep -q x watched.txt & touch PWNED_SF3" \
     --paths "watched.txt" --tier P2 --duplicate-ok >/dev/null 2>&1; then
  miss "intake accepted a backgrounded command ('&' screened as a separator)"
elif [ -e PWNED_SF3 ]; then
  miss "the backgrounded command was refused but its second statement ran"
else
  ok "backgrounding refused, second statement never ran (ADR-041)"
fi

say "FAULT SF4 (ADR-041): an expansion the runner does not perform must be refused, not passed as a literal"
if $T claim "the home directory is named" --class VERIFIED \
     --evidence-cmd "echo \$HOME" --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  miss "intake accepted '\$HOME' -- the runner would record a literal the shell used to substitute"
else
  ok "'\$VAR' refused rather than silently recorded as a literal (ADR-041)"
fi

say "FAULT SF5 (ADR-041, negative control): a glob-and-pipe recipe must still file AND recheck must agree with its own recorded hash"
# The behavioural half of the ADR: 114 filed claims carry hashes produced
# by `subprocess.run(shell=True)`. If the shell-free runner expanded or
# piped differently -- unsorted matches, an empty expansion dropped, a
# pipeline exit code taken from the wrong stage -- this recheck diverges.
if CID_SF5=$($T claim "watched.* is one line long" --class VERIFIED \
     --evidence-cmd "grep -c hello watched.* | wc -l" --paths "watched.txt" \
     --tier P2 --duplicate-ok 2>/dev/null); then
  if $T verdict "$CID_SF5" --recheck 2>&1 | grep -q "hash matches"; then
    ok "glob+pipe recipe filed and rechecked to the same hash ($CID_SF5)"
  else
    miss "the shell-free runner did not reproduce its own recorded hash"
  fi
else
  miss "screen wrongly refused a read-only glob+pipe recipe"
fi

say "FAULT ED (ADR-022): an accidentally-allowlisted shell must still be refused (deny-wins)"
echo "bash" >> .truth/evidence-allow  # consumer allowlists a shell by accident
if $T claim "the widget tests pass" --class VERIFIED \
     --evidence-cmd "bash -c 'grep -q x watched.txt'" --paths "watched.txt" \
     --tier P2 --duplicate-ok >/dev/null 2>&1; then
  miss "screen accepted an allowlisted shell -- ADR-022 deny baseline not applied"
else
  ok "allowlisted shell refused by the template-owned deny baseline (ADR-022 deny-wins)"
fi
grep -v '^bash$' .truth/evidence-allow > .truth/evidence-allow.tmp && mv .truth/evidence-allow.tmp .truth/evidence-allow

# ---- FAULT AL (ADR-040): the audited allowlist default ------------------
# The shipped default was cut to the programs a per-program audit found
# read-only. Removal alone protects only NEW consumers -- the allowlist is
# consumer-owned and copier never clobbers it -- so the propagating half is
# the doctor grey-zone warning, which is code-owned. Both halves are pinned
# here: the default carries no grey-zone program, and a consumer who keeps
# one is warned rather than silently trusted.
say "FAULT AL (ADR-040): the shipped allowlist default is grey-zone free, and a consumer keeping a removed program is warned"
AL_TMP=$(mktemp -d); TDIRS+=("$AL_TMP")
cp "$HERE/../.truth/evidence-allow" "$AL_TMP/shipped"
cp .truth/evidence-allow "$AL_TMP/mine.bak"
if grep -qxE 'rg|file|date' "$AL_TMP/shipped"; then
  miss "AL1: the shipped allowlist default still carries rg/file/date (ADR-040 removal reverted)"
else
  ok "AL1: shipped allowlist default carries no ADR-040-removed program"
fi
# The sandbox list has drifted by now (FAULT G appended `date`, FAULT E5
# `sort`), so AL runs against a PRISTINE copy of the shipped default. Both
# arms below must assert on the WARN line specifically: doctor prints an
# 'OK ... grey-zone -- no code-executing programs listed' line when the
# list is clean, so a bare grep for 'grey-zone' matches whether the
# advisory fired or not -- an arm that can never MISS.
cp "$AL_TMP/shipped" .truth/evidence-allow
if $T doctor 2>&1 | grep -qE '^WARN.*grey-zone'; then
  miss "AL2a: doctor warned grey-zone on the SHIPPED default -- the default carries a code-executing program"
else
  ok "AL2a: no grey-zone warning on the shipped default (negative control)"
fi
# AL2b: the propagating half -- a consumer whose own list keeps a removed
# program is warned (WARN, never a failure: policy stays theirs, ADR-022).
echo "rg" >> .truth/evidence-allow
if $T doctor 2>&1 | grep -qE '^WARN.*grey-zone.*rg'; then
  ok "AL2b: doctor warns a consumer whose allowlist keeps a removed program (rg)"
else
  miss "AL2b: doctor stayed silent on an allowlisted rg -- the propagating half of ADR-040 is dead"
fi
if $T doctor >/dev/null 2>&1; then
  ok "AL3: the grey-zone finding is an advisory, not a failure (doctor still exits 0)"
else
  miss "AL3: a grey-zone allowlist entry FAILED doctor -- ADR-022 says warn, never block"
fi
cp "$AL_TMP/mine.bak" .truth/evidence-allow
rm -rf "$AL_TMP"

# ---- FAULT SEP: RETIRED (ADR-046) ---------------------------------------
# SEP1/SEP2/SEP3 pinned the ADR-010 separation instrument through the
# `truth stats` separation section, which left the template CLI (Tier C).
# Their assertions moved VERBATIM-in-substance to the meta-repo gate
# scripts/test-instruments.sh, which drives the same separation_report
# through instruments/separation-report.py (incl. the SEP3 negative
# control and the JSON-field-not-text-grep lesson).

say "FAULT T (INV-M): a dead evidence-path tripwire must be refused at intake"
if $T claim "a and watched are fine" --class VERIFIED \
     --evidence-cmd "cat watched.txt" --paths "watched.txt fabricated.txt" \
     --tier P1 2>/dev/null; then
  miss "intake accepted a space-joined literal (comma forgotten) -- dead tripwire on arrival"
else
  ok "intake refused the whitespace-no-comma literal"
fi
if $T claim "ghost.sh is fine" --class VERIFIED \
     --evidence-cmd "echo ok" --paths "ghost.sh" --tier P1 2>/dev/null; then
  miss "intake accepted a literal matching zero tracked files"
else
  ok "intake refused the zero-match literal"
fi
# Step 3.2: the freehand watch budget is ONE path, so this fixture now
# carries --paths-ok. The arm's subject is unchanged and still the point --
# INV-M must not mistake a comma-separated LIST for a space-joined literal
# -- and it gained a second one for free: the budget's stated-basis escape
# hatch, exercised end to end through the CLI rather than only as a unit.
if CID_T=$($T claim "watched and fabricated are fine" --class VERIFIED \
     --evidence-cmd "cat watched.txt fabricated.txt" \
     --paths "watched.txt,fabricated.txt" --tier P1 --duplicate-ok \
     --paths-ok "the recipe reads both files, so both belong in the set" \
     2>/dev/null); then
  ok "comma-separated literals still accepted ($CID_T)"
else
  miss "intake wrongly refused legitimate comma-separated paths"
fi
if CID_TG=$($T claim "future docs stay clean" --class VERIFIED \
     --evidence-cmd "echo ok" --paths "ghost-dir/*.md" --tier P1 --duplicate-ok 2>/dev/null); then
  ok "explicit glob matching nothing yet is exempt (legitimate intent)"
else
  miss "intake wrongly refused an explicit glob with zero current matches"
fi
# ADR-023 (H5), FLIPPED in step 2.5. The intake exemption above is
# unchanged and still the point of the arm: a zero-match glob has no single
# referent, so INV-M must not call it dead. The second half used to assert
# that the glob then FIRED once its namespace filled -- a statement about
# the path invalidator, which is retired. Same fixture, inverted: filling
# the namespace must now change nothing about the claim's status.
git add .truth/claims.jsonl && git commit -qm "canary: empty-glob claim T" --no-verify
mkdir -p ghost-dir && echo "# appeared" > ghost-dir/appeared.md
git add ghost-dir/appeared.md && git commit -qm "canary: materialize ghost-dir/*.md" --no-verify
$T ttl-scan --quiet
if $T list --stale --json | grep -q "$CID_TG"; then
  miss "glob $CID_TG staled on a path touch -- the retired path invalidator is back"
else
  ok "glob $CID_TG unaffected by its namespace filling (path proxy retired)"
fi
# ADR-024 (H5 follow-up): an UNREACHABLE glob is dead despite the exemption
# -- '.git/*' contains '*' (so dead_literal_paths passes it) yet matches no
# git-diff path. Intake must refuse it.
if $T claim "git internals stay put" --class VERIFIED \
     --evidence-cmd "echo ok" --paths ".git/*" --tier P1 --duplicate-ok >/dev/null 2>&1; then
  miss "intake accepted an unreachable glob (.git/*) -- dead tripwire (ADR-024)"
else
  ok "intake refused the unreachable glob .git/* (ADR-024)"
fi
# and a reachable look-alike must still pass (no false refusal)
if $T claim "workflow files stay watched" --class VERIFIED \
     --evidence-cmd "echo ok" --paths ".github/**" --tier P1 --duplicate-ok >/dev/null 2>&1; then
  ok "intake kept the reachable glob .github/** (ADR-024 sound, no false refusal)"
else
  miss "intake wrongly refused the reachable glob .github/**"
fi

say "FAULT H (G12): a verdict after retraction must not resurrect the claim"
CID_H=$($T claim "this claim is simply wrong" --tier P2)
# ADR-011: headless human retraction acknowledges the exact id
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID_H" $T verdict "$CID_H" retracted --cause wrong --basis "human: factually wrong, tombstoned" >/dev/null
if $T verdict "$CID_H" agree --basis "resurrection attempt" >/dev/null 2>&1; then
  miss "tool accepted a verdict on a retracted claim"
else
  ok "tool refused a verdict on retracted $CID_H"
fi
if $T list --retracted --json | grep -q "$CID_H" && \
   ! $T list --live --json | grep -q "$CID_H"; then
  ok "fold holds $CID_H as retracted (terminal)"
else
  miss "retracted claim $CID_H changed status"
fi

say "FAULT RV (ADR-020): a diverged claim must RECOVER to live via a later agree"
# Mirror of FAULT H: only retracted is terminal -- diverged/cannot_verify
# are recoverable. Author session diverges (self-diverge is allowed), a
# fresh verifier session agrees later (ADR-010 + LWW) -> back to live.
CID_RV=$(TRUTH_SESSION=s-author-rv $T claim "the retry backoff is exponential" \
         --class INFERRED --basis "reasoned from the config" --tier P2)
TRUTH_SESSION=s-author-rv $T verdict "$CID_RV" diverge --basis "recipe drifted" >/dev/null
if TRUTH_SESSION=s-verifier-rv $T verdict "$CID_RV" agree --basis "re-checked the fact holds" >/dev/null 2>&1 \
   && $T list --live --json | grep -q "$CID_RV"; then
  ok "diverged $CID_RV recovered to live via a later cross-session agree (ADR-020)"
else
  miss "a diverged claim could not recover to live -- negative verdicts wrongly terminal"
fi

say "FAULT I (G8): near-duplicate of an active claim must be refused"
$T claim "the payments module handles all currency conversion logic" --tier P2 >/dev/null
if $T claim "the payments module handles currency conversion" --tier P2 2>/dev/null; then
  miss "intake accepted a near-duplicate active claim"
else
  ok "intake refused the near-duplicate"
fi
if DUP=$($T claim "the payments module handles currency conversion" \
         --tier P2 --duplicate-ok 2>/dev/null); then
  ok "--duplicate-ok override works ($DUP)"
else
  miss "--duplicate-ok override rejected a legitimate refile"
fi
# MEDIUM-1: the override must leave an auditable trace, not vanish silently
if python3 -c "import json,sys
for line in open('.truth/claims.jsonl'):
    r=json.loads(line)
    if r.get('id')=='$DUP':
        sys.exit(0 if r['payload'].get('overridden_duplicates') else 1)
sys.exit(1)" 2>/dev/null; then
  ok "the --duplicate-ok record carries overridden_duplicates (MEDIUM-1 trace)"
else
  miss "the --duplicate-ok override left no overridden_duplicates trace"
fi
# ADR-018 (H1): the metric is Jaccard, NOT the overlap coefficient. A
# strict token-superset of an active claim (an elaboration) is Jaccard
# 0.5/0.375 against the two active payments claims -- below 0.6, so it
# must be ACCEPTED with no --duplicate-ok. An overlap-coefficient
# implementer would compute 1.0 and refuse it: this arm fails if the
# metric ever drifts to overlap-coefficient/Dice.
if $T claim "the payments module handles all currency conversion logic and also validates refund tax rounding audit trails" \
     --tier P2 >/dev/null 2>&1; then
  ok "a token-superset elaboration is accepted (metric is Jaccard, ADR-018)"
else
  miss "intake refused a Jaccard<0.6 elaboration -- metric drifted off Jaccard"
fi

say "FAULT J (ADR-001): issue premised on a stale claim must be HELD"
cat > bd <<'EOF'
#!/usr/bin/env bash
if [ "${1:-}" = "ready" ]; then
  echo '[{"id":"bd-x1","title":"issue on stale premise"},{"id":"bd-x2","title":"issue on live premise"}]'
fi
EOF
chmod +x bd
CID_L=$($T claim "watched.txt now says hello changed" --class VERIFIED \
        --evidence-cmd "cat watched.txt" --paths "watched.txt" --tier P1 --duplicate-ok)
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_L" agree --basis "canary: verified at filing" >/dev/null
# Step 2.5: this arm used $CID_B, which a path touch used to leave stale.
# It no longer does, so the HELD side stands on the sandbox's deliberately
# dead claim (see FAULT B) -- ADR-001 treats `diverged` exactly as it
# treated `stale`.
$T premise bd-x1 "$CID_DEAD" >/dev/null
$T premise bd-x2 "$CID_L" >/dev/null
READY_OUT=$(PATH="$PWD:$PATH" $T ready)
if echo "$READY_OUT" | grep -q "^HELD bd-x1" && echo "$READY_OUT" | grep -q "^bd-x2"; then
  ok "bd-x1 held on stale premise; bd-x2 passed on live premise"
else
  miss "ready join wrong: $READY_OUT"
fi
# v0.4.1 -- the adapter seam is a property, not a promise:
READY_ENV=$(PATH="/usr/bin:/bin" TRUTH_TRACKER_CMD="$PWD/bd ready --json" $T ready)
if echo "$READY_ENV" | grep -q "^HELD bd-x1" && echo "$READY_ENV" | grep -q "^bd-x2"; then
  ok "TRUTH_TRACKER_CMD adapter joins identically (no bd on PATH)"
else
  miss "TRUTH_TRACKER_CMD adapter wrong: $READY_ENV"
fi
READY_STDIN=$(./bd ready | $T ready --stdin)
if echo "$READY_STDIN" | grep -q "^HELD bd-x1" && echo "$READY_STDIN" | grep -q "^bd-x2"; then
  ok "--stdin adapter joins identically (tracker-agnostic pipe)"
else
  miss "--stdin adapter wrong: $READY_STDIN"
fi
# v0.4.1 -- the bundled bd adapter must normalize varied JSON shapes and
# still drive the join (restored after TL merge dropped these two checks).
cat > bd-variant <<'EOF'
#!/usr/bin/env bash
printf '%s' '{"issues":[{"issue_id":"bd-x1","summary":"issue on stale premise"},{"key":"bd-x2","name":"issue on live premise"}]}'
EOF
chmod +x bd-variant
READY_ADAPT=$(TRUTH_BD_CMD="$PWD/bd-variant" TRUTH_TRACKER_CMD="bash $HERE/truth-bd-adapter.sh" $T ready)
if echo "$READY_ADAPT" | grep -q "^HELD bd-x1" && echo "$READY_ADAPT" | grep -q "^bd-x2"; then
  ok "bd adapter normalizes {issue_id,summary,key,name} and joins correctly"
else
  miss "bd adapter join wrong: $READY_ADAPT"
fi
# adapter must FAIL LOUDLY (non-zero) rather than emit an empty join
cat > bd-noid <<'EOF'
#!/usr/bin/env bash
printf '%s' '[{"foo":"bar"}]'
EOF
chmod +x bd-noid
if TRUTH_BD_CMD="$PWD/bd-noid" bash "$HERE/truth-bd-adapter.sh" >/dev/null 2>&1; then
  miss "bd adapter silently accepted issues with no id"
else
  ok "bd adapter fails loudly when no id field is recognized"
fi
if PATH="/usr/bin:/bin" TRUTH_TRACKER_CMD="definitely-not-a-tracker --json" $T ready >/dev/null 2>&1; then
  miss "ready succeeded with a nonexistent tracker command"
else
  if PATH="/usr/bin:/bin" TRUTH_TRACKER_CMD="definitely-not-a-tracker --json" $T ready 2>&1 | grep -q "Traceback"; then
    miss "missing tracker produced a raw traceback, not guidance"
  else
    ok "missing tracker degrades with guidance, no traceback"
  fi
fi

# ---- FAULT K (v0.4): duplicate-id append must not resurrect a tombstone ----
say "FAULT K (INV-G'): appending a duplicate claim id must not reset status"
cp .truth/claims.jsonl claims.k.bak
python3 - "$CID_H" <<'PYEOF'
import json, sys
rec={"id":sys.argv[1],"kind":"claim","actor":"agent-x","session":"s-evil",
     "ts":"2099-01-01T00:00:00.000000+00:00",
     "payload":{"text":"resurrection via duplicate id","evidence_class":"UNVERIFIED",
                "cost_tier":"P0","ttl_days":None,"evidence_paths":[]}}
open(".truth/claims.jsonl","a").write(json.dumps(rec,sort_keys=True)+"\n")
PYEOF
if $T list --retracted --json | grep -q "$CID_H" && \
   ! $T list --unverified --json | grep -q "$CID_H"; then
  ok "duplicate-id append ignored; $CID_H stays retracted"
else
  miss "duplicate-id append resurrected retracted $CID_H"
fi
# ADR-031 (v0.9.13) flips this arm's validate expectation: the later-ts
# content-distinct duplicate is harmless to the first-wins fold (checked
# above -- UNCHANGED) but has no legitimate producer, so validate now
# refuses it instead of accepting it. Pre-v0.9.13 this record stayed in
# the ledger with validate green; now the arm restores the ledger.
say "FAULT K2 (ADR-031): the same LATER-ts distinct duplicate must fail validate"
if ! grep -q "resurrection via duplicate id" .truth/claims.jsonl; then
  miss "fault injection failed: later-ts duplicate was never appended"
elif $T validate >/dev/null 2>&1; then
  miss "validate passed a later-ts content-distinct duplicate (ADR-031 open)"
else
  ok "validate refused the later-ts distinct duplicate (ADR-031: only byte-identical union-merge duplicates may share an id)"
fi
mv claims.k.bak .truth/claims.jsonl

say "FAULT B1 (ADR-008 case, ADR-031 rule): a BACKDATED duplicate-id append must fail validate (commit gate blocks)"
cp .truth/claims.jsonl claims.b1.bak
python3 - "$CID_H" <<'PYEOF'
import json, sys
rec={"id":sys.argv[1],"kind":"claim","actor":"agent-x","session":"s-evil",
     "ts":"2000-01-01T00:00:00+00:00",
     "payload":{"text":"content substitution via backdated duplicate","evidence_class":"UNVERIFIED",
                "cost_tier":"P0","ttl_days":None,"evidence_paths":[]}}
open(".truth/claims.jsonl","a").write(json.dumps(rec,sort_keys=True)+"\n")
PYEOF
if ! grep -q "content substitution via backdated" .truth/claims.jsonl; then
  miss "fault injection failed: backdated duplicate was never appended"
elif $T validate >/dev/null 2>&1; then
  miss "validate passed a backdated duplicate id (canonical-order substitution open)"
elif ! $T validate 2>&1 | grep -q "duplicate-id substitution (ADR-031)"; then
  miss "validate refused the backdated duplicate but not with the unified ADR-031 message"
else
  ok "validate failed the backdated duplicate with the ADR-031 unified message; the commit gate blocks INV-G's composition gap"
fi
mv claims.b1.bak .truth/claims.jsonl

say "FAULT B2 (ADR-008, ADR-031 exemption): an IDENTICAL duplicated line (union-merge shape) must still validate"
cp .truth/claims.jsonl claims.b2.bak
tail -1 .truth/claims.jsonl >> .truth/claims.jsonl
if $T validate >/dev/null 2>&1; then
  ok "identical duplicate line (equal ts) passed -- legitimate union-merge shape"
else
  miss "validate rejected a union-merge-duplicated identical line"
fi
mv claims.b2.bak .truth/claims.jsonl

say "FAULT B3 (ADR-008/F2 case, ADR-031 rule): a backdated duplicate with a tz-NAIVE ts must fail validate"
cp .truth/claims.jsonl claims.b3.bak
python3 - "$CID_H" <<'PYEOF'
import json, sys
# naive ts (no offset) string-sorts before the tz-aware genuine record;
# the pre-F2 parsed comparison abstained on the tz mismatch and passed it
rec={"id":sys.argv[1],"kind":"claim","actor":"agent-x","session":"s-evil",
     "ts":"2026-01-01T00:00:00",
     "payload":{"text":"substitution via naive-ts backdated duplicate","evidence_class":"UNVERIFIED",
                "cost_tier":"P0","ttl_days":None,"evidence_paths":[]}}
open(".truth/claims.jsonl","a").write(json.dumps(rec,sort_keys=True)+"\n")
PYEOF
if ! grep -q "naive-ts backdated" .truth/claims.jsonl; then
  miss "fault injection failed: naive-ts duplicate was never appended"
elif $T validate >/dev/null 2>&1; then
  miss "validate passed a naive-ts backdated duplicate (F2 evasion still open)"
elif ! $T validate 2>&1 | grep -q "duplicate-id substitution (ADR-031)"; then
  miss "validate refused the naive-ts duplicate but not with the unified ADR-031 message"
else
  ok "validate failed the naive-ts backdated duplicate (F2 closed, ADR-031 message)"
fi
mv claims.b3.bak .truth/claims.jsonl

say "FAULT B4 (ADR-008/F2 case, ADR-031 rule): a backdated duplicate with an UNPARSEABLE ts must fail validate"
cp .truth/claims.jsonl claims.b4.bak
python3 - "$CID_H" <<'PYEOF'
import json, sys
# junk ts made parse_ts return None, so the pre-F2 comparison abstained;
# by raw string it still sorts before any ISO ts and wins the fold
rec={"id":sys.argv[1],"kind":"claim","actor":"agent-x","session":"s-evil",
     "ts":"1",
     "payload":{"text":"substitution via junk-ts backdated duplicate","evidence_class":"UNVERIFIED",
                "cost_tier":"P0","ttl_days":None,"evidence_paths":[]}}
open(".truth/claims.jsonl","a").write(json.dumps(rec,sort_keys=True)+"\n")
PYEOF
if ! grep -q "junk-ts backdated" .truth/claims.jsonl; then
  miss "fault injection failed: junk-ts duplicate was never appended"
elif $T validate >/dev/null 2>&1; then
  miss "validate passed a junk-ts backdated duplicate (F2 evasion still open)"
elif ! $T validate 2>&1 | grep -q "duplicate-id substitution (ADR-031)"; then
  miss "validate refused the junk-ts duplicate but not with the unified ADR-031 message"
else
  ok "validate failed the junk-ts backdated duplicate (F2 closed, ADR-031 message)"
fi
mv claims.b4.bak .truth/claims.jsonl

say "FAULT B5 (ADR-016/C1 case, ADR-031 rule): an EQUAL-ts duplicate id with different content must fail validate"
cp .truth/claims.jsonl claims.b5.bak
python3 - "$CID_H" <<'PYEOF'
import json, sys
cid = sys.argv[1]
# copy the genuine record's ts byte-for-byte -- NOT backdated. It ties
# (ts, id) with the genuine claim, so file order alone would decide the
# fold winner and two union-merge directions could disagree (INV-I).
# ADR-008's strictly-earlier rule passed this; ADR-016 refused it;
# ADR-031's unified content-distinct rule (v0.9.13) subsumes both.
genuine = next(json.loads(l) for l in open(".truth/claims.jsonl")
               if json.loads(l).get("id") == cid)
rec = {"id": cid, "kind": "claim", "actor": "agent-x", "session": "s-evil",
       "ts": genuine["ts"],
       "payload": {"text": "substitution via equal-ts copied-timestamp duplicate",
                   "evidence_class": "UNVERIFIED", "cost_tier": "P0",
                   "ttl_days": None, "evidence_paths": []}}
open(".truth/claims.jsonl", "a").write(json.dumps(rec, sort_keys=True) + "\n")
PYEOF
if ! grep -q "equal-ts copied-timestamp" .truth/claims.jsonl; then
  miss "fault injection failed: equal-ts duplicate was never appended"
elif $T validate >/dev/null 2>&1; then
  miss "validate passed an equal-ts substitution duplicate (C1 open -- INV-I falsifiable)"
elif ! $T validate 2>&1 | grep -q "duplicate-id substitution (ADR-031)"; then
  miss "validate refused the equal-ts duplicate but not with the unified ADR-031 message"
else
  ok "validate failed the equal-ts substitution duplicate (C1 closed at the gate, ADR-031 message)"
fi
mv claims.b5.bak .truth/claims.jsonl

say "FAULT B6 (ADR-016, C1): the fold's order is total -- a tied pair folds identically both ways"
B6_OUT=$(python3 - <<'PYEOF'
import json
from importlib.machinery import SourceFileLoader
tm = SourceFileLoader("truth", "scripts/truth").load_module()
# two DISTINCT records tied on (ts, id): the fold must not depend on
# which one the file lists first (canon() is the total third key)
a = {"id":"tr-aaaaaaaa","kind":"claim","actor":"x","session":"s1",
     "ts":"2026-07-01T00:00:00.000000+00:00",
     "payload":{"text":"alpha","evidence_class":"UNVERIFIED","cost_tier":"P2",
                "ttl_days":None,"evidence_paths":[]}}
b = dict(a); b = json.loads(json.dumps(a)); b["payload"] = dict(a["payload"], text="beta")
def winner(evs):
    c = tm.fold([(i,e) for i,e in enumerate(evs)])[0]["tr-aaaaaaaa"]["claim"]
    return c.get("text") or c.get("payload",{}).get("text")
print("SAME" if winner([a,b]) == winner([b,a]) else "DIVERGED")
PYEOF
)
if [ "$B6_OUT" = "SAME" ]; then
  ok "fold is confluent on a tied (ts,id) pair -- file order does not decide the winner"
else
  miss "fold picked different winners by file order ($B6_OUT) -- (ts,id) not total"
fi

# ---- FAULTS AN (ADR-027): anchor_commit/commit git-SHA-prefix floor ------
# A git SHA prefix is >=7 chars everywhere the system emits one. Each arm
# appends a record that is well-formed EXCEPT the anchor length, so a failed
# validate can only be the anchor floor -- a mutant that drops the check is
# caught. Schema + mirror are asserted in lockstep by the core corpus; these
# arms gate the same floor at the acceptance layer, across all three kinds.
H64="sha256:0000000000000000000000000000000000000000000000000000000000000000"
an_reject() {  # $1=label  $2=jsonl-record : validate MUST fail
  cp .truth/claims.jsonl claims.an.bak
  printf '%s\n' "$2" >> .truth/claims.jsonl
  if $T validate >/dev/null 2>&1; then
    miss "validate passed $1 (anchor floor open)"
  else
    ok "validate rejected $1 (ADR-027 anchor floor)"
  fi
  mv claims.an.bak .truth/claims.jsonl
}
say "FAULT AN1 (ADR-027): a VERIFIED claim with a sub-7 anchor must fail validate"
an_reject "a VERIFIED claim with a 6-char anchor" \
  "{\"id\":\"tr-a11c0001\",\"kind\":\"claim\",\"actor\":\"a\",\"session\":\"s\",\"ts\":\"2026-07-01T00:00:00.000000+00:00\",\"payload\":{\"text\":\"short anchor\",\"evidence_class\":\"VERIFIED\",\"cost_tier\":\"P0\",\"anchor_commit\":\"abc123\",\"ttl_days\":5,\"evidence\":{\"command\":\"true\",\"output_hash\":\"$H64\"}}}"
say "FAULT AN2 (ADR-027): a VERIFIED claim with a null anchor must fail validate"
an_reject "a VERIFIED claim with a null anchor" \
  "{\"id\":\"tr-a11c0002\",\"kind\":\"claim\",\"actor\":\"a\",\"session\":\"s\",\"ts\":\"2026-07-01T00:00:00.000000+00:00\",\"payload\":{\"text\":\"null anchor\",\"evidence_class\":\"VERIFIED\",\"cost_tier\":\"P0\",\"anchor_commit\":null,\"ttl_days\":5,\"evidence\":{\"command\":\"true\",\"output_hash\":\"$H64\"}}}"
say "FAULT AN3 (ADR-027): a verdict with a sub-7 anchor must fail validate"
an_reject "a verdict with a 3-char anchor" \
  "{\"id\":\"tr-a11c0003\",\"kind\":\"verdict\",\"actor\":\"a\",\"session\":\"s\",\"ts\":\"2026-07-01T00:00:00.000000+00:00\",\"payload\":{\"claim\":\"tr-00000001\",\"verdict\":\"agree\",\"basis\":\"b\",\"anchor_commit\":\"abc\"}}"
say "FAULT AN4 (ADR-027): an invalidation with a sub-7 commit must fail validate"
an_reject "an invalidation with a 3-char commit" \
  "{\"id\":\"tr-a11c0004\",\"kind\":\"invalidation\",\"actor\":\"a\",\"session\":\"s\",\"ts\":\"2026-07-01T00:00:00.000000+00:00\",\"payload\":{\"claim\":\"tr-00000001\",\"commit\":\"abc\"}}"
say "FAULT AN5 (ADR-027): the floor is exactly 7 -- a 7-char anchor must PASS validate"
cp .truth/claims.jsonl claims.an5.bak
printf '%s\n' "{\"id\":\"tr-a11c0005\",\"kind\":\"claim\",\"actor\":\"a\",\"session\":\"s\",\"ts\":\"2026-07-01T00:00:00.000000+00:00\",\"payload\":{\"text\":\"seven char anchor\",\"evidence_class\":\"VERIFIED\",\"cost_tier\":\"P0\",\"anchor_commit\":\"abc1234\",\"ttl_days\":5,\"evidence\":{\"command\":\"true\",\"output_hash\":\"$H64\"}}}" >> .truth/claims.jsonl
if $T validate >/dev/null 2>&1; then
  ok "validate accepted a 7-char anchor (floor is 7, not over-tightened)"
else
  miss "validate rejected a valid 7-char anchor (floor over-tightened past 7)"
fi
mv claims.an5.bak .truth/claims.jsonl

# ---- FAULTS TS1-TS3 (ADR-015): canonical timestamp profile ---------------
say "FAULT TS1 (ADR-015): a fresh-id record with a Z-suffix ts must fail validate"
cp .truth/claims.jsonl claims.ts1.bak
python3 - <<'PYEOF'
import json
# Z is valid ISO 8601 UTC, but ASCII 'Z' > '+' -- the raw-string fold
# would order this record inconsistently against +00:00 records at the
# same instant, so the profile refuses the form outright
rec={"id":"tr-00000ad5","kind":"claim","actor":"agent-x","session":"s-evil",
     "ts":"2026-01-01T00:00:00.000000Z",
     "payload":{"text":"honest fact in a Z-suffix timestamp","evidence_class":"UNVERIFIED",
                "cost_tier":"P2","ttl_days":None,"evidence_paths":[]}}
open(".truth/claims.jsonl","a").write(json.dumps(rec,sort_keys=True)+"\n")
PYEOF
if ! grep -q "Z-suffix timestamp" .truth/claims.jsonl; then
  miss "fault injection failed: Z-suffix record was never appended"
elif $T validate >/dev/null 2>&1; then
  miss "validate passed a Z-suffix ts (non-canonical form breaks raw-string order)"
else
  ok "validate failed the Z-suffix ts (canonical profile enforced)"
fi
mv claims.ts1.bak .truth/claims.jsonl

say "FAULT TS2 (ADR-015): a naive TRUTH_NOW override must still mint a canonical ts"
TS2_OUT=$(TRUTH_NOW="2026-06-30T12:00:00" $T claim \
  "canary ts2 canonical mint probe fact" --class UNVERIFIED --tier P2 \
  --duplicate-ok 2>/dev/null)
TS2_TS=$(tail -1 .truth/claims.jsonl | python3 -c "import json,sys; print(json.load(sys.stdin)['ts'])")
if [ "$TS2_TS" = "2026-06-30T12:00:00.000000+00:00" ] && $T validate >/dev/null 2>&1; then
  ok "naive override normalized to canonical UTC microseconds; validate green"
else
  miss "naive TRUTH_NOW minted '$TS2_TS' (expected 2026-06-30T12:00:00.000000+00:00)"
fi

say "FAULT TS3 (ADR-015): a real-clock append must not sort before the ledger tail (clock-push)"
TS3_FUTURE=$(python3 -c "from datetime import datetime,timedelta,timezone; print((datetime.now(timezone.utc)+timedelta(seconds=120)).isoformat(timespec='microseconds'))")
TRUTH_NOW="$TS3_FUTURE" $T claim "canary ts3 future tail fact" \
  --class UNVERIFIED --tier P2 --duplicate-ok >/dev/null 2>&1
$T claim "canary ts3 real clock follower fact" \
  --class UNVERIFIED --tier P2 --duplicate-ok >/dev/null 2>&1
TS3_ORDER=$(tail -2 .truth/claims.jsonl | python3 -c "
import json,sys
a,b=[json.loads(l)['ts'] for l in sys.stdin]
print('PUSHED' if b > a else 'INVERTED')")
if [ "$TS3_ORDER" = "PUSHED" ] && $T validate >/dev/null 2>&1; then
  ok "real-clock record bumped past the future tail; file order stays sort order"
else
  miss "real-clock append sorted before the ledger tail ($TS3_ORDER) -- clock-push inert"
fi

# ---- FAULT L (v0.4, re-aimed in step 2.5) -------------------------------
# The arm's purpose is unchanged: a re-verification must not be undone by
# ordinary repository movement. What used to threaten it was the next
# invalidate-scan, and the defence was the advancing anchor (F2). With the
# path invalidator retired, the threat is gone and the anchor no longer
# defends anything -- so the arm now asserts the guarantee that DID
# replace it: after an ADR-051 refresh the claim is live AND its recorded
# capsule still reproduces. A live claim that cannot reproduce is exactly
# the population `truth reproduce` exists to name.
say "FAULT L (ADR-051): re-verified claim stays live and its refreshed capsule reproduces"
CID_R=$($T claim "watched.txt has multiple lines" --class VERIFIED \
        --evidence-cmd "wc -l < watched.txt" --paths "watched.txt" --tier P1 --duplicate-ok)
echo "another line" >> watched.txt
git add watched.txt && git commit -qm "canary: touch evidence again" --no-verify
# ADR-051: appending a line CHANGES `wc -l`'s output, so this agree
# would advance the anchor past a capsule that can no longer be
# produced -- the exact orphaning this arm's own fixture demonstrates
# ("a count that grew" is the ADR's canonical example). The
# re-verification F2 built is unchanged in purpose; it now carries the
# capsule with it instead of leaving it behind.
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_R" agree \
  --basis "human re-verified at new HEAD" \
  --refresh-evidence "the line count grew; the claim is that the file has MULTIPLE lines, which still holds" >/dev/null
if $T list --live --json | grep -q "$CID_R" \
   && $T reproduce 2>&1 | grep -q "^$CID_R  reproduces"; then
  ok "re-verified $CID_R is live and its refreshed capsule reproduces"
else
  miss "re-verified $CID_R lost live status, or its refreshed capsule no longer reproduces"
  $T reproduce 2>&1 | grep "$CID_R" || true
fi

# ---- FAULT M (v0.4) + H1-H3 (ADR-011): tombstone confirmation ladder ------
say "FAULT M (G12 enforced): retraction without TRUTH_HUMAN=1 must be refused"
CID_M=$($T claim "a claim a verifier wants dead" --tier P2)
if $T verdict "$CID_M" retracted --cause wrong --basis "verifier overreach" >/dev/null 2>&1; then
  miss "non-human retraction accepted"
else
  ok "retraction refused without TRUTH_HUMAN=1"
fi
say "FAULT H1 (ADR-011): TRUTH_HUMAN=1 alone, headless, must be refused"
# </dev/null is load-bearing, not tidiness: this arm asserts the HEADLESS
# refusal, and headlessness is decided by isatty(). Run from a terminal
# without it, the CLI takes the interactive branch and BLOCKS on
# input("type <id> to confirm"). It then passes anyway -- on the typed
# text mismatching, never on the rule this arm names -- so the arm was
# both a hang and a dark arm: green on a tty for the wrong reason.
if TRUTH_HUMAN=1 $T verdict "$CID_M" retracted --cause wrong --basis "agent set the env var" </dev/null >/dev/null 2>&1; then
  miss "env-var-only retraction accepted with no TTY and no acknowledgment"
else
  ok "headless TRUTH_HUMAN=1 without acknowledgment refused"
fi
say "FAULT H3 (ADR-011): an acknowledgment naming a different id must be refused"
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="tr-deadbeef" $T verdict "$CID_M" retracted --cause wrong --basis "stale ack" >/dev/null 2>&1; then
  miss "retraction accepted under an acknowledgment naming another id"
else
  ok "mismatched TRUTH_HUMAN_ACK refused (lingering exports cannot kill arbitrary claims)"
fi
say "FAULT H2 (ADR-011): id-specific acknowledgment must be accepted"
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID_M" $T verdict "$CID_M" retracted --cause wrong --basis "human confirms" >/dev/null 2>&1; then
  ok "human-confirmed retraction accepted (exact-id acknowledgment)"
else
  miss "human-confirmed retraction refused"
fi

say "FAULT V1 (ADR-010): agree from the claim's own session must be refused"
CID_V=$($T claim "self-verification probe" --tier P2)
if $T verdict "$CID_V" agree --basis "I checked my own work" >/dev/null 2>&1; then
  miss "the authoring session filed its own agree (self-verification open)"
else
  ok "same-session agree refused; dispatch to a fresh session required"
fi
say "FAULT V3 (ADR-010): diverge from the claim's own session must be ALLOWED (self-incrimination)"
if $T verdict "$CID_V" diverge --basis "author retracts confidence: probe was wrong" >/dev/null 2>&1; then
  ok "same-session diverge accepted (runs against interest)"
else
  miss "self-incrimination was refused -- corrections must stay cheap"
fi
say "FAULT V2 (ADR-010): agree from a different session must be accepted"
CID_V2=$($T claim "independent verification probe" --tier P2)
if TRUTH_SESSION=s-canary-verifier $T verdict "$CID_V2" agree --basis "independently decoded and confirmed" >/dev/null 2>&1; then
  ok "fresh-session agree accepted"
else
  miss "the verifier path itself is broken"
fi

say "FAULT M1 (ADR-012): diverge --mechanical must round-trip subtype to the queue"
CID_M1=$($T claim "recipe-drift probe" --tier P1)
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_M1" diverge --mechanical --basis "output format changed, fact holds" >/dev/null
if $T queue --json | grep -q "mechanical" && \
   $T stats --json | grep -q '"diverge_mechanical": 1'; then
  ok "mechanical subtype visible in queue and split out in stats"
else
  miss "mechanical divergence subtype lost between verdict, queue, and stats"
fi

# ---- FAULT R (ADR-002, v0.5): native work kernel ---------------------------
say "FAULT R (ADR-002): premise-at-birth must warn when skipped"
WK_NP=$($T issue "kernel probe with no premise" 2>r_warn.txt)
if grep -q "premise-at-birth" r_warn.txt && [ -n "$WK_NP" ]; then
  ok "issue filed without premises carries the discipline warning ($WK_NP)"
else
  miss "no premise-at-birth warning: $(cat r_warn.txt)"
fi
rm -f r_warn.txt

say "FAULT R2 (ADR-002): unknown dep must be rejected at filing (cycle defense)"
if $T issue "dep on nothing" --deps wk-deadbeef >/dev/null 2>&1; then
  miss "issue accepted a dep on a nonexistent wk- id"
else
  ok "unknown dep refused -- CLI dep graphs stay acyclic by construction"
fi

say "FAULT R3 (ADR-002): native ready must HOLD broken premises, pass live ones"
WK_LIVE=$($T issue "kernel issue on live premise" --premise "$CID_R" 2>/dev/null)
WK_STALE=$($T issue "kernel issue on a dead premise" --premise "$CID_DEAD" 2>/dev/null)
READY_NATIVE=$(PATH="/usr/bin:/bin" $T ready)
if echo "$READY_NATIVE" | grep -q "^$WK_LIVE" && \
   echo "$READY_NATIVE" | grep -q "^HELD $WK_STALE"; then
  ok "native ready: $WK_LIVE passes, $WK_STALE HELD (no tracker involved)"
else
  miss "native ready join wrong: $READY_NATIVE"
fi

say "FAULT R4 (ADR-002): dep-blocked issue must be absent until its dep closes"
WK_DEP=$($T issue "kernel issue blocked by dep" --deps "$WK_LIVE" 2>/dev/null)
if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_DEP"; then
  miss "dep-blocked $WK_DEP appeared in ready"
else
  ok "dep-blocked $WK_DEP absent from ready"
fi
$T start "$WK_LIVE" >/dev/null
$T done "$WK_LIVE" --basis "canary: dep work finished" >/dev/null
if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_DEP"; then
  ok "$WK_DEP became ready after its dep closed"
else
  miss "$WK_DEP still blocked after dep closed"
fi

say "FAULT RL (ADR-002, HIGH-3): start --release returns a claimed item to open; refused from open"
WK_REL=$($T issue "kernel issue for release probe" 2>/dev/null)
if [ -z "$WK_REL" ] || ! grep -q "$WK_REL" .truth/claims.jsonl; then
  miss "fault injection failed: the release-probe issue was never filed (an empty id makes grep -q match anything)"
else
  $T start "$WK_REL" >/dev/null 2>&1                     # -> claimed
  # releasing a claimed item must put it back in ready (open, deps ok)
  $T start "$WK_REL" --release >/dev/null 2>&1
  if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_REL"; then
    ok "start --release returned $WK_REL to the ready pool (claimed -> open)"
  else
    miss "start --release did not return $WK_REL to open"
  fi
  # released is valid ONLY from claimed: a second release (now open) must refuse
  if $T start "$WK_REL" --release >/dev/null 2>&1; then
    miss "start --release accepted from open state (transition guard missing)"
  else
    ok "start --release refused from open -- released is valid only from claimed"
  fi
fi

say "FAULT R5 (ADR-002): kernel-as-tracker seam must join identically to native"
NATIVE_OUT=$(PATH="/usr/bin:/bin" $T ready)
SEAM_OUT=$($T issues --ready-json | $T ready --stdin)
if [ "$NATIVE_OUT" = "$SEAM_OUT" ] && [ -n "$NATIVE_OUT" ]; then
  ok "issues --ready-json | ready --stdin equals native ready (seam == kernel)"
else
  miss "seam and kernel disagree: native=[$NATIVE_OUT] seam=[$SEAM_OUT]"
fi

say "FAULT R6 (ADR-002/G12): cancel is a human tombstone; terminal after"
WK_DEAD=$($T issue "kernel issue a verifier wants dead" 2>/dev/null)
if $T done "$WK_DEAD" --cancel --basis "agent overreach" >/dev/null 2>&1; then
  miss "non-human cancel accepted"
else
  ok "cancel refused without TRUTH_HUMAN=1"
fi
# </dev/null: same reason as FAULT H1 above -- this arm's subject IS the
# headless branch, and on a terminal the CLI blocks on input() instead.
if TRUTH_HUMAN=1 $T done "$WK_DEAD" --cancel --basis "env var alone" </dev/null >/dev/null 2>&1; then
  miss "env-var-only cancel accepted headless (ADR-011)"
else
  ok "headless TRUTH_HUMAN=1 cancel without acknowledgment refused (ADR-011)"
fi
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$WK_DEAD" $T done "$WK_DEAD" --cancel --basis "human confirms" >/dev/null 2>&1; then
  ok "human-confirmed cancel accepted (exact-id acknowledgment)"
else
  miss "human-confirmed cancel refused"
fi
if $T done "$WK_DEAD" --reopen --basis "resurrection attempt" >/dev/null 2>&1 || \
   $T start "$WK_DEAD" >/dev/null 2>&1; then
  miss "cancelled $WK_DEAD accepted a lifecycle event (not terminal)"
else
  ok "cancelled $WK_DEAD is terminal: reopen and start both refused"
fi

say "FAULT IF (ADR-028): a future-dated issue must not silently swallow its transitions"
# The hole: a schema-valid future-dated issue record makes every honest-clock
# event on it sort BEFORE it, so fold_issues drops the event while intake
# reports '-> closed'. Two gates: intake refuses; order_check refuses a raw
# forward-reference event that bypassed intake.
cp .truth/claims.jsonl claims.if.bak
printf '%s\n' '{"id":"wk-0000f00d","kind":"issue","actor":"a","session":"s","ts":"2099-06-01T00:00:00.000000+00:00","payload":{"title":"future issue"}}' >> .truth/claims.jsonl
if $T done wk-0000f00d --basis "did the work" >/dev/null 2>&1; then
  miss "done on a future-dated issue succeeded -- intake reported a transition the fold drops"
else
  ok "done on a future-dated issue refused at intake (ADR-028)"
fi
printf '%s\n' '{"id":"tr-0f0f0f01","kind":"issue_event","actor":"a","session":"s","ts":"2026-07-19T00:00:00.000000+00:00","payload":{"issue":"wk-0000f00d","event":"closed","basis":"raw"}}' >> .truth/claims.jsonl
if $T validate >/dev/null 2>&1; then
  miss "validate passed an issue_event sorting before its issue -- forward reference the fold drops"
else
  ok "validate failed the forward-reference issue_event (ADR-028 order_check)"
fi
mv claims.if.bak .truth/claims.jsonl

say "FAULT R7 (ADR-002): done --claim must file both records or neither"
WK_AT=$($T issue "kernel issue closing with a claim" 2>/dev/null)
N_BEFORE=$(grep -c "" .truth/claims.jsonl)
if $T done "$WK_AT" --basis "canary" --claim "the clock ticked" \
     --class VERIFIED --evidence-cmd "date +%s%N" --paths "watched.txt" \
     2>/dev/null; then
  miss "done --claim accepted nondeterministic completion evidence"
else
  N_AFTER=$(grep -c "" .truth/claims.jsonl)
  if [ "$N_AFTER" -eq "$N_BEFORE" ]; then
    ok "failed claim intake filed NEITHER record (issue still open)"
  else
    miss "failed claim intake left a torn write ($((N_AFTER-N_BEFORE)) record(s))"
  fi
fi
DONE_OUT=$($T done "$WK_AT" --basis "canary: finished" \
           --claim "intact.txt still says hello after kernel work" \
           --class VERIFIED --evidence-cmd "cat intact.txt" \
           --paths "intact.txt" --duplicate-ok)
N_FINAL=$(grep -c "" .truth/claims.jsonl)
if [ "$N_FINAL" -eq $((N_BEFORE + 2)) ] && echo "$DONE_OUT" | grep -q "filed tr-" \
   && $T issues --json | grep -A1 "\"id\": \"$WK_AT\"" | grep -q closed; then
  ok "claim-at-death filed claim + closed event atomically"
else
  miss "claim-at-death wrong: lines $N_BEFORE->$N_FINAL, out=$DONE_OUT"
fi

say "FAULT R8 (INV-A): mutating a historical issue record must block the commit"
git add -A && git commit -qm "canary: settle kernel records" --no-verify
python3 - "$WK_LIVE" <<'PYEOF'
import sys
lines = open(".truth/claims.jsonl").readlines()
for i, ln in enumerate(lines):
    if f'"id": "{sys.argv[1]}"' in ln and '"kind": "issue"' in ln:
        lines[i] = ln.replace('"kind": "issue"', '"kind": "ISSUE_TAMPERED"')
        break
open(".truth/claims.jsonl", "w").writelines(lines)
PYEOF
git add .truth/claims.jsonl
if ! grep -q ISSUE_TAMPERED .truth/claims.jsonl; then
  miss "fault injection failed: issue record was never mutated"
elif bash scripts/check-truth.sh >/dev/null 2>&1; then
  miss "gate accepted a mutated historical issue record"
else
  ok "gate blocked the tampered issue record"
fi
git checkout -q -- .truth/claims.jsonl

say "FAULT R9 (ADR-006): appending a duplicate issue id must not strip premises"
python3 - "$WK_STALE" <<'PYEOF'
import json, sys
wid = sys.argv[1]
rec = {"id": wid, "kind": "issue", "actor": "agent-x", "session": "s-evil",
       "ts": "2099-01-01T00:00:00.000000+00:00",
       "payload": {"title": "kernel issue on stale premise", "text": "",
                   "deps": [], "premises": []}}
open(".truth/claims.jsonl", "a").write(json.dumps(rec, sort_keys=True) + "\n")
PYEOF
if ! grep -q '"session": "s-evil"' .truth/claims.jsonl; then
  miss "fault injection failed: duplicate issue record was never appended"
elif PY3="$(command -v python3)" && PATH="/usr/bin:/bin" "$PY3" scripts/truth ready | grep -q "^HELD $WK_STALE"; then
  ok "duplicate-id append ignored; $WK_STALE still HELD (premises intact)"
else
  miss "duplicate-id append stripped $WK_STALE's premises -- it is now ready"
fi
git checkout -q -- .truth/claims.jsonl 2>/dev/null || true

# Step 2.5: the arm is unchanged in shape and stricter in wording. `impact`
# used to say "next commit STALES <claim>"; nothing stales on a path touch
# now, so it reports the relationship it can actually see (WATCHED BY) and
# leaves the verdict to `reproduce` or a judge. Exit 3 is unchanged -- the
# fatigue budget (W2's silence on an unwatched path) is what that code is for.
say "FAULT W1 (ADR-005): impact on a watched path must report the claim and exit 3"
echo whisper > w.txt
git add w.txt   # INV-M: literal paths must be tracked at filing
CID_W=$($T claim "w.txt says whisper" --class VERIFIED \
        --evidence-cmd "cat w.txt" --paths "w.txt" --tier P0 --duplicate-ok)
W1_OUT=$($T impact w.txt) && W1_RC=0 || W1_RC=$?
if ! grep -q "$CID_W" .truth/claims.jsonl; then
  miss "fault injection failed: watched claim $CID_W was never filed"
elif [ "$W1_RC" -eq 3 ] && echo "$W1_OUT" | grep -q "WATCHED BY $CID_W"; then
  ok "impact reported $CID_W as watching the path, and exited 3"
elif [ "$W1_RC" -eq 3 ] && echo "$W1_OUT" | grep -q "STALES $CID_W"; then
  miss "impact still predicts STALES -- a path touch no longer stales anything (step 2.5)"
else
  miss "impact on watched path wrong (rc=$W1_RC): $W1_OUT"
fi

say "FAULT W2 (ADR-005): impact on an unwatched path must stay silent and exit 0 (fatigue budget)"
echo quiet > unwatched-w2.txt
git add unwatched-w2.txt
W2_OUT=$($T impact unwatched-w2.txt) && W2_RC=0 || W2_RC=$?
if [ "$W2_RC" -eq 0 ] && [ -z "$W2_OUT" ]; then
  ok "unwatched path produced zero output, exit 0"
else
  miss "impact broke the fatigue budget (rc=$W2_RC): '$W2_OUT'"
fi

say "FAULT W3 (ADR-005): impact must predict which work ready would HOLD"
WK_W=$($T issue "work standing on w.txt" --premise "$CID_W" 2>/dev/null)
W3_OUT=$($T impact w.txt) && W3_RC=0 || W3_RC=$?
if ! $T issues --json | grep -q "$WK_W"; then
  miss "fault injection failed: issue $WK_W was never filed"
elif [ "$W3_RC" -eq 3 ] && echo "$W3_OUT" | grep -q "HOLDs.*$WK_W"; then
  ok "impact predicted ready HOLDs $WK_W"
else
  miss "impact missed the premised issue (rc=$W3_RC): $W3_OUT"
fi

say "FAULT W4 (ADR-005): unreadable ledger must degrade visibly, never exit 0/3"
cp .truth/claims.jsonl claims.w4.bak
echo 'this is not json' >> .truth/claims.jsonl
W4_ERR=$($T impact w.txt 2>&1 >/dev/null) && W4_RC=0 || W4_RC=$?
if ! grep -q 'this is not json' .truth/claims.jsonl; then
  miss "fault injection failed: ledger was never corrupted"
elif [ "$W4_RC" -ne 0 ] && [ "$W4_RC" -ne 3 ] && echo "$W4_ERR" | grep -q "not valid JSON"; then
  ok "corrupted ledger degraded visibly (rc=$W4_RC), not silently"
else
  miss "impact on corrupt ledger wrong (rc=$W4_RC): $W4_ERR"
fi
mv claims.w4.bak .truth/claims.jsonl

say "FAULT S1 (spec-health): spec citing only live/open ids must pass"
mkdir -p docs/specs
printf '# Spec: canary good\ncites %s and %s\n' "$CID_R" "$WK_DEP" > docs/specs/good.md
if bash scripts/spec-health.sh >/dev/null 2>&1; then
  ok "healthy spec passed (live claim $CID_R, open issue $WK_DEP)"
else
  miss "spec-health failed a spec citing only live/open ids"
fi

say "FAULT S2 (spec-health): spec standing on a dead fact must fail"
if ! $T list --json | grep -q "$CID_DEAD"; then
  miss "fault injection failed: $CID_DEAD was never filed, S2 cannot run armed"
elif $T list --live --json | grep -q "$CID_DEAD"; then
  miss "fault injection failed: $CID_DEAD is still live, S2 cannot run armed"
else
  printf '# Spec: canary bad\nstands on %s\n' "$CID_DEAD" > docs/specs/bad.md
  S2_OUT=$(bash scripts/spec-health.sh 2>&1) && S2_RC=0 || S2_RC=$?
  if [ "$S2_RC" -ne 0 ] && echo "$S2_OUT" | grep -q "FAIL  $CID_DEAD"; then
    ok "spec on dead $CID_DEAD failed with exit $S2_RC"
  else
    miss "spec-health passed a spec standing on dead $CID_DEAD (rc=$S2_RC)"
  fi
  rm -f docs/specs/bad.md
fi

say "FAULT S2D (R1): spec citing a DISPUTED side must fail -- contradicts promises specs citing either side fail"
CID_DS1=$($T claim "ds-fixture parser accepts unicode identifiers" --class UNVERIFIED --tier P1)
CID_DS2=$($T claim "ds-fixture serializer emits ascii output only" --class UNVERIFIED --tier P1)
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_DS1" agree --basis "canary: ds" >/dev/null
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_DS2" agree --basis "canary: ds" >/dev/null
$T contradicts "$CID_DS1" "$CID_DS2" --basis "canary: unicode in cannot leave ascii-only out" >/dev/null
if ! $T list --disputed | grep -q "$CID_DS1"; then
  miss "fault injection failed: $CID_DS1 never derived DISPUTED, S2D cannot run armed"
else
  printf '# Spec: canary disputed\nstands on %s\n' "$CID_DS1" > docs/specs/disputed.md
  S2D_OUT=$(bash scripts/spec-health.sh 2>&1) && S2D_RC=0 || S2D_RC=$?
  if [ "$S2D_RC" -ne 0 ] && echo "$S2D_OUT" | grep -q "FAIL  $CID_DS1  disputed"; then
    ok "spec on disputed $CID_DS1 failed with exit $S2D_RC"
  else
    miss "spec-health passed a spec citing disputed $CID_DS1 (rc=$S2D_RC): $(echo "$S2D_OUT" | grep "$CID_DS1" || true)"
  fi
  rm -f docs/specs/disputed.md
fi

say "FAULT S3 (spec-health): zero-id spec must WARN but not fail"
printf '# Spec: canary unwired\nprose with no ids\n' > docs/specs/unwired.md
S3_OUT=$(bash scripts/spec-health.sh 2>&1) && S3_RC=0 || S3_RC=$?
if [ "$S3_RC" -eq 0 ] && echo "$S3_OUT" | grep -q "WARN  no ledger ids cited"; then
  ok "unwired spec warned without failing the sweep"
else
  miss "unwired spec handling wrong (rc=$S3_RC): $(echo "$S3_OUT" | tail -2)"
fi
rm -rf docs/specs

say "FAULT S4 (spec-health, ADR-003): issues-side degradation must announce and continue, not crash"
mkdir -p docs/specs
printf '# Spec: canary degraded\ncites %s and %s\n' "$CID_R" "$WK_DEP" > docs/specs/degraded.md
mv scripts/truth scripts/truth.real
cat > scripts/truth <<'SH'
#!/usr/bin/env bash
[ "${1:-}" = "issues" ] && { echo "truth: simulated issues failure" >&2; exit 1; }
exec python3 "$(dirname "$0")/truth.real" "$@"
SH
chmod +x scripts/truth
if scripts/truth issues --json >/dev/null 2>&1; then
  miss "fault injection failed: wrapped truth still serves issues --json"
else
  S4_OUT=$(bash scripts/spec-health.sh 2>&1) && S4_RC=0 || S4_RC=$?
  if echo "$S4_OUT" | grep -q "treating issue records as absent" \
     && echo "$S4_OUT" | grep -q "ok    $CID_R" \
     && echo "$S4_OUT" | grep -q "FAIL  $WK_DEP  missing" \
     && echo "$S4_OUT" | grep -q "spec-health: .* failure(s)"; then
    ok "degraded sweep announced on stderr, still judged claims, wk- reported missing (rc=$S4_RC)"
  else
    miss "spec-health degradation wrong (rc=$S4_RC): $(echo "$S4_OUT" | tail -3)"
  fi
fi
mv -f scripts/truth.real scripts/truth
rm -rf docs/specs

say "FAULT D1 (doc-health): clean corpus must pass; absent patterns file must only skip check A"
mkdir -p docs
printf '# target\n' > docs/target.md
printf '# live\nsee [target](target.md)\n' > docs/live.md
git add docs/target.md docs/live.md
D1_OUT=$(bash scripts/doc-health.sh 2>&1) && D1_RC=0 || D1_RC=$?
if [ "$D1_RC" -eq 0 ] && echo "$D1_OUT" | grep -q "0 failure(s)" \
   && echo "$D1_OUT" | grep -q "name-pattern check skipped"; then
  ok "clean corpus passed, patterns check skipped gracefully"
else
  miss "doc-health wrong on clean corpus (rc=$D1_RC): $(echo "$D1_OUT" | tail -2)"
fi

say "FAULT D2 (doc-health): broken relative link must fail"
printf '# live2\nsee [gone](no-such-file-xyz.md)\n' > docs/live2.md
git add docs/live2.md
if ! grep -q "no-such-file-xyz" docs/live2.md; then
  miss "fault injection failed: broken link was never seeded"
else
  D2_OUT=$(bash scripts/doc-health.sh 2>&1) && D2_RC=0 || D2_RC=$?
  if [ "$D2_RC" -ne 0 ] && echo "$D2_OUT" | grep -q "broken link 'no-such-file-xyz.md'"; then
    ok "broken link failed with exit $D2_RC"
  else
    miss "doc-health passed a broken link (rc=$D2_RC)"
  fi
fi
git rm -q --cached docs/live2.md && rm -f docs/live2.md

say "FAULT D3 (doc-health): forbidden name pattern must fail when patterns file exists"
printf '# forbidden names\nold[-_]widget\n' > scripts/doc-health.patterns
printf '# live3\nthe old-widget component\n' > docs/live3.md
git add docs/live3.md
if ! grep -q "old-widget" docs/live3.md; then
  miss "fault injection failed: forbidden name was never seeded"
else
  D3_OUT=$(bash scripts/doc-health.sh 2>&1) && D3_RC=0 || D3_RC=$?
  if [ "$D3_RC" -ne 0 ] && echo "$D3_OUT" | grep -q "forbidden name 'old-widget'"; then
    ok "forbidden name failed with exit $D3_RC"
  else
    miss "doc-health missed a forbidden name (rc=$D3_RC): $(echo "$D3_OUT" | tail -2)"
  fi
fi
git rm -q --cached docs/live3.md docs/target.md docs/live.md
rm -f docs/live3.md docs/target.md docs/live.md scripts/doc-health.patterns

# ---- FAULT N (v0.4): mid-file insertion must block the commit -------------
say "FAULT N (INV-A strict): mid-file insertion (pure addition) must be blocked"
git add -A && git commit -qm "canary: settle before insertion" --no-verify
python3 - <<'PYEOF'
import json
lines=open(".truth/claims.jsonl").readlines()
forged={"id":"tr-deadbeef","kind":"claim","actor":"agent-x","session":"s-evil",
        "ts":"2020-01-01T00:00:00+00:00",
        "payload":{"text":"forged backdated record","evidence_class":"UNVERIFIED",
                   "cost_tier":"P2","ttl_days":None,"evidence_paths":[]}}
lines.insert(0, json.dumps(forged,sort_keys=True)+"\n")
open(".truth/claims.jsonl","w").writelines(lines)
PYEOF
git add .truth/claims.jsonl
if bash scripts/check-truth.sh >/dev/null 2>&1; then
  miss "gate accepted a mid-file insertion (additions-only tampering)"
else
  ok "gate blocked the mid-file insertion"
fi
git checkout -q -- .truth/claims.jsonl

say "FAULT A (INV-A): mutating a historical ledger line must block the commit"
git add -A && git commit -qm "canary: settle ledger" --no-verify
# -i.bak is the only sed -i form GNU and BSD/macOS sed both accept
sed -i.bak '1s/claim/CLAIM_TAMPERED/' .truth/claims.jsonl && rm -f .truth/claims.jsonl.bak
git add .truth/claims.jsonl
if ! grep -q CLAIM_TAMPERED .truth/claims.jsonl; then
  miss "fault injection failed: ledger line was never mutated (sed)"
elif bash scripts/check-truth.sh >/dev/null 2>&1; then
  miss "check-truth.sh allowed a mutated historical record"
else
  ok "check-truth.sh blocked the tampered ledger"
fi
git checkout -q -- .truth/claims.jsonl

say "FAULT GE (L3-F7): unreadable staged ledger must route to the environment lane (exit 2), never a false green"
# Own sandbox (the FAULT DG pattern): FAULT N/A above restore the ledger
# from the INDEX, so the main sandbox's ledger is still tampered here and
# an honest append could never pass its gate. No subshell -- ok/miss
# mutate the counters; cwd restored below.
GE="$(mktemp -d)"; TDIRS+=("$GE")
mkrepo "$GE"
git add -A && git commit -qm "ge: init" --no-verify
$T claim "ge environment lane probe fact" --class UNVERIFIED --tier P2 >/dev/null 2>&1
git add .truth/claims.jsonl
GESHIM="$(mktemp -d)"; TDIRS+=("$GESHIM")
GEREAL="$(command -v git)"
printf '#!/usr/bin/env bash\n[ "${1:-}" = "show" ] && { echo "git: simulated show failure" >&2; exit 128; }\nexec "%s" "$@"\n' "$GEREAL" > "$GESHIM/git"
chmod +x "$GESHIM/git"
if PATH="$GESHIM:$PATH" git show ":.truth/claims.jsonl" >/dev/null 2>&1; then
  miss "fault injection failed: the git shim still serves show"
else
  PATH="$GESHIM:$PATH" bash scripts/check-truth.sh >/dev/null 2>&1; GE_RC=$?
  if [ "$GE_RC" -eq 2 ]; then
    ok "dead git show exited 2 (environment, not governance)"
  else
    miss "check-truth with a dead git show exited $GE_RC instead of 2 (empty-pipe false green?)"
  fi
  # negative control: the shim was the only fault -- the same staged
  # honest append passes with a working git
  bash scripts/check-truth.sh >/dev/null 2>&1; GE2_RC=$?
  if [ "$GE2_RC" -eq 0 ]; then
    ok "same staged append passes with a working git (exit 0)"
  else
    miss "negative control failed: healthy gate exited $GE2_RC on an honest append"
  fi
fi
cd "$TMP1" || { echo "canary: cannot cd into $TMP1 -- refusing to continue" >&2; exit 1; }
rm -rf "$GE" "$GESHIM"

# ======================================================= sandbox 2 (G1)
say "FAULT F (G1): VERIFIED claim in a zero-commit repo must be refused"
mkrepo "$TMP2"
echo x > f.txt
if $T claim "f.txt exists" --class VERIFIED --evidence-cmd "cat f.txt" \
     --paths "f.txt" --tier P0 2>/dev/null; then
  miss "intake anchored a claim in a repo with no commits"
else
  ok "intake refused: no commits, no anchor"
fi

# ======================================================= sandbox 3 (G14)
# FAULT E FLIPPED (step 2.6). Its subject was _anchor_unreachable, retired
# with the rest of the path/anchor cascade: an unreachable anchor says the
# HISTORY moved, not that the FACT did, and `truth reproduce` answers the
# second question without guessing from the first. Same fixture (a genuine
# orphan-branch history rewrite), inverted expectation, plus the positive
# half that matters now: the capsule is still producible, so the claim is
# still trustworthy and the rewrite was never evidence against it.
say "FAULT E (step 2.6): an erased anchor commit must NOT invalidate a reproducible claim"
mkrepo "$TMP3"
echo data > g.txt
git add -A && git commit -qm "canary: init"
CID_E=$($T claim "g.txt says data" --class VERIFIED \
        --evidence-cmd "cat g.txt" --paths "g.txt" --tier P0)
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_E" agree --basis "canary: verified at filing" >/dev/null
git checkout -q --orphan rewritten
git add -A && git commit -qm "canary: history rewritten"
git branch -D main -q
git reflog expire --expire=now --expire-unreachable=now --all
git gc --prune=now -q
$T ttl-scan --quiet
if $T list --stale --json | grep -q "$CID_E"; then
  miss "history rewrite staled $CID_E -- the retired _anchor_unreachable strategy is back"
elif grep -q "anchor unreachable" .truth/claims.jsonl; then
  miss "an 'anchor unreachable' invalidation record was written -- that writer is retired"
elif $T reproduce 2>&1 | grep -q "^$CID_E  reproduces"; then
  ok "claim $CID_E survives a history rewrite and still reproduces (history moved, the fact did not)"
else
  miss "claim $CID_E no longer reproduces after a history rewrite"
fi

# =========================== sandbox 4 (TL-2: work-kernel discovery, v0.6.3)
# Own sandbox on purpose: sandbox 1's adapter-seam checks (FAULT J) depend
# on the ledger holding NO native issue records, and an issue record is a
# permanent append.
mkrepo "$TMP4"
git add -A && git commit -qm "canary: init tl2"

say "TL-2 (wk-968bc087): wk- records with no discovery of 'truth ready' must WARN"
$T issue "tl2 canary work item" >/dev/null 2>&1
if $T doctor 2>/dev/null | grep -q "WARN  work-kernel discovery"; then
  ok "doctor warned: work kernel in use but invisible in discovery files"
else
  miss "doctor silent while the work kernel is invisible to agents"
fi
printf '# Agents\nTruth ledger: use scripts/truth; pick work with scripts/truth ready.\n' > AGENTS.md
if $T doctor 2>/dev/null | grep -q "WARN  work-kernel discovery"; then
  miss "doctor still warned though AGENTS.md names truth ready"
else
  ok "doctor quiet once a discovery file names truth ready"
fi

say "FAULT R10 (ADR-013): supersede releases HELD work; passing premises refused"
echo "r10" > r10.txt
git add -A && git commit -qm "canary: r10 watched file"
CID_R10A=$($T claim "r10 fact alpha" --class VERIFIED \
           --evidence-cmd "cat r10.txt" --paths "r10.txt" --tier P1)
WK_R10=$($T issue "r10 premised work" --premise "$CID_R10A")
CID_R10B=$($T claim "r10 corrected statement beta" --class UNVERIFIED --tier P1)
if $T premise "$WK_R10" "$CID_R10B" --supersedes "$CID_R10A" >/dev/null 2>&1; then
  miss "supersede accepted an unverified premise that passes ready as-is"
else
  ok "supersede refused while the old premise still passes ready"
fi
echo "changed" >> r10.txt
git add r10.txt && git commit -qm "canary: touch r10 watched path"
# Step 2.5: the touch above no longer kills the premise; a judge does.
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_R10A" agree --basis "canary: verified at filing" >/dev/null
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_R10A" diverge --basis "canary: r10.txt moved" >/dev/null
if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_R10"; then
  miss "issue $WK_R10 ready despite a stale premise (pre-supersede)"
else
  ok "issue $WK_R10 HELD on the stale premise"
fi
if $T premise "$WK_R10" "$CID_R10B" --supersedes "$CID_R10A" >/dev/null 2>&1; then
  ok "supersede accepted for the stale premise"
else
  miss "supersede refused for a stale premise"
fi
if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_R10"; then
  ok "supersede released the HELD issue (redirect honored by ready)"
else
  miss "issue $WK_R10 still HELD after supersede"; PATH="/usr/bin:/bin" $T ready || true
fi
# R10-shape (v0.9.32): intake may not be weaker than the validate mirror.
# A non-tr-hex8 claim ref used to APPEND -- and `truth validate` then
# refused the line, on an append-only file.
R10SL=$(wc -l < .truth/claims.jsonl)
R10SERR=$($T premise "$WK_R10" '#' 2>&1); R10SRC=$?
if [ "$R10SRC" -ne 0 ] && printf '%s\n' "$R10SERR" | grep -q "tr-hex8" \
   && [ "$(wc -l < .truth/claims.jsonl)" -eq "$R10SL" ] \
   && $T validate >/dev/null 2>&1; then
  ok "premise refuses a non-tr-hex8 claim ref before appending -- the ledger never goes invalid-by-its-own-validator"
else
  miss "premise accepted a malformed claim ref (rc=$R10SRC) -- intake weaker than validate"
fi

say "FAULT R11 (ADR-017, C3): superseding a RETRACTED premise needs the human gate"
CID_R11=$($T claim "r11 database is safe to drop" --class UNVERIFIED --tier P0)
WK_R11=$($T issue "r11 premised on a to-be-retracted fact" --premise "$CID_R11")
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID_R11" $T verdict "$CID_R11" retracted \
  --cause wrong --basis "canary: human veto" >/dev/null 2>&1
CID_R11B=$($T claim "r11 corrected statement" --class UNVERIFIED --tier P0)
# (a) an agent (no TRUTH_HUMAN) must NOT redirect a retracted premise
if $T premise "$WK_R11" "$CID_R11B" --supersedes "$CID_R11" >/dev/null 2>&1; then
  miss "agent superseded a RETRACTED premise -- human veto spent without authority (C3)"
else
  ok "agent supersede of a retracted premise refused (ADR-017 human gate)"
fi
if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_R11"; then
  miss "issue $WK_R11 released despite a retracted premise and no human authority"
else
  ok "issue $WK_R11 stays HELD -- the retraction's block survived the agent"
fi
# (b) the human (TRUTH_HUMAN + id-specific ack) MAY redirect it
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID_R11" $T premise "$WK_R11" "$CID_R11B" \
     --supersedes "$CID_R11" >/dev/null 2>&1; then
  ok "human supersede of a retracted premise accepted (symmetric authority)"
else
  miss "human supersede of a retracted premise refused -- legitimate flow broken"
fi

say "FAULT AC1 (ADR-014): --accept-cmd with no accept-allow must fail closed"
if $T issue "ac1 work" --accept-cmd "true" >/dev/null 2>&1; then
  miss "issue filed an acceptance oracle with no .truth/accept-allow"
else
  ok "intake refused: acceptance allowlist absent (fail closed)"
fi

say "FAULT AC2 (ADR-014): unlisted oracle program refused; unsafe-ok stamps screened=false"
printf 'true\nfalse\nsh\n' > .truth/accept-allow
if $T issue "ac2 work" --accept-cmd "cargo test" >/dev/null 2>&1; then
  miss "intake accepted an oracle program not in accept-allow"
else
  ok "intake refused the unlisted oracle program"
fi
WK_AC2=$($T issue "ac2 unscreened" --accept-cmd "cargo test" --accept-unsafe-ok 2>/dev/null)
if grep "$WK_AC2" .truth/claims.jsonl | grep -q '"screened": false'; then
  ok "unsafe-ok filed with accept.screened=false stamped"
else
  miss "unsafe-ok intake did not stamp screened=false"
fi

say "FAULT AC3 (ADR-014): failing oracle must refuse the close; work stays claimed"
WK_AC3=$($T issue "ac3 red oracle" --accept-cmd "sh -c 'exit 1'" --accept-kind validation)
$T start "$WK_AC3" >/dev/null
if $T done "$WK_AC3" --basis "narrative says done" >/dev/null 2>&1; then
  miss "done closed $WK_AC3 over a failing acceptance oracle"
else
  ok "done refused: oracle exit non-zero"
fi
if $T issues | grep "$WK_AC3" | grep -q claimed; then
  ok "issue stayed claimed after the refused close"
else
  miss "issue status changed despite the refused close"
fi

say "FAULT AC4 (ADR-014): --accept-unsafe-ok must NOT bypass an oracle that ran and failed"
if $T done "$WK_AC3" --basis "bypass attempt" --accept-unsafe-ok >/dev/null 2>&1; then
  miss "--accept-unsafe-ok closed over a FAILING (executable) oracle"
else
  ok "unsafe-ok refused: it only covers oracles that cannot run"
fi

say "FAULT AC5 (ADR-014): passing oracle closes; event stamps executed+returncode 0"
WK_AC5=$($T issue "ac5 green oracle" --accept-cmd "true")
$T start "$WK_AC5" >/dev/null
if $T done "$WK_AC5" --basis "oracle green" >/dev/null 2>&1; then
  ok "done closed on the passing oracle"
else
  miss "done refused a passing oracle"
fi
if grep '"issue_event"' .truth/claims.jsonl | grep "$WK_AC5" \
   | grep -q '"executed": true, "kind": "verification", "returncode": 0'; then
  ok "close event carries accept {executed:true, returncode:0}"
else
  miss "close event missing the acceptance stamp"
fi

say "FAULT AC6 (ADR-014): unscreened oracle -- done refuses to execute; unsafe-ok close is stamped"
$T start "$WK_AC2" >/dev/null
if $T done "$WK_AC2" --basis "try plain close" >/dev/null 2>&1; then
  miss "done executed (or skipped) an unscreened oracle on a plain close"
else
  ok "done refused to execute the unscreened oracle"
fi
$T done "$WK_AC2" --basis "conscious unscreened close" --accept-unsafe-ok >/dev/null 2>&1
if grep '"issue_event"' .truth/claims.jsonl | grep "$WK_AC2" \
   | grep -q '"executed": false'; then
  ok "unsafe-ok close stamped executed=false on the event"
else
  miss "unsafe-ok close left no executed=false stamp"
fi

say "FAULT AC7 (ADR-014): --accept-kind without --accept-cmd refused; cancel skips the oracle"
if $T issue "ac7 shape only" --accept-kind validation >/dev/null 2>&1; then
  miss "intake accepted --accept-kind with no --accept-cmd"
else
  ok "intake refused the oracle shape with no oracle"
fi
WK_AC7=$($T issue "ac7 doomed work" --accept-cmd "sh -c 'exit 1'")
$T start "$WK_AC7" >/dev/null
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$WK_AC7" $T done "$WK_AC7" --cancel \
   --basis "canary: killing failed work must not need its finish line" >/dev/null 2>&1; then
  ok "cancel skipped the failing oracle (tombstone path unblocked)"
else
  miss "cancel was blocked by the acceptance oracle"
fi
if $T validate >/dev/null 2>&1; then
  ok "ledger with acceptance records validates (schema mirror in sync)"
else
  miss "acceptance records fail validate"; $T validate || true
fi

say "FAULT AC8 (issue #7): exact path-form accept-allow entry admits the oracle; near-miss and absolute refused"
mkdir -p tools && printf '#!/bin/sh\nexit 0\n' > tools/oracle.sh && chmod +x tools/oracle.sh
git add tools && git commit -qm "canary: ac8 oracle" --no-verify
printf 'true\nfalse\nsh\ntools/oracle.sh\n/bin/echo\n' > .truth/accept-allow
WK_AC8=$($T issue "ac8 path oracle" --accept-cmd "tools/oracle.sh" 2>/dev/null)
if [ -n "$WK_AC8" ]; then
  ok "listed repo-relative path oracle accepted at filing"
  $T start "$WK_AC8" >/dev/null
  if $T done "$WK_AC8" --basis "ac8 close" >/dev/null 2>&1; then
    ok "path-form oracle executed and closed the issue"
  else
    miss "path-form oracle did not execute at done"
  fi
else
  miss "listed repo-relative path oracle refused at filing"
fi
if $T issue "ac8 near miss" --accept-cmd "tools/oracle2.sh" >/dev/null 2>&1; then
  miss "unlisted path oracle accepted"
else
  ok "unlisted path oracle refused (exact match only)"
fi
if $T issue "ac8 absolute" --accept-cmd "/bin/echo hi" >/dev/null 2>&1; then
  miss "absolute path oracle accepted despite being listed"
else
  ok "absolute path refused even when listed (inert entry)"
fi

say "FAULT W5 (issue #5): impact --inverse lists dark files, keeps watched ones, exits 4"
echo "dark" > lone.txt
mkdir -p watched-dir && echo "wf" > watched-dir/f.txt
git add lone.txt watched-dir && git commit -qm "canary: inverse fixtures" --no-verify
INV_OUT=$($T impact --inverse 2>/dev/null); INV_RC=$?
if [ "$INV_RC" -eq 4 ] && printf '%s\n' "$INV_OUT" | grep -qx "lone.txt"; then
  ok "dark file lone.txt listed, exit 4"
else
  miss "inverse missed lone.txt or wrong exit ($INV_RC)"
fi
# CID_R10A is STALE and watches r10.txt -- stale is knowledge needing
# re-check, not absence: r10.txt must NOT be dark.
if printf '%s\n' "$INV_OUT" | grep -qx "r10.txt"; then
  miss "stale claim's watched file r10.txt reported dark"
else
  ok "stale claim still watches: r10.txt not dark"
fi

say "FAULT W6 (issue #5): fully watched --under scope exits 0 silent"
$T claim "watched-dir contents are canary fixtures" --class UNVERIFIED \
   --paths "watched-dir/**" >/dev/null
if $T impact --inverse --under watched-dir >/dev/null 2>&1; then
  ok "fully watched scope: exit 0"
else
  miss "fully watched scope did not exit 0"
fi

say "FAULT W7 (issue #5): retraction kills the watch -- file goes dark again"
CID_W7=$($T claim "lone.txt is a canary fixture" --class UNVERIFIED --paths "lone.txt")
if $T impact --inverse 2>/dev/null | grep -qx "lone.txt"; then
  miss "lone.txt dark despite an active claim watching it"
else
  ok "active claim watching lone.txt removes it from dark"
fi
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID_W7" $T verdict "$CID_W7" retracted \
  --cause expired --basis "canary: fixture retired" >/dev/null 2>&1
if $T impact --inverse 2>/dev/null | grep -qx "lone.txt"; then
  ok "retracted claim's watch died: lone.txt dark again"
else
  miss "retracted claim still counted as watching lone.txt"
fi

say "FAULT W8 (issue #5): usage refusals -- positionals, dangling flags, empty scope"
if $T impact --inverse lone.txt >/dev/null 2>&1; then
  miss "--inverse accepted positional paths"
else
  ok "--inverse with positional paths refused"
fi
if $T impact --under watched-dir lone.txt >/dev/null 2>&1; then
  miss "--under accepted without --inverse"
else
  ok "--under without --inverse refused"
fi
$T impact --inverse --under no-such-dir >/dev/null 2>&1; W8_RC=$?
if [ "$W8_RC" -eq 2 ]; then
  ok "empty scope exits 2 (usage), never a false-green 0"
else
  miss "empty scope exited $W8_RC instead of 2"
fi

# ================= sandbox 5 (SC: session-close survival gate, wk-7218c85b)
# Own sandbox: the arms need exact control of tree/kernel/claim state, and
# sandbox 4 ends with uncommitted ledger appends by design.
mkrepo "$TMP5"
git add -A && git commit -qm "canary: init sc"

say "FAULT SC (session-close): survival gate must FAIL on holes, WARN on debt, pass clean"
if bash scripts/session-close.sh >/dev/null 2>&1; then
  ok "clean repo: safe to close (exit 0)"
else
  miss "clean repo refused"; bash scripts/session-close.sh || true
fi
echo probe > sc-dirty.txt
if bash scripts/session-close.sh >/dev/null 2>&1; then
  miss "dirty tree passed the survival gate"
else
  ok "dirty tree refused (uncommitted changes are a survival hole)"
fi
git add -A && git commit -qm "canary: sc file"
WK_SC=$($T issue "sc probe item" 2>/dev/null)
$T start "$WK_SC" >/dev/null
git add .truth/claims.jsonl && git commit -qm "canary: sc claimed" --no-verify
# capture rc, not just the phrase: a fail->warn downgrade in
# session-close.sh would keep printing "still claimed" at exit 0
SCC_OUT=$(bash scripts/session-close.sh 2>/dev/null); SCC_RC=$?
if [ "$SCC_RC" -ne 0 ] && printf '%s' "$SCC_OUT" | grep -q "still claimed"; then
  ok "claimed work item refused (non-zero exit) with the claimed-count named"
else
  miss "in-flight claimed item not flagged as a blocking hole (rc=$SCC_RC)"
fi
$T start "$WK_SC" --release --basis "canary: hand back" >/dev/null
$T claim "sc unverified probe fact" --class UNVERIFIED --tier P2 >/dev/null
git add .truth/claims.jsonl && git commit -qm "canary: sc released + unverified" --no-verify
SC_OUT=$(bash scripts/session-close.sh 2>/dev/null); SC_RC=$?
if [ "$SC_RC" -eq 0 ] && printf '%s' "$SC_OUT" | grep -q "WARN.*unverified"; then
  ok "unverified claims WARN without blocking (triage debt, not a hole)"
else
  miss "unverified-claim debt handling wrong (rc=$SC_RC)"
fi
# R3: the claimed probe must count the STATUS column, never free text --
# an issue whose TITLE contains "claimed" used to false-FAIL the gate
WK_SCT=$($T issue "audit claimed counter probe" 2>/dev/null)
git add .truth/claims.jsonl && git commit -qm "canary: sc titled probe" --no-verify
SCT_OUT=$(bash scripts/session-close.sh 2>/dev/null); SCT_RC=$?
if ! $T issues | grep -q "audit claimed counter probe"; then
  miss "fault injection failed: the titled probe issue was never filed"
elif printf '%s' "$SCT_OUT" | grep -q "still claimed"; then
  miss "the word 'claimed' in an OPEN issue's title false-matched the claimed count (rc=$SCT_RC)"
else
  ok "open issue titled 'claimed' did not trip the claimed count (rc=$SCT_RC)"
fi
# R3/F1: a dead CLI must scream, never degrade to zero counts and
# "Safe to close" -- the gate's own sensor may not die silently
cp .truth/claims.jsonl claims.sc.bak
echo 'sc corrupt probe: not json' >> .truth/claims.jsonl
SCD_OUT=$(bash scripts/session-close.sh 2>/dev/null); SCD_RC=$?
if ! grep -q 'sc corrupt probe' .truth/claims.jsonl; then
  miss "fault injection failed: the ledger was never corrupted"
elif [ "$SCD_RC" -ne 0 ] && printf '%s' "$SCD_OUT" | grep -q "nothing below was checked"; then
  ok "corrupt ledger screamed 'nothing below was checked' at exit $SCD_RC"
else
  miss "dead CLI degraded silently (rc=$SCD_RC): $(printf '%s' "$SCD_OUT" | tail -2)"
fi
mv claims.sc.bak .truth/claims.jsonl
mkdir -p scripts/session-gates.d
printf '#!/usr/bin/env bash\nexit 1\n' > scripts/session-gates.d/always-fail.sh
git add -A && git commit -qm "canary: sc failing gate" --no-verify
if bash scripts/session-close.sh >/dev/null 2>&1; then
  miss "failing project gate did not block the close"
else
  ok "failing scripts/session-gates.d/ gate refused the close"
fi

say "FAULT BL1 (issue #3): baseline at an older ref excludes later records; HEAD includes them"
git add .truth/claims.jsonl
git commit -qm "canary: bl ref point" --no-verify >/dev/null 2>&1 || true
REF_BL=$(git rev-parse HEAD)
CID_BL=$($T claim "bl canary fact" --class UNVERIFIED --tier P2)
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_BL" agree --basis "canary bl" >/dev/null
git add .truth/claims.jsonl && git commit -qm "canary: bl new claim" --no-verify
if $T baseline "$REF_BL" --json 2>/dev/null | grep -q "$CID_BL"; then
  miss "older baseline contains a claim filed after it"
else
  ok "older baseline excludes the later claim"
fi
if $T baseline HEAD --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if '$CID_BL' in d['claims']['ids'].get('live',[]) else 1)"; then
  ok "HEAD baseline shows the new claim live"
else
  miss "HEAD baseline missing the new live claim"
fi

say "FAULT BL2 (issue #3): diff shows the born claim, exit 0"
BL_DIFF=$($T baseline "$REF_BL" --diff HEAD 2>/dev/null); BL_RC=$?
if [ "$BL_RC" -eq 0 ] && printf '%s\n' "$BL_DIFF" | grep -q "+ $CID_BL"; then
  ok "diff lists $CID_BL as born, exit 0"
else
  miss "diff missed the born claim or wrong exit ($BL_RC)"
fi

say "FAULT BL3 (issue #3): a record vanishing between refs must alarm (exit 5, 10007 omission)"
git checkout -qb bl-rewrite
# drop the last TWO lines (CID_BL's claim AND its verdict) -- deleting
# only the verdict would be a status transition, not a disappearance
sed -i.bak '$d' .truth/claims.jsonl && sed -i.bak '$d' .truth/claims.jsonl
rm -f .truth/claims.jsonl.bak
git add .truth/claims.jsonl && git commit -qm "canary: rewritten ledger" --no-verify
git checkout -q main
$T baseline main --diff bl-rewrite >/dev/null 2>&1; BL3_RC=$?
if [ "$BL3_RC" -eq 5 ]; then
  ok "disappeared record raised exit 5"
else
  miss "rewritten-history diff exited $BL3_RC instead of 5"
fi
if $T baseline main --diff bl-rewrite 2>/dev/null | grep -q "DISAPPEARED"; then
  ok "diff names the DISAPPEARED record"
else
  miss "diff silent about the disappeared record"
fi

say "FAULT BL4 (issue #3): unreadable ref exits 2"
$T baseline no-such-ref >/dev/null 2>&1; BL4_RC=$?
if [ "$BL4_RC" -eq 2 ]; then
  ok "bad ref exits 2 (usage)"
else
  miss "bad ref exited $BL4_RC instead of 2"
fi

say "FAULT C1 (issue #4): contradicts edge on two live claims folds both to DISPUTED and HOLDs premised work"
CID_C1=$($T claim "c-fixture formula alpha" --class UNVERIFIED --tier P1)
CID_C2=$($T claim "c-fixture formula beta variant disagreeing" --class UNVERIFIED --tier P1 --duplicate-ok)  # contradicting claims are inherently near-dups: G8 fires, --duplicate-ok is the honest path
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_C1" agree --basis "canary c" >/dev/null
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_C2" agree --basis "canary c" >/dev/null
WK_C1=$($T issue "work standing on alpha" --premise "$CID_C1")
if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_C1"; then
  ok "premised work READY while both claims live"
else
  miss "issue $WK_C1 not ready before the dispute"
fi
$T contradicts "$CID_C1" "$CID_C2" --basis "canary: the two formulas cannot both hold" >/dev/null
if $T list --disputed | grep -q "$CID_C1" && $T list --disputed | grep -q "$CID_C2"; then
  ok "both sides derive DISPUTED"
else
  miss "DISPUTED not derived for both sides"; $T list --disputed || true
fi
if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_C1"; then
  miss "issue $WK_C1 still READY on a disputed premise"
else
  ok "premised work HELD by the dispute"
fi
if $T queue | grep "$CID_C1" | grep -q "$CID_C2"; then
  ok "queue names the counterpart on the disputed row"
else
  miss "queue row missing the counterpart"; $T queue || true
fi

say "FAULT C2 (issue #4): retracting one side resolves the dispute -- the other returns live"
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK="$CID_C2" $T verdict "$CID_C2" retracted \
  --cause wrong --basis "canary: beta loses" >/dev/null 2>&1
if $T list --live | grep -q "$CID_C1" && ! $T list --disputed | grep -q "$CID_C1"; then
  ok "surviving side live again after the retraction"
else
  miss "dispute did not resolve on retraction"
fi
if PATH="/usr/bin:/bin" $T ready | grep -q "^$WK_C1"; then
  ok "premised work released after resolution"
else
  miss "issue $WK_C1 still HELD after resolution"
fi

say "FAULT C3 (issue #4): intake refusals -- self-edge, unknown id, duplicate either direction"
if $T contradicts "$CID_C1" "$CID_C1" --basis "x" >/dev/null 2>&1; then
  miss "self-edge accepted"
else
  ok "self-edge refused"
fi
if $T contradicts "$CID_C1" tr-00000bad --basis "x" >/dev/null 2>&1; then
  miss "unknown claim accepted"
else
  ok "unknown claim refused"
fi
CID_C3=$($T claim "c-fixture formula gamma third contender" --class UNVERIFIED --tier P2 --duplicate-ok)
$T contradicts "$CID_C1" "$CID_C3" --basis "canary dup seed" >/dev/null
if $T contradicts "$CID_C3" "$CID_C1" --basis "reversed dup" >/dev/null 2>&1; then
  miss "duplicate edge accepted in reverse direction"
else
  ok "duplicate edge refused either direction"
fi

say "FAULT C4 (issue #4): edge with a non-live side files DORMANT -- no status change"
if $T list --live | grep -q "$CID_C1"; then
  ok "live side untouched by the dormant edge (gamma is unverified)"
else
  miss "dormant edge changed a status"
fi
if $T contradicts "$CID_C2" "$CID_C3" --basis "x" >/dev/null 2>&1; then
  miss "edge to a RETRACTED claim accepted (dispute already resolved)"
else
  ok "edge to a retracted claim refused"
fi

say "FAULT C5 (issue #4): contradicts records survive validate and the commit gate"
git add .truth/claims.jsonl && git commit -qm "canary: c-edges" --no-verify
if $T validate >/dev/null 2>&1; then
  ok "ledger with contradicts records validates (mirror+schema in sync)"
else
  miss "contradicts records fail validate"; $T validate || true
fi

# FAULT RA RE-AIMED (step 2.6). `truth reaffirm` is retired -- after step
# 2.5 the only route to `stale` is TTL expiry, which was reaffirm_triage's
# first arm and an unconditional refusal, so every input the verb could
# still receive was one it declined by contract.
#
# Its LOAD-BEARING NEGATIVE outlives it and is what this arm now pins,
# against `truth reproduce` and the same two-claim fixture: a claim whose
# evidence output CHANGED must never be auto-agreed, and never
# auto-diverged either (mechanical-vs-genuine is ADR-012's judgment call).
# reproduce is stricter than reaffirm was -- it files NOTHING in EITHER
# direction, so the unchanged peer is not auto-agreed either -- and it
# reports the divergence by exit code 7 instead of by a dispatch list.
say "FAULT RA (step 2.6): reproduce must file nothing either way, and exit 7 on a changed capsule"
RA="$(mktemp -d)"; TDIRS+=("$RA"); RA_PREV="$PWD"
mkrepo "$RA"   # NB: mkrepo cd's into $RA. No subshell -- ok/miss mutate the
               # PASS/FAIL counters; cwd restored via $RA_PREV below.
echo "solid"  > ra-ok.txt
echo "peer"   > ra-peer.txt
echo "shifty" > ra-mm.txt
git add -A && git commit -qm "ra: init" --no-verify -q
CID_RA_OK=$($T claim "ra-ok.txt says solid" --class VERIFIED \
        --evidence-cmd "cat ra-ok.txt" --paths "ra-ok.txt,ra-peer.txt" --tier P1 \
        --paths-ok "the fixture deliberately watches a path the recipe does NOT read, to prove a touch of it is inert")
CID_RA_MM=$($T claim "ra-mm.txt says shifty" --class VERIFIED \
        --evidence-cmd "cat ra-mm.txt" --paths "ra-mm.txt" --tier P1)
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_RA_OK" agree --basis "canary: verified at filing" >/dev/null
TRUTH_SESSION=s-canary-verifier $T verdict "$CID_RA_MM" agree --basis "canary: verified at filing" >/dev/null
echo "touched" >> ra-peer.txt   # a watched path of the OK claim; its evidence OUTPUT is unchanged
echo "mutated" >  ra-mm.txt     # the MM claim's evidence output CHANGED
git add -A && git commit -qm "ra: mutate watched paths" --no-verify -q
N_RA=$(grep -c "" .truth/claims.jsonl)
RAOUT=$($T reproduce 2>&1); RARC=$?
MM_VERDICTS=$(grep '"kind": "verdict"' .truth/claims.jsonl | grep -c "\"claim\": \"$CID_RA_MM\"")
if [ "$RARC" -eq 7 ] \
   && printf '%s\n' "$RAOUT" | grep -q "^$CID_RA_MM  capsule-stale" \
   && [ "$MM_VERDICTS" -eq 1 ]; then
  ok "changed capsule: $CID_RA_MM reported capsule-stale at exit 7, no verdict filed"
else
  miss "reproduce mis-handled the changed capsule for $CID_RA_MM (rc=$RARC)"
fi
if [ "$(grep -c "" .truth/claims.jsonl)" -eq "$N_RA" ]; then
  ok "reproduce filed NOTHING in either direction -- the sweep leaves no record"
else
  miss "reproduce wrote to the ledger; on-read verification must store no state"
fi
if printf '%s\n' "$RAOUT" | grep -q "^$CID_RA_OK  reproduces" \
   && $T list --live | grep -q "$CID_RA_OK"; then
  ok "unchanged peer $CID_RA_OK still reproduces and stays live (a path touch is not evidence)"
else
  miss "unchanged peer $CID_RA_OK lost live status or stopped reproducing"
fi
cd "$RA_PREV" || { echo "canary: cannot cd into $RA_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$RA"

# ---- FAULT SD-decay (ADR-032, v0.9.14): --scope-ok default expiry -------
# A scope_basis override (ADR-007) filed WITHOUT --ttl-days is stamped a
# default 30-day expiry + ttl_default; it never refuses. Four arms: (1) the
# default lands (arm goes red if override_decay is patched out -- the
# assertion reads the exact ttl_days/ttl_default the mechanism writes);
# (2) an explicit --ttl-days is preserved unflagged; (3) NEGATIVE CONTROL:
# an equally old PLAIN claim gets no default and stays live after a scan;
# (4) the expired override is stale and reaffirm lists it as re-file
# (ADR-032 -> ADR-019 scan -> ADR-030 arm 1). Own sandbox; no subshell so
# ok/miss mutate the counters; cwd restored via $SD_PREV.
say "FAULT SD-decay (ADR-032): a --scope-ok override without --ttl-days must decay to a default 30-day expiry"
SD="$(mktemp -d)"; TDIRS+=("$SD"); SD_PREV="$PWD"
mkrepo "$SD"
echo "data" > f.txt
git add -A && git commit -qm "sd: init" --no-verify -q
SD_SB="the include filter deliberately covers the whole codebase"
SD_EC="grep -rc data --include=f.txt ."
CID_SD1=$($T claim "no occurrences remain anywhere in the codebase" \
          --class VERIFIED --evidence-cmd "$SD_EC" --paths f.txt --tier P1 \
          --scope-ok "$SD_SB" 2>/dev/null)
if python3 -c "import json,sys; p=json.loads(open('.truth/claims.jsonl').read().splitlines()[-1])['payload']; sys.exit(0 if p.get('ttl_days')==30 and p.get('ttl_default') is True else 1)"; then
  ok "scope-ok override without --ttl-days landed ttl_days=30 + ttl_default ($CID_SD1)"
else
  miss "scope-ok override did not decay to the default TTL (mechanism patched out?)"
fi
$T claim "no occurrences remain anywhere in the codebase" \
   --class VERIFIED --evidence-cmd "$SD_EC" --paths f.txt --tier P1 \
   --scope-ok "$SD_SB" --ttl-days 90 --duplicate-ok >/dev/null 2>&1
if python3 -c "import json,sys; p=json.loads(open('.truth/claims.jsonl').read().splitlines()[-1])['payload']; sys.exit(0 if p.get('ttl_days')==90 and 'ttl_default' not in p else 1)"; then
  ok "explicit --ttl-days 90 preserved unflagged (the visible opt-out)"
else
  miss "explicit --ttl-days was overwritten or flagged defaulted"
fi
CID_SD3=$(TRUTH_NOW="2026-06-01T00:00:00+00:00" $T claim \
          "f.txt plainly contains data" --class VERIFIED \
          --evidence-cmd "cat f.txt" --paths f.txt --tier P2 2>/dev/null)
$T ttl-scan --quiet
if $T list --stale --json | grep -q "$CID_SD3"; then
  miss "negative control failed: a plain claim got a default TTL and expired"
else
  ok "negative control: an equally old PLAIN claim has no default TTL, stays live after a scan"
fi
CID_SD4=$(TRUTH_NOW="2026-06-01T00:00:00+00:00" $T claim \
          "no matches exist anywhere in the whole repo" --class VERIFIED \
          --evidence-cmd "$SD_EC" --paths f.txt --tier P1 \
          --scope-ok "$SD_SB" 2>/dev/null)
$T ttl-scan --quiet
# Step 2.6: the reaffirm --dry-run half is gone with the verb. What it
# asserted -- an expired override lands in the "re-file required" arm --
# is now structural rather than reported: TTL expiry is the ONLY route to
# `stale`, and ADR-019 says re-verification never resets it, so re-filing
# is the only exit. The arm keeps the half that is still mechanically
# checkable, and gains the reason_code that proves WHICH arm staled it.
if $T list --stale --json | grep -q "$CID_SD4" \
   && grep "\"claim\": \"$CID_SD4\"" .truth/claims.jsonl \
      | grep -q '"reason_code": "ttl"'; then
  ok "expired scope-ok override is stale, by the clock arm ($CID_SD4)"
else
  miss "expired override not staled, or staled by something other than TTL"
fi
cd "$SD_PREV" || { echo "canary: cannot cd into $SD_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$SD"

# ---- FAULT OV: RETIRED (ADR-046) ----------------------------------------
# The two override-velocity stats arms ("verbatim re-justification after
# expiry raised the advisory" and its narrowed-re-file negative control)
# pinned the `truth stats` overrides section, which left the template CLI
# (Tier C). Their assertions moved to the meta-repo gate
# scripts/test-instruments.sh, which seeds the identical expiry/repeat
# fixture and drives override_report through
# instruments/override-velocity.py. The PURE detector tests
# (TestOverrideReport in test-truth-core.py) never moved.

# ---- FAULT GS (ADR-034, v0.9.20): staged gate table + CC-1 advisories ----
# The intake gate sequence is data (INTAKE_GATES) and post-append
# advisories fold into ONE prefixed block. Five arms: (1) GS1 a filing
# tripping BOTH the G8 near-duplicate gate and the evidence screen
# refuses with the G8 message -- pre-execution precedes the execution
# boundary, nothing ran; (2) GS2 same contrast for the ADR-007 gate vs
# the screen; (3) GS3 --json: the echoed record carries advisories[]
# while the LEDGER line stays advisory-free; (4) GS4 two advisories
# render as one contiguous prefixed block; (5) GS5 NEGATIVE CONTROL: a
# clean filing prints zero advisory lines (silence on clean, CC-1).
say "FAULT GS (ADR-034): staged gate order + one CC-1 advisory block"
GS="$(mktemp -d)"; TDIRS+=("$GS"); GS_PREV="$PWD"
mkrepo "$GS"
echo "data" > f.txt
git add -A && git commit -qm "gs: init" --no-verify -q
$T claim "f.txt plainly holds the data marker" --class VERIFIED \
   --evidence-cmd "cat f.txt" --paths f.txt --tier P2 >/dev/null 2>&1
GS1ERR=$($T claim "f.txt plainly holds the data marker now" \
         --class VERIFIED --evidence-cmd "rm -rf f.txt" --paths f.txt \
         --tier P2 2>&1); GS1RC=$?
if [ "$GS1RC" -ne 0 ] && printf '%s\n' "$GS1ERR" | grep -q "(G8)" \
   && ! printf '%s\n' "$GS1ERR" | grep -qi "allowlist" && [ -f f.txt ]; then
  ok "GS1: near-duplicate (pre-execution) refused before the screen saw rm"
else
  miss "GS1: staged order broken -- G8 did not precede the screen"
fi
GS2ERR=$($T claim "no stray markers exist anywhere in the codebase" \
         --class VERIFIED --evidence-cmd "rm -rf --include=f.txt src/" \
         --paths f.txt --tier P2 2>&1); GS2RC=$?
if [ "$GS2RC" -ne 0 ] && printf '%s\n' "$GS2ERR" | grep -q "ADR-007" \
   && ! printf '%s\n' "$GS2ERR" | grep -qi "allowlist" && [ -f f.txt ]; then
  ok "GS2: quantifier-scope (pre-execution) refused before the screen saw rm"
else
  miss "GS2: staged order broken -- ADR-007 did not precede the screen"
fi
GS3OUT=$($T claim "the data marker sits in f.txt as committed" \
         --class VERIFIED --evidence-cmd "cat f.txt" --paths f.txt \
         --tier P2 --scope-ok "single-file scope is the whole domain" \
         --json 2>/dev/null)
if printf '%s\n' "$GS3OUT" | python3 -c "import json,sys; o=json.load(sys.stdin); sys.exit(0 if any('ADR-032' in a for a in o.get('advisories', [])) else 1)" \
   && ! tail -1 .truth/claims.jsonl | grep -q '"advisories"'; then
  ok "GS3: --json echo carries advisories[]; the ledger line does not"
else
  miss "GS3: advisories missing from --json echo, or leaked into the ledger line"
fi
GS4ERR=$($T claim "f.txt visibly lacks any zebra marker" --class VERIFIED \
         --evidence-cmd "grep zebra f.txt" --paths f.txt --tier P2 \
         --scope-ok "single-file scope is the whole domain" \
         2>&1 >/dev/null)
GS4N=$(printf '%s\n' "$GS4ERR" | grep -c "^truth: advisory:")
GS4CONTIG=$(printf '%s\n' "$GS4ERR" | grep -n "^truth: advisory:" \
            | cut -d: -f1 | python3 -c "import sys; ns=[int(l) for l in sys.stdin]; print('yes' if ns and ns[-1]-ns[0]==len(ns)-1 else 'no')")
if [ "$GS4N" -ge 2 ] && [ "$GS4CONTIG" = "yes" ]; then
  ok "GS4: decay notice + exit warning fold into one contiguous advisory block ($GS4N lines)"
else
  miss "GS4: advisories not folded into one contiguous prefixed block (n=$GS4N contig=$GS4CONTIG)"
fi
GS5ERR=$($T claim "f.txt carries the plain data line as committed" \
         --class VERIFIED --evidence-cmd "cat f.txt" --paths f.txt \
         --tier P2 2>&1 >/dev/null)
if printf '%s\n' "$GS5ERR" | grep -q "^truth: advisory:"; then
  miss "GS5: a clean filing printed an advisory line (CC-1 silence broken)"
else
  ok "GS5: negative control -- a clean filing prints zero advisory lines"
fi
# GS6 (P2, SI-3 at claim-at-death): done --claim --json emits one object
# {issue, event, claim, accept, advisories}; the advisory messages ride
# the ECHO, never either ledger line (the GS3 contract, done edition).
$T issue "gs6 work closing with a scoped claim" >/dev/null 2>&1
GS6ID=$(python3 -c "
import json
last = None
for l in open('.truth/claims.jsonl'):
    r = json.loads(l)
    if r.get('kind') == 'issue': last = r['id']
print(last)")
$T start "$GS6ID" >/dev/null 2>&1
GS6OUT=$($T done "$GS6ID" --basis "gs6 close" \
         --claim "the gs6 data marker sits committed in f.txt" \
         --class VERIFIED --evidence-cmd "cat f.txt" --paths f.txt \
         --duplicate-ok --scope-ok "single-file scope is the whole domain" \
         --json 2>/dev/null)
if printf '%s\n' "$GS6OUT" | python3 -c "
import json, sys
o = json.load(sys.stdin)
ok = (o.get('event') == 'closed' and (o.get('claim') or {}).get('id')
      and any('ADR-032' in a for a in o.get('advisories', [])))
sys.exit(0 if ok else 1)" \
   && ! tail -2 .truth/claims.jsonl | grep -q '"advisories"'; then
  ok "GS6: done --claim --json echoes advisories[]; neither ledger line carries them"
else
  miss "GS6: done --json advisory echo broken, or advisories leaked into the ledger ($GS6OUT)"
fi
# GS7 (2026-08-02 audit gap): the gate table's FIRST row, text-nonempty
# (G0), had no end-to-end arm -- its only pins were the table-order test
# and the schema's minLength, both of which a gutted gate body leaves
# green. A hard, override-less refusal with no arm is the vacuous class
# one level up, so it gets one: empty and whitespace-only text refused,
# nothing appended, plus a NEGATIVE CONTROL that ordinary text still files.
GS7N=$(grep -c "" .truth/claims.jsonl)
GS7A=$($T claim "" --tier P2 2>&1); GS7ARC=$?
GS7B=$($T claim "   " --tier P2 2>&1); GS7BRC=$?
GS7M=$(grep -c "" .truth/claims.jsonl)
if [ "$GS7ARC" -ne 0 ] && [ "$GS7BRC" -ne 0 ] \
   && printf '%s\n' "$GS7A" | grep -q "must be non-empty" \
   && printf '%s\n' "$GS7B" | grep -q "must be non-empty" \
   && [ "$GS7M" -eq "$GS7N" ]; then
  ok "GS7: empty and whitespace-only claim text refused (G0), ledger unchanged"
else
  miss "GS7: text-nonempty gate did not refuse (rc=$GS7ARC/$GS7BRC, lines $GS7N->$GS7M)"
fi
if $T claim "gs7 negative control files ordinary sentence text" \
     --tier P2 >/dev/null 2>&1; then
  ok "GS7b: negative control -- ordinary text still files (G0 is not a blanket refusal)"
else
  miss "GS7b: the text-nonempty gate refused legitimate text"
fi
cd "$GS_PREV" || { echo "canary: cannot cd into $GS_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$GS"

# ---- FAULT X (ADR-035, v0.9.21): positive-claim exit gate ---------------
# A VERIFIED filing whose sentence carries no NEGATION_TOKENS token and
# whose recorded evidence exit is non-zero is refused; a negation token
# keeps the v0.9.11 warning path; --evidence-exit-ok stores its basis
# and silences the warning; a basis beside exit 0 is refused at intake
# and by validate (X5). X6 (the lexicon subset tripwire) is a core
# unit test. Arms: X1 refusal (nothing appended); X2 negation warning
# path; X3 basis stored + warning silenced, and basis-with-exit-0
# refused; X4 NEGATIVE CONTROL positive+exit0 files silently; X5
# validate refuses basis-beside-rc0, tolerates a legacy capsule with
# no returncode; X7 done --claim parity.
say "FAULT X (ADR-035): positive text + failing evidence must refuse; absence proofs keep the warning path"
XG="$(mktemp -d)"; TDIRS+=("$XG"); XG_PREV="$PWD"
mkrepo "$XG"
echo "data" > f.txt
git add -A && git commit -qm "x: init" --no-verify -q
X1ERR=$($T claim "f.txt holds a zebra marker" --class VERIFIED \
        --evidence-cmd "grep zebra f.txt" --paths f.txt 2>&1); X1RC=$?
if [ "$X1RC" -ne 0 ] && printf '%s\n' "$X1ERR" | grep -q "ADR-035" \
   && [ ! -s .truth/claims.jsonl ]; then
  ok "X1: positive sentence + exit 1 refused naming ADR-035, nothing appended"
else
  miss "X1: hollow positive filing not refused (rc=$X1RC)"
fi
X2ERR=$($T claim "f.txt lacks a zebra marker" --class VERIFIED \
        --evidence-cmd "grep zebra f.txt" --paths f.txt 2>&1 >/dev/null); X2RC=$?
if [ "$X2RC" -eq 0 ] && printf '%s\n' "$X2ERR" | grep -q "^truth: advisory: evidence command exited 1"; then
  ok "X2: negation token keeps the warning path (filed + advisory)"
else
  miss "X2: absence proof did not file with the warning (rc=$X2RC)"
fi
X3ERR=$($T claim "the zebra differential probe reports a difference by design" \
        --class VERIFIED --evidence-cmd "grep zebra f.txt" --paths f.txt \
        --evidence-exit-ok "diff-style probe: exit 1 is the demonstration" \
        2>&1 >/dev/null); X3RC=$?
X3STORED=$(tail -1 .truth/claims.jsonl | grep -c "evidence_exit_basis")
if [ "$X3RC" -eq 0 ] && [ "$X3STORED" -eq 1 ] \
   && ! printf '%s\n' "$X3ERR" | grep -q "evidence command exited"; then
  ok "X3: --evidence-exit-ok files, stores the basis, silences the warning"
else
  miss "X3: basis path broken (rc=$X3RC stored=$X3STORED)"
fi
if $T claim "f.txt plainly holds the data line" --class VERIFIED \
     --evidence-cmd "cat f.txt" --paths f.txt \
     --evidence-exit-ok "spurious" >/dev/null 2>&1; then
  miss "X3b: a basis beside exit 0 filed (nothing to excuse)"
else
  ok "X3b: a basis beside exit 0 is refused at intake"
fi
X4ERR=$($T claim "f.txt carries the committed data marker" --class VERIFIED \
        --evidence-cmd "grep data f.txt" --paths f.txt 2>&1 >/dev/null); X4RC=$?
if [ "$X4RC" -eq 0 ] && ! printf '%s\n' "$X4ERR" | grep -q "^truth: advisory:"; then
  ok "X4: negative control -- positive sentence + exit 0 files silently"
else
  miss "X4: clean positive filing not silent (rc=$X4RC)"
fi
X5LINE=$(tail -1 .truth/claims.jsonl | python3 -c "
import json,sys
r=json.load(sys.stdin); r['id']='tr-0000feed'
r['payload']['evidence_exit_basis']='noise'
r['payload']['evidence']['returncode']=0
print(json.dumps(r))")
printf '%s\n' "$X5LINE" >> .truth/claims.jsonl
if $T validate 2>&1 | grep -q "nothing to excuse"; then
  ok "X5: validate refuses evidence_exit_basis beside a recorded exit of 0"
else
  miss "X5: validate accepted a basis with nothing to excuse"
fi
python3 -c "
import json
lines=open('.truth/claims.jsonl').read().splitlines()
lines=lines[:-1]
r=json.loads(lines[-1]); r['id']='tr-0000f00d'
r['payload']['evidence_exit_basis']='legacy capsule tolerance probe'
del r['payload']['evidence']['returncode']
lines.append(json.dumps(r))
open('.truth/claims.jsonl','w').write('\n'.join(lines)+'\n')"
if $T validate >/dev/null 2>&1 && ! $T validate 2>&1 | grep -q "nothing to excuse"; then
  ok "X5b: validate tolerates a basis on a legacy capsule with no returncode"
else
  miss "X5b: validate flagged (or crashed on) a legacy capsule lacking returncode"
fi
git checkout -q -- .truth/claims.jsonl 2>/dev/null || true
$T issue "x7 probe" >/dev/null 2>&1
X7ID=$($T issues --json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)[-1]['id'])" 2>/dev/null)
[ -n "$X7ID" ] || X7ID=$(python3 -c "
import json
for l in open('.truth/claims.jsonl'):
    r=json.loads(l)
    if r.get('kind')=='issue': last=r['id']
print(last)")
$T start "$X7ID" >/dev/null 2>&1
X7ERR=$($T done "$X7ID" --basis "probe" --claim "the probe left a zebra marker" \
        --class VERIFIED --evidence-cmd "grep zebra f.txt" --paths f.txt 2>&1); X7RC=$?
if [ "$X7RC" -ne 0 ] && printf '%s\n' "$X7ERR" | grep -q "ADR-035"; then
  ok "X7: done --claim hits the identical exit gate (both-or-neither held)"
else
  miss "X7: claim-at-death evaded the exit gate (rc=$X7RC)"
fi
cd "$XG_PREV" || { echo "canary: cannot cd into $XG_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$XG"

# ---- FAULT TG (ADR-036, v0.9.22): tombstone citation gate ---------------
# After the ADR-011 ceremony, `verdict retracted` / `done --cancel`
# grep the id bare at the repo root (SI-2) and refuse with a distinct
# exit code while scope-covered files cite it. Scope is consumer policy
# (SI-4): absent -> default docs/specs/** + notice; committed-empty ->
# silent; pathspec-magic lines refused; dead scope loud. --orphan-ok
# stores its basis; the ledger itself never blocks (TG9).
say "FAULT TG (ADR-036): retraction must refuse while the id is cited inside the scope"
TG="$(mktemp -d)"; TDIRS+=("$TG"); TG_PREV="$PWD"
mkrepo "$TG"
mkdir -p docs/specs docs/notes
echo "data" > f.txt
git add -A && git commit -qm "tg: init" --no-verify -q
TG_ID=$($T claim "f.txt holds the data marker" --class VERIFIED \
        --evidence-cmd "grep data f.txt" --paths f.txt 2>/dev/null)
echo "grounded on $TG_ID" > docs/specs/spec-a.md
git add -A && git commit -qm "tg: spec" --no-verify -q
TG1ERR=$(TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID $T verdict "$TG_ID" retracted \
         --cause wrong --basis kill 2>&1); TG1RC=$?
if [ "$TG1RC" -eq 6 ] && printf '%s\n' "$TG1ERR" | grep -q "docs/specs/spec-a.md" \
   && ! printf '%s\n' "$TG1ERR" | grep -q "orphan-ok"; then
  ok "TG1: cited retraction refused (exit 6), file listed, bypass unnamed"
else
  miss "TG1: cited retraction not refused correctly (rc=$TG1RC)"
fi
TG_ID2=$($T claim "f.txt still carries its committed data line" \
         --class VERIFIED --evidence-cmd "grep data f.txt" --paths f.txt \
         --duplicate-ok 2>/dev/null)
sed -i.bak "s/$TG_ID/$TG_ID2/" docs/specs/spec-a.md && rm -f docs/specs/spec-a.md.bak
git add -A && git commit -qm "tg: swap" --no-verify -q
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID $T verdict "$TG_ID" retracted \
     --cause wrong --basis kill >/dev/null 2>&1; then
  ok "TG2: after the citation swaps to a successor, the retraction proceeds"
else
  miss "TG2: swap did not unblock the retraction"
fi
echo "see also $TG_ID2" > docs/notes/aside.md
git add -A && git commit -qm "tg: note" --no-verify -q
printf 'docs/specs/**\n' > .truth/citation-scope
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID2 $T verdict "$TG_ID2" retracted \
     --cause wrong --basis kill --orphan-ok "spec cites it as history by policy" \
     >/dev/null 2>&1 \
   && tail -1 .truth/claims.jsonl | grep -q orphan_basis; then
  ok "TG3: --orphan-ok proceeds past an in-scope citation and stores the basis"
else
  miss "TG3: orphan-ok path broken"
fi
TG_ID3=$($T claim "f.txt keeps holding that same data line today" \
         --class VERIFIED --evidence-cmd "grep data f.txt" --paths f.txt \
         --duplicate-ok 2>/dev/null)
echo "outside-scope mention of $TG_ID3" >> docs/notes/aside.md
git add -A && git commit -qm "tg: outside" --no-verify -q
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID3 $T verdict "$TG_ID3" retracted \
     --cause wrong --basis kill >/dev/null 2>&1; then
  ok "TG4: a citation OUTSIDE the scope file's globs does not block"
else
  miss "TG4: out-of-scope citation blocked a retraction"
fi
TG_ID4=$($T claim "f.txt anchors one more data assertion for the gate" \
         --class VERIFIED --evidence-cmd "grep data f.txt" --paths f.txt \
         --duplicate-ok 2>/dev/null)
mkdir -p shim
printf '#!/usr/bin/env bash\nif [ "$1" = grep ]; then exit 128; fi\nexec /usr/bin/git "$@"\n' > shim/git
chmod +x shim/git
TG5ERR=$(TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID4 PATH="$PWD/shim:$PATH" \
         $T verdict "$TG_ID4" retracted --cause wrong --basis kill 2>&1); TG5RC=$?
if [ "$TG5RC" -ne 0 ] && printf '%s\n' "$TG5ERR" | grep -q "cannot verify citations"; then
  ok "TG5: git-grep unavailable refuses loudly (fails CLOSED)"
else
  miss "TG5: unavailable grep did not fail closed (rc=$TG5RC)"
fi
echo "cited again: $TG_ID4" > docs/specs/spec-b.md
git add -A && git commit -qm "tg: spec-b" --no-verify -q
TG6OUT=$($T citations "$TG_ID4" tr-deadbeef 2>/dev/null); TG6RC=$?
if [ "$TG6RC" -eq 6 ] && printf '%s\n' "$TG6OUT" | grep -q "spec-b.md" \
   && printf '%s\n' "$TG6OUT" | grep -q "tr-deadbeef: clean"; then
  ok "TG6: preflight lists the citing file, marks the clean id, exits 6"
else
  miss "TG6: preflight contract broken (rc=$TG6RC)"
fi
TG7RC=0
( cd docs && TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID4 \
  python3 ../scripts/truth verdict "$TG_ID4" retracted --cause wrong --basis kill \
  >/dev/null 2>&1 ) || TG7RC=$?
if [ "$TG7RC" -eq 6 ]; then
  ok "TG7: the sweep still refuses from a subdirectory (SI-2 cwd anchor)"
else
  miss "TG7: subtree cwd truncated the sweep (rc=$TG7RC)"
fi
printf 'nosuch-dir/**\n' > .truth/citation-scope
TG8ERR=$(TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID4 $T verdict "$TG_ID4" retracted \
         --cause wrong --basis kill 2>&1 >/dev/null); TG8RC=$?
if [ "$TG8RC" -eq 0 ] && printf '%s\n' "$TG8ERR" | grep -q "dead scope"; then
  ok "TG8: dead scope voices the loud notice and the sweep proceeds"
else
  miss "TG8: dead-scope path broken (rc=$TG8RC)"
fi
TG_ID5=$($T claim "the ledger records its own id references in bases" \
         --class VERIFIED --evidence-cmd "grep data f.txt" --paths f.txt \
         2>/dev/null)
printf '.truth/**\n' > .truth/citation-scope
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID5 $T verdict "$TG_ID5" retracted \
     --cause wrong --basis "superseded; predecessor $TG_ID5 recorded here" \
     >/dev/null 2>&1; then
  ok "TG9: with the scope covering .truth/**, the ledger's own citation of the id still never blocks (structural exclusion)"
else
  miss "TG9: the ledger's own citations blocked a retraction"
fi
printf ':(exclude)docs/**\n' > .truth/citation-scope
if $T citations tr-deadbeef >/dev/null 2>&1; then
  miss "TG10: a pathspec-magic scope line was accepted"
else
  ok "TG10: a pathspec-magic scope line is refused at load (SI-1)"
fi
rm -f .truth/citation-scope
TG_ID6=$($T claim "f.txt data stays greppable for the unicode arm" \
         --class VERIFIED --evidence-cmd "grep data f.txt" --paths f.txt \
         --duplicate-ok 2>/dev/null)
printf 'cited by %s\n' "$TG_ID6" > "docs/specs/spéc-ü.md"
git add -A && git commit -qm "tg: unicode spec" --no-verify -q
TG11RC=0
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$TG_ID6 $T verdict "$TG_ID6" retracted \
  --cause wrong --basis kill >/dev/null 2>&1 || TG11RC=$?
if [ "$TG11RC" -eq 6 ]; then
  ok "TG11: a NON-ASCII-named citing file still blocks (git grep -z, SI-2 -- quotepath cannot hide it)"
else
  miss "TG11: unicode-named citing file was invisible to the sweep (fail-open, rc=$TG11RC)"
fi
# TG12 (v0.9.32): the preflight takes LEDGER ids, nothing else. A junk
# arg used to be swept literally across the corpus and reported "clean".
# Both junk shapes must refuse, name the expected shape, and sweep
# nothing; a well-formed unknown id must still answer clean at rc 0
# (the negative control -- the refusal may not swallow TG6's contract).
TG12A=$($T citations '#' 2>&1); TG12ARC=$?
TG12B=$($T citations not-an-id 2>&1); TG12BRC=$?
TG12C=$($T citations tr-deadbeef 2>/dev/null); TG12CRC=$?
if [ "$TG12ARC" -ne 0 ] && [ "$TG12BRC" -ne 0 ] \
   && printf '%s\n' "$TG12A" | grep -q "tr-hex8" \
   && printf '%s\n' "$TG12B" | grep -q "tr-hex8" \
   && ! printf '%s\n' "$TG12A" | grep -q "^#: " \
   && [ "$TG12CRC" -eq 0 ] \
   && printf '%s\n' "$TG12C" | grep -q "tr-deadbeef: clean"; then
  ok "TG12: a non-id arg is refused by shape before any sweep (both junk forms), while a well-formed unknown id still reports clean at rc 0"
else
  miss "TG12: citations accepted a non-id arg or broke the clean case (rc=$TG12ARC/$TG12BRC/$TG12CRC)"
fi
cd "$TG_PREV" || { echo "canary: cannot cd into $TG_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$TG"

# ---- FAULT RX (ADR-049, v0.9.34): the retraction cause ------------------
# A retraction records WHY, and the why carries an obligation: `restated`
# (the fact still holds) must name a successor, because deleting a live
# belief with nothing carrying it forward is the operation this gate
# exists to refuse. The check is PURE and runs BEFORE the ADR-011
# ceremony and before the ADR-036 sweep, so a malformed invocation never
# consumes a typed-id confirmation. No override flag exists.
say "FAULT RX (ADR-049): a retraction must record why, and 'restated' must name a successor"
RX="$(mktemp -d)"; TDIRS+=("$RX"); RX_PREV="$PWD"
mkrepo "$RX"
mkdir -p docs/specs
echo "data" > f.txt
# Declare the citation scope explicitly, anchored on a tracked file: the
# ADR-036 sweep runs on every retraction here, and an UNDECLARED scope
# voices its default-scope advisory (a live one voices the dead-scope
# notice) on each. RX7 is a negative control asserting the good
# retraction is advisory-SILENT, so the sandbox must not carry an
# unrelated ADR-036 notice for it to trip over. `docs/specs/**` is the
# built-in default, so RX9's cited spec stays inside the scope and the
# ordering arm keeps its teeth.
echo "rx scope anchor (cites no ledger id)" > docs/specs/anchor.md
printf 'docs/specs/**\n' > .truth/citation-scope
git add -A && git commit -qm "rx: init" --no-verify -q
RX_ID=$($T claim "f.txt holds the rx data marker" --tier P2)
RX_LINES_BEFORE=$(wc -l < .truth/claims.jsonl | tr -d ' ')

RX1ERR=$(TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_ID $T verdict "$RX_ID" retracted \
         --basis "no reason given" 2>&1); RX1RC=$?
if [ "$RX1RC" -ne 0 ] \
   && printf '%s\n' "$RX1ERR" | grep -q "ADR-049" \
   && printf '%s\n' "$RX1ERR" | grep -q -- "--cause restated" \
   && printf '%s\n' "$RX1ERR" | grep -q -- "--cause expired" \
   && printf '%s\n' "$RX1ERR" | grep -q -- "--cause wrong" \
   && [ "$(wc -l < .truth/claims.jsonl | tr -d ' ')" -eq "$RX_LINES_BEFORE" ]; then
  ok "RX1: a causeless retraction is refused, the two-question tree is printed, nothing appended"
else
  miss "RX1: causeless retraction not refused correctly (rc=$RX1RC)"
fi

# RX2: the ADR-011 surface rule -- this refusal must not teach the human
# ceremony's bypass, and there is no ADR-049 bypass for it to teach
# either (no --cause-ok exists anywhere in the CLI's surface).
if ! printf '%s\n' "$RX1ERR" | grep -q "TRUTH_HUMAN" \
   && ! $T verdict --help 2>&1 | grep -q -- "--cause-ok"; then
  ok "RX2: the cause refusal names no env-var ritual, and no --cause-ok override exists to name"
else
  miss "RX2: the cause refusal leaked the human-gate bypass, or an override flag was added"
fi

# RX3: ORDER + human-gate integrity. The pure cause check runs FIRST, so
# a well-formed --cause does NOT weaken the ceremony (each rung still
# refuses), and a missing --cause is refused by ADR-049 -- not swallowed
# by, and not swallowing, the ADR-011 ladder.
RX3A=0; $T verdict "$RX_ID" retracted --cause wrong --basis b >/dev/null 2>&1 || RX3A=$?
RX3B=0; TRUTH_HUMAN=1 $T verdict "$RX_ID" retracted --cause wrong --basis b \
        </dev/null >/dev/null 2>&1 || RX3B=$?   # headless branch, see FAULT H1
RX3C=0; TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-deadbeef $T verdict "$RX_ID" retracted \
        --cause wrong --basis b >/dev/null 2>&1 || RX3C=$?
RX3D=$($T verdict "$RX_ID" retracted --basis b 2>&1); RX3DRC=$?
if [ "$RX3A" -ne 0 ] && [ "$RX3B" -ne 0 ] && [ "$RX3C" -ne 0 ] \
   && [ "$RX3DRC" -ne 0 ] && printf '%s\n' "$RX3D" | grep -q "ADR-049" \
   && [ "$(wc -l < .truth/claims.jsonl | tr -d ' ')" -eq "$RX_LINES_BEFORE" ]; then
  ok "RX3: every ADR-011 rung still refuses with a valid --cause, and a missing cause refuses BEFORE the ceremony (order held, nothing appended)"
else
  miss "RX3: the human gate weakened or the gate order inverted (rc=$RX3A/$RX3B/$RX3C/$RX3DRC)"
fi

# RX4: `restated` says the fact still holds -- with nothing to carry it
# forward the retraction is refused. This is the user-proposed `moved`
# case, made mechanical: fix the recipe on a successor, do not tombstone
# a live belief.
RX4ERR=$(TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_ID $T verdict "$RX_ID" retracted \
         --cause restated --basis "recipe drifted; fact holds" 2>&1); RX4RC=$?
if [ "$RX4RC" -ne 0 ] && printf '%s\n' "$RX4ERR" | grep -q -- "--successor" \
   && [ "$(wc -l < .truth/claims.jsonl | tr -d ' ')" -eq "$RX_LINES_BEFORE" ]; then
  ok "RX4: 'restated' with no successor is refused (a live fact may not be deleted), nothing appended"
else
  miss "RX4: restated-without-successor was accepted (rc=$RX4RC)"
fi

# RX5: successor integrity -- shape, self-reference, unknown id, and a
# successor that is itself a tombstone.
RX_DEAD=$($T claim "f.txt rx marker, doomed successor candidate" --tier P2 --duplicate-ok 2>/dev/null)
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_DEAD $T verdict "$RX_DEAD" retracted \
  --cause wrong --basis "kill the candidate" >/dev/null 2>&1
RX5A=0; TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_ID $T verdict "$RX_ID" retracted \
        --cause restated --successor not-an-id --basis b >/dev/null 2>&1 || RX5A=$?
RX5B=0; TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_ID $T verdict "$RX_ID" retracted \
        --cause restated --successor "$RX_ID" --basis b >/dev/null 2>&1 || RX5B=$?
RX5C=0; TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_ID $T verdict "$RX_ID" retracted \
        --cause restated --successor tr-deadbeef --basis b >/dev/null 2>&1 || RX5C=$?
RX5D=$(TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_ID $T verdict "$RX_ID" retracted \
       --cause restated --successor "$RX_DEAD" --basis b 2>&1); RX5DRC=$?
if [ "$RX5A" -ne 0 ] && [ "$RX5B" -ne 0 ] && [ "$RX5C" -ne 0 ] \
   && [ "$RX5DRC" -ne 0 ] \
   && printf '%s\n' "$RX5D" | grep -q "itself retracted"; then
  ok "RX5: successor must be a tr- id, not self, present in the ledger, and not itself a tombstone"
else
  miss "RX5: successor integrity broken (rc=$RX5A/$RX5B/$RX5C/$RX5DRC)"
fi

# RX6: the happy path -- 'restated' with a live successor files and
# stores BOTH fields.
RX_SUCC=$($T claim "f.txt rx marker, restated with a stable recipe" --tier P2 --duplicate-ok 2>/dev/null)
if TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_ID $T verdict "$RX_ID" retracted \
     --cause restated --successor "$RX_SUCC" \
     --basis "recipe re-anchored" >/dev/null 2>&1 \
   && tail -1 .truth/claims.jsonl | grep -q '"cause": "restated"' \
   && tail -1 .truth/claims.jsonl | grep -q "\"successor\": \"$RX_SUCC\""; then
  ok "RX6: 'restated' with a live successor files and stores cause + successor"
else
  miss "RX6: the restated happy path did not store both fields"
fi

# RX7 (NEGATIVE CONTROL): a good retraction of a fact that really died
# files at exit 0 with ZERO advisory lines and no successor key -- the
# gate must not fire on the case it exists to permit. Advisory lines,
# not raw stderr: the commit-gate banner is ADR-034's documented CC-1
# exemption and fires on every write verb in an unwired sandbox (GS5's
# convention).
RX_OK=$($T claim "f.txt rx marker for the negative control" --tier P2 --duplicate-ok 2>/dev/null)
RX7ERR=$(TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_OK $T verdict "$RX_OK" retracted \
         --cause expired --basis "the file was deleted in 0000000" 2>&1 >/dev/null)
RX7RC=$?
if [ "$RX7RC" -eq 0 ] \
   && ! printf '%s\n' "$RX7ERR" | grep -q "^truth: advisory:" \
   && ! printf '%s\n' "$RX7ERR" | grep -q "ADR-049" \
   && tail -1 .truth/claims.jsonl | grep -q '"cause": "expired"' \
   && ! tail -1 .truth/claims.jsonl | grep -q '"successor"'; then
  ok "RX7 (negative control): a clean 'expired' retraction files at exit 0 with no advisory and no successor key"
else
  miss "RX7: the gate fired on a good retraction (rc=$RX7RC, stderr='$RX7ERR')"
fi

# RX8: the flags belong to the terminal verb only -- a recoverable
# verdict says its own why in --basis.
RX_D=$($T claim "f.txt rx marker for the diverge arm" --tier P2 --duplicate-ok 2>/dev/null)
RX8A=$(TRUTH_SESSION=s-canary-verifier $T verdict "$RX_D" diverge --cause wrong \
       --basis b 2>&1); RX8ARC=$?
RX8B=0; TRUTH_SESSION=s-canary-verifier $T verdict "$RX_D" diverge \
        --successor "$RX_SUCC" --basis b >/dev/null 2>&1 || RX8B=$?
if [ "$RX8ARC" -ne 0 ] && [ "$RX8B" -ne 0 ] \
   && printf '%s\n' "$RX8A" | grep -q "ADR-049"; then
  ok "RX8: --cause/--successor are refused on a non-terminal verdict"
else
  miss "RX8: cause/successor leaked onto a recoverable verdict (rc=$RX8ARC/$RX8B)"
fi

# RX9: ORDER against the ADR-036 sweep -- the pure check precedes the
# git-consuming one. A retraction that is BOTH causeless and cited
# refuses on ADR-049, not exit 6: nothing ran, and no ceremony was spent.
RX_TG=$($T claim "f.txt rx marker cited by a spec" --tier P2 --duplicate-ok 2>/dev/null)
echo "grounded on $RX_TG" > docs/specs/rx.md
git add -A && git commit -qm "rx: spec" --no-verify -q
RX9ERR=$(TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$RX_TG $T verdict "$RX_TG" retracted \
         --basis b 2>&1); RX9RC=$?
if [ "$RX9RC" -ne 6 ] && printf '%s\n' "$RX9ERR" | grep -q "ADR-049" \
   && ! printf '%s\n' "$RX9ERR" | grep -q "docs/specs/rx.md"; then
  ok "RX9: the pure cause check refuses BEFORE the ADR-036 git sweep (staged order, nothing ran)"
else
  miss "RX9: the citation sweep ran ahead of the cause check (rc=$RX9RC)"
fi

# RX10: the validate MIRROR. Back-compat first -- a hand-appended legacy
# retraction with NO cause must validate forever (the ledger is
# append-only and validate runs inside the commit gate). Then the three
# cross-field rules the schema deliberately cannot express (ADR-027).
RXV="$(mktemp -d)"; TDIRS+=("$RXV")
rx_line() { printf '{"id":"%s","kind":"%s","ts":"2026-07-01T00:00:00.000000+00:00","actor":"t","session":"s","payload":%s}\n' "$1" "$2" "$3"; }
rx_line tr-00000001 verdict '{"claim":"tr-00000002","verdict":"retracted","basis":"legacy, no cause"}' > "$RXV/legacy.jsonl"
rx_line tr-00000001 verdict '{"claim":"tr-00000002","verdict":"retracted","basis":"b","cause":"restated"}' > "$RXV/nosucc.jsonl"
rx_line tr-00000001 verdict '{"claim":"tr-00000002","verdict":"agree","basis":"b","cause":"wrong"}' > "$RXV/onagree.jsonl"
rx_line tr-000000e7 issue_event '{"issue":"wk-00000001","event":"cancelled","basis":"b","cause":"wrong"}' > "$RXV/onevent.jsonl"
RXV_OK=0
$T validate --stdin < "$RXV/legacy.jsonl" >/dev/null 2>&1 || RXV_OK=1
RXV_A=0; $T validate --stdin < "$RXV/nosucc.jsonl"  >/dev/null 2>&1 || RXV_A=$?
RXV_B=0; $T validate --stdin < "$RXV/onagree.jsonl" >/dev/null 2>&1 || RXV_B=$?
RXV_C=0; $T validate --stdin < "$RXV/onevent.jsonl" >/dev/null 2>&1 || RXV_C=$?
if [ "$RXV_OK" -eq 0 ] && [ "$RXV_A" -ne 0 ] && [ "$RXV_B" -ne 0 ] \
   && [ "$RXV_C" -ne 0 ]; then
  ok "RX10: validate keeps admitting a causeless LEGACY retraction, and refuses restated-without-successor, cause-on-agree, and cause-on-an-issue_event"
else
  miss "RX10: validate mirror wrong (legacy=$RXV_OK restated=$RXV_A agree=$RXV_B event=$RXV_C)"
fi
cd "$RX_PREV" || { echo "canary: cannot cd into $RX_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$RX"

# ---- FAULT ST (ADR-050, v0.9.38): the staling breakdown -----------------
# A synthetic ledger whose answer is known BY CONSTRUCTION: four claims,
# seven invalidation records forming five episodes, and four resolving
# verdicts hand-built to land one in each arm plus a second mechanical
# via `reaffirm_cleared`. Two negative controls: a verdict on a claim
# with no open staling must count NOTHING (ST5 proves it by deleting the
# line and demanding an identical report), and a ledger of pure agrees
# must report zero rather than something (ST4).
say "FAULT ST (ADR-050): the staling breakdown must reproduce a hand-built ledger's known answer"
ST="$(mktemp -d)"; TDIRS+=("$ST"); ST_PREV="$PWD"
mkrepo "$ST"
echo "data" > f.txt
git add -A && git commit -qm "st: init" --no-verify -q
st_line() { printf '{"id":"%s","kind":"%s","ts":"2026-07-01T00:00:%02d.000000+00:00","actor":"t","session":"s","payload":%s}\n' "$1" "$2" "$4" "$3"; }
st_claim() { st_line "$1" claim "{\"text\":\"st fixture claim $1\",\"evidence_class\":\"UNVERIFIED\",\"cost_tier\":\"P2\",\"ttl_days\":null}" "$2"; }
{
  st_claim tr-0000c001 1
  st_claim tr-0000c002 2
  st_claim tr-0000c003 3
  st_claim tr-0000c004 4
  # episode 1: staled by a .py watch, cleared by reaffirm's own basis
  st_line tr-0000a001 invalidation '{"claim":"tr-0000c001","commit":"abc1234","reason":"evidence paths changed","touched":["f.py"]}' 5
  st_line tr-0000b001 verdict '{"claim":"tr-0000c001","verdict":"agree","basis":"reaffirm: hash-match, no judgment re-run"}' 6
  # episode 2: staled by a .md watch, cleared by a human re-reading
  st_line tr-0000a002 invalidation '{"claim":"tr-0000c002","commit":"abc1234","reason":"evidence paths changed","touched":["d.md"]}' 7
  st_line tr-0000b002 verdict '{"claim":"tr-0000c002","verdict":"agree","basis":"re-read the doc; the sentence still holds"}' 8
  # episode 3: two path kinds, and the fact really had moved
  st_line tr-0000a003 invalidation '{"claim":"tr-0000c003","commit":"abc1234","reason":"evidence paths changed","touched":["g.py","h.md"]}' 9
  st_line tr-0000b003 verdict '{"claim":"tr-0000c003","verdict":"diverge","basis":"the number moved"}' 10
  # episode 4: opened once, re-staled TWICE while still open (not three
  # stalings), cleared mechanically by the reaffirm_cleared record
  st_line tr-0000a004 invalidation '{"claim":"tr-0000c001","commit":"abc1234","reason":"evidence paths changed","touched":["f.py"]}' 11
  st_line tr-0000a005 invalidation '{"claim":"tr-0000c001","commit":"abc1234","reason":"evidence paths changed","touched":["f.py"]}' 12
  st_line tr-0000a006 invalidation '{"claim":"tr-0000c001","commit":"abc1234","reason":"evidence paths changed","touched":["f.py"]}' 13
  # NEGATIVE CONTROL: c4 has never been invalidated, so this agree
  # answers no staling and must land in no column at all
  st_line tr-0000b004 verdict '{"claim":"tr-0000c004","verdict":"agree","basis":"first verification, nothing was stale"}' 14
  st_line tr-0000b005 verdict '{"claim":"tr-0000c001","verdict":"agree","basis":"hand-written basis, machine-cleared record","reaffirm_cleared":{"prior_anchor":"abc1234","touched":["f.py"]}}' 15
  # episode 5: pathless (a TTL expiry names no touched file) and left open
  st_line tr-0000a007 invalidation '{"claim":"tr-0000c004","commit":"abc1234","reason":"ttl expired","reason_code":"ttl"}' 16
} > .truth/claims.jsonl

ST_JSON=$($T staling --json 2>/dev/null)
if printf '%s\n' "$ST_JSON" | python3 -c "
import json, sys
r = json.load(sys.stdin)
want = {'mechanical_agree': 2, 'human_agree': 1, 'true_stale': 1,
        'false_stale': 3, 'resolved': 4, 'unresolved': 1}
sys.exit(0 if all(r.get(k) == v for k, v in want.items()) else 1)"; then
  ok "ST1: the three arms reproduce the hand-built answer (2 mechanical, 1 human, 1 true, 4 resolved, 1 unresolved)"
else
  miss "ST1: staling breakdown wrong: $ST_JSON"
fi

if printf '%s\n' "$ST_JSON" | python3 -c "
import json, sys
r = json.load(sys.stdin)
sys.exit(0 if (r['invalidations'] == 7 and r['restaled'] == 2
               and r['stalings'] == 5
               and r['stalings'] == r['resolved'] + r['unresolved']) else 1)"; then
  ok "ST2: seven invalidation records fold to FIVE stalings (two re-staled an already-stale claim), and stalings == resolved + unresolved"
else
  miss "ST2: episode accounting wrong (a re-scan of an unanswered staling was counted as a new one): $ST_JSON"
fi

if printf '%s\n' "$ST_JSON" | python3 -c "
import json, sys
r = json.load(sys.stdin)
sys.exit(0 if (r['by_path_kind'] == [{'kind': '.py', 'stalings': 3},
                                     {'kind': '.md', 'stalings': 2}]
               and r['pathless'] == 1) else 1)"; then
  ok "ST3: path kinds rank .py=3 over .md=2, and the pathless staling is counted separately, never invented as a kind"
else
  miss "ST3: watched-path-kind breakdown wrong: $ST_JSON"
fi

# ST4 (NEGATIVE CONTROL): a ledger with verdicts but no invalidation has
# no stalings to break down. An implementation that counted verdicts
# instead of answered stalings reddens here.
ST_N="$(mktemp -d)"; TDIRS+=("$ST_N")
cp .truth/claims.jsonl "$ST_N/keep.jsonl"
{
  st_claim tr-0000c001 1
  st_line tr-0000b001 verdict '{"claim":"tr-0000c001","verdict":"agree","basis":"reaffirm: hash-match, no judgment re-run"}' 6
  st_line tr-0000b002 verdict '{"claim":"tr-0000c001","verdict":"agree","basis":"a human read it"}' 8
  st_line tr-0000b003 verdict '{"claim":"tr-0000c001","verdict":"diverge","basis":"it moved"}' 10
} > .truth/claims.jsonl
ST4_JSON=$($T staling --json 2>/dev/null)
ST4_TXT=$($T staling 2>/dev/null)
if printf '%s\n' "$ST4_JSON" | python3 -c "
import json, sys
r = json.load(sys.stdin)
sys.exit(0 if all(r[k] == 0 for k in
                  ('invalidations', 'restaled', 'stalings', 'resolved',
                   'unresolved', 'mechanical_agree', 'human_agree',
                   'true_stale', 'false_stale', 'pathless'))
         and r['by_path_kind'] == [] else 1)" \
   && printf '%s\n' "$ST4_TXT" | grep -q "no invalidations in range"; then
  ok "ST4 (negative control): three verdicts and no invalidation report ZERO stalings, and say so in plain text"
else
  miss "ST4: a verdict answering no staling was counted: $ST4_JSON"
fi

# ST5 (NEGATIVE CONTROL): the same property proved by deletion. Drop the
# one verdict on the never-invalidated claim; the report must come out
# BYTE-IDENTICAL. If the fold credited it to any column, this reddens.
cp "$ST_N/keep.jsonl" .truth/claims.jsonl
grep -v '"first verification, nothing was stale"' .truth/claims.jsonl \
  > "$ST_N/pruned.jsonl"
ST5_BEFORE=$($T staling --json 2>/dev/null)
ST5_LINES=$(wc -l < "$ST_N/pruned.jsonl" | tr -d ' ')
cp "$ST_N/pruned.jsonl" .truth/claims.jsonl
ST5_AFTER=$($T staling --json 2>/dev/null)
if [ "$ST5_LINES" -eq 15 ] && [ -n "$ST5_BEFORE" ] \
   && [ "$ST5_BEFORE" = "$ST5_AFTER" ]; then
  ok "ST5 (negative control): deleting the verdict on the never-invalidated claim leaves the report identical -- it was credited to nothing"
else
  miss "ST5: the report moved when a staling-less verdict was removed (pruned to $ST5_LINES lines)"
fi

# ST6: the arms above must be reading a LEGAL ledger, not junk that only
# this verb tolerates (a check that examined nothing is a failure), and
# the read verb must stay banner-free on this deliberately unwired clone
# (the FAULT VC rule: satellites poll read verbs and stderr noise trains
# 2>/dev/null).
cp "$ST_N/keep.jsonl" .truth/claims.jsonl
ST6_V=0; $T validate >/dev/null 2>&1 || ST6_V=$?
ST6_ERR=$($T staling 2>&1 >/dev/null)
if [ "$ST6_V" -eq 0 ] && [ -z "$ST6_ERR" ] \
   && $T staling 2>/dev/null | grep -q "^the fact had NOT changed: 3 (mechanical 2, human 1)$"; then
  ok "ST6: the fixture passes validate (16 legal records), the read verb prints no banner, and the plain line is greppable"
else
  miss "ST6: fixture illegal (validate rc=$ST6_V), banner leaked [$ST6_ERR], or plain output changed shape"
fi
# ST7/ST8 (ADR-050 decision 4): ORDER. A ledger whose append order and
# whose fold order genuinely disagree -- the union-merge shape, where a
# verdict was appended before an invalidation that predates it. The verb
# must walk the fold's (ts, id, canon) order (a staling is a status
# transition, and status is DEFINED by that order), while
# --append-order reproduces the file walk. The two answers must DIFFER,
# or the fixture has no teeth and the flag is a no-op.
{
  st_claim tr-0000c001 1
  st_line tr-0000a001 invalidation '{"claim":"tr-0000c001","commit":"abc1234","reason":"evidence paths changed","touched":["f.py"]}' 10
  st_line tr-0000b001 verdict '{"claim":"tr-0000c001","verdict":"diverge","basis":"appended first, but dated later"}' 12
  st_line tr-0000a002 invalidation '{"claim":"tr-0000c001","commit":"abc1234","reason":"evidence paths changed","touched":["f.py"]}' 11
  st_line tr-0000b002 verdict '{"claim":"tr-0000c001","verdict":"agree","basis":"reaffirm: hash-match, no judgment re-run"}' 13
} > .truth/claims.jsonl
ST7_JSON=$($T staling --json 2>/dev/null)
ST8_JSON=$($T staling --append-order --json 2>/dev/null)
if printf '%s\n' "$ST7_JSON" | python3 -c "
import json, sys
r = json.load(sys.stdin)
sys.exit(0 if (r['order'] == 'fold' and r['resolved'] == 1
               and r['restaled'] == 1 and r['stalings'] == 1
               and r['mechanical_agree'] == 0
               and r['true_stale'] == 1) else 1)"; then
  ok "ST7: the verb walks FOLD order -- the back-dated invalidation joins the open episode instead of opening a second one (ADR-016/ADR-050)"
else
  miss "ST7: staling did not sort by fold_key: $ST7_JSON"
fi
if printf '%s\n' "$ST8_JSON" | python3 -c "
import json, sys
r = json.load(sys.stdin)
sys.exit(0 if (r['order'] == 'append' and r['resolved'] == 2
               and r['restaled'] == 0 and r['stalings'] == 2
               and r['mechanical_agree'] == 1
               and r['true_stale'] == 1) else 1)" \
   && [ "$ST7_JSON" != "$ST8_JSON" ]; then
  ok "ST8: --append-order reproduces the raw FILE walk, and its answer DIFFERS from the fold walk (the fixture has teeth, the flag is not a no-op)"
else
  miss "ST8: append-order walk wrong or identical to the fold walk: $ST8_JSON"
fi
cd "$ST_PREV" || { echo "canary: cannot cd into $ST_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$ST" "$ST_N"

# ---- FAULT RC (ADR-037, v0.9.23): recipe lints + generated-paths --------
say "FAULT RC (ADR-037): recipe rot classes warn; generated-artifact watches refuse"
RC="$(mktemp -d)"; TDIRS+=("$RC"); RC_PREV="$PWD"
mkrepo "$RC"
mkdir -p gen
echo "data" > f.txt
echo "out" > gen/out.csv
git add -A && git commit -qm "rc: init" --no-verify -q
RC1ERR=$($T claim "f.txt line one carries the data marker" --class VERIFIED \
         --evidence-cmd "grep -n data f.txt" --paths f.txt 2>&1 >/dev/null)
if printf '%s\n' "$RC1ERR" | grep -q "advisory: recipe: -n"; then
  ok "RC1: grep -n earns the line-number lint"
else
  miss "RC1: -n lint missing"
fi
RC1B=$($T claim "f.txt sorts its data content stably" --class VERIFIED \
       --evidence-cmd "grep data f.txt | sort -n" --paths f.txt \
       --duplicate-ok 2>&1 >/dev/null)
if printf '%s\n' "$RC1B" | grep -q "advisory: recipe: -n"; then
  miss "RC1b: sort -n false-fired the grep lint (segment blindness)"
else
  ok "RC1b: sort -n does not fire the grep -n lint (per-segment)"
fi
RC2ERR=$($T claim "the banner in f.txt names the current release train" \
         --class VERIFIED --evidence-cmd "grep v9.9.9 f.txt" --paths f.txt \
         --evidence-exit-ok "banner probe exits 1 until the banner lands" \
         2>&1 >/dev/null)
if printf '%s\n' "$RC2ERR" | grep -q "'v9.9.9' is a volatile literal"; then
  ok "RC2: a version-shaped literal warns naming the token"
else
  miss "RC2: version literal lint missing"
fi
RC3ERR=$($T claim "the schema id anchor and dated path stay greppable" \
         --class VERIFIED \
         --evidence-cmd "grep truth-ledger-record.v0 f.txt | cat docs-2026-01-01/x.md" \
         --paths f.txt --duplicate-ok --evidence-exit-ok "compound absence probe" \
         2>&1 >/dev/null)
RC3N=$(git -C . rev-parse >/dev/null 2>&1; tail -1 .truth/claims.jsonl | grep -c '"kind": "claim"')
if printf '%s\n' "$RC3ERR" | grep -q "volatile literal\|date-shaped"; then
  miss "RC3: a carve-out class false-fired (schema-id or path token)"
elif [ "$RC3N" -ne 1 ]; then
  miss "RC3: the carve-out filing never appended (vacuous arm)"
else
  ok "RC3: schema-\$id and path-context tokens do not warn (carve-outs, filing appended)"
fi
printf 'gen/**\n' > .truth/generated-paths
RC4ERR=$($T claim "regeneration rewrites the csv artifact between runs" \
         --class INFERRED --basis b --paths "gen/out.csv" 2>&1); RC4RC=$?
if [ "$RC4RC" -ne 0 ] && printf '%s\n' "$RC4ERR" | grep -q "generated-artifact list"; then
  ok "RC4: an INFERRED watch on a generated path is refused (INV-M stance)"
else
  miss "RC4: generated watch not refused for a non-VERIFIED class (rc=$RC4RC)"
fi
$T claim "the shipped csv artifact itself is the customer-read fact" \
   --class INFERRED --basis b --paths "gen/out.csv" \
   --generated-ok "the artifact is the deliverable" >/dev/null 2>&1
if python3 -c "import json,sys; p=json.loads(open('.truth/claims.jsonl').read().splitlines()[-1])['payload']; sys.exit(0 if p.get('generated_ok_basis') and p.get('ttl_default') is True and p.get('ttl_days')==30 else 1)"; then
  ok "RC4b: --generated-ok stores the basis and takes the ADR-032 default decay"
else
  miss "RC4b: generated override basis/decay not stamped"
fi
rm .truth/generated-paths
RC5ERR=$($T claim "f.txt keeps the data marker for the absent-list arm" \
         --class VERIFIED --evidence-cmd "grep -n data f.txt" --paths f.txt \
         --duplicate-ok 2>&1 >/dev/null)
if printf '%s\n' "$RC5ERR" | grep -q "generated-artifact check is dark" \
   && printf '%s\n' "$RC5ERR" | grep -q "advisory: recipe: -n"; then
  ok "RC5: absent list voices the dark notice; the lints still fire"
else
  miss "RC5: absent-list degradation broken"
fi
cp "$HERE/../.truth/generated-paths" .truth/generated-paths
RC6ERR=$($T claim "f.txt plainly carries its committed marker line" \
         --class VERIFIED --evidence-cmd "grep data f.txt" --paths f.txt \
         --duplicate-ok 2>&1 >/dev/null)
RC6N=$(tail -1 .truth/claims.jsonl | grep -c '"kind": "claim"')
if printf '%s\n' "$RC6ERR" | grep -q "^truth: advisory:"; then
  miss "RC6: a clean filing under the shipped empty list printed advisories"
elif [ "$RC6N" -ne 1 ]; then
  miss "RC6: the clean filing never appended (vacuous arm)"
else
  ok "RC6: committed-empty list is conscious policy -- silence on clean (SI-4)"
fi
RC7ERR=$($T claim "the quote-split literal still reads as one token" \
         --class VERIFIED --evidence-cmd "grep 'v9.8''.7' f.txt" --paths f.txt \
         --duplicate-ok --evidence-exit-ok "absence probe for the split literal" \
         2>&1 >/dev/null)
if printf '%s\n' "$RC7ERR" | grep -q "volatile literal"; then
  ok "RC7: a quote-split version literal still warns (shlex token stream, one parser)"
else
  miss "RC7: quote-splitting evaded the volatile-literal lint"
fi
RC8ERR=$($T claim "the dropped generated override must not decay" \
         --class INFERRED --basis b --paths f.txt \
         --generated-ok "matches nothing on the list" 2>&1 >/dev/null)
RC8OK=$(python3 -c "import json; p=json.loads(open('.truth/claims.jsonl').read().splitlines()[-1])['payload']; print('ok' if 'generated_ok_basis' not in p and not p.get('ttl_default') and p.get('ttl_days') is None else 'bad')")
if [ "$RC8OK" = ok ] && printf '%s\n' "$RC8ERR" | grep -q "NOT.*stored\|was NOT"; then
  ok "RC8: a --generated-ok that matched nothing is voiced, not stored, and does NOT decay"
else
  miss "RC8: dropped override stored or decayed silently (state=$RC8OK)"
fi
cd "$RC_PREV" || { echo "canary: cannot cd into $RC_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$RC"

# ---- FAULT DW (ADR-038, v0.9.24): the dirty-watch advisory --------------
say "FAULT DW (ADR-038): a claim watching uncommitted content must hear about restale-at-birth"
DW="$(mktemp -d)"; TDIRS+=("$DW"); DW_PREV="$PWD"
mkrepo "$DW"
mkdir -p ns
echo "data" > f.txt
echo "keep" > other.txt
git add -A && git commit -qm "dw: init" --no-verify -q
echo "pending" >> f.txt
DW1=$($T claim "f.txt carries data plus a pending line" --class VERIFIED \
      --evidence-cmd "grep data f.txt" --paths f.txt 2>&1 >/dev/null)
if printf '%s\n' "$DW1" | grep -q "dirty watch: f.txt"; then
  ok "DW1: a modified watched path earns the restale-at-birth advisory"
else
  miss "DW1: dirty watched path stayed silent"
fi
git checkout -q f.txt
DW2=$($T claim "f.txt carries just the committed data line" --class VERIFIED \
      --evidence-cmd "grep data f.txt" --paths f.txt --duplicate-ok \
      2>&1 >/dev/null)
DW2N=$(tail -1 .truth/claims.jsonl | grep -c '"kind": "claim"')
if ! printf '%s\n' "$DW2" | grep -q "dirty watch" && [ "$DW2N" -eq 1 ]; then
  ok "DW2: a clean tree files silently (negative control, appended)"
else
  miss "DW2: clean filing printed a dirty-watch line or never appended"
fi
echo "x" > unrelated.txt
DW3=$($T claim "f.txt data survives beside an unrelated dirty file" \
      --class VERIFIED --evidence-cmd "grep data f.txt" --paths f.txt \
      --duplicate-ok 2>&1 >/dev/null)
if printf '%s\n' "$DW3" | grep -q "dirty watch"; then
  miss "DW3: an unwatched dirty file false-fired the advisory"
else
  ok "DW3: dirtiness outside the watch stays silent (fatigue budget)"
fi
rm -f unrelated.txt
echo "seed" > ns/new-thing.txt
DW4=$($T claim "the ns namespace is filling with seeded content" \
      --class VERIFIED --evidence-cmd "grep data f.txt" --paths "ns/**" \
      2>&1 >/dev/null)
if printf '%s\n' "$DW4" | grep -q "dirty watch: ns/new-thing.txt"; then
  ok "DW4: an UNTRACKED file under a glob watch fires (the INV-M glob-exemption vector)"
else
  miss "DW4: untracked-under-glob stayed dark"
fi
rm -f ns/new-thing.txt
git mv other.txt moved.txt
# The OLD name leaves the index on git mv, so a literal watch on it is
# INV-M-dead (correctly refused); the arm watches the NEW name and the
# rename entry must fire via either of its two NUL fields.
# Step 3.2: two paths, so the freehand budget wants a stated basis. The
# arm needs BOTH names deliberately -- the old one to show it is
# INV-M-dead after the mv, the new one to catch the rename entry -- which
# is exactly the "this set is right and no policy fits" case --paths-ok
# exists for.
DW6=$($T claim "the rename keeps its keep marker under the new watch" \
      --class VERIFIED --evidence-cmd "grep keep moved.txt" \
      --paths f.txt,moved.txt --duplicate-ok \
      --paths-ok "the arm needs the pre-mv and post-mv names together to see the rename entry" \
      2>&1 >/dev/null) || true
if printf '%s\n' "$DW6" | grep -q "dirty watch: moved.txt"; then
  ok "DW6: an uncommitted git mv fires on the rename entry (two-field parse)"
else
  miss "DW6: rename entry invisible to the watch"
fi
git commit -qm "dw: land rename" --no-verify -q
printf 'plain ascii\n' > "spät-ü.txt"
git add "spät-ü.txt" && git commit -qm "dw: unicode" --no-verify -q
echo "dirt" >> "spät-ü.txt"
DW7=$($T claim "the unicode-named file carries pending dirt" \
      --class VERIFIED --evidence-cmd "grep data f.txt" \
      --paths "sp*.txt" 2>&1 >/dev/null)
if printf '%s\n' "$DW7" | grep -q "dirty watch: sp"; then
  ok "DW7: a NON-ASCII-named dirty watch still fires (-z, SI-2 -- quotepath cannot hide it)"
else
  miss "DW7: unicode-named dirty file invisible (quotepath fail-open)"
fi
git checkout -q -- "spät-ü.txt"
git checkout -q -b dw-side
printf 'side\n' > f.txt && git add f.txt && git commit -qm side --no-verify -q
git checkout -q main
printf 'main\n' > f.txt && git add f.txt && git commit -qm mainline --no-verify -q
git merge -q dw-side >/dev/null 2>&1 || true
DW8=$($T claim "f.txt sits mid-conflict while this files" --class VERIFIED \
      --evidence-cmd "cat .truth/evidence-allow" --paths f.txt \
      --duplicate-ok 2>&1 >/dev/null)
if printf '%s\n' "$DW8" | grep -q "dirty watch: f.txt"; then
  ok "DW8: the UU both-modified conflict state fires (structural dirtiness -- the QB-011 scenario)"
else
  miss "DW8: mid-merge conflict invisible to the advisory"
fi
cd "$DW_PREV" || { echo "canary: cannot cd into $DW_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$DW"

# ---- FAULT BF (ADR-039, v0.9.25): blast forecast + churn report ---------
say "FAULT BF (ADR-039): a hot watch must voice its blast forecast; cold, shallow and unborn repos must degrade loudly or silently as designed"
BF="$(mktemp -d)"; TDIRS+=("$BF"); BF_PREV="$PWD"
mkrepo "$BF"
echo "w0" > w.txt
echo "cold" > cold.txt
git add -A && git commit -qm "bf: init" --no-verify -q
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16; do
  echo "w$i" >> w.txt && git commit -aqm "bf: touch $i" --no-verify -q
done
# Step 3.2 LAYERED this arm rather than replacing it. The ADR-039
# forecast now drives BOTH a refusal and the advisory, at one threshold,
# and which one you get says something: an UN-EXCUSED hot watch is
# refused, an ACCEPTED one is filed and told what it costs. So BF1 is two
# arms now -- the refusal must fire, and the advisory must still voice
# for the claim that took an exit. Either half going silent is the
# regression this pair exists to catch.
BF1R=$($T claim "w.txt keeps accumulating its numbered lines" --class VERIFIED \
       --evidence-cmd "grep w0 w.txt" --paths w.txt 2>&1 >/dev/null)
if printf '%s\n' "$BF1R" | grep -q "at or above the churn floor"; then
  ok "BF1a: an un-excused hot watch (>=floor commits/30d) is REFUSED"
else
  miss "BF1a: hot watch filed with no refusal and no basis"
fi
BF1=$($T claim "w.txt keeps accumulating its numbered lines" --class VERIFIED \
      --evidence-cmd "grep w0 w.txt" --paths w.txt \
      --paths-ok "the claim is ABOUT this file accumulating, so the hot watch is the subject" \
      2>&1 >/dev/null)
if printf '%s\n' "$BF1" | grep -q "blast: watch matched 1[0-9] commits"; then
  ok "BF1b: an ACCEPTED hot watch still voices the upper-bound advisory"
else
  miss "BF1b: hot watch stayed silent"
fi
# BF4 FLIPPED by ADR-046 (the item-2 red-proof arm): the forecast is
# computed on read and NEVER stamped -- the payload must NOT carry
# blast_forecast while the BF1 advisory above still voiced at/above the
# floor from the live computation. Legacy stored ints stay validate-
# tolerated (checked by appending one).
BF4OK=$(python3 -c "import json; p=json.loads(open('.truth/claims.jsonl').read().splitlines()[-1])['payload']; print('ok' if 'blast_forecast' not in p else 'bad')")
BF4LEGACY='{"id": "tr-00bf4bf4", "kind": "claim", "actor": "canary", "session": "s-legacy", "ts": "2026-01-01T00:00:00.000000+00:00", "payload": {"text": "legacy forecast line for BF4", "evidence_class": "UNVERIFIED", "cost_tier": "P2", "ttl_days": null, "evidence_paths": ["w.txt"], "blast_forecast": 3}}'
if [ "$BF4OK" = ok ] && printf '%s\n' "$BF1" | grep -q "blast: watch matched" \
   && $T validate >/dev/null 2>&1 \
   && printf '%s\n' "$BF4LEGACY" | $T validate --stdin >/dev/null 2>&1; then
  ok "BF4: blast_forecast NOT stored (ADR-046 computed-on-read) while the advisory still voiced; validate keeps admitting a legacy stored line"
else
  miss "BF4: forecast stamped again, advisory dark, or legacy line refused (state=$BF4OK)"
fi
BF2=$($T claim "cold.txt sits untouched since the initial commit" \
      --class VERIFIED --evidence-cmd "grep cold cold.txt" --paths cold.txt \
      2>&1 >/dev/null)
if printf '%s\n' "$BF2" | grep -q "^truth: advisory: blast:"; then
  miss "BF2: a cold watch printed a blast line (fatigue budget broken)"
else
  ok "BF2: a sub-floor watch stays silent (negative control)"
fi
GIT_COMMITTER_DATE="2026-01-01T00:00:00 +0000" GIT_AUTHOR_DATE="2026-01-01T00:00:00 +0000" \
  bash -c 'echo old >> cold.txt && git commit -aqm "bf: backdated" --no-verify -q'
BF6N=$(python3 -c "
import sys; sys.path.insert(0, 'scripts')
import importlib.machinery, importlib.util
ld = importlib.machinery.SourceFileLoader('t', 'scripts/truth')
sp = importlib.util.spec_from_loader('t', ld); t = importlib.util.module_from_spec(sp); ld.exec_module(t)
hist, state = t.blast_history()
print(t.blast_forecast(['cold.txt'], hist) if state == 'ok' else 'ERR')")
BF6W=$(python3 -c "
import sys; sys.path.insert(0, 'scripts')
import importlib.machinery, importlib.util
ld = importlib.machinery.SourceFileLoader('t', 'scripts/truth')
sp = importlib.util.spec_from_loader('t', ld); t = importlib.util.module_from_spec(sp); ld.exec_module(t)
hist, state = t.blast_history()
print(t.blast_forecast(['w.txt'], hist) if state == 'ok' else 'ERR')")
# cold.txt has exactly ONE legitimate in-window commit (bf: init); the
# backdated touch must be filtered OUT (count stays 1, does not become
# 2) while the hot watch still counts fully -- a plain --since would
# stop the traversal at the backdated tip and read BOTH as 0.
if [ "$BF6N" = "1" ] && [ "$BF6W" -ge 16 ] 2>/dev/null; then
  ok "BF6: the backdated commit is filtered OUT (cold stays 1, hot stays $BF6W) -- a filter, not a traversal stop"
else
  miss "BF6: window semantics broken (cold=$BF6N hot=$BF6W -- a plain --since would empty the log here)"
fi
# BF5 RETIRED (ADR-046): the stats blast section left the template CLI
# (Tier C). Its render assertion (floor + observed-vs-forecast rows)
# moved to scripts/test-instruments.sh, driven through
# instruments/blast-report.py against the identical hot-watch fixture.
BFSH="$(mktemp -d)"; TDIRS+=("$BFSH")
git clone -q --depth 1 "file://$PWD" "$BFSH/shallow" 2>/dev/null
( cd "$BFSH/shallow" && mkdir -p .truth scripts \
  && cp "$BF/scripts/truth" scripts/truth \
  && cp -R "$BF/truthlib" truthlib \
  && cp "$BF/.truth/evidence-allow" .truth/ \
  && cp "$BF/.truth/generated-paths" .truth/ 2>/dev/null; touch .truth/claims.jsonl
  BF3=$(TRUTH_ACTOR=canary TRUTH_SESSION=s-bf python3 scripts/truth claim \
        "w.txt carries its numbered lines in the shallow clone" \
        --class VERIFIED --evidence-cmd "grep w0 w.txt" --paths w.txt \
        2>&1 >/dev/null)
  if printf '%s\n' "$BF3" | grep -q "blast: shallow history"; then
    echo "BF3-OK" > "$BFSH/bf3"
  fi )
if [ -f "$BFSH/bf3" ]; then
  ok "BF3: a shallow clone voices the floor-not-bound notice, never a quietly-cold number"
else
  miss "BF3: shallow history degraded silently"
fi
rm -rf "$BFSH"
BFU="$(mktemp -d)"; TDIRS+=("$BFU")
( cd "$BFU" && git init -q -b main . && git config user.email t@t \
  && git config user.name t && mkdir -p .truth scripts \
  && cp "$BF/scripts/truth" scripts/truth \
  && cp -R "$BF/truthlib" truthlib \
  && cp "$BF/.truth/evidence-allow" .truth/ && touch .truth/claims.jsonl \
  && echo seed > s.txt && git add -A
  BF7=$(TRUTH_ACTOR=canary TRUTH_SESSION=s-bf python3 scripts/truth claim \
        "the seeded file exists before the first commit lands" \
        --class INFERRED --basis b --paths s.txt 2>&1 >/dev/null)
  if printf '%s\n' "$BF7" | grep -q "blast: history unavailable" \
     && ! tail -1 .truth/claims.jsonl | grep -q blast_forecast; then
    echo "BF7-OK" > .bf7
  fi )
if [ -f "$BFU/.bf7" ]; then
  ok "BF7: an unborn-HEAD repo voices history-unavailable and stores no forecast"
else
  miss "BF7: unborn HEAD read as a quietly-cold forecast"
fi
rm -rf "$BFU"
cd "$BF_PREV" || { echo "canary: cannot cd into $BF_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$BF"

# ---- FAULT VC (P2 contract layer, v0.9.27): the vocab verb --------------
# `truth vocab` exports the machine vocabulary; spec-health/fact-health
# source their citation-blocking set from it at runtime, so the R1
# hand-copy drift class is structurally closed: removing `disputed` from
# CITATION_BAD reddens VC1 AND the S2D / fact-health disputed arms
# together (proven in the P2 red-run) -- that cascade is the contract.
say "FAULT VC (P2): vocab --json exports the contract; the read verb stays banner-free"
VC="$(mktemp -d)"; TDIRS+=("$VC"); VC_PREV="$PWD"
mkrepo "$VC"
echo "data" > f.txt
git add -A && git commit -qm "vc: init" --no-verify -q
VC1OUT=$($T vocab --json 2>/dev/null)
if printf '%s\n' "$VC1OUT" | python3 -c "
import json, sys
v = json.load(sys.stdin)
ok = ('disputed' in v['citation_bad']
      and set(v['active']) == {'live', 'unverified'}
      and set(v['verdicts']) == {'agree', 'diverge', 'cannot_verify',
                                 'retracted'}
      and set(v['citation_bad']) <= set(v['statuses'])
      and 'disputed' in v['premise_blocking']
      and 'unverified' in v['premise_warn'])
sys.exit(0 if ok else 1)"; then
  ok "VC1: vocab --json parses; citation_bad carries disputed; the sets cohere"
else
  miss "VC1: vocab contract broken: $VC1OUT"
fi
# VC2: one greppable line per key, and NO commit-gate banner -- this
# sandbox is deliberately unwired, so a write verb would print it; the
# satellites poll vocab on every sweep and banner noise would train
# 2>/dev/null (the exemption a read verb earns by changing nothing).
VC2ERR=$($T vocab 2>&1 >/dev/null)
VC2OUT=$($T vocab 2>/dev/null)
if [ -z "$VC2ERR" ] && printf '%s\n' "$VC2OUT" | grep -q "^citation_bad: .*disputed"; then
  ok "VC2: plain output greppable (citation_bad line) and zero stderr on an unwired clone"
else
  miss "VC2: plain vocab output or read-verb silence broken (stderr=[$VC2ERR])"
fi
cd "$VC_PREV" || { echo "canary: cannot cd into $VC_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$VC"

# ---- FAULT UM (union merge): the headline sync path, driven for real ----
# Union-merge confluence was only ever validated by in-process permutation
# (B6) and a hand-duplicated line (B2); the merge=union attribute binding
# itself -- the path git actually takes when two sessions' branches meet
# -- was untested. Two branches append distinct claims, git merges them,
# and the fold must come out identical in BOTH merge directions.
# NB: this arm pins the UNGATED merge behavior (no hooks installed); the
# deferred gate-fires assertion lives in UM5-UM7 below (ADR-045/D3).
say "FAULT UM (union merge): branch ledgers must merge conflict-free, keep both sides, validate, and fold direction-independently"
UM="$(mktemp -d)"; TDIRS+=("$UM"); UM_PREV="$PWD"
mkrepo "$UM"   # NB: mkrepo cd's into $UM. No subshell -- ok/miss mutate the
               # PASS/FAIL counters; cwd restored via $UM_PREV below.
echo ".truth/claims.jsonl merge=union" >> .gitattributes   # committed BEFORE branching
git add -A && git commit -qm "um: init (union attribute first)" --no-verify -q
CID_UM0=$($T claim "um base fact stands committed" --class UNVERIFIED --tier P2 2>/dev/null)
git add .truth/claims.jsonl && git commit -qm "um: base claim" --no-verify -q
git checkout -qb um-side
CID_UMA=$(TRUTH_SESSION=s-um-side $T claim "um side branch filed its own fact" --class UNVERIFIED --tier P2 2>/dev/null)
git add .truth/claims.jsonl && git commit -qm "um: side claim" --no-verify -q
git checkout -q main
CID_UMB=$(TRUTH_SESSION=s-um-main $T claim "um mainline filed a different fact" --class UNVERIFIED --tier P2 2>/dev/null)
git add .truth/claims.jsonl && git commit -qm "um: main claim" --no-verify -q
UMR="$(mktemp -d)"; TDIRS+=("$UMR")   # pre-merge clone for the reverse direction
git clone -q "$PWD" "$UMR/rev" 2>/dev/null
git merge -q --no-edit um-side >/dev/null 2>&1   # direction A: main <- side
if grep -q "<<<<<<<" .truth/claims.jsonl; then
  miss "UM1: union merge left conflict markers in the ledger (merge=union not bound)"
else
  ok "UM1: merged ledger carries no conflict markers"
fi
if [ -n "$CID_UMA" ] && [ -n "$CID_UMB" ] \
   && grep -q "$CID_UMA" .truth/claims.jsonl \
   && grep -q "$CID_UMB" .truth/claims.jsonl; then
  ok "UM2: both sides' claims survive the merge ($CID_UMA + $CID_UMB)"
else
  miss "UM2: a side's claim vanished in the merge (side=${CID_UMA:-unfiled} main=${CID_UMB:-unfiled})"
fi
if $T validate >/dev/null 2>&1; then
  ok "UM3: validate accepts the union-merged ledger (exit 0; an ADR-008 order warning on stderr is tolerable)"
else
  miss "UM3: validate refused the union-merged ledger"
fi
UM_FOLD='import json,sys; print(sorted((r["id"], r["status"]) for r in json.load(sys.stdin)))'
UM_A=$($T list --json 2>/dev/null | python3 -c "$UM_FOLD")
UM_B=$( cd "$UMR/rev" \
        && git checkout -q um-side 2>/dev/null \
        && git merge -q --no-edit main >/dev/null 2>&1 \
        && python3 scripts/truth list --json 2>/dev/null | python3 -c "$UM_FOLD" )
if [ -n "$UM_A" ] && [ "$UM_A" = "$UM_B" ]; then
  ok "UM4: the opposite-direction merge folds to the identical id->status map"
else
  miss "UM4: fold changed with merge direction (a=[$UM_A] b=[$UM_B])"
fi
cd "$UM_PREV" || { echo "canary: cannot cd into $UM_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$UM" "$UMR"

# ---- FAULT UM5-UM7 (ADR-045/D3): the pre-merge-commit hook gates the ----
# ---- merge-commit class the union-merge sync story produces          ----
# P0 deliberately deferred the gate-fires assertion to the phase where the
# hook exists; this is that phase. Hooks land via scripts/install-hooks.sh
# so the INSTALLER itself is exercised, then: (i) the honest bidirectional
# sync must still commit THROUGH the gate (a union-merged ledger is a
# prefix extension of ours, so check-truth passes), and (ii) a branch that
# REWRITES an early committed ledger line and lands it with --no-verify
# must be BLOCKED when the union merge tries to auto-commit (non-prefix
# result, INV-A).
say "FAULT UM5-UM7 (ADR-045): pre-merge-commit gates merge commits -- honest sync passes, tampered merge refused"
UMH="$(mktemp -d)"; TDIRS+=("$UMH"); UMH_PREV="$PWD"
mkrepo "$UMH"   # NB: mkrepo cd's into $UMH; cwd restored via $UMH_PREV
cp "$HERE/install-hooks.sh" scripts/install-hooks.sh
echo ".truth/claims.jsonl merge=union" >> .gitattributes
git add -A && git commit -qm "umh: init" --no-verify -q
bash scripts/install-hooks.sh >/dev/null 2>&1
if [ -x .git/hooks/pre-merge-commit ] \
   && grep -q "check-truth" .git/hooks/pre-merge-commit; then
  ok "UM5: install-hooks.sh wrote an executable pre-merge-commit invoking check-truth"
else
  miss "UM5: installer did not wire pre-merge-commit (ADR-045)"
fi
CID_UH0=$($T claim "umh base fact stands committed" --class UNVERIFIED --tier P2 2>/dev/null)
git add .truth/claims.jsonl && git commit -qm "umh: base" -q  # NO --no-verify: the wired pre-commit gate must pass this
git checkout -qb umh-side
CID_UHA=$(TRUTH_SESSION=s-umh-side $T claim "umh side branch filed its own fact" --class UNVERIFIED --tier P2 2>/dev/null)
git add .truth/claims.jsonl && git commit -qm "umh: side" -q
git checkout -q main
CID_UHB=$(TRUTH_SESSION=s-umh-main $T claim "umh mainline filed a different fact" --class UNVERIFIED --tier P2 2>/dev/null)
git add .truth/claims.jsonl && git commit -qm "umh: main" -q
if git merge --no-edit umh-side >/dev/null 2>&1 \
   && [ ! -f "$(git rev-parse --git-dir)/MERGE_HEAD" ] \
   && grep -q "$CID_UHA" .truth/claims.jsonl \
   && grep -q "$CID_UHB" .truth/claims.jsonl; then
  ok "UM6: honest union merge auto-commits THROUGH the gate (merged ledger is a prefix extension of ours)"
else
  miss "UM6: the pre-merge-commit gate blocked (or the merge lost) an honest union merge"
fi
# RED direction: rewrite an early COMMITTED ledger line on a branch, land
# it with --no-verify, merge it back. The 3-way union takes the tampered
# line (ours left it untouched), so the staged result is NOT a prefix
# extension of ours and the new hook must refuse the merge commit.
UMH_HEAD_BEFORE=$(git rev-parse HEAD)
git checkout -qb umh-tamper
# -i.bak is the only sed -i form GNU and BSD/macOS sed both accept
sed -i.bak "s/umh base fact stands committed/umh base fact stands TAMPERED/" .truth/claims.jsonl && rm -f .truth/claims.jsonl.bak
git add .truth/claims.jsonl && git commit -qm "umh: tamper an early line" --no-verify -q
git checkout -q main
CID_UHC=$(TRUTH_SESSION=s-umh-main2 $T claim "umh mainline advanced once more" --class UNVERIFIED --tier P2 2>/dev/null)
git add .truth/claims.jsonl && git commit -qm "umh: advance main (forces a real 3-way merge, no fast-forward)" -q
git merge --no-edit umh-tamper >/dev/null 2>&1; UMH_RC=$?
if { [ "$UMH_RC" -ne 0 ] || [ -f "$(git rev-parse --git-dir)/MERGE_HEAD" ]; } \
   && ! git show HEAD:.truth/claims.jsonl 2>/dev/null | grep -q "stands TAMPERED"; then
  ok "UM7: pre-merge-commit BLOCKED the tampered union merge (nothing tampered committed)"
else
  miss "UM7: a merge rewriting a committed ledger line landed past the gate (ADR-045/INV-A)"
fi
git merge --abort >/dev/null 2>&1 || true
cd "$UMH_PREV" || { echo "canary: cannot cd into $UMH_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$UMH"

# ---- FAULT LK (ADR-045/D2): write verbs serialize on the ledger lock ----
# Deterministic two-process serialization through the REAL CLI: a holder
# takes LOCK_EX on the lock target, a background `truth claim` must NOT
# append while it is held, and must land promptly once released.
say "FAULT LK (ADR-045): a write verb blocks on the held ledger lock and lands after release"
LK="$(mktemp -d)"; TDIRS+=("$LK"); LK_PREV="$PWD"
mkrepo "$LK"   # NB: mkrepo cd's into $LK; cwd restored via $LK_PREV
git add -A && git commit -qm "lk: init" --no-verify -q
rm -f .lk-held .lk-release
python3 - <<'PYEOF' &
import fcntl, os, time
fd = os.open(".git/truth-ledger.lock", os.O_CREAT | os.O_RDWR, 0o644)
fcntl.flock(fd, fcntl.LOCK_EX)
open(".lk-held", "w").close()
deadline = time.time() + 30          # backstop: never wedge the suite
while not os.path.exists(".lk-release") and time.time() < deadline:
    time.sleep(0.05)
PYEOF
LK_HOLDER=$!
LK_WAITED=0
while [ ! -f .lk-held ] && [ "$LK_WAITED" -lt 100 ]; do sleep 0.05; LK_WAITED=$((LK_WAITED+1)); done
$T claim "lk fact filed under contention" --class UNVERIFIED --tier P2 >/dev/null 2>&1 &
LK_CLAIMER=$!
sleep 1
LK_N=$(wc -l < .truth/claims.jsonl | tr -d ' ')
if [ "$LK_N" -eq 0 ] && kill -0 "$LK_CLAIMER" 2>/dev/null; then
  ok "LK1: the claim neither appended nor exited while the lock was held (~1s)"
else
  miss "LK1: a write verb proceeded past a held ledger lock (appended=$LK_N lines; ADR-045/R10)"
fi
touch .lk-release
wait "$LK_CLAIMER" 2>/dev/null
wait "$LK_HOLDER" 2>/dev/null
if [ "$(wc -l < .truth/claims.jsonl | tr -d ' ')" -eq 1 ] \
   && grep -q "lk fact filed under contention" .truth/claims.jsonl; then
  ok "LK2: the blocked claim landed exactly once after the lock was released"
else
  miss "LK2: the record did not land (or landed twice) after release"
fi
rm -f .lk-held .lk-release
cd "$LK_PREV" || { echo "canary: cannot cd into $LK_PREV -- refusing to continue" >&2; exit 1; }
rm -rf "$LK"

# ---- FAULT EF (ADR-051, v0.9.38): capsule coherence ---------------------
# An `agree` on a path-claim advances the effective anchor (F2) while the
# capsule lives in the immutable claim record. Filed over a CHANGED
# output, that agree leaves the claim live and permanently
# un-recheckable: every later --recheck compares against a hash nobody
# can produce, and (before step 2.6 retired it) reaffirm's hash-match arm
# could never take it back either. `truth reproduce` is what NAMES that
# population now, which is why EF3 below is measured against it.
# Measured before the gate: 13 of 126 live claims in that state.
say "FAULT EF (ADR-051): an agree over a changed output is refused, and the refresh returns the claim to the mechanical arm"
EF="$(mktemp -d)"; TDIRS+=("$EF"); EF_PREV="$PWD"
mkrepo "$EF"
printf 'x\nx\n' > f.txt
git add -A >/dev/null 2>&1; git commit -qm init
EF_CID="$($T claim "f.txt holds exactly two x lines" --class VERIFIED \
  --evidence-cmd "grep -c x f.txt" --paths f.txt 2>/dev/null | tail -1)"
TRUTH_SESSION=s-ef-v1 $T verdict "$EF_CID" agree --basis "re-ran it" \
  >/dev/null 2>&1
# EF4 (negative control) FIRST: a matching capsule must need no flag.
if [ -n "$($T list --live --json 2>/dev/null | grep -o "$EF_CID")" ]; then
  ok "EF4 (negative control): a clean agree passes with no --refresh-evidence"
else
  miss "EF4: the gate refused an agree whose capsule still reproduces"
fi
printf 'x\nx\nx\n' > f.txt; git add f.txt >/dev/null 2>&1
git commit -qm "third x" >/dev/null 2>&1
EF_N="$(wc -l < .truth/claims.jsonl | tr -d ' ')"
EF_OUT="$(TRUTH_SESSION=s-ef-v2 $T verdict "$EF_CID" agree \
  --basis "sentence still holds" 2>&1)"
if printf '%s' "$EF_OUT" | grep -q "ADR-051" \
   && printf '%s' "$EF_OUT" | grep -q -- "--refresh-evidence" \
   && printf '%s' "$EF_OUT" | grep -q "diverge"; then
  ok "EF1: the orphaning agree is refused, naming BOTH exits (refresh, diverge)"
else
  miss "EF1: the orphaning agree was accepted or the refusal taught only one exit"
fi
if [ "$(wc -l < .truth/claims.jsonl | tr -d ' ')" = "$EF_N" ]; then
  ok "EF2: the refusal appended nothing"
else
  miss "EF2: the refusal still wrote to the ledger"
fi
TRUTH_SESSION=s-ef-v2 $T verdict "$EF_CID" agree \
  --basis "sentence still holds" \
  --refresh-evidence "the count grew 2->3; the sentence is about the file's shape" \
  >/dev/null 2>&1
printf 'x\nx\nx\n#c\n' > f.txt; git add f.txt >/dev/null 2>&1
git commit -qm "comment only" >/dev/null 2>&1
if $T reproduce 2>&1 | grep -q "^$EF_CID  reproduces"; then
  ok "EF3: the refreshed claim reproduces again -- the refresh bought a producible capsule"
else
  miss "EF3: the refresh bought nothing -- still outside the hash-match arm"
fi
if $T validate >/dev/null 2>&1; then
  ok "EF5: validate admits the refreshed verdict"
else
  miss "EF5: validate refuses a record the CLI itself writes"
fi
cd "$EF_PREV" || { echo "canary: cannot cd into $EF_PREV -- refusing to continue" >&2; exit 1; }

# ---- FAULT PA (F3.1): an empty policy file must SAY it is empty ---------
# ADR-037/SI-4 reads a committed-empty policy file as a conscious "nothing
# here" and goes silent; ADR-042 rule 2 says zero coverage is a failure.
# Both are on record and they contradict, and until now the earlier one
# won by default -- not on merit, just by being first. The attestation is
# the reconciliation: emptiness stays a legitimate statement, but it has
# to be stated, dated and justified, because an untouched shipped default
# is byte-identical to a decision nobody made.
say "FAULT PA (F3.1): an unattested empty policy file fails doctor; an attested one passes; a populated one needs no attestation"
PA="$(mktemp -d)"; TDIRS+=("$PA"); PA_PREV="$PWD"
mkrepo "$PA"
echo ".truth/claims.jsonl merge=union" >> .gitattributes
printf '# Agents\nUse scripts/truth (see .truth/README.md)\n' > AGENTS.md
printf '#!/usr/bin/env bash\nexec bash scripts/check-truth.sh\n' > .git/hooks/pre-commit
printf '#!/usr/bin/env bash\nexec python3 scripts/truth reproduce\n' > .git/hooks/pre-push
chmod +x .git/hooks/pre-push 2>/dev/null || true
printf '#!/usr/bin/env bash\nexec bash scripts/check-truth.sh\n' > .git/hooks/pre-merge-commit
chmod +x .git/hooks/pre-commit .git/hooks/post-merge .git/hooks/pre-merge-commit
mkdir -p src/generated
printf 'col\n1\n' > src/generated/out.csv
git add -A >/dev/null 2>&1; git commit -qm "pa: wired repo with a generated artifact" --no-verify

# PA1 (negative control) FIRST: mkrepo attested, so the wired repo passes.
if $T doctor >/dev/null 2>&1; then
  ok "PA1 (negative control): an ATTESTED empty policy file passes doctor"
else
  miss "PA1: doctor failed a repo whose empty policy file carries an attestation"
  $T doctor 2>&1 | grep -E "^(FAIL|WARN)" || true
fi
# PA4: the cross-check. The attestation says nothing is generated; the
# repository says otherwise, and only this arm asks the repository.
if $T doctor 2>&1 | grep -q "WARN  generated-paths covers what looks generated"; then
  ok "PA4: a tracked file under generated/ is named even though the empty list is attested"
else
  miss "PA4: an attested-empty list was trusted over a tracked src/generated/out.csv"
fi
# PA2: strip the attestation -- back to the untouched default, which
# records no decision.
grep -v '^# attested ' .truth/generated-paths > .truth/gp.tmp
mv .truth/gp.tmp .truth/generated-paths
PA_OUT="$($T doctor 2>&1)"; PA_RC=$?
if [ "$PA_RC" -ne 0 ] \
   && printf '%s\n' "$PA_OUT" | grep -q "FAIL  policy file attested (.truth/generated-paths)"; then
  ok "PA2: an UNATTESTED empty policy file FAILs doctor (exit 1), naming the one-line fix"
else
  miss "PA2: doctor read an untouched empty default as a conscious statement (rc=$PA_RC)"
fi
# PA3: entries ARE the statement -- a populated list needs no attestation.
printf 'src/generated/**\n' >> .truth/generated-paths
PA_OUT="$($T doctor 2>&1)"
if printf '%s\n' "$PA_OUT" | grep -q "OK    policy file attested (.truth/generated-paths) -- populated" \
   && ! printf '%s\n' "$PA_OUT" | grep -q "WARN  generated-paths covers what looks generated"; then
  ok "PA3: a POPULATED list needs no attestation, and covering the artifact silences the cross-check"
else
  miss "PA3: a populated list was still asked to attest, or the cross-check kept firing after it was covered"
fi
cd "$PA_PREV" || { echo "canary: cannot cd into $PA_PREV -- refusing to continue" >&2; exit 1; }

# ---- FAULT RP (F1.1): the reproduction sweep ----------------------------
# `truth reproduce` asks the question no other verb asks: can this LIVE
# claim's recorded capsule still be produced, here, now? invalidate-scan
# watches PATHS (right about 1 time in 8 -- ADR-050); recheck and reaffirm
# only reach claims already knocked out of live. Four arms plus a negative
# control. RP2 is seeded as a RAW LEGACY RECORD on purpose: since ADR-051
# the CLI refuses to create an orphaned capsule, so the only way to seed
# the population that still exists in deployed ledgers (7 live claims in
# kuchnie at ae16a60) is to append the pre-ADR-051 shape directly.
say "FAULT RP (F1.1): reproduce classifies live capsules, and a sweep that measured nothing FAILS"
RP="$(mktemp -d)"; TDIRS+=("$RP"); RP_PREV="$PWD"
mkrepo "$RP"

# RP5 (negative control) FIRST, before any claim exists: ADR-042 rule 2 --
# an instrument that examined nothing has not passed, it failed to run.
# This arm is the reason the verb has an exit code of its own; a sweep
# that exits 0 over an empty population is indistinguishable from a
# healthy repo at the CI summary line.
printf 'x\nx\n' > f.txt
printf 'dark.txt\n' > .gitignore
printf 'x\n' > dark.txt          # gitignored: the dependency no watch sees
git add -A >/dev/null 2>&1; git commit -qm "rp: init"
$T reproduce >/dev/null 2>&1; RP_RC=$?
if [ "$RP_RC" -eq 8 ]; then
  ok "RP5 (negative control): a sweep over zero live claims exits 8, not 0"
else
  miss "RP5: the empty sweep exited $RP_RC -- a green that measured nothing"
fi
RP_C0="$(git rev-parse HEAD)"
printf 'x\nx\nx\n' > f.txt
git add f.txt >/dev/null 2>&1; git commit -qm "rp: third x"
RP_C1="$(git rev-parse HEAD)"

# RP2's seed: a pre-ADR-051 legacy pair. The claim anchors at C0 with a
# hash nothing can produce; the agree anchors at C1, so the EFFECTIVE
# anchor advanced over a commit that changed the watched file. That makes
# the buried window (C0..C1) carry f.txt and the ahead window (C1..HEAD)
# carry nothing -- the orphaned-capsule signature.
RP_H="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
printf '%s\n' "{\"id\":\"tr-0aa00001\",\"kind\":\"claim\",\"actor\":\"canary\",\"session\":\"s-rp-legacy\",\"ts\":\"2026-07-01T00:00:00.000000+00:00\",\"payload\":{\"text\":\"the legacy claim whose capsule an agree left behind\",\"evidence_class\":\"VERIFIED\",\"cost_tier\":\"P1\",\"ttl_days\":null,\"evidence_paths\":[\"f.txt\"],\"anchor_commit\":\"$RP_C0\",\"evidence\":{\"command\":\"grep -c x f.txt\",\"output_hash\":\"$RP_H\",\"returncode\":0,\"screened\":true}}}" >> .truth/claims.jsonl
printf '%s\n' "{\"id\":\"tr-0aa00002\",\"kind\":\"verdict\",\"actor\":\"canary\",\"session\":\"s-rp-legacy-v\",\"ts\":\"2026-07-02T00:00:00.000000+00:00\",\"payload\":{\"claim\":\"tr-0aa00001\",\"verdict\":\"agree\",\"basis\":\"legacy: an agree filed over a changed output, before ADR-051 refused it\",\"anchor_commit\":\"$RP_C1\"}}" >> .truth/claims.jsonl

# RP1's subject: a capsule that still produces, filed and agreed normally.
RP_A="$($T claim "f.txt holds exactly three x lines" --class VERIFIED \
  --evidence-cmd "grep -c x f.txt" --paths f.txt 2>/dev/null | tail -1)"
TRUTH_SESSION=s-rp-v $T verdict "$RP_A" agree --basis "re-ran it" \
  >/dev/null 2>&1
# RP4's subject: an INFERRED claim carries no capsule at all.
RP_B="$($T claim "the decomposition rests on judgment, not a probe" \
  --class INFERRED --basis "read the module and reasoned about it" \
  2>/dev/null | tail -1)"
TRUTH_SESSION=s-rp-v $T verdict "$RP_B" agree --basis "read it too" \
  >/dev/null 2>&1
# RP3's subject: filed while `cat` was allowlisted, swept after it was
# withdrawn -- the ADR-009 posture is that the screen is committed policy
# NOW, not at filing time.
RP_D="$($T claim "cat reads f.txt without a filter" --class VERIFIED \
  --evidence-cmd "cat f.txt" --paths f.txt 2>/dev/null | tail -1)"
TRUTH_SESSION=s-rp-v $T verdict "$RP_D" agree --basis "ran it" \
  >/dev/null 2>&1
grep -v '^cat$' .truth/evidence-allow > .truth/ea.tmp
mv .truth/ea.tmp .truth/evidence-allow

RP_OUT="$($T reproduce --json 2>/dev/null)"; RP_RC=$?
if printf '%s' "$RP_OUT" | python3 -c '
import json,sys
d=json.load(sys.stdin)
a=[r for r in d["claims"] if r["id"]=="'"$RP_A"'"]
# Deliberately NOT asserting the global reproduces count: coupling this
# arm to it made RP1 redden for RP3'"'"'s and RP4'"'"'s mutations too, and an arm
# that fires for someone else'"'"'s defect cannot testify about its own.
sys.exit(0 if a and a[0]["arm"]=="reproduces" else 1)'; then
  ok "RP1: a capsule that still produces lands in reproduces"
else
  miss "RP1: a producible capsule was not reported as reproduces"
fi
if printf '%s' "$RP_OUT" | python3 -c '
import json,sys
d=json.load(sys.stdin)
r=[r for r in d["claims"] if r["id"]=="tr-0aa00001"]
sys.exit(0 if r and r[0]["arm"]=="capsule-stale"
         and r[0].get("shape")=="orphaned-capsule"
         and r[0].get("watched_buried")==["f.txt"]
         and r[0].get("watched_touched")==[] else 1)' \
   && [ "$RP_RC" -eq 7 ]; then
  ok "RP2: the legacy orphan is capsule-stale, shaped orphaned-capsule by the buried window, exit 7"
else
  miss "RP2: the orphaned capsule went unreported, was mis-shaped, or did not raise exit 7 (rc=$RP_RC)"
fi
if printf '%s' "$RP_OUT" | python3 -c '
import json,sys
d=json.load(sys.stdin)
r=[r for r in d["claims"] if r["id"]=="'"$RP_D"'"]
sys.exit(0 if r and r[0]["arm"]=="unexecutable"
         and "not in .truth/evidence-allow" in r[0]["detail"] else 1)'; then
  ok "RP3: a claim the CURRENT allowlist refuses is unexecutable, never counted as drift"
else
  miss "RP3: a de-allowlisted capsule was executed anyway, or miscounted as capsule-stale"
fi
if printf '%s' "$RP_OUT" | python3 -c '
import json,sys
d=json.load(sys.stdin)
r=[r for r in d["claims"] if r["id"]=="'"$RP_B"'"]
sys.exit(0 if r and r[0]["arm"]=="no-capsule" else 1)'; then
  ok "RP4: an INFERRED claim with no capsule lands in no-capsule, not in reproduces"
else
  miss "RP4: a capsule-less claim was not separated out"
fi
cd "$RP_PREV" || { echo "canary: cannot cd into $RP_PREV -- refusing to continue" >&2; exit 1; }

say ""
say "canary result: $PASS caught, $FAIL missed"
if [ "$FAIL" -gt 0 ]; then
  say "CANARY FAILED -- the immune system has a hole."
  exit 1
fi
say "ALL CANARIES CAUGHT."
