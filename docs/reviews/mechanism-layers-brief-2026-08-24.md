# TODO — mechanism layers, from the 2026-08-24 session

Ledger of what landed and what is still open, from the standards analysis of
2026-08-24. The layer stack L0-L5 is defined in the table below and is
self-contained here; the original working sketch lives untracked in `.local`
and is deliberately not cited, since a reference no clone can resolve is the
very class this brief is about.

Language note: this repository's artifacts are written in English (ADR
headings and bodies, code, tables). `AGENTS.md` carries **no** language rule —
the convention is practice, not policy. Commit messages are, in practice,
Polish. Four artifacts produced in this session broke the artifact convention
and are listed under "remediation" below.

---

## The layer stack

| layer | question it answers |
|---|---|
| **L0** identity | does a name survive relocation? |
| **L1** resolvability | does a reference resolve, or fail loudly? |
| **L2** link freshness | does a resolvable link still mean the same? |
| **L3** position lifecycle | can a position die, instead of keeping its promise? |
| **L4** diagnostics | who checks the checkers, and how often? |
| **L5** refusal observability | does a gate leave a record when it refuses? |

Order is load-bearing: L2 is meaningless without L1, and L1 without L0.

## Landed

| # | layer | what | commit | proved by |
|---|---|---|---|---|
| 1 | — | four Appendix A rows described retired machinery; INV-C/F/J corrected, INV-D's arm named | `ee2f541` | `FAULT B`/`FAULT E` assert the inverse of the rows they gated |
| 2 | L1 | reconciliation pass: Appendix A ↔ arms, three classes, baseline-gated | `c905656` | a row naming `FAULT QQ` exits 1; reverting exits 0 |
| 3 | L1(b) | `arm-index` read 4 of 9 sources for nine days; missing input is now a failure, `SOURCES` corrected | `dc6099c` | count went from "1216 over 9" to 1245 over 5, +29 previously invisible arms |
| 4 | L0/L1 | INV-U pointed at retired `FAULT OV`; repointed at its real gate, and the test declares INV-U back | `dc6099c` | `arm-index` reports INV-U reconciled; the test passes |
| 5 | L2 | **suspect links**: each row↔arm link carries a hash of its target; a change makes the row SUSPECT | `834b210` | inverting `FAULT B`'s header fires `INV-C … CHANGED`, exit 1 |
| 6 | — | ADR-060: normative prose cites a position, and the citation is freshness-checked | `c5c575a` | measurement killed the weaker half of the rule before it shipped |
| 7 | **L2** | **ADR-060 half two**: 221 normative paragraphs carry a hash of the position they cite — the position **plus everything that amends it**, because ADR-019 was never edited; ADR-057 invalidated it from outside | `d786552` | deleting ADR-057's `Amends: ADR-019` fires 13 suspect paragraphs, exit 1; restoring returns 0 |
| 8 | — | ADR-060 and both `.truth/` headers rewritten in English | `d786552` | sibling ADRs are English; `AGENTS.md` states no rule |

---

## Open, ranked by return

| # | layer | what | cost | why it matters |
|---|---|---|---|---|
| 1 | L1(a) | `doc-health` checks backtick paths, not only links — the gap §7 row 4 names | ~20 lines + baseline | **20 of 183 backtick paths are dead (11%)**, two of them inside the paper itself |
| 2 | L0 | `.truth/moved` forwarding table with enforced integrity (dead target = FAIL; resurrected source = FAIL) | one file + ~40 lines | inverts the economics of relocation: one line instead of N edits. `FAULT OV` moved twice with no forward |
| 3 | L3 | registration status per Appendix A row: `Active` / `Superseded-by` / `Retired` (ISO/IEC 11179) | one column + one rule | a row currently cannot die; it can only keep promising. The four rows in `ee2f541` had to be rewritten instead of retired |
| 4 | L4(c) | proof-test interval: the canary proves the detectors once, not on a schedule (IEC 61508) | scheduling + a record | `arm-index`'s own docstring still says `Gate: NONE yet` — the instrument built to find dark gates is one |
| 5 | L5 | refusal log — a separate stream, not the claims ledger | large | without it INV-O stays undecidable: "a refusal writes no record, so this is what the ledger can show, not proof the gate ever fired" (§8 item 1a) |

---

## Findings recorded, not fixed

