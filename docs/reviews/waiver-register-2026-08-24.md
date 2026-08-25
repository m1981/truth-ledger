# The waiver register — item 0b built, and the false premise it exposed

Operator finding, 2026-08-24: `instruments/semantic-audit.py` and ADR-059
enumerate five of the eight `--*-ok` flags, and the three missing ones are
exactly those that lift execution gates rather than justification-quality
gates. Item 0b of `docs/reviews/mechanism-layers-brief-2026-08-24.md` names
the bidirectional register that would catch it.

Re-measured before acting. The finding holds, and the split is not a
coincidence — it is mechanical.

## 1. The eight, measured from the parser

Harvested by running `truth <verb> --help` for all 22 verbs and reading the
usage lines, not by grepping `cli.py`:

| flag | admitted on | gate it lifts | kind of gate |
|---|---|---|---|
| `--scope-ok` | SENTENCE | a quantifier wider than its evidence (ADR-007) | justification quality |
| `--paths-ok` | SENTENCE | the freehand watch budget (FAZA 3, ADR-055) | justification quality |
| `--generated-ok` | SENTENCE | watching a generated artifact (ADR-037) | justification quality |
| `--evidence-exit-ok` | SENTENCE | a positive claim on a failing probe (ADR-035) | justification quality |
| `--orphan-ok` | SENTENCE | retracting with citations dangling (ADR-036) | justification quality |
| `--duplicate-ok` | **bare boolean** | the G8 near-duplicate refusal | **execution** |
| `--evidence-unsafe-ok` | **bare boolean** | **the evidence screen** (ADR-009) | **execution** |
| `--accept-unsafe-ok` | **bare boolean** | **the acceptance screen** (ADR-014) | **execution** |

**All five sentence-bearing flags are extracted. All three bare flags are
missing. The correlation is exact**, and it is not a stale list: the extractor
walks payload fields, and the three leave no basis field to walk to.

## 2. So the defect is not a rotten list — it is a false premise

ADR-059 opens: *"Every override in this system is admitted on a **sentence**."*
`AGENTS.md` and the extractor's own docstring repeated it.

**It has never been true.** Three of eight are admitted on a bare boolean, and
they are the three with the largest blast radius. The consequence for the
design ADR-059 specifies is structural, not cosmetic: the L2 reader it puts
outside the repository **cannot distinguish "no override happened" from "an
override happened and said nothing"**, because both emit no row. The audit is
blind to the three bypasses that matter most, and blind to its own blindness.

**Population, measured across the whole ledger** (structurally, parsing each
record — see §4 for why that matters):

```
scope_basis                 12      overridden_duplicates       23
paths_basis                  4      accept.screened = false      5
orphan_basis                 1      accept.executed = false      2
evidence_exit_basis          0      evidence.screened = false    0
generated_ok_basis           0
-------------------------------------------------------------------
admitted on a SENTENCE      23      admitted on NOTHING         28
```

More of this repository's standing bypasses were admitted on nothing than on
an argument.

## 3. What was built

**`docs/waivers.md`** — the register. Seven columns: flag, verbs, gate it
lifts, admitted on, stamp on the record, decays, governing record.

**`instruments/waiver-index.py`** — Tier C, bidirectional from the start:

- **forward** — every listed flag is accepted by the parser, on the verbs the
  row names, taking the argument the row says it takes;
- **reverse** — every `--*-ok` flag the parser accepts has a row. *This is the
  direction whose absence let `--exit-ok`, a flag that has never existed, live
  in `AGENTS.md`, ADR-059 and `semantic-audit.py` simultaneously, all three
  citing ADR-035, whose own text says `--evidence-exit-ok`.*

The inventory comes from **running the CLI**, not from a regex over `cli.py`.
A regex would be a second implementation of the parser, and this repository's
standing finding is that a second implementation drifts silently because both
copies look right in isolation — the same defect as `fact-health.sh` holding
its own copy of a corpus the gate read from a file.

**No baseline, deliberately.** Every other sweep here has one because each was
introduced onto an existing backlog. This register is complete at birth, so
there is nothing to freeze and a baseline file would be an empty apparatus
inviting its first entry.

