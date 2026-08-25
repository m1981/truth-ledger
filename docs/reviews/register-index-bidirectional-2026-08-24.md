# register-index — the seven open defects, closed, and the rule they all shared

Third pass over `instruments/register-index.py`, after two adversarial reviews
found fifteen defects between them. This document is the implement role's
output under ADR-062: the change, and a demonstration of each gate going red,
restored byte-identically. It is written **before** the review of this change
is dispatched (rule 4).

## The rule the two reviews were both pointing at

Every defeat this instrument suffered had one shape: **a check that walks from
A to B and never walks back.**

| defeat | the direction that existed | the direction that did not |
|---|---|---|
| review 2, defect 1 | a filed decision the plan never mentions | an id the plan mentions that was never filed |
| review 1, defect 2 | a location cell naming a path that is gone | a location cell naming nothing at all |
| review 1, defect 5 (old form) | the roadmap's highest id vs the register's | — the measure itself was the wrong one |

So the rule is now written into the file's docstring under its own heading
rather than left to be re-learned a fourth time, and each of checks (a), (b)
and (c) states both directions.

---

## Defect 1 (chief): one line pre-accounted every future decision

**What review 2 reported.** Appending `<!-- ADR-062 … ADR-200 -->` to the
roadmap makes every future decision accounted for on arrival, because ids
mentioned-but-not-filed were never examined.

**What I measured, before fixing it.** The report is right in substance and
**not reproducible as printed**, which matters because the difference is the
whole fix. Two forms, and only one of them is silent:

| probe | old behaviour |
|---|---|
| append `<!-- ADR-062 ... ADR-200 -->` verbatim | the ellipsis is prose; the regex matches only `ADR-062` and `ADR-200`. Exit 0 — but it accounts for two ids, not a range |
| append every id 001–200 enumerated | 42 baselined entries stop being findings → **42 mirror-rule failures, exit 1.** LOUD. The bulk clear does not work |
| append every id **063–200** — unfiled and unbaselined only | **exit 1 with the one pre-existing failure and nothing else.** Then file `docs/decisions/100-probe.md`: still that same one failure. ADR-100 was accounted for on arrival, in total silence |

The third row is the defect. It is narrower than reported and worse than it
looks: the noisy forms are the ones an attacker would not use.

**The fix.** Check (b) reverse. Every id the roadmap mentions with no file is
PHANTOM, a finding, baselineable under `adr-phantom:`.

**Demonstrated** (throwaway copy of the tree; the real tree byte-identical
throughout, `.truth/claims.jsonl` never opened for writing):

```
$ printf '<!-- ADR-063 ... ADR-200 (enumerated) -->' >> docs/roadmap-v3.md
  adr accounting  62 ADR file(s), 62 id(s) filed, 157 mentioned; 43 unaccounted
                  (42 excused), 138 phantom (0 excused)
  138 × "ADR-nnn is mentioned in docs/roadmap-v3.md and has no decision record"
  register-index: 139 failure(s)                                       exit 1
$ # restored
  register-index: 1 failure(s)                                         exit 1
```

The line that used to cost nothing now costs one finding per id.

---

## Defect 2: a deleted decision record, and a remedy that WAS the regression

**Reproduced first.** `mv docs/decisions/061-*.md` away:

```
FAIL  adr-unaccounted:ADR-061 ... but docs/roadmap-v3.md now mentions it
      -- the baseline entry outlived its finding; drop the line
```

The roadmap never mentioned ADR-061. The record vanished. And following the
prescribed remedy — dropping the line — returned the sweep to its baseline
exit, so a deleted decision record became indistinguishable from a resolved
one.

**Why the first attempt at this fix did not work, recorded because it is the
instructive part.** My first discriminator asked "is this id PHANTOM?". It is
not: phantom is `cited − filed`, and a deleted record that the roadmap never
cited is in neither set. The correct question is which set the id left, so the
sweep now carries `filed_ids` and `cited_ids` rather than only their counts.
Three outcomes, and a fourth that says so:

| the baselined id is | meaning | prescribed remedy |
|---|---|---|
| no longer in `filed` | the RECORD VANISHED | restore the record; **do NOT drop the line** |
| now in `cited` | the roadmap accounts for it | drop the line |
| filed, uncited, yet not a finding | arithmetically impossible | reported as a bug in the sweep, not in the register |

**And the residue.** Dropping the line still removed the last pointer at
ADR-061. So check (b) gained a **third** direction: a hole in the number
space. `docs/decisions/README.md` states the space is single, never
restarted, and that a superseded record is superseded IN PLACE — so a hole is
a record that vanished. Measured before relying on it: 62 ids, 001–062, **0
gaps** today.

