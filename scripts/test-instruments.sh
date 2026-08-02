#!/usr/bin/env bash
# Regression gate for the Tier C instruments (ADR-046: the separation,
# override-velocity, blast, and concern-tag reports left `truth stats`/
# `truth doctor` for instruments/*.py). Meta-repo only, deliberately NOT
# templated (ADR-003 rule 2 shape: instruments are the research half,
# consumers never receive them). Two lanes:
#   - REAL-LEDGER arms: each instrument runs against this repository's
#     own ledger and must report its known data (separation pairs exist,
#     the 3650d scope TTL is on record, a blast floor renders, legacy
#     concern tags are counted) -- and each --json mode parses.
#   - RED-PROOF arms: each instrument runs against a sandbox ledger
#     seeded with the exact fault its report exists to expose (instant
#     agree, verbatim scope re-justification, hot watch, legacy tag) and
#     must name it -- these arms carry the assertions of the retired
#     canary arms SEP1-SEP3, the two FAULT OV stats arms, and BF5, and
#     prove each instrument CAN fail (an instrument patched to print
#     nothing goes red here, not silently green).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
INST="$ROOT/instruments"
PASS=0; FAIL=0
say() { printf '%s\n' "$*"; }
ok()   { PASS=$((PASS+1)); say "  CAUGHT: $*"; }
bad()  { FAIL=$((FAIL+1)); say "  MISSED: $*"; }

TDIRS=()
cleanup() { for d in "${TDIRS[@]:-}"; do [ -n "$d" ] && rm -rf "$d"; done; }
trap cleanup EXIT

mkrepo() {  # $1 = dir; a minimal wired sandbox with its own ledger
  cd "$1" || exit 1
  git init -q .
  git config user.email t@t; git config user.name t
  cp -R "$ROOT/template/scripts" scripts
  cp -R "$ROOT/template/truthlib" truthlib
  mkdir -p .truth && : > .truth/claims.jsonl
  printf 'cat\ngrep\nwc\nls\n' > .truth/evidence-allow
  printf '.truth/claims.jsonl merge=union\n' > .gitattributes
  printf 'scripts/truth\n' > AGENTS.md
  echo data > f.txt
  git add -A && git commit -qm init --no-verify
}

say "LANE 1: instruments against this repository's real ledger"

SEP_TXT=$(cd "$ROOT" && python3 "$INST/separation-report.py")
if printf '%s\n' "$SEP_TXT" | grep -Eq "^separation: [1-9][0-9]* first-agree pair"; then
  ok "separation-report renders a non-zero first-agree pair count on the real ledger"
else
  bad "separation-report shows no pairs on a ledger with a long agree history: [$SEP_TXT]"
fi
if (cd "$ROOT" && python3 "$INST/separation-report.py" --json) \
   | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d['pairs'] > 0 and d['same_session'] == 0 else 1)"; then
  ok "separation-report --json parses; pairs>0, same_session=0 (the ADR-010 gate has not regressed)"
else
  bad "separation-report --json malformed, empty, or reporting a same-session regression"
fi

OV_TXT=$(cd "$ROOT" && python3 "$INST/override-velocity.py")
if printf '%s\n' "$OV_TXT" | grep -Eq "scope-ok=[1-9]" \
   && printf '%s\n' "$OV_TXT" | grep -q "max scope ttl 3650d"; then
  ok "override-velocity renders scope-ok filings and this ledger's known 3650d max scope TTL"
else
  bad "override-velocity lost the scope-ok count or the 3650d TTL: [$OV_TXT]"
fi
if (cd "$ROOT" && python3 "$INST/override-velocity.py" --json) \
   | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d['scope_basis_filings'] > 0 and d['max_scope_ttl_days'] == 3650 else 1)"; then
  ok "override-velocity --json parses with the same figures"
else
  bad "override-velocity --json malformed or figures drifted from the plain render"
fi

BL_TXT=$(cd "$ROOT" && python3 "$INST/blast-report.py")
if printf '%s\n' "$BL_TXT" | grep -Eq "^blast: floor [0-9]+ \((calibrated|fallback)\)"; then
  ok "blast-report renders an effective floor with its source"
else
  bad "blast-report lost the floor line: [$BL_TXT]"