**Three corrections** to the premise: ADR-059 (PROPOSED, body edit permitted),
the extractor's docstring, and `AGENTS.md` — each now states five-of-eight,
names the three, and says why the split falls where it does.

## 4. Two defects I introduced and caught before shipping

Recorded because a self-demonstration that reports only successes is the
failure mode this repository measures.

**The first population count was a substring scan, and it under-reported.** It
looked for the stamp's field name in each ledger line, and reported **0** for
`accept.screened = false` where the truth is **5** — a nested field and a
required value are both invisible to a substring match. It was silently wrong
about exactly the three flags the register exists to surface, and it failed in
the shrinking direction: the number gets smaller as the problem gets bigger,
which is the same shape as an ADR count that shrank when a directory went
missing. Replaced with a structural read: a dotted path into the payload,
optionally with a required value, over parsed JSON. A ledger line that will
not parse is now COUNTED, not skipped.

**The ADR-042 guard was aimed at the wrong case, and an arm caught it.** I
guarded "zero rows" and "zero flags" separately, each returning exit 8. With
rows present and zero flags harvested that is both inaccurate — 22 verbs and
every row *were* examined — and less informative than the divergence itself,
which is that every waiver names a flag the CLI no longer accepts. The case
the rule is really about is **both** sides empty: empty agrees with empty,
produces no finding, and would report a clean escape surface having read
neither. That is now the only case that exits 8; the rest report the
divergence at exit 1. Both block, so nothing fails open either way — exit 1
just says more.

## 5. The gate, and every arm demonstrated red (ADR-061)

Four arms in `TestTierCInstruments`, which runs at
`scripts/release-battery.sh:251` — the pre-push battery. They use a **stub CLI
whose `--help` the suite controls**, because the honest way to seed a
divergence in an instrument that harvests by running a program is to control
that program's output, not to patch the instrument.

Each check disabled in turn, the suite run, then restored from a sha-verified
copy (`62de8774…` before and after):

| check disabled | arm that went red |
|---|---|
| reverse direction (flag with no row) | `runs_in_both_directions`, `refuses_to_report_health_over_nothing` |
| forward direction (row with no flag) | `runs_in_both_directions`, `refuses_to_report_health_over_nothing` |
| argument-shape check | `checks_what_a_waiver_is_admitted_on` |
| verb-list check | `checks_what_a_waiver_is_admitted_on` |
| structural population → substring scan | `counts_the_population_structurally` |
| unreadable ledger line skipped silently | `counts_the_population_structurally` |
| both-empty ADR-042 guard | `refuses_to_report_health_over_nothing` |
| the no-table-header finding | `refuses_to_report_health_over_nothing` |
| the CLI-exited-non-zero guard | `refuses_to_report_health_over_nothing` |

**Two probes were initially mis-aimed and reported STILL GREEN, and both were
my error, not a gap.** The first patched a string that occurs twice and edited
the wrong occurrence — `.replace()` silently did nothing, so the "disabled"
check was never disabled. The second targeted the `OSError` branch, but the
test's case (a CLI that is a directory) is caught by the *non-zero exit*
branch instead; and disabling that one still exited 3, because a second guard
— empty help yields no verbs — caught it. Defence in depth, not coverage. An
arm that cannot tell two guards apart is not proof of either, so a case was
added that isolates it: **a stub CLI that prints perfectly usable help and
then exits 3.** Trusting a parser that reported failure is reading an
inventory from a program that said it was broken. With the guard removed, that
arm now goes red.

The register was also added as a row in `docs/registers.md`, so
`register-index` checks its location and its currency paths; and
`waiver-index.py` was classified in `TestTierCInstruments`. That
classification was not voluntary — **the coverage arm added earlier today
failed the moment the new instrument appeared**, which is the reverse
direction of that check doing its job unprompted.

## 6. Standing state

