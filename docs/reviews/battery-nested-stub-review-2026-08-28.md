# Review: the nested-integrations stub — 2026-08-28

Reviewer: a dispatched agent given the diff, the house conventions and a
complete disposable copy of the tree. **Not** given the brief, the author's
account, or any measurement. Prompt:
`template/prompts/review-battery-nested-stub-2026-08-28.md`.

Artifact: an uncommitted change to `scripts/release-battery.sh` and
`scripts/test-release-battery.sh`, 41 insertions and 1 deletion, which made
the battery's integration stage report a stub line instead of running
`template/scripts/test-integrations.py` whenever `TRUTH_BATTERY_NO_META` was
set.

**Outcome: the change was WITHDRAWN.** Not patched. Five defects, of which the
first is a live push-boundary bypass and the second is the file's own header
forbidding the shape in advance.

## The sentence that settles it

`scripts/release-battery.sh:20-28`, standing in the file before the change and
after it:

> *A check that examined nothing is a **FAILURE**, never a pass — the same F1
> audit law that says a sensor which cannot run must scream. … **NO SKIP FLAG,
> deliberately.** `git push --no-verify` is the honest emergency exit and it is
> loud in the reflog. **A second, softer bypass would be this hook teaching its
> own workaround** (the ADR-011 lesson).*

The change was a second, softer bypass. The header forbids it nine paragraphs
above the line where it was written.

## Confirmed defects

**D1 — a silent bypass of the whole integration suite at the push boundary.**
The branch keys on an environment variable **nothing in the push path
clears**: `.githooks/pre-push` ends `TRUTH_BATTERY_SCOPE="$SCOPE" exec bash
scripts/release-battery.sh` and `grep -c "unset\|NO_META" .githooks/pre-push`
returns 0. Reproduced end to end with exit codes captured directly — a failing
integration test plus `TRUTH_BATTERY_NO_META=1` gives `HOOK_EXIT=0` and
`release-battery: all arms green`; without the variable, `HOOK_EXIT=1` and
`BLOCKED`.

What is lifted is larger than one arm. `scripts/release-battery.sh` is the
**only push-boundary root** that runs the integration suite (`Makefile` aside,
which is a manual entry point). Per `AGENTS.md` and `docs/registers.md:52,:61`
that suite is the declared gate for the consumer hooks, the Tier C
instruments, `register-index` and `waiver-index`. None has a second root, so
under the stub all of them are unwatched at push.

**The `unset` that would have closed this existed** — in the withdrawn
plan-mode diff (D7 of `docs/reviews/plan-mode-review-2026-08-26.md`) — and was
removed by the same hand that later wrote the stub, while reverting that
change. Neither step noticed the dependency.

**D2 — the stub's "LOUD" defence is the weakest part.** The line does print,
but in the failing case it prints a false sentence — *"nested run; the outer
battery verifies this stage"* when there is no outer battery — and the run
still ends `all arms green` at exit 0. Contrast the canary's `skip` at
`:246-248`, keyed on `TRUTH_BATTERY_SCOPE`, which the hook derives from the
pushed range and widens to `ALL` when unresolvable: that skip carries a
liveness argument. The stub carries none.

**D3 — `docs/waivers.md:129` now understates the carrier**, whose *gate it
lifts* cell reads "the battery meta-gate". The same carrier would also lift
the integration stage and everything it gates. `waiver-index` stays green:
`docs/registers.md:61` states why — the four content columns are held by
reading, and item 0b is DECLARED, not DONE. The widening is unobservable to
every mechanism in the tree.

**D4 — the new ARM 11 comment contradicts itself ten lines apart.** Paragraph
one states correctly that `mutate()` compares the whole file and returns 0 if
either substitution matched. Paragraph two then claims it "fails the arm
loudly if EITHER pattern stops matching". It does not; the arm's own drift
branch is unreachable unless BOTH drift. Both directions were reproduced, each
restored byte-identically. **And the diff REMOVES a property that existed
before it**: with one substitution, ARM 11 used to diagnose a drift correctly.

**D5 — three standing sentences falsified and left in place**, chiefly
`scripts/test-release-battery.sh:25-26` — *"the battery runs that suite
unconditionally"* — which is one of the two stated reasons that file is bash
rather than a class inside `test-integrations.py`, and which the diff edits
400 lines below without touching.

**Minor:** dead assignments at `:272`, never read.

## Measurements, which did not reproduce

The rationale claimed the suite's arms sum to 503s with the integration stage
~450s of it, over ~19 nested runs. The reviewer measured the full 17-arm gate
at **578.9s at HEAD and 218.8s with the diff — a 360s reduction, ~62%, not
~89%** — and counted **24 battery invocations per full suite**, of which 21 are
stubbed and **3 still pay full price, unmentioned in the rationale**. The
standalone suite is 23.9s over 64 tests. Direction and mechanism reproduce;
the absolute numbers do not.

## What the reviewer verified is sound

The full 17-arm gate is green under the diff (18 caught, 0 missed) and at HEAD.
ARM 11 in isolation CAUGHT, and the new two-substitution sed matches under this
machine's BSD sed. No recursion; ARM 14's re-entrancy assertion holds. No arm
can assert `ok integrations` against a run that did not have it. Three
hypotheses were formed and killed, including that the dead assignments could
manufacture a green verdict — fed to the section-7 checker they produce
`FAIL integrations -- 0 failing test(s)`, i.e. fail-safe. Every mutation was
restored byte-identically and confirmed by sha256.

## What it could not check

Whether `TRUTH_BATTERY_NO_META` is ever exported in a real pushing shell —
that needed the operator's shell or the brief. Arms 2 and 3 in isolation
(`CANARY_STUB: unbound variable`, pre-existing). A real `git push`.
Concurrency: the suite plants mutants into `scripts/`, so every run was
sequential.

## Why withdrawn rather than patched

Restoring the `unset` closes D1's exploit path and nothing else. A nested run
would still end green having examined nothing, which is what the header
forbids; and D4's regression — a diagnosis that was correct before the change
and is not after — argues against keeping the shape at all.

The saving is real. **The mechanism was wrong, and the constraint that would
have caught it was written in the file before the work began.** The successor
carries it as its first condition, not as a note at the end.

## Residue, filed rather than lost

`scripts/release-battery.sh:400-403` says `TRUTH_BATTERY_NO_META` "is set by
THIS LINE and nowhere else". **That was already false at HEAD** —
`scripts/test-release-battery.sh:176` is an unconditional top-level export.
Untouched by the withdrawal and untouched by the change; it is a pre-existing
defect this review surfaced in passing.