| finding | why left alone |
|---|---|
| paper §1 says "the fold never reads the clock (ADR-019)"; `kernel.py` under ADR-057 derives expiry from `now_dt` | ADR-057 is `PROPOSED`, agent-authored, **not independently reviewed**. Here the code may be ahead of the record, not the record behind the code. Fixing the prose first would freeze an unaccepted state |
| `docs/truth-ledger-explained.md` carries the three invariant descriptions corrected in `ee2f541` and now contradicts the paper | one file, three lines; deliberately left for a separate decision rather than widened scope |
| 38 unreconciled row↔arm links (baseline) | structural, not neglect: an arm declares a subject from one register, a row points at it from another. Both names are correct; the link is still one-way |
| `INV-U`'s gate is a Python test, so the sweep still classes it `no-arm` | conservative matching under-reports by construction; documented in `arm-index`'s docstring |
| `gate-reachability.sh` CHECKS: 12 globs + 8 literal names, **0 dead** | confirms the prediction that pattern references do not rot; nothing to fix |
| ADR-046 migration table: 2 of 6 named paths dead | will be covered by open item 2 |

---

## Remediation — language convention

| artifact | issue | fix |
|---|---|---|
| ~~`docs/decisions/060-*.md`~~ | — | **done** (`d786552`) |
| ~~`.truth/arm-index-*`~~ | — | **done** (`d786552`) |
| `.local/warstwy-mechanizmow.md` | Polish | `.local` is a working area; lower priority, but inconsistent with the rest |
| commits `ee2f541`…`c5c575a` | Polish messages | matches this repo's *observed* practice (the last three upstream commits are Polish); no history rewrite proposed |

Worth deciding separately: `AGENTS.md` states no language rule. If artifacts
are English and commits are Polish, that is a convention worth writing down —
it is exactly the class of unstated norm this session kept finding.

---

## Hypotheses, with their falsifiers

| hypothesis | status |
|---|---|
| generic `Gate` wording marks decay | **falsified** — INV-B and INV-L have generic wording and live mechanisms |
| the cost of navigation is missing referential integrity, not vocabulary size | standing — falsified if any of findings 1–6 recurs after L0–L2 |
| pattern references do not rot, name references do | **confirmed** — `gate-reachability` 0 dead, ADR-046 2 of 6 dead |
| mechanisms only catch what has an address | standing — falsified by a mechanism catching drift in unaddressed prose |


---

## Handoff — state at session end (2026-08-24)

Seven commits, `ee2f541` → `d786552`. Every one passed `doc-health` (0/15) and
`.githooks/pre-commit` (0). `.truth/claims.jsonl` was never staged: it carries
an uncommitted verdict `tr-06ef0af9` ("weryfikacja po naprawie lockstepu")
that belongs to the operator.

**Layer state**

```
L0 identity              open        .truth/moved
L1 resolvability     (a) open        backtick paths in doc-health  <- next, best return
                     (b) DONE        missing SOURCES entry is a failure
L2 link freshness        DONE        rows (834b210) + prose paragraphs (d786552)
L3 position lifecycle    open        Status column, ISO/IEC 11179
L4 diagnostics       (a) DONE    (c) open   proof-test interval, IEC 61508
L5 refusal log           open        without it INV-O stays undecidable
```

**Two things a successor must not misread**

1. `arm-index` exiting 0 does **not** mean the paper agrees with the code.
   Baselines record today's backlog; they never flag retroactively. §1's clock
   sentence is still false against `kernel.py`, deliberately unrepaired —
   ADR-057 is `PROPOSED` and unreviewed, so the code may be ahead of the
   record rather than the record behind the code.
2. The 38 baselined row↔arm findings are structural, not neglect. Resolving
   one means either the arm names the invariant in its header, or the row
   stops naming the arm. Do not bulk-close them.

**Next action, if picking this up cold**

Open item 1 (L1(a)): teach `doc-health` to check backtick paths, not only
links. ~20 lines plus a baseline. 20 of 183 backtick paths across 57 live docs
are dead (11%), two of them inside the paper. The gap is named by the paper
itself, §7 row 4: *"the sweep guards links and names, not backtick paths, and
reproduction instructions are where the exemption bites."*

**Refresh discipline.** `python3 instruments/arm-index.py --record-links`
rewrites both hash files. Run it **after** reading the suspect rows and
paragraphs, never instead of reading them — refreshing first destroys the
signal the layer exists to produce.
