# ADR-058: epistemic isolation — the battery may not judge with an apparatus the run authored

Status: **PROPOSED** (2026-08-23, agent-authored). The mechanism is
implemented and tested; it is deliberately **NOT WIRED** to anything.

The open question this record was filed with — as specified, the gate makes
a legitimate change to `template/truthlib/` unpushable — was ruled on by the
operator on 2026-08-23: *the local battery must test the working tree;
isolation moves to the CI/CD boundary only.* The call from
`scripts/release-battery.sh` was reverted in the same sitting, and that file
is byte-identical to its pre-session state.

The ruling is recorded here rather than folded silently into the Decision
section, because it is the reason this script currently runs nowhere. See
*Residual*.

Date: 2026-08-23

Cites: ADR-003 rule 2 (meta-repo policy is untemplated), ADR-009 (the
evidence-command screen, whose allowlist is one of the isolated files),
ADR-025 (the commit gate), ADR-048 (the battery's orphaned-gate arms),
the release battery's own header law (*every arm reports what it examined;
an arm that examined nothing is a failure*) and its refusal of a skip flag.

## Context

The layer has three tiers. L0 is the code and the world. L1 is the ledger
and its instrument — `truthlib`, the gates, the fold. L2 is the oracle that
checks whether L1 told the truth: CI, the release battery, a human. The
worst available failure is a leak between L1 and L2, because a system that
can authorize its own lies produces confident false statements at scale,
which is worse than producing none.

`scripts/release-battery.sh` is L2. It runs at the push boundary and decides
whether a change may ship. It has always run the `truthlib` sitting in the
working tree — which means, whenever an agent edits `truthlib`, L1 grading
its own paper.

This does not require malice and would not look like an attack in review.
Widening `.truth/evidence-allow` by one entry, softening a refusal string a
test greps for, making one gate return `None` on a branch — each turns a red
battery green, and each reads as an ordinary edit in the diff.

## Decision

`scripts/epistemic-isolate.sh` (meta-repo only, untemplated) restores the
measuring apparatus from `origin/main` before any judging step reads code.

**It is not called from `scripts/release-battery.sh`.** The pre-push battery
runs on the working tree, deliberately: a local hook cannot isolate the very
thing a local change is editing without making that change unpushable, and a
gate whose only effect is to block honest work is a gate that gets bypassed.
The isolation belongs at the CI/CD boundary, where the run is not the author.

Isolated, and only these:

| path | why |
|---|---|
| `template/truthlib/` | the instrument: every gate, every refusal, the fold |
| `scripts/truth` | the entry the meta-repo's own tooling calls |
| `.truth/evidence-allow` | the POLICY deciding which commands the screen will execute at all — not code, and the highest-leverage file in the set |

Exit codes are **0 isolated, 2 could not isolate**. There is no 1 and no
skip flag, matching the battery's own refusal of one. Fail-closed is the
whole content of the decision: a script that cannot establish which
instrument it is holding must stop its caller, not hand it whatever is
lying around.

Two additions beyond the minimum, both load-bearing:

1. **Refuse when the isolated paths are dirty.** `git checkout origin/main
   -- <path>` overwrites the working tree *and* the index with no undo, no
   reflog entry and no stash. A gate that silently eats an operator's
   uncommitted work is a gate they will disable, which costs more than the
   leak it closed. Refusing here is strictly *more* fail-closed than the
   minimum: an uncommitted instrument has been judged by nothing.
2. **Report what was installed.** The battery's header law applies to this
   step too. It prints the `origin/main` short ref and whether the apparatus
   differs from HEAD; an isolation that reports nothing is indistinguishable
   from one that did nothing.

**Whatever calls this must restore the working tree afterwards.** The
isolation has to hold for the judging steps and must not outlive them:
leaving `origin/main`'s `truthlib` in place poisons every later run in that
checkout, and the operator ends up debugging code they are not looking at.
A `trap 'git checkout -q HEAD -- …' EXIT` in the caller is the shape; it
lived briefly in `release-battery.sh` and was reverted with the rest of the
wiring. A CI job on a throwaway checkout does not need it, which is one
more reason the CI boundary is the right home.

## Consequences

**Wanted.** An agent that softens a gate cannot soften the run that catches
it. Verified in a sandbox: a committed `TRUSTED=0 # gate softened` edit to
the instrument is replaced by `origin/main`'s version before any arm reads
it (four cases exercised — identical, tampered-committed, tampered-uncommitted,
no remote).

**Accepted.** Any caller of this script requires network access to
`origin`. That is the intended reading of fail-closed, not a regression:
without a trusted reference there is nothing to isolate against. It is also
the sharpest argument against the local-hook placement that was reverted —
it would have made every offline push fail.

**Accepted.** `scripts/truth` in this repo is a symlink to
`template/scripts/truth`, so checking it out restores the link, not the
entry file. The entry is thin (ADR-044) and the implementation it re-exports
*is* isolated, but the asymmetry is real and stated rather than papered over.

## Residual

**The instrument cannot vouch for itself, and moving the gate does not
dissolve that.** The suites are local while `truthlib` would be
`origin/main`'s, so any run using this script judges new tests against an
old implementation. That asymmetry is exactly right for the case this record
was written for — an agent softening a gate cannot soften the run that
catches it — and exactly wrong for the honest case. No single run has both
properties. The operator's ruling resolves *where* the gate may sit; it does
not resolve that, and a CI job wiring this script will meet it again on the
first push that changes `truthlib`.

**This script currently runs nowhere, and that is a real state, not a
formality.** The meta-repo has no `.github/workflows/` of its own — the only
workflows in the tree are `template/.github/workflows/`, which is the product
shipped to consumers, and ADR-003 rule 2 forbids putting meta-repo release
policy there. So the CI surface the ruling points at does not exist yet.
Until it does, `epistemic-isolate.sh` is an unwired gate: tested, correct,
and detecting nothing.

Two things follow that a later reader should not have to rediscover:

* `scripts/gate-reachability.sh` does **not** flag it. Measured after the
  revert: 14 checks examined, 14 reachable, 0 unreachable — the sweep's
  inventory never included this script, so its darkness is invisible to the
  one mechanism built to see dark gates. That is a gap in the sweep, not
  evidence the script is wired.
* Whoever builds the CI job must also pick from the three candidates below,
  because the job will hit the same wall the local hook did:
  * judge instrument changes in a second, *unisolated* pass and require a
    recorded human verdict on the instrument diff before the merge lands;
  * isolate the suites too, accepting that new tests cannot gate their own
    subject — which moves the problem rather than solving it;
  * isolate only `.truth/evidence-allow` and the gate policy files, and
    *report* rather than substitute the instrument, making the L1/L2 leak
    visible instead of impossible.