```
python3 instruments/waiver-index.py                     exit 0   8 waivers over 22 verbs
python3 instruments/register-index.py                   exit 1   the ONE pre-existing failure
python3 instruments/arm-index.py                        exit 0   1259 arms
bash scripts/fact-health.sh                             exit 0
bash template/scripts/doc-health.sh                     exit 0
bash scripts/gate-reachability.sh                       exit 0
bash .githooks/pre-commit                               exit 0
.venv/bin/python template/scripts/test-integrations.py  Ran 43 -- OK
.venv/bin/python template/scripts/test-truth-core.py    Ran 538 -- OK
```

The register-index failure is unchanged and is the operator's ruling: ADR-062
has a file and the roadmap accounts for it in no tense.

**A suspect link was raised and cleared by reading, for the second time this
session.** Adding four arms to `TestTierCInstruments` changed that family's
hash, so INV-U's Appendix A row went SUSPECT again. The row names
`test_override_velocity_real_and_sandbox` specifically, which this change does
not touch (`git diff … | grep -c override_velocity` → 0). Refreshed after
reading: one line moved, prose hashes byte-identical.

Twice in one session is now enough to call it a property rather than an
incident: `arm_text()` hashes the whole FAMILY — the class plus every arm
label in it — so adding any unrelated test to a class makes every Appendix A
row naming any arm in that class SUSPECT. Deliberate coarseness, documented in
its own docstring. But at this rate it trains a reader to refresh without
reading, which is the one thing the refresh discipline forbids. Worth an item.

## 7. What is NOT done

- **The three overrides still carry no rationale.** This work made that
  *visible and gated*; it did not fix it. Giving `--duplicate-ok` a SENTENCE
  and adding basis fields for the two unsafe flags changes the intake gates
  and belongs in its own record, with its own adversarial pass. ADR-059 now
  names that residue instead of asserting it away.
- **`stamp`, `decays` and `governing record` are unchecked columns.** Each
  needs its own reader: whether the kernel really writes that field, whether
  the decay is implemented, whether the cited record says what the row says.
  Named in both the register and the docstring rather than left blank — an
  unchecked column not marked as unchecked is what this register exists to
  catch.
- **`--evidence-unsafe-ok` has never been used** (0 records). The flag is live
  and the trace is possible; nothing has taken it. Recorded so a future zero
  is not read as a gate that fired.

---

# The adversarial review of this change, and what it cost

Dispatched on the diff per ADR-062 rule 3, without the finding or any defect
list. It returned thirteen findings. **The first one is the same defect this
change was written to end, committed inside the artifact that names it**, and
it is the most instructive thing in this document.

## D1 — the register omitted an override, and the count shrank to fit the list