fi
if (cd "$ROOT" && python3 "$INST/blast-report.py" --json) \
   | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if isinstance(d['effective_floor'], int) and d['effective_floor'] >= 1 and d['history_state'] == 'ok' else 1)"; then
  ok "blast-report --json parses; floor >= 1 (the R5/F2 clamp) over readable history"
else
  bad "blast-report --json malformed, floor below the clamp, or history unreadable here"
fi

CT_TXT=$(cd "$ROOT" && python3 "$INST/concern-tag.py")
if printf '%s\n' "$CT_TXT" | grep -Eq "^concerns: .*untagged-active=[0-9]+"; then
  ok "concern-tag renders the legacy tag tally + untagged-active count"
else
  bad "concern-tag lost the tally render: [$CT_TXT]"
fi
if (cd "$ROOT" && python3 "$INST/concern-tag.py" --json) \
   | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if isinstance(d['concerns'], dict) and isinstance(d['concerns_untagged_active'], int) else 1)"; then
  ok "concern-tag --json parses"
else
  bad "concern-tag --json malformed"
fi

say "LANE 2 (red-proofs): each instrument must expose a seeded fault in a sandbox"

# -- separation: carries retired canary SEP1/SEP2/SEP3 ---------------------
SEPD="$(mktemp -d)"; TDIRS+=("$SEPD"); PREV="$PWD"
mkrepo "$SEPD"
CID=$(TRUTH_ACTOR=gate TRUTH_SESSION=s-author python3 scripts/truth claim \
      "the widget probe is separation-instrumented" --tier P2 2>/dev/null)
TRUTH_ACTOR=gate TRUTH_SESSION=s-verifier python3 scripts/truth verdict \
      "$CID" agree --basis "gate: immediate agree, no reading possible" >/dev/null 2>&1
SEPOUT=$(python3 "$INST/separation-report.py")
if printf '%s\n' "$SEPOUT" | grep -Eq "[1-9][0-9]* inside the 1.0s floor" \
   && python3 "$INST/separation-report.py" --json \
      | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if '$CID' in d['live_unevidenced'] else 1)"; then
  ok "an agree filed inside the floor is reported unevidenced AND named while live (retired SEP1+SEP2)"
else
  bad "a sub-second agree was not reported or not named -- the instrument is dark: [$SEPOUT]"
fi
CID2=$(TRUTH_ACTOR=gate TRUTH_SESSION=s-author python3 scripts/truth claim \
       "the widget probe is separation-clean" --tier P2 2>/dev/null)
sleep 1.1
TRUTH_ACTOR=gate TRUTH_SESSION=s-verifier python3 scripts/truth verdict \
      "$CID2" agree --basis "gate: agree filed after the floor" >/dev/null 2>&1
if python3 "$INST/separation-report.py" --json \
   | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if '$CID2' not in d['live_unevidenced'] else 1)"; then
  ok "an agree after the floor is not flagged (negative control, retired SEP3)"
else
  bad "a claim agreed AFTER the floor was flagged -- false positive on an honest verification"
fi
cd "$PREV"

# -- override-velocity: carries the retired FAULT OV stats arms ------------
OVD="$(mktemp -d)"; TDIRS+=("$OVD")
mkrepo "$OVD"
OV_SB="the include filter deliberately covers the whole codebase"
OV_EC="grep -rc data --include=f.txt ."
CID_P=$(TRUTH_NOW="2026-06-01T00:00:00+00:00" TRUTH_ACTOR=gate \
        TRUTH_SESSION=s-ov python3 scripts/truth claim \
        "no occurrences remain anywhere in the codebase" --class VERIFIED \
        --evidence-cmd "$OV_EC" --paths f.txt --tier P1 \
        --scope-ok "$OV_SB" 2>/dev/null)
TRUTH_ACTOR=gate TRUTH_SESSION=s-ov python3 scripts/truth invalidate-scan --quiet 2>/dev/null
CID_R=$(TRUTH_ACTOR=gate TRUTH_SESSION=s-ov python3 scripts/truth claim \
        "no occurrences remain anywhere in the codebase" --class VERIFIED \
        --evidence-cmd "$OV_EC" --paths f.txt --tier P1 \
        --scope-ok "$OV_SB" 2>/dev/null)
CID_N=$(TRUTH_ACTOR=gate TRUTH_SESSION=s-ov python3 scripts/truth claim \
        "every call site is covered by the services grep" --class VERIFIED \
        --evidence-cmd "$OV_EC" --paths f.txt --tier P2 \
        --scope-ok "now narrowed to the single services subtree after refactor" 2>/dev/null)
