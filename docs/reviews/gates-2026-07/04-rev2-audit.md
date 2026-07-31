# Audit of revision 2 (proposed ADRs 034–038)

> Reader: the truth-ledger operator | Method: one fresh Fable agent,
> adversarial, read-only — absorption audit of all 2026-07-30 review
> findings plus attack on rev-2's NEW (never-fact-checked) assertions,
> with simulations run against both real ledgers. Two facts
> pre-established mechanically by the operator session at current
> HEAD: meta retractions = 49 (the reviewer's 27 = the count through
> 07-28 — stale snapshot, not method difference; 07-29 added 22,
> incl. the 21-id sweep of commit 217306c); 12/49 retracted ids cited
> in tracked md outside archive, confirmed with the file list.
> Date: 2026-07-31.

## Verdict

**Yes, with listed fixes** — rev-2 is fit as the working proposal
after a rev-3 pass. Absorption score: ~33 of 38 review findings
cleanly absorbed (several re-verified against code and both
ledgers), 5 partial, **1 botched, 0 missed**. The header claim
"none are declined" is false on a strict read (three ways, below).

## The five fixes rev-3 must carry

1. **Canary prefix BL collides — the one botched absorption.**
   Rev-2 renamed away from B/T/R but ADR-038's proposed BL1–BL5
   collide with *existing* FAULT BL1–BL4 (truth-canary.sh:1588–1634,
   the ADR-baseline arms). CC-3 prescribes exactly the grep that was
   never run on the proposal itself. Verified free: X (X1–X7), CC,
   DW, TG, RC. Also anchor CC-3's check as `FAULT <prefix>[0-9]` to
   avoid C/CC-style aliasing.
2. **ADR-034 (dirty-watch) has a real mechanism bug.** Git pathspec
   `*` crosses `/` (verified: `git ls-files -- 'template/*.md'`
   matches `template/docs/adr/truth/001-….md`), while the CLI's
   `_glob_rx` deliberately stops `*` at `/` — a v0.4 fix for exactly
   this over-match (truth:211–219). Passing evidence_paths as git
   pathspecs reintroduces it: dirty advisories for files the claim
   does not watch. Fix: run bare `git status --porcelain` and filter
   through `match_paths()`. Also: "INV-M refuses untracked paths" is
   true for literals only — explicit globs are exempt by design
   (truth:514–516), so a glob watching only untracked content is a
   restale-at-birth vector the advisory must cover (`??` entries).
   Affected population: 4/96 meta, 22/175 kuchnie glob-watch claims.
3. **ADR-036 (tombstone gate): the default scope is vacuous at
   home and TG6 has no carrier verb.** The meta-repo has no
   `docs/specs/` at all — with the shipped default every retraction
   proceeds grep-clean, unacknowledged (and the home repo's 12 stale
   historical citations plus one live stale field-note citation of
   tr-bbdff732 stay unprotected; "spec-health remains the backstop"
   is a backstop over zero files at home). In kuchnie the default is
   well-calibrated: 6 specs, 81 citation occurrences, 28 distinct
   ids, intersection with the 66 retracted ids = **empty** — zero
   day-one false refusals; good evidence, uncited. TG6 ("a 25-id
   sweep meets 25 verdicts in one pass") is unimplementable:
   `truth verdict` takes one positional claim_id (truth:3149–3154)
   and the ADR-011 ceremony is per-id — rewrite or drop.
4. **tr-bbdff732 is cited as a live successor but is itself
   retracted** (verdict tr-2e8a4440, meta ledger line 2129,
   2026-07-29, "superseded by the v0.9.18 docs/adr/truth path
   re-anchor successor"). Rev-2's ADR-037 Context violates the
   citation discipline its own tombstone gate mechanizes — note the
   fate, point at the current successor. (tr-da868d5c, the other
   rolled-over successor, is correctly left unnamed in rev-2.)
5. **BLAST_ADVISORY_FLOOR=15 is rev-1's falsified number reused as
   a print threshold.** With 82/96 meta claims above it, the
   advisory prints on ~85% of meta path-carrying filings —
   "silence on clean" becomes wallpaper at home (kuchnie stays
   mostly silent, on the one-commit margin the review noted and
   rev-2 dropped). Derive the floor per-repo from the report the
   ADR itself ships, or own the home-repo noise explicitly.

Minor: correct "(none are declined)" — the compound-sentence
advisory is deferred with a reason (a decline), the BL collision is
a wrong absorption, and fact-health's currently-RED-46-failures
state plus the kuchnie floor margin were dropped without mention;
consider lexicon additions (removed/deleted/empty — zero misfires
today but foreseeable false refusals); consider a frozen-date
carve-out for ADR-037 (4 of 13 residual warnings are greps of
immutable ADR acceptance dates); X6 is a one-directional tripwire
(catches removals from NEGATION_TOKENS, cannot catch new
negation-shaped additions to ADR-007's set) — fine, but say so;
ADR-034's "approach zero" metric cannot distinguish own-content
restales from fast unrelated commits — an upper-bound target.

## New evidence in rev-2's favor (worth citing in rev-3)

- **The exit gate simulates superbly on 244 real filings.** Full
  simulation (tokens() + proposed NEGATION_TOKENS) over both
  ledgers: meta — 98 VERIFIED, refusal path fires exactly once,
  on tr-3b69f8ff, the motivating defect; zero false refusals.
  Kuchnie — 146 VERIFIED, 6 warnings (all genuine absence proofs,
  incl. tr-d59194ea) and 4 refusals: tr-0e884e02 (QB-011 itself)
  plus tr-dc64bbc0/tr-cb1dec8a/tr-4674581b — positive claims whose
  grep chains exited 1, plausibly three *additional undetected
  hollow claims* the gate would have caught. The "no" token
  triggers only on genuine absence texts in both corpora.
- **The carve-outs hit their flagship pair exactly**: tr-da868d5c
  (schema-$id anchor) exempted, tr-22853f21 (hardcoded v0.9.8)
  still warns. Recount: 29/98 version/date-shaped (review said 25;
  regex boundary), 16 exempted, 13 residual — 9 correctly
  release-expiring, 4 false-ish (frozen ADR dates).
- **The dirty-watch class is real and measured**: invalidations
  within 30 min of their claim's own birth — meta 29/895, kuchnie
  37/390 (tr-fd1bbb24 restaled 3× within 18 min of filing). The
  new ADR-034 has a denominator before it ships, as it claims.
- The machinery.md authoring-loop quote is genuine
  (machinery.md:160–163, "commits the CONTENT first … restales at
  birth").

## Process recommendation (the operator's open question)

File first, revise second. The review's numbers have already moved
twice in one day (27→49 by HEAD drift; 25→29 by regex boundary) —
exactly the drift the ledger exists to pin. File the review's
load-bearing facts as verifier-session claims (TRUTH_SESSION
exported, author≠verifier respected), then rev-3 swaps each
*[review]* for an id. Candidate claims, each with a mechanical
evidence command: (1) meta retracted-verdict count at HEAD;
(2) the 12-cited-outside-archive measurement; (3) kuchnie retracted
count 66; (4) the 82/96 threshold replay; (5) the exit-gate
simulation profile (5 refusals / 6 warnings over 244 filings);
(6) the birth-restale counts (29/895, 37/390); (7) FAULT-prefix
inventory (BL taken; X/CC/DW/TG/RC free). Counts over a mutable
ledger should be pinned to an anchor commit or filed with
--ttl-days — they are facts about a moment, which is what the 27
vs 49 episode just demonstrated.