```
$ mv docs/decisions/061-*.md away  &&  drop its baseline line
  number-space gaps  ADR-061 (0 excused)
FAIL  ADR-061 has no record in docs/decisions or docs/archive/adr, but
      higher-numbered decisions do ... Restore it, or record adr-gap:ADR-061
  register-index: 2 failure(s)                                         exit 1
```

The old prescribed remedy no longer buries anything.

---

## The other five, each reproduced then demonstrated red

| # | defect | before | after |
|---|---|---|---|
| **(2)** | a location cell with no backticks yields zero locations and prints `OK` | `OK ledger (no location)`, total failures **unchanged** — a register outside `docs/` un-administered in total silence | `FAIL ledger` + "the index row names no location this sweep can read" |
| **(4)/(3)** | the ADR scan degrades silently: a missing directory shrinks the finding, an unparseable filename vanishes from a count taken from the matches | `9 ADR file(s), 9 id(s) filed` and **34 mirror-rule findings misdiagnosed** as "roadmap now mentions it"; `ADR-063-new.md` → still `62 ADR file(s)`, exit 0 | the measure is **SUSPENDED** and says so, the mirror rule is skipped entirely (**0 misdiagnoses**), the count comes from the directory (`63 ADR file(s), 62 filed`) and the unparseable name is its own finding |
| **(7)** | absolute and `../` locations accepted — check (a) satisfiable by any path on the machine | `OK roadmap /etc/passwd` | `FAIL … 'is an absolute path'` / `'escapes the repository with ..'` |
| **(9)** | an unreadable input raises a traceback and exits 1, conflated with findings | `Traceback (most recent call last)` … exit 1 | exit **3**, `cannot read the register index (docs/registers.md): Permission denied -- the sweep did NOT run. This is an environment failure, not a finding`, zero traceback lines |
| **(6)** | column 5, `currency evidence` — the file's stated reason to exist — asserted and never swept | ten backticked paths nothing verified | every backticked token **containing a slash** is a path and must exist; an empty cell is a finding. Rule stated in the docstring rather than guessed. Measured against the real index: **20** path tokens across 10 rows at the time of this change (22 across 11 once the waiver register was added later the same day — read the number off the sweep, not off this line), all live, and **zero false positives** on the non-path tokens (`currency evidence`, `adr-unaccounted:`, `adr-phantom:`, `adr-gap:`, `nnn-slug.md`). An earlier draft of this line said 19 and named two tokens (`wk-1d000ad4`, `*.md`) that are not in the file — a hand count and a stale example, in a change whose thesis is that hand counts are what this repository keeps getting wrong. The sweep now prints the number itself, so the next reader does not have to trust this sentence |
| **(10)** | `sweep(baseline)` never uses its parameter | — | parameter removed |
| **(r2-4)** | a baseline line needs no reason — the key alone excuses | — | a bare key is a finding: "a bare key excuses a finding while recording nothing about why" |
| **(r2-5)** | `--record-baseline` stamps a literal `2026-08-24` whatever the date — a staleness generator inside the anti-staleness file | every re-record restamped every entry | **first-seen dates are preserved.** Demonstrated: 25 entries hand-dated `2026-07-01`, re-recorded → all 25 **still** `2026-07-01`; a newly uncovered file gets today. And it now prints **every key it records** (68 lines), not a count |

**Regression guard.** The previously-fixed defect 3 was re-checked, since this
was a substantial rewrite: `--record-baseline` over an index with every row
mangled still exits **8** having read zero registers, and the baseline file is
**byte-identical** afterwards.

---

## Defect 8: the index was outside every sweep it described

`docs/registers.md` asserted the index "is swept like any other register"
while the instrument's own docstring said `Gate: NONE yet`. One of the two had
to change. **The gate was built**, because a norm without a red-gate condition
is not DONE (ADR-061).

Four arms in `template/scripts/test-integrations.py`
(`TestTierCInstruments`), which rides the release battery:

- `test_register_index_on_the_real_repository` — deliberately does **not**
  assert exit 0. Check (b) carries a real backlog, and an arm demanding green
  would be satisfied by somebody baselining the backlog away. It demands the
  sweep RAN: exit 8 and exit 3 both fail it, and `measured` must be true.
- `test_register_index_check_b_runs_in_both_directions` — forward and reverse
  against a throwaway tree, from a control tree proved clean first.
- `test_register_index_tells_a_deleted_record_from_a_resolution` — the same
  baseline entry, both causes, opposite remedies, then the number-space arm.
