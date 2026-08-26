# Review: plan mode in `scripts/release-battery.sh` — 2026-08-26

Reviewer: a dispatched agent given the diff, the house conventions and a
complete disposable copy of the tree at `e84de9e`. **Not** given the brief,
the author's account of what was verified, or any measurement taken. Prompt:
`template/prompts/review-plan-mode-2026-08-26.md`.

Outcome: **seven confirmed defects. The change is not patchable and was
withdrawn.** D1 and D3 were independently reproduced by the dispatcher before
this record was written; the rest are recorded as the reviewer reported them,
each with its reproducing command.

The full 17-arm meta-gate finished green under the diff (18 caught, 0 missed,
rc=0), so nothing existing was broken. The defects are all in the new
mechanism.

## The one sentence underneath D1–D4

> `CANARY_SCOPE_RE` and `META_SCOPE_RE` genuinely do have one definition each
> — the comment at 88–91 is true **of the regexes**. It is asserted **of the
> plan**, and the plan is the conjunction of the regex, the guard's spelling,
> the `NO_META` branch, and a counter with no floor. Three of those four are
> unguarded.

One sentence true at the wrong level: the failure shape named in
`docs/governance/architects-crib.md`, produced by that document's author the
day after writing it.

## Confirmed defects

**D1 — the completeness check is a roster.**
`scripts/release-battery.sh:119`, `GUARDS=$(grep -cE '^(if|elif) touches "\$' "$0")`
recognises exactly one spelling. Three of four mutants evade it green: a
guard written with a **literal regex** — the style *both guards used at HEAD
one commit earlier* — the named variable **indented** inside any block, and
`if ! touches "$X"` at column 0. Only `if touches "$X"` at column 0 is caught.

Reproduced by the dispatcher: injecting `if touches '^docs/'; then …; fi`
leaves the plan printing *"every other stage is unconditional and always
runs"*, which is then false, at exit 0. `git show HEAD:scripts/release-battery.sh
| grep -cE "^(if|elif) touches '"` returns 2 — the evading form is the style
the next author copies from the surrounding file, and nothing says the
spelling is load-bearing.

This class is already named here. `instruments/capsule-blindness.py:19` — *"A
CAPSULE THAT ENUMERATES BY PATTERN COUNTS WHAT IT RECOGNISES, NOT WHAT
EXISTS"* — was commissioned by operator RULING 8 after a `grep -oE` counter
**over this same file** reported 10 arms while the battery carried 12, green
for four days. The remedy that file names: an enumerating recipe must also
assert its own complement is empty.

The reviewer sought the refuting observation — another gate enforcing the
`"$..._SCOPE_RE"` spelling — searched the tree and read all 17 arms, and
found none. `capsule-blindness.py:75` reads `.truth/claims.jsonl` only, so it
cannot see a counter living inside a shell script.

**D2 — no non-zero floor.** `[ "$PLAN_COVERED" != "$GUARDS" ]` passes when
both are 0. With both guards reverted to the literal style and both
`plan_decision` calls removed, the plan reports no decisions and exits 0 while
two scope-guarded stages still exist. The comment cites ADR-042 rule 2 as the
thing the check implements; the floor is the half of rule 2 it does not.

**D3 — the plan disagrees with the run, in the environment it was built for.**
The meta-gate's real decision is `NO_META ? skip : touches(META_SCOPE_RE)`;
the plan models only the second half. Reproduced by the dispatcher:

```
TRUTH_BATTERY_PLAN=1 TRUTH_BATTERY_NO_META=1 TRUTH_BATTERY_SCOPE=scripts/release-battery.sh
  →   plan  RUN   battery meta-gate
same env, real run
  →   skip  battery meta-gate -- re-entrant run under the outer battery
