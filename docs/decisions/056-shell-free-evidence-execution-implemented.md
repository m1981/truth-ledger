# ADR-056: shell-free evidence execution, implemented — what ADR-041 proposed, and what it cost

Status: **PROPOSED** (2026-08-18, agent-authored) — the CODE has landed; this
record has not been independently reviewed. ADR-041 named two conditions for
its own acceptance: a simulation against all filed evidence commands, and an
independent adversarial pass. **The simulation is done and passed (196/196
hash-identical, below). The adversarial pass has not happened.** That matters
more here than usual: ADR-041 was drafted with the observation that the last
patch in this area passed 235 canary arms and was then broken three ways by a
red team, so a green suite is explicitly not sufficient evidence for this one.
Accepting this record is the operator's call after that pass, not an agent's.

Date: 2026-08-18

Amends: **ADR-041** (shell-free evidence execution — one interpreter, not two),
which is frozen at `docs/archive/adr/041-shell-free-evidence-execution.md` and
still says PROPOSED / NOT implemented. Its four decisions are implemented as
written except decision 3, which is implemented in a weaker form than its own
text claimed — see *Where the implementation departs from the proposal*.

Cites: ADR-009 (the evidence-command screen), ADR-021 (screen/executor
tokenizer parity — the H4 newline), ADR-022 (the deny baseline), ADR-029 (the
screen is an execution gate), ADR-014 (acceptance oracles, deliberately
untouched), ADR-040 (the audited allowlist default, whose R4a-R4c residuals
ADR-041 exists to close), ADR-044 (the truthlib DAG this had to respect).

## What shipped

`evidence.parse_evidence_command` is now the only reader of an evidence
command, and `shellio.run_evidence` executes what it emits. There is no command
STRING below the parse — the plan is data:

```
plan    := [{"op": None|"&&"|"||"|";", "pipeline": [segment, ...]}, ...]
segment := {"words": [(text, pattern_or_None), ...], "stdin": None|path,
            "stdout": "pipe"|"devnull", "stderr": "devnull"|"merge"}
```

`screen_evidence_command` is a pass over that same plan, so the words it
allowlist-checks are the words that reach `execve`. The runner does the
pipelines, the and-or list, `>/dev/null`, `2>&1` and `<FILE` itself, with
`shell=False`.

The ADR-044 DAG is unchanged and was the binding constraint on the shape:
`evidence` is pure and therefore never expands a glob or opens a redirection;
`shellio` remains the only `subprocess` importer and cannot import a pure
module; so `cli` is what carries a plan from the one to the other. That is why
`run_evidence` takes a plan rather than a string — not style, but the only
factoring the DAG admits.

**shlex had to go, and this is the reason worth remembering.** Its token stream
cannot distinguish `2>&1` from `2 >&1` — both lex to `['2', '>&', '1']` — while
`/bin/sh` reads the first as an fd redirection and the second as an argument
plus a dup. A screen that cannot see that difference cannot gate an executor
that acts on it. The replacement lexer keeps the glue and implements exactly
the POSIX word subset the runner can honour: single quotes, double quotes,
backslash, and nothing that expands.

## Evidence

* **196 of 196** distinct evidence commands in this repository's ledger
  produce a byte-identical `(output_hash, returncode)` pair under `/bin/sh` and
  under the new runner. Zero diverged, zero refused. ADR-041 asked for this
  over "both ledgers" and counted 116; the second ledger is a consumer's and is
  not reachable from here, so this measures one of the two and says so.
  `template/scripts/adr041-hash-stability.py` ships so a consumer can run the
  same check against their own ledger before adopting the version.
* `truth reproduce` over the live population: 68 reproduces, 1 capsule-stale,
  and that one is `grep -c '^say "FAULT' template/scripts/truth-canary.sh` —
  stale because this change ADDS canary arms, which is the ledger working.
* Core suite 531 tests OK (was 512): `TestEvidenceParse` (13 arms) pins the
  parse, `TestShellFreeEvidenceRunner` runs 27 command shapes through BOTH
  executors and asserts the pair is identical, `TestEvidenceExecutionIsShellFree`
  pins by ast that the only `shell=True` sites left in `shellio` are the two
  named decisions (`run_accept_command`, `tracker_issues`).
