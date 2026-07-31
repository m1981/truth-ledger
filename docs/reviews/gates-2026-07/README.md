# Gates adoption review — 2026-07-30/31

The complete provenance chain for the six proposed gate ADRs
(gate system R0 + five gates), from the external reviewer's first
draft to the adopted plan. Read `07-proposed-adrs-rev3.md` for the
current proposal; everything earlier is history that explains it.

| # | File | What it is |
|---|---|---|
| 01 | proposed-adrs-rev1.md | External reviewer's original four ADRs (034–037) |
| 02 | adversarial-review.md | Five-agent fact-check + design review of rev-1 (all numbers recomputed) |
| 03 | proposed-adrs-rev2.md | Reviewer's revision absorbing 02 |
| 04 | rev2-audit.md | Absorption audit of rev-2 (33/38 absorbed, 5 fixes) + process recommendation |
| 05 | architecture-review.md | Architect pass: static/dynamic views, antipatterns AP-1..7, algorithms A-1..6 |
| 06 | plan-of-record.md | Synthesis after the 14-agent structured review (7 lenses, adversarially verified: 4 confirmed / 3 refuted) — binds the implementation |
| 07 | proposed-adrs-rev3.md | Six ADRs implementing 06 — the adopted working proposal |
| 08 | citation-measurement.md | Data artifact behind ledger claim tr-f0c94c6c (12/49 retracted ids cited outside archive) |

Ledger facts backing the numbers cited throughout (filed 2026-07-31,
session `verifier-adr-review-2026-07-31`, commit 0d35e3e):
tr-d0759df4, tr-efc43840, tr-f0c94c6c, tr-c3087292, tr-166c4616,
tr-5c2bd165, tr-624d5916, tr-4387f0ea, tr-f49a00ee. Counts carry
30-day TTLs — they are facts about a moment.

Historical note: these documents deliberately cite retracted and
pilot-ledger ids (tr-bbdff732, tr-da868d5c, tr-23661434, …) as
*record* of what was found — they
are not live dependencies. `fact-health.sh` hits on this directory
are expected for that reason.

Adoption decision (operator, 2026-07-31): all six releases in order
R0→R1→R2→R3→R4→R5; deployment consumes batched after R1 and after
R5. Work tracked in the ledger as wk- issues with premises citing
the tr- facts above.