- `test_register_index_fails_loudly_on_a_missing_or_unreadable_input` —
  unlocated row, absolute location, exit 8, `--record-baseline` refusing to
  bless an unread corpus, exit 3 with no traceback.

**Each arm was made to fail by removing the check it covers**, then the
instrument restored from a sha-verified copy:

| break | result |
|---|---|
| `accounting["phantom"] = []` | `FAIL: test_register_index_check_b_runs_in_both_directions` |
| the `filed_ids` discriminator disabled | `FAIL: …tells_a_deleted_record_from_a_resolution` |
| the unlocated-row finding disabled | `FAIL: …fails_loudly_on_a_missing_or_unreadable_input` |
| the absolute-path refusal disabled | `FAIL: …fails_loudly_on_a_missing_or_unreadable_input` |
| `InputError` replaced by a bare `raise` | `FAIL: …fails_loudly_on_a_missing_or_unreadable_input` |
| restored | `sha256 f88631af…` identical, **Ran 34 tests, OK** |

A fifth arm was added while here, for the same reason: the class docstring
claimed "6 of the 10 scripts in `instruments/`" for a directory of **eleven**,
having previously claimed "all 5" for a set of nine. Prose counts are what
this repository keeps getting wrong, so the two sets are now data and
`test_every_instrument_is_classified` reconciles them against the directory in
both directions. Demonstrated red both ways: an unclassified new instrument
fails it, and a declared name with no file fails it.

## Defect r2-7: stale prose in the previous pass's own edits

- The docstring claimed "one token clears exactly the one decision it names".
  One *line* clears as many as it enumerates. Rewritten.
- `docs/reviews/register-index-remaining-work.md` says the first review found
  **ten** defects. It lists **nine**. Its own remaining list then numbers an
  item `#10` that review 1 does not contain — `sweep(baseline)` never uses its
  parameter, which is a real defect that was discovered while writing the
  summary and folded into a count of the review. Recorded rather than silently
  renumbered.

---

## Standing state

```
python3 instruments/register-index.py        exit 1   -- ONE failure, pre-existing
python3 instruments/arm-index.py             exit 0   -- 1250 arms (was 1245: +5 new test arms)
bash scripts/fact-health.sh                  exit 0
bash template/scripts/doc-health.sh          exit 0
bash scripts/gate-reachability.sh            exit 0
bash .githooks/pre-commit                    exit 0
.venv/bin/python template/scripts/test-integrations.py   Ran 34 tests -- OK
.venv/bin/python template/scripts/test-truth-core.py     Ran 538 tests -- OK
```

**The one failure is an operator ruling, not a defect, and it is deliberately
left standing:** ADR-062 has a file and the roadmap accounts for it in no
tense. `docs/reviews/register-index-remaining-work.md` names this exact
question as one the sweep cannot decide — whether the unaccounted decisions
genuinely have no place in the plan. Citing ADR-062 in the roadmap, or
baselining it, is the operator's call. Nothing here made that call, and the
gate arm was written so that it never has to be made to keep the suite green.

**One suspect link was raised and cleared by reading, not by refreshing
first.** Adding five arms to `TestTierCInstruments` changed that family's
hash, so INV-U's row went SUSPECT. The row names
`test_override_velocity_real_and_sandbox` specifically — untouched — and the
family gained five unrelated siblings, so the row still holds. Then
`--record-links`: exactly one line moved, and `.truth/arm-index-prose-hashes`
is byte-identical.

That is worth recording as a property of `arm-index`, not a defect in it:
`arm_text()` hashes **the whole family** (the class) plus its arm labels, so
adding any unrelated test to a class makes every Appendix A row naming any arm
in that class SUSPECT. Deliberate coarseness — its docstring says so — but it
is a noise source that will, at some volume, train a reader to refresh without
reading. Named here so the next person meets it as a known property.

## What is NOT done

- The **operator rulings** the sweep cannot make: whether the 25 baselined
  documents belong to no register, and whether the 43 unaccounted decisions
  belong in the plan.
- **The number-space gap check rests on a stated convention, not a gate.**
  `docs/decisions/README.md` says the space is never restarted; nothing
  enforces that a withdrawn number stays occupied. If a legitimate hole is
  ever created, this check fires and the remedy is a baseline line with a
  reason — which is the designed behaviour, but it is a convention holding a
  check, and that is the weakest link in the three directions.
- **Coverage is by path prefix**, so a register whose membership is a LIST
  (`.truth/citation-scope`) still covers nothing. Unchanged, by construction.
- The currency column is checked for path EXISTENCE only. Whether the
  mechanism a cell names is wired to anything is still `gate-metrics.md`'s
  question — and six of its rows are past their review date with no reader.
