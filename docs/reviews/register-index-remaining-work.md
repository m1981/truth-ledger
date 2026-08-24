# Register index — what is left to finish

The change is **uncommitted, in the working tree**, with its adversarial review
beside it in `register-index-review-2026-08-24.md`. Three of the ten defects that
review found are fixed; **seven remain**. Read the review first — it carries the
reproduction command for each.

## Fixed, and demonstrated

| # | defect | proof |
|---|---|---|
| 1 | a malformed table row was silently dropped, un-administering its register — the same nine-sources-four-read shape this instrument exists to catch | a sixth column on the `arms` row now yields `exit 1` and `the index row for 'arms' has 6 columns, not the five its header declares`; restored byte-identically |
| 3 | `--record-baseline` fail-opened over a broken index, blessing the whole corpus at exit 0 having read no register | the ADR-042 guards now precede the record branch; mangling every row and recording gives **exit 8**, `read ZERO register rows` |
| 5 | check (b) was the wrong measure: it failed the roadmap for behaving correctly, and its only green path was gameable | check (b) is now **ADR accounting**, not recency — every id with a file in `docs/decisions` or `docs/archive/adr` minus every id mentioned anywhere in `docs/roadmap-v3.md`. `ADR_GAP_THRESHOLD` and the gap logic are deleted. Today's **42** unaccounted ids are baselined in the existing `.truth/register-index-baseline` under the `adr-unaccounted:` key prefix, which cannot collide with the coverage paths already recorded there. Demonstrated three ways, each restored byte-identically: green at rest (**exit 0**); a throwaway `docs/decisions/099-probe.md` gives **exit 1** naming `ADR-099`, and deleting it returns to 0; appending `ADR-061` to the roadmap removes **exactly one** id from the unaccounted set (42 → 41, `removed: ['ADR-061']`) and then trips the mirror rule for that one baselined entry — **exit 1** — instead of clearing the finding |

Why baselining is honest here and was not honest before: the gap was a wrong
measure, and freezing a wrong measure only makes it permanent. Accounting is
the right measure with a real backlog behind it, so the baseline freezes **a
backlog, not a measure** — and the mirror rule keeps that backlog live: an id
recorded there that the roadmap later mentions is itself a failure, so the
file cannot quietly become "whatever used to be true".

At rest the sweep now exits 0: every remaining finding is a recorded backlog
entry, and the seven defects below are latent rather than firing.
`doc-health` and `pre-commit` still pass.

## Remaining, in the order I would take them

**First, the fail-open family — the same class as #1 and #3**

- **#2** a location cell with no backticks yields zero locations and prints `OK`.
- **#4** the ADR-file scan degrades silently when a directory is missing, so
  the finding *shrinks* after a real regression.
- **#7** absolute and `../` paths are accepted; check (a) is satisfiable by any
  path on the machine.
- **#9** an unreadable input raises a traceback and exits 1, conflated with
  findings.

**Then the honesty gaps**

- **#6** column 5, `currency evidence` — the file's stated reason to exist — is
  asserted and never swept. It names ten backticked paths nothing verifies.
- **#8** the index sits outside every sweep it describes: absent from
  doc-health, `.truth/citation-scope`, `gate-metrics.md`,
  `gate-reachability.sh`. Its docstring says `Gate: NONE yet` while the
  markdown asserts it "is swept like any other register" — **the ISO/IEC 11179
  claim is false as shipped** and must either become true or be removed.
- **#10** `sweep(baseline)` never uses its parameter.

## Two operator rulings the sweep cannot make

- Whether the 25 baselined documents genuinely belong to no register.
- Whether the 42 baselined decisions genuinely have no place in the plan, or
  whether the plan should account for them. (The old form of this question —
  whether a threshold of 5 means anything — died with the gap check.)

## The rule this work is judged by

ADR-061: an item is DONE when a gate exists that can go red for its named
reason **and someone has demonstrated it going red**. Both fixes above were
demonstrated. Nothing here is DONE until the same is true of it.


---

## Second review (see `register-index-review-2-2026-08-24.md`)

Defect #5's replacement is **not** finished. The set-difference measure removes
the old threshold's wrongness and introduces a cheaper defeat: one line
pre-accounting ids that do not exist yet defeats the whole check permanently,
because ids mentioned-but-not-filed are never examined. The fix is the lesson
this session keeps re-learning — **make it bidirectional**: an id named in the
plan with no file is itself a finding.

Six further defects are listed there, chief among them a deleted decision
record producing a false message whose prescribed remedy *is* the regression.

Nothing here is DONE under ADR-061 until it has been made to fail and shown to.
