# Second adversarial review: the ADR-accounting measure (still NOT done)

Independent pass over the replacement for defect #5, run entirely in a
scratchpad copy; the real tree is byte-identical and `.truth/claims.jsonl`
untouched.

## Verdict: better in principle, gameable in a new way. Do not call it fixed.

The set-difference measure is right to replace a threshold — a token count was
a proxy for currency, and the roadmap was failed for behaving correctly. But
the replacement has a cheaper defeat than the one it removed.

**1. One line pre-accounts decisions that do not exist yet.** Appending
`<!-- ADR-062 … ADR-200 -->` to the roadmap makes every future decision
accounted for on arrival: a later `docs/decisions/100-probe.md` gives exit 0,
no baseline edit, no mirror-rule trip. **Ids mentioned but not filed are never
checked**, so nothing notices. HTML comment, code fence and link all count
identically. Two commands clear the current backlog as well.

*The fix is the lesson this session keeps re-learning: make it bidirectional.*
An id mentioned in the plan with no file is itself a finding.

**2. Deleting a decision record passes, and the tool prescribes the
regression.** `mv docs/decisions/061-*.md` → exit 1 with `… but roadmap now
mentions it -- drop the line`. The message is **false** — the roadmap never
mentioned it, the file vanished — and following the prescribed remedy gives
exit 0. The mirror rule cannot tell "accounted for" from "record deleted".

**3. An ADR filename that does not parse is invisible.** `ADR-062-new.md` →
exit 0, still `61 ADR file(s)`. The count is taken from matches, so the reading
hides its own skip. This is the silent residue of defect #4.

**4. A baseline line needs no reason** — the key alone excuses.
**5. `--record-baseline` is a one-command green** for both key spaces, and
stamps a literal `2026-08-24` whatever the date: a staleness generator inside
the anti-staleness file.
**6.** With `docs/archive/adr` missing the sweep fails loudly but misdiagnoses
34 findings as "roadmap now mentions it".
**7. Stale prose in the edits**: the review is cited as finding ten defects
where it lists nine, and the docstring's "one token clears exactly the one
decision it names" is false — one *line* clears 139, including unwritten ones.

## Verified sound

Check (b) fires on a new unaccounted id and on a stale baselined entry, exactly
as documented. The two baseline key spaces are genuinely disjoint — no crafted
entry in one silenced a finding in the other. Counts reproduce: 42 unaccounted,
25 uncovered, 61 filed, exit 0 at rest. The threshold and the `highest_*`
helpers are fully gone. Tier C respected; exits 0/1/2/8 reachable. Defects #2,
#7, #9 confirmed still open as documented. doc-health and pre-commit pass.

## The standing state

`docs/registers.md` now names check (b) as the currency evidence for two rows
while **no gate runs it** — the docstring's `Gate: NONE yet` is still accurate.
Until it is wired, the currency column asserts a measurement nobody performs.