`--refresh-evidence` lifts a hard ADR-051 refusal (`policy.py`: *"Nothing was
filed."*), takes a `SENTENCE`, stamps `evidence_refresh.basis`, is counted as
an override by `reports.py`, and is extracted by `semantic-audit.py` — the
sibling instrument this very change edits. It had **no row**, and the reverse
check could not have found it: `USAGE_FLAG_RE` matched `--*-ok` only.

And the prose gave it away. My own sentence read:

> **FIVE of the eight overrides in this system are admitted on a sentence.**
> `--scope-ok` … `--paths-ok` … `--generated-ok`, `--evidence-exit-ok`,
> `--orphan-ok`, and ADR-051's `--refresh-evidence` …

Six named, five asserted. The identical error was in `semantic-audit.py` and
`AGENTS.md`. That is not a slip: **the count was fitted to the list**, which
is exactly the failure the change is a response to, reproduced by the author
one paragraph after describing it.

## The tenth override, which the review did not find and the fix did

Widening the check to "`-ok` suffix OR takes a SENTENCE" would have caught
`--refresh-evidence` and stopped there. Rebuilding the reverse direction as a
**total** classification instead — every flag the parser accepts must be a
waiver row or a declared non-override — immediately surfaced five unclassified
flags, of which one more was a real override:

> **`--single-run` skips the G6 determinism double-run**, "accepting
> false-divergence risk", and **writes no field into the record at all**.

It matches neither historical shape. The other three bare overrides at least
leave `screened: false` or `overridden_duplicates`; this one is invisible in
the ledger, so its use cannot be counted by this instrument or any other. The
sweep now prints `NOT COUNTABLE` for it rather than printing a zero, because a
zero would read as "never used".

**The general lesson, and it is the third time this session:** a heuristic over
names is not a reverse direction. Both name-shaped rules were wrong here, in
the same direction, about different flags. The only check that closes it makes
the judgement explicit per flag and refuses until somebody has made it.

So the true figures are **ten overrides, six on a sentence, four on nothing** —
and no count in these files is authoritative any more. `docs/waivers.md` now
says so and points at the instrument.

## D2 — the headline number counted the flag the register omitted

I published "23 records carry an override sentence, 28 carry none". The five
registered sentence fields total **17**; the 23 was reachable only by
including `evidence_refresh`, which had no row. The conclusion survives — 28
against 17 is a *wider* margin, not a narrower one — but it was derived from a
set the register did not admit existed. Corrected wherever it was restated.

## The rest, all confirmed and fixed

| # | finding | fix |
|---|---|---|
| D3 | six argparse renderings walked straight past the harvester at exit 0 — a lowercase metavar, a digit in the flag name, a non-`-ok` name, an alternation group, a required unbracketed argument, and a verb whose name carries a digit | the inventory is read from the `options:` section and **cross-checked against the usage line**; a disagreement between the two renderings of one parser is itself a finding. Verb regex widened to `[a-z][a-z0-9-]*` |
| D4 | the prose claimed the reverse direction is "what would have caught `--exit-ok` in three documents" — it reads two files and neither is those three | claim removed. The register catches a phantom flag only if someone files a row for it; what it actually closes is a flag arriving with nobody having judged it |
| D5 | **eleven checks could be deleted with the suite green**, including the missing-trailing-pipe check that is the block parser's entire justification, and the zero-verbs guard my own §5 credited as defence-in-depth | **all eleven now have arms**, plus three more the review did not name. Every one demonstrated red below |
| D6 | "how many bypasses are standing" is a raw count over an append-only history; the docstring said "standing" two paragraphs from "does not fold and must not imply that it derived a status" | reported as `record(s) in history`, with the contradiction removed and `semantic-audit` named as the folded answer for the six sentence-bearing ones |
| D7 | "the expiry for two" against three rows marked decaying; and `decays: yes, 30d` is defeasible by an explicit `--ttl-days`, already used in this ledger at **3650 days** | count removed, opt-out named in the Not-checked section |
| D8 | the population half fails open on a missing or empty ledger | `population unknown` is printed and gated by an arm; the deeper point stands and is disclosed |
| D9 | `gate it lifts` is unchecked and was not in the Not-checked list, in a file whose argument is that an unmarked unchecked column is the defect | added, together with the note that `--accept-unsafe-ok`'s cell conflates two refusals on two verbs |
| D10 | the register restated five counts, carried zero ledger ids, and sits outside the prose corpus, so nothing would ever re-check them | every count removed from the prose; the file now says explicitly that the instrument is the only authority |
| D11 | a blank line mid-table silently truncated the register, and the resulting message prescribed "add the row" for a row three lines below | the truncation is reported at its own line number |
| D12 | `bare = "nothing" in cell.lower()` fired on the legitimate cell `SENTENCE, never nothing` — a check going red on a valid input | `admitted on` is a controlled vocabulary; anything but `SENTENCE` or `nothing` is its own finding |
| D13 | committing this would sweep in the `AGENTS.md` redraft that `d7735fa` deliberately did NOT commit | **process, and correct.** Flagged for the operator; these are separate changes and must be separate commits |

## Every check demonstrated red (ADR-061), including the eleven

Each disabled in turn, the suite run, the instrument restored from a
sha-verified copy (`196bad55…` before and after):

| check disabled | arm that went red |
|---|---|
| classification of an unclassified flag | 4 arms |
| a flag on both sides (row and policy) | `classifies_every_flag…` |
| the policy mirror rule | `classifies_every_flag…` |
| an unreasoned policy entry | `classifies_every_flag…` |
| M11 not-a-row (missing trailing pipe) | `reads_the_table_as_a_block` |
| M10 seven-column check | `reads_the_table_as_a_block` |
| M12 duplicate-row check | `reads_the_table_as_a_block` |
| M13 no-backticked-flag check | `reads_the_table_as_a_block` |
| M15 header-not-followed-by-separator | `reads_the_table_as_a_block` |
| M17 blank-line truncation | `reads_the_table_as_a_block` |
| M14 one-flag-two-shapes | `harvests_flag_shapes…` |
| M16 zero-verbs harvested | `refuses_to_report_health…` |
| M20 ledger-missing → population unknown | `population_says_when_it_cannot_measure` |
| M18 / M19 usage guards | `usage_guards` |
| options/usage cross-check | `harvests_flag_shapes…` |
| the forward direction | `runs_in_both_directions` |
| the argument-shape check | `checks_what_a_waiver_is_admitted_on` |
| the verb-list check | `checks_what_a_waiver_is_admitted_on` |
| the controlled vocabulary | `admitted_on_is_a_controlled_vocabulary` |
| structural population → substring scan | `counts_the_population_structurally` |

M14 and M16 were **still green on the first pass** — two checks with no arm,
exactly as the review said. Each needed a case that isolates it: a stub whose
top-level help lists no verbs at all (M16), and a flag taking a sentence on one
verb and nothing on another (M14). The options/usage cross-check needed a stub
able to disagree with itself, which argparse never does — the arm exists
because a reader quietly wrong about one rendering is how an override goes
unlisted.

## Standing state

```
python3 instruments/waiver-index.py     exit 0  10 waivers, 50 flags, 0 unclassified
python3 instruments/register-index.py   exit 1  the ONE pre-existing failure
python3 instruments/arm-index.py        exit 0  1268 arms
bash scripts/fact-health.sh             exit 0
bash template/scripts/doc-health.sh     exit 0
bash scripts/gate-reachability.sh       exit 0
.venv/bin/python .../test-integrations.py   Ran 49 -- OK
.venv/bin/python .../test-truth-core.py     Ran 538 -- OK
```

INV-U's suspect link fired a third time and was cleared by reading, not by
refreshing first: the row names `test_override_velocity_real_and_sandbox`,
which this change does not touch (`git diff … | grep -c` → 0); its class
gained the waiver arms. Three times in one session settles it — see the item
on `arm_text()`'s family-level granularity above.

## What is still NOT done

- **The four sentence-less overrides still carry no rationale**, and
  `--single-run` still carries no record at all. Making it stamp something is
  a change to the intake path and belongs in its own record.
- **`gate it lifts`, `stamp`, `decays` and `governing record` remain
  unchecked.** Hand-verified once, gated by nothing.
- **The population does not fold.** The active figures are roughly half the
  historical ones.
- **`AGENTS.md` must not ride this commit** (D13). The redraft is its own
  change with its own review.

---

# Operator round, 2026-08-25

Four instructions, and two of them found defects the two adversarial reviews
had not.

## 1. Three reasons were abandoned mid-clause, and now a gate says so

`.truth/waiver-not-an-override` carried three entries that stopped mid-sentence:

```
--basis         reasoning basis (required for INFERRED), so it is the opposite
--watch-policy  names a REVIEWED watch set, which is the alternative to an
--ttl-days      the shelf life; a large value is ADR-032's visible opt-out, so
```

All three restored to finished sentences. **A half-written reason is worse
than a missing one**: a missing reason is refused by the existing check, while
a truncated one satisfies it and reads as a judgement somebody made, so
nothing ever prompts anyone to finish it and the flag stays excused on half an
argument.

New check: a reason ending on a joining word, or with no sentence-final mark,
is a finding. Arm: `test_waiver_index_refuses_a_reason_abandoned_mid_clause`.

**The narrow half cost as much as the broad half.** The first cut listed every
conjunction and preposition and produced **five false positives** against
legitimate reasons — "never by this.", "rather than through it." Pronouns and
negations end English sentences perfectly well. A check that fires on a valid
input is worse than one that misses, so `DANGLING_WORDS` is now the narrower
set of words after which a sentence cannot stop, and the arm carries six
negative controls alongside its four positives.

**Demonstrated red**, then restored byte-identically:

```
disable the check              -> FAIL: ..._refuses_a_reason_abandoned_mid_clause
restore the three truncations  -> 3 FAILs, each naming its own tail:
    --basis        'opposite' and no sentence-final mark
    --watch-policy joining word 'an' and with no full stop
    --ttl-days     joining word 'so' and with no full stop
sha256 instruments/waiver-index.py    b5f71c57…  before and after
sha256 .truth/waiver-not-an-override  9d27b401…  before and after
```

## 2. `--ttl-days` moved to the register, and the vocabulary grew a third value

The truncated reason was truncated **around the fact that decides the
question**: ADR-032 calls an explicit `--ttl-days` "the visible opt-out", and
the entry recorded that and then classified the flag as not-an-override. It
argued against itself.

Ruling: **it is a waiver.** It suppresses the 30-day shelf life ADR-032 stamps
on a claim carrying `--scope-ok`, `--paths-ok` or `--generated-ok`, so the
override judgement is never re-asked. On a claim with no override basis it
lifts nothing — that condition is prose in the `gate it lifts` column and is
not checked.

It takes a number, which is neither a rationale nor nothing, so `admitted on`
became a three-value vocabulary: `SENTENCE`, `a value`, `nothing`. **A value
admits an override without justifying it**, and that is worth being able to
say rather than rounding to one of the other two.

**The other 39 were scanned for the same defect** — a reason arguing against
its own classification — by grepping each flag's own help text for bypass
language (`skip`, `without`, `despite`, `accepts risk`, `override`, `refus*`,
`exempt`, `unsafe`, `force`). Four hit, all four cleared on reading: for
`--accept-cmd` and `--supersedes` a refusal acts *on* the flag, not through
it; `--cause` is REQUIRED; `--paths`'s hit is real but is not about the flag.

**And it surfaced a bypass that is not a flag at all.** A
`<path>#<selector>` entry is exempt from the one-path and churn budgets by
ADR-055. No row in this register can hold it and the sweep cannot see it,
because the register's unit is a flag. Recorded under `--paths` in the policy
file and in the brief's residue.

## 3. The `--accept-unsafe-ok` row, corrected to what the code does

It named one refusal. The code has two, on two verbs:

| verb | refusal lifted | stamp |
|---|---|---|
| `issue` | the ADR-014 **screen** — an `--accept-cmd` the allowlist rejects is refused; this files it anyway | `accept.screened = false` |
| `done` | **execution** — a stored unscreened oracle will not be run; this closes without running it | `accept.executed = false`, plus the above |

Measured 2026-08-25: 5 records and 2 records, **the second a strict subset of
the first**. The flag's population is 5, never 7.

## 4. The counting rule, so "28" is reproducible

That subset relation is exactly why a population figure needs a stated rule,
and ADR-059 now carries one: count distinct **record ids**; one field per
waiver — the field set *whenever* the flag is used; a total across waivers is
a **union**, never a sum; a value is not a rationale; and **every total is a
lower bound**, because `--single-run` writes nothing and appears in no figure.

Verified for today's ledger: the three sentence-less stamps are pairwise
disjoint (0 overlap in all three pairs), so 23 + 5 + 0 happens to equal the
union of 28 — an observation about this data, not a property, and the rule
says to take the union anyway.

## 5. Item 0b is DECLARED, not DONE

Membership is DONE — gated in both directions, without a naming heuristic,
twenty checks each demonstrated red. **The four content columns are not**, and
the argument for DECLARED is a measurement rather than caution: `--ttl-days`
and `--accept-unsafe-ok` are **two defects in one column inside the change
that built the register**, both found by reading, neither reachable by any
check that exists. The membership gate was satisfied in both cases — the flag
*was* classified, the row *was* present.

Marking the register DONE on that evidence would be *"Batch 3 —
self-consistency — DONE"* with a fresh date. The brief now carries the
residue, what DONE would require per column, and the note that `gate it lifts`
may never be mechanisable — in which case it is DECLARED permanently, and the
register says which columns are which.
