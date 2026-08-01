# ADR-041: Shell-free evidence execution — one interpreter, not two

Status: **PROPOSED** (2026-08-01, drafted) — NOT accepted, NOT implemented.
Written as the named closure for ADR-040's R4 residuals. Requires an
independent adversarial pass and a simulation against all filed evidence
commands before it can be accepted; the last patch in this area passed 235
canary arms and was then broken three ways by a red team, so a green suite
is explicitly not sufficient evidence for this one.
Date: 2026-08-01
Supersedes: — (replaces the executor half of ADR-009; the ADR-021
allowlist boundary is unchanged and still load-bearing)

## Context

Evidence commands are screened statically at filing, stored, and later
re-executed inside a *verifier's* session — deferred code execution across
the trust seam G11 protects. The screen tokenizes with `shlex`; the
executor runs `subprocess.run(cmd, shell=True)`. **Two interpreters read
the same string.**

ADR-021 (H4) found the first divergence: a newline is word-whitespace to
shlex and a statement separator to `/bin/sh`, so a post-newline program
landed in argument position for the screen and in command position for the
shell. The fix refused control characters, making the screen's
tokenization a safe superset *for that class*.

The 2026-08-01 review found the class was not closed, only narrowed. Three
further divergences, each demonstrated writing or creating a file:

- **Glob expansion.** `uniq *` is ONE word to shlex and N words to
  `/bin/sh`. Any rule the screen enforces per-word — a positional cap, an
  argument deny table, a path check — is enforced against a word count the
  executor will not use. Confirmed overwriting a file that expansion moved
  into `uniq`'s output positional.
- **Read-write open.** `cat <>FILE` creates the target. The screen
  classifies every `<` as read-only input and accepts any source.
- **Digit redirect targets.** `>1` writes a file named `1`; the screen's
  `isdigit()` carve-out was meant for fd dups (`2>&1`).

The pattern is now legible, and it is the same one ADR-021 stated for
blocklists, one level down: **every divergence between the screen's model
and the shell's behaviour is a channel, and enumerating divergences does
not terminate.** Control chars, then globs, then `<>`, then whatever is
next. The screen cannot win a modelling race against `/bin/sh`, because
only `/bin/sh` implements `/bin/sh`.

## Decision (proposed)

**Stop giving the string to a shell.** The screen already parses the
command into segments and words — that parse becomes the execution.

1. **Execute argv arrays, not strings.** `run_evidence` takes the screen's
   own token stream and runs each segment with `subprocess.run(argv,
   shell=False)`, plumbing pipelines by connecting stdout to stdin across
   segments. There is then exactly ONE interpretation of the command, and
   "the screen's model diverges from the executor's" becomes unstatable
   rather than untrue.
2. **Redirection is handled by the runner, not by a shell.** `>/dev/null`
   and `2>&1` are the only sinks ADR-009 ever allowed; both are file
   descriptors the runner can set directly. `<FILE` opens read-only, by
   flag, so `<>` cannot exist. R4b and R4c close by construction.
3. **Globs are expanded by the runner, with stdlib `glob`,** on the words
   the screen already counted — after the per-program rules run, on the
   expanded list. A language small enough to model (a documented,
   stdlib-implemented pattern syntax) replaces one that is not. R4a closes.
4. **Refuse what the runner cannot express.** Anything in the token stream
   that has no argv equivalent is refused rather than approximated. The
   refusal list gets *shorter* than today's, because constructs that
   currently pass by being invisible now have to be named to survive.

Landed together with ADR-040's R1-R3 (long-option prefixes, glued and
clustered short options, output positionals), since a single adversarial
pass should cover the whole screen once rather than twice.

## Consequences (anticipated — none of this is measured yet)

- The ADR-021 class is closed structurally. That claim is worth more than
  the three specific fixes, and is the reason to prefer this over patching.
- `PROGRAM_ARG_DENY` and the positional cap become *sound* rather than
  advisory: the words they inspect are the words that execute.
- Cost: the runner owns pipeline plumbing and glob expansion — real code
  where there was none. This is the honest trade. Two interpreters is
  ~zero code and unbounded risk; one interpreter is bounded risk and
  perhaps 80 lines.
- Behavioural risk to real filings is the thing to measure first: 116
  distinct commands exist across both ledgers, and every one must produce
  a byte-identical output hash under the new runner, or the change silently
  diverges live claims. This is a hash-stability test, not a screen test.
- Pure stdlib is preserved (`subprocess`, `glob`); no new dependency.
- Does NOT close the program-level channels (`rg --pre`, `sort --com=`).
  Those are properties of the programs, not of the shell, and remain the
  allowlist's job — ADR-021's boundary is untouched and still the boundary.

## Non-goals

Not sandboxing. An OS-level read-only sandbox (`sandbox-exec`, `bwrap`,
seccomp) is the only construct that would make "evidence commands are
read-only" true regardless of program surface, and it is the honest
long-term answer — but it is platform-specific, and this ADR is
deliberately the portable, stdlib-only step. If a sandbox is ever adopted
it should follow the `docs/growth-gate/` pattern: designed, tested, shelved,
with a written trigger.

Not re-litigating the allowlist boundary (ADR-021 stands). Not touching
acceptance oracles (ADR-014), which execute repository code on purpose and
legitimately want a shell.

## Open questions for the reviewer

1. Does any filed evidence command rely on shell behaviour the runner
   would not reproduce — brace expansion, tilde, `$VAR`, command
   substitution (already refused), exit-status semantics of a pipeline
   (`set -o pipefail` is not POSIX default; what does the current
   `returncode` mean for `a | b` today, and must that be preserved)?
2. Glob semantics: `/bin/sh` leaves an unmatched pattern as a literal
   word; Python's `glob` returns an empty list. That difference changes
   both argv and exit codes. Which is correct for evidence, and does the
   choice alter any existing output hash?
3. Is `2>&1` merging into the hashed stdout today, and does the runner
   preserve the interleaving byte-for-byte?
4. Should the screen's refusal of control characters (ADR-021) be kept
   after it becomes redundant? Recommendation: keep — defence in depth
   costs nothing, and the reason it is redundant is subtle.
