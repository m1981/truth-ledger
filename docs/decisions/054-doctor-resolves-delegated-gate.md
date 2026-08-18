# ADR-054: doctor resolves one hop of delegation when deciding the ADR-025 hook arm

Status: Accepted (2026-08-18, operator) — the operator approved this resolution
after the two alternatives below were laid out and costed. Implementation lands
with this record.
Date: 2026-08-18
Amends: **ADR-025** (the hook arm of the hook-or-CI commit-gate decision). The
MUST itself is unchanged; what changes is how the hook arm is decided.
Cites: ADR-048 (a check no root invokes is prose — its transitive-closure sweep
is the instrument that contradicts doctor here), ADR-052 (the reproduction
sweep this hook actually runs), ADR-014 (a gate that refuses legitimate work
teaches its own bypass — the test this must pass).
Supersedes: —

## Context

ADR-025 made the README's one **MUST** decidable: `doctor` fails unless an
executable hook names the gate, or a top-level CI config does. It was itself a
correction of a false FAIL — before it, a repository correctly gated by CI got
`doctor: FAIL`, and ADR-025 §2 states the principle that motivated the fix:

> A health check that false-fails a valid configuration teaches its operator to
> ignore it — the worst outcome for the one mechanism meant to decide the MUST.

The hook arm is implemented by `find_gate_hook` (`template/truthlib/shellio.py`),
which tests `needle in open(hook).read()` — a substring test over the hook
file's bytes, one file deep.

That test is exact for the hook `install-hooks.sh` writes, which names the verb
directly (`exec python3 scripts/truth reproduce`). It is wrong for a hook that
**delegates**. This repository's `.githooks/pre-push` is untemplated — consumers
do not release the template, so it carries release-coherence logic of its own —
and it ends by handing off:

    TRUTH_BATTERY_SCOPE="$SCOPE" exec bash scripts/release-battery.sh

The battery runs `truth reproduce` and blocks on its exit 7. So the gate is
armed, and `doctor` reports `FAIL: no executable hook invoking reproduce`.

Three things establish that the FAIL is false rather than merely arguable:

1. **Empirically.** On 2026-08-17 the battery ran `reproduce`, found a
   capsule-stale claim, and refused the push. The regulation this check exists
   to detect executed and did its job while the check denied it existed.
2. **A second instrument disagrees.** `scripts/gate-reachability.sh` computes
   the transitive closure from the same roots and reports
   `ok  ... reached by .githooks/pre-push -> scripts/release-battery.sh`.
   Two independent measurements, opposite answers, on one wiring.
3. **The disagreement is structural, not a bug.** The gate is not a file. It is
   the composite `pre-push + release-battery.sh + truth reproduce`.
   `find_gate_hook` inspects one part and reports a property of the whole;
   the reachability sweep models the composite. They differ in what they take
   the object to be.

## Decision

The needle must appear in an **invocation position**: on a non-comment line of
the hook, or of a file the hook hands off to, one hop away. Two changes fall out
of that single rule, and they fix opposite errors.

**Comment lines no longer count.** The check tested the whole file, so a hook
that merely *names* the verb in prose passed. That is the false PASS the
`invalidate-scan` incident was made of, and it was still live: implementing this
record found `.githooks/pre-merge-commit` passing on the word `check-truth`
inside a comment describing its delegation. The hook is genuinely wired — it
just was not wired the way the check believed.

**Delegates are resolved, one hop.** Two bases, because hooks delegate two ways:
repo-relative (`exec bash scripts/release-battery.sh`) resolves against the work
tree, and sibling-hook (`exec "$(dirname "$0")/pre-commit"`, how ADR-045's
pre-merge-commit shares the pre-commit body) resolves against the hook's own
directory. Command-substitution and variable segments are dropped before
resolving; a token counts only if it names a real file under one of the bases.
doctor renders the resolved chain, so the detail line reports where the verb
runs: `.githooks/pre-push -> scripts/release-battery.sh`.

One hop, not the full closure. The bound is deliberate: it covers the shape that
occurs (a hook handing off to a runner), keeps the check cheap and decidable at
CLI startup, and leaves the transitive question to the sweep that already owns
it (ADR-048). A deeper chain that doctor cannot see is exactly what the
reachability sweep reports.

This applies to both arms, because `find_gate_hook` is shared with
`commit_gate_wired`: a delegating `pre-commit` gains the same treatment.

## Consequences

`doctor` stops false-failing a delegating hook, and stops false-passing a hook
that only mentions the verb. The meta-repository's own `doctor` returns zero
failures without any edit to `.githooks/pre-push`, and its three hook rows now
report OK for the reason each is actually wired.

The two errors are one error. A check that cannot tell an invocation from a
mention will, on the same wiring, report a live gate as absent and a dead gate
as present; which way it errs is an accident of where the word happens to sit.

**Residual, stated rather than left for a reviewer to find:** the leaf test is
still a substring test. A hook that delegates to a script which merely *mentions*
the needle in a comment will pass. This record narrows the *mereology* — what
object the check examines — not the *semantics*: use and mention remain
indistinguishable at the leaf. That is the same residual the reachability sweep
carries and states plainly in its own header (*"EDGES are textual and
grep-shaped, and that is stated plainly"*). Closing it would require parsing
shell, which is out of proportion to a startup-time health check.

Tests that must hold, and must fail if this record is reverted:

* a `pre-push` delegating to a script that runs the verb **passes**;
* a `pre-push` whose only occurrence of the needle is a **comment** does not
  pass — neither in the hook nor in the delegate;
* removing the delegating `exec` line returns the check to **FAIL**.

## Alternatives considered and rejected

**Add a marker comment to the hook** (`# reproduce via release-battery.sh`).
One line, and `doctor` goes green immediately. Rejected: it satisfies the check
at the byte layer while severing it from the property it measures. Today the
presence of the token correlates with the gate being armed — falsely negative,
but not zero. After the edit the token is present unconditionally and the
correlation is zero, so deleting the `exec` line would leave the check green.

This is not a hypothetical failure mode in this repository; it is a repeat. The
comment above the check in `template/truthlib/cli.py` records that an earlier
one-hop grep matched `invalidate-scan` inside a comment *explaining that gate's
removal*, and so kept reporting a retired check as enforced — "a check that
passes on its own retirement notice is the dark gate this repo exists to
refuse." That fix re-aimed the needle and kept the mechanism. Marking the hook
would re-create the incident knowingly, with a different word.

**Record the FAIL as a known deviation.** Defensible on type grounds: the
consumer hook and the meta-repo hook are different kinds, and doctor's contract
speaks about the product's wiring. Rejected because doctor is *run* here and
read by operators here, so this repository is in its domain in practice. A check
whose domain excludes the repository it runs in should report *not applicable*,
not FAIL — which is itself a code change, so the option buys nothing and leaves
a red line operators learn to skip past.
