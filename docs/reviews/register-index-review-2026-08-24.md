# Adversarial review: the register index change (UNCOMMITTED — do not merge as-is)

Independent pass over `docs/registers.md`, `instruments/register-index.py` and
`.truth/register-index-baseline`, by a reviewer given the diff and the house
conventions only — never the specification, so it checked correctness rather
than compliance. All probes restored byte-identically; `.truth/claims.jsonl`
verified unchanged by sha256.

## Verdict: rework before committing. One check is conceptually wrong.

**Defects, ranked by how well they hide a regression.**

1. **A malformed table row is silently dropped.** A sixth column on the `arms`
   row leaves it un-administered: never mentioned, its location never checked,
   exit unchanged. `index_rows` skips `len(cells) != 5`. **This is the exact
   nine-sources-four-read bug this instrument was built to prevent**,
   reproduced inside it on day one.
2. A location cell without backticks yields zero locations and prints `OK`.
3. `--record-baseline` fail-opens over a broken index: with every row mangled
   it blessed the whole corpus, exit 0, having read no register.
4. `highest_adr_file` degrades silently when a directory is missing — the
   currency gap **shrinks** after a real regression.
5. **Non-zero at rest, and red for a documented non-defect.** `registers.md`
   itself records that the roadmap is a history log citing ids live at the
   time; check (b) fails it for exactly that. The only green path is gameable:
   appending `ADR-061` to the roadmap turns it green with zero review.
6. Column 5, `currency evidence` — the file's stated reason to exist — is
   asserted, never swept.
7. Absolute and `../` locations are accepted; check (a) is satisfiable by any
   path on the machine.
8. The index is outside every sweep it describes: absent from doc-health,
   `citation-scope`, `gate-metrics.md`, `gate-reachability.sh`. Its own
   docstring says `Gate: NONE yet` while the markdown asserts it "is swept like
   any other register" — the ISO-11179 claim is false as shipped.
9. An unreadable input raises a traceback and exits 1, conflated with findings.

**Sound.** Checks (a) and (c) and the mirror rule each fire with a named
message. All documented exits reachable (0/1/2/8). Tier C respected. Measured
claims verified: 25 uncovered docs, 61 ADR files, the fact-health lockstep.
`doc-health` and `pre-commit` both pass.

## What this changes about the plan

Item 0's check (b) as specified is **the wrong measure**: a token count is a
proxy for currency, not currency. Baselining the 28-gap — the fix proposed
before this review — would only have frozen a wrong measure. Currency needs a
different signal, or the roadmap needs to be generated rather than checked
(the EU consolidated-text option in the item-0 brief).

## Why this review exists

The implementing agent demonstrated its own gate going red on all three checks
and reported honestly. Defect 1 still passed under it. A single observer
verifying its own work is the failure mode §8 item 1a measures on this
repository's own verifier separation, and it reproduced here exactly.