OVOUT=$(python3 "$INST/override-velocity.py")
if printf '%s\n' "$OVOUT" | grep -q "ADR-033" \
   && printf '%s\n' "$OVOUT" | grep -q "$CID_R" \
   && printf '%s\n' "$OVOUT" | grep -q "$CID_P"; then
  ok "verbatim scope re-justification after expiry raises the advisory naming both claims (retired OV arm 1)"
else
  bad "override-velocity advisory missing for a verbatim re-justification (detector patched out?): [$OVOUT]"
fi
if python3 "$INST/override-velocity.py" --json \
   | python3 -c "import json,sys; ids=[r['claim'] for r in json.load(sys.stdin)['repeats']]; sys.exit(0 if '$CID_N' not in ids and '$CID_R' in ids else 1)"; then
  ok "a genuinely narrowed re-file produces no advisory (negative control, retired OV arm 2)"
else
  bad "override-velocity false-fired on a narrowed re-file, or lost the real repeat"
fi
cd "$PREV"

# -- blast: carries retired BF5 + the ADR-046 not-stored red-proof ---------
BLD="$(mktemp -d)"; TDIRS+=("$BLD")
mkrepo "$BLD"
for i in $(seq 1 16); do
  echo "line $i" >> w.txt; git add w.txt; git commit -qm "w $i" --no-verify
done
CID_B=$(TRUTH_ACTOR=gate TRUTH_SESSION=s-bl python3 scripts/truth claim \
        "w.txt keeps accumulating its numbered lines" --class VERIFIED \
        --evidence-cmd "cat w.txt" --paths w.txt --tier P2 2>/dev/null)
if tail -1 .truth/claims.jsonl | grep -q blast_forecast; then
  bad "intake STORED blast_forecast -- the ADR-046 payload stamp is back"
else
  ok "intake stores no blast_forecast (ADR-046: computed on read)"
fi
BLOUT=$(python3 "$INST/blast-report.py")
if printf '%s\n' "$BLOUT" | grep -q "floor 15 (fallback)" \
   && printf '%s\n' "$BLOUT" | grep -Eq "top observed-vs-forecast: .*${CID_B}=0/1[0-9]"; then
  ok "blast-report renders floor + a LIVE-computed forecast for the unstored hot watch (retired BF5)"
else
  bad "blast-report lost the floor/rows render or the live forecast: [$BLOUT]"
fi
cd "$PREV"

# -- concern-tag: the legacy reader must see a pre-ADR-046 tag -------------
CTD="$(mktemp -d)"; TDIRS+=("$CTD")
mkrepo "$CTD"
TRUTH_ACTOR=gate TRUTH_SESSION=s-ct python3 scripts/truth claim \
  "cache layer evicts old entries" --tier P2 >/dev/null 2>&1
# a legacy record, written the only way one can exist now: it predates
# ADR-046 (fixture-appended here exactly like the canary's legacy lines)
printf '%s\n' '{"id": "tr-00c0ffee", "kind": "claim", "actor": "legacy", "session": "s-old", "ts": "2026-01-01T00:00:00.000000+00:00", "payload": {"text": "worker pool drains on shutdown", "evidence_class": "UNVERIFIED", "cost_tier": "P2", "ttl_days": null, "evidence_paths": [], "concerns": ["security"]}}' >> .truth/claims.jsonl
if python3 scripts/truth validate >/dev/null 2>&1; then
  ok "a legacy concerns record still validates (admitted pre-ADR-046)"
else
  bad "validate refused a legacy concerns record -- legacy admission broken"
fi
CTOUT=$(python3 "$INST/concern-tag.py")
if printf '%s\n' "$CTOUT" | grep -q "concerns: security=1, untagged-active=1"; then
  ok "concern-tag counts the legacy tag and the untagged active claim (retired stats tally)"
else
  bad "concern-tag mis-tallied the sandbox ledger: [$CTOUT]"
fi
cd "$PREV"

say ""
say "test-instruments result: $PASS caught, $FAIL missed"
if [ "$FAIL" -gt 0 ]; then
  say "INSTRUMENTS GATE FAILED."
  exit 1
fi
say "ALL INSTRUMENT ARMS CAUGHT."