* Canary 289 caught / 0 missed (was 284): FAULT SF1-SF5. SF1 (`cat <>PWNED`)
  and SF4 (`echo $HOME`) were verified to be **accepted** by the pre-change
  screen, so those two arms are new coverage rather than pins; SF2/SF3 pin
  refusals that already held; SF5 is the negative control — a glob-and-pipe
  recipe files and rechecks to its own recorded hash end to end.

## Where the implementation departs from the proposal

**Decision 3 (globs) does not close R4a, and ADR-041's text said it did.** The
proposal reads "after the per-program rules run, on the expanded list", which
would require screening the expansion. Expansion happens at run time, on
purpose: freezing one expansion and reusing it for the G6 double-run would hide
exactly the nondeterminism G6 exists to catch. So what R4a actually gets is
*modelling*, not closure — one documented stdlib expander instead of the
shell's locale-dependent one, quoted metacharacters that can no longer be
smuggled into an expansion, and a screen that can see which words are patterns.
A glob whose expansion lands a written positional (`uniq *`, and `uniq` is on
the shipped allowlist) still reaches the program. That is ADR-040's positional
cap (R1-R3), which ADR-041 planned to land in the same pass and which did NOT
land here. `/bin/sh` had the identical exposure, so this is not a regression —
it is the residual this change does not pay for, and naming it is the point.

**A glob in program position is refused**, which the proposal did not mention.
No allowlist entry can carry a metacharacter, so a pattern there could only
ever be an attempt to reach an allowlisted name sideways.

**The `$` refusal is narrower than "no expansions".** POSIX expands `$` only
when what follows can name an expansion, so `grep -c "a$"` is an anchored regex
to the shell and stays one here. A blanket refusal would have failed a common
recipe shape for a divergence that does not exist.

## ADR-041's open questions, answered

1. **Does any filed command rely on shell behaviour the runner does not
   reproduce?** No — 196/196. Brace expansion is not POSIX `sh`; `$` and `~`
   are refused rather than approximated; `` ` `` and `$(` were already refused.
   Pipeline exit status is the LAST stage's: `pipefail` is not the POSIX
   default and was never in force, so recorded returncodes keep their meaning.
2. **Glob semantics.** The shell's rule won: an unmatched pattern passes
   through as a literal word (Python's `glob` returns `[]`), so a recipe whose
   glob went empty keeps failing the way it did instead of silently losing an
   argument. Matches are sorted, because an unsorted argv would make
   `wc -l lib/*.py` nondeterministic and G6 would refuse the filing. No
   existing hash moved either way.
3. **Is `2>&1` merging into the hashed stdout, byte-for-byte?** Yes —
   `stderr=subprocess.STDOUT` is the same descriptor dup, applied in the order
   the redirections were written (`>/dev/null 2>&1` discards both; the reverse
   order is refused rather than silently treated as the first). **One
   divergence exists and is pinned by a test**: `nosuch 2>&1` used to hash
   `/bin/sh`'s own "not found" line, and there is no shell to write it now, so
   the merged stream carries only what the command itself wrote — nothing.
   Synthesizing a fake shell message to preserve the old bytes would be
   inventing evidence. No filed command has this shape.
4. **Keep the ADR-021 control-character refusal?** Kept, and it is not merely
   defence in depth: the ADR-014 acceptance oracle still runs through `/bin/sh`
   on purpose, and there a newline is still a statement separator that would
   drop an unallowlisted program into a screened command. The screen is shared
   between the two, so the refusal stays load-bearing on one side of it.

## What is refused that used to pass

All of it named rather than silent, and none of it present in any filed
command: `$`/`${...}` expansion, `~`, `<>` (the R4b write channel), `&`
backgrounding, `>&-`, `;;`, here-documents, a glob in program position, and
`2>&1 >/dev/null` (the runner captures one stream). A consumer whose evidence
recipes use any of these will see a refusal at the next intake or recheck, with
the construct named; `scripts/adr041-hash-stability.py` finds them in advance.

## Non-goals, unchanged from ADR-041

Not sandboxing — an OS-level read-only sandbox is still the only construct that
would make "evidence commands are read-only" true regardless of program
surface, and it is still platform-specific. Not re-litigating the allowlist
boundary (ADR-021 stands, and the program-level channels `rg --pre`,
`sort --com=` remain the allowlist's problem, not the shell's). Not touching
acceptance oracles: ADR-014 oracles execute repository code on purpose, still
run through `/bin/sh`, and share only the program screen (`shell_free=False`).