```

`scripts/test-release-battery.sh:176` is an unconditional top-level
`export TRUTH_BATTERY_NO_META=1`, and `run()` does not clear it — so **every
arm the mode was built for inherits it**, and ARM 14, whose declared subject
is the meta-gate's scope decision, is the arm it would most obviously
mislead. The header's claim that a disagreeing plan "is not expressible" is
false with no code edit at all.

**D4 — the one failure it detects is reported backwards.** The message names
one direction of an equality enforced in both. An author who adds the
`plan_decision` but writes the guard in the literal style gets
`FAIL … plan reports 3 … this script makes 2 — a stage gained a scope guard
the plan does not name`, one line below the plan printing that stage.
Combined with D1 the mechanism inverts: **omit the plan entry and it is
green; supply it and the gate fires with text that says the opposite of what
happened.**

**D5 — no consumers, so the saving is not realised and the gate has never
been seen red in service.** `TRUTH_BATTERY_PLAN` has five occurrences: two in
the hook, one in `docs/waivers.md`, two in the battery. Zero in
`scripts/test-release-battery.sh`, which the diff does not touch. The
rationale is written as an accomplished fix, and the waiver row states in the
present tense a purpose no arm exhibits.

**D6 — `$0` fragility.** The counter greps `"$0"`, so invoking the battery by
a path that does not resolve from the caller's cwd makes `GUARDS` empty. It
fails closed, which is the right direction, but the message renders malformed
and sends the operator hunting a stage guard that does not exist. Every wired
caller invokes from the repo root, so this is reachable by hand, not by the
wiring.

**D7 — the hook is guarded; the documented operator entry point is not.**
`.githooks/pre-push:76` unsets the variable and that works. `Makefile:58`,
*"Run official push-boundary release battery"*, does not.

## What the reviewer verified is fine

* The `unset` in the hook does what its comment says **and is load-bearing**:
  with a probe substituted for the exec target, the variable arrives unset;
  with that one line deleted it arrives as `1`. `SCOPE=ALL` still passes
  through intact.
* The extracted regexes are **byte-identical** to the HEAD literals; tested
  over 8 scope strings (three canary-matching, two meta-matching, three
  neither) — identical decisions in all 16 comparisons.
* The `docs/waivers.md` row is required and its gate goes red: removing only
  that row gives `waiver-index` rc=1 naming the carrier; restored, `sha256`
  of the file is identical before and after; with the row present the
  instrument is green at 37 waivers, 0 unclassified, and `TRUTH_BATTERY_PLAN`
  lands in the NOT COUNTABLE population.
* The row's mechanical claims hold: exits 0 before any content check at three
  scopes, files no record, the hook unsets it, `make battery` is the
  direct-invocation case it warns about.
* Plan decisions are correct for the two stages named, including the
  ALL-widens rule.
* Nothing currently gated regressed: full meta-gate rc=0, 18 caught, 0 missed,
  including ARM 6, which asserts the hook keeps its tag-check ahead of the
  battery and between which the new `unset` was inserted.
  `gate-reachability.sh` 14 examined / 14 reachable, `waiver-index` green.

## Hypotheses the reviewer formed and then killed

* *"`governing record` = the plan-mode header is a level error — the artifact
  governing itself."* Refuted by precedent: `--single-run` cites G6,
  `TRUTH_ALLOW_NO_JSONSCHEMA` cites the F1 arm, `TRUTH_BATTERY_NO_META` cites
  the battery header. Citing a code header is established in this register.
* *"The regex refactor changes what the guards select."* Refuted —
  byte-identical, 8 scopes agree pairwise.
* *"The `unset` is decorative."* Refuted by probe; it is load-bearing.
* *"The two new `# ---` headers disturb the capsule counting battery
  sections."* Refuted — the new headers are unnumbered and the diff of
  section lists is empty.
* *"The early `exit 0` makes a check read as dark to the reachability
  sweep."* Refuted — 14 examined, 14 reachable, rc=0.

## What the reviewer could not check, and what it would have needed

* **Whether the 45–60 s in the rationale was ever true.** It measured ~26 s
  per arm and 27 s for one full battery under a `scripts/` scope. Direction
  and mechanism reproduce; the number does not, on that hardware. It reports
  the discrepancy and claims nothing from it — it would have needed the
  author's measurement, which it was correctly not given.
* **The suite's arm-selection wiring.** `bash scripts/test-release-battery.sh 2`
  alone dies with `line 262: CANARY_STUB: unbound variable` — `CANARY_STUB`
  is defined inside `if want 1`. **Pre-existing, untouched by this diff.** It
  worked around this by running `1 2 3` together, so arms 2 and 3 were never
  exercised in isolation.
* **Behaviour under a real `git push`.** The hook was driven through a stubbed
  exec target with synthetic stdin; the tag-check printed its WARN branch (no
  `v0.10.0` tag in the copy). The FAIL branch and a real remote were not
  exercised.
* **The regex refactor beyond 8 scope strings** — agreement is established
  over 8 paths, not over the population of pushable paths.

## Consequence

The change was withdrawn rather than patched: D1, D2, D3 and D4 are four
symptoms of one cause, and repairing them individually leaves the plan a
second copy of a decision it does not fully model. Successor work is tracked
in `docs/reviews/work-in-flight-2026-08-26.md`.

One finding here outlives the change. **A pattern-based counter in this file
is a recurring class** — RULING 8 produced `capsule-blindness.py` for exactly
it, and that instrument reads the ledger only, so a counter living in a shell
script is outside its domain. Any successor must carry that warning.
