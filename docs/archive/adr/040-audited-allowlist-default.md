# ADR-040: An audited evidence-allowlist default, and the grey zone as its propagating half

Status: Accepted (2026-08-01, operator) — prompted by a per-program audit
of every entry on the shipped allowlist (4 independent agents) plus an
adversarial review of a proposed screen patch, which together found three
program-level exec/write channels on shipped entries and three shell-level
channels no allowlist can close. Amends ADR-022 (extends DOCTOR_GREY_ZONE)
and ADR-009 (narrows the shipped default). Does NOT amend ADR-021: the
allowlist is still the boundary, and this ADR is the first time that
boundary was audited rather than assumed. Canary FAULT AL1-AL3; core test
test_grey_zone_covers_adr040_removals. Implemented in CLI v0.9.26
(no schema change).
Date: 2026-08-01
Supersedes: — (subtraction from the ADR-009 default; no mechanism changes)

## Context

ADR-021 concluded that a blocklist cannot bound an interpreter, so the
**allowlist is the security boundary**. ADR-022 added a deny baseline for
programs whose sole job is running other programs, and a doctor advisory
for the grey zone. What neither did was ask the obvious follow-up
question: *are the programs on the shipped allowlist actually read-only?*
Nobody had checked. The list was assembled from intuition about which
tools "just read".

A per-program audit of all 28 entries — flags AND positionals, GNU and
BSD, each channel demonstrated rather than inferred — found three that are
not read-only, all reachable by an unprivileged attacker:

- **`rg --pre PROG`** (and `--hostname-bin PROG`) executes an arbitrary
  program per file searched. Confirmed running a marker script under
  ripgrep 15.1.0. This is `find -exec` with no deny-table entry.
- **`file -C -m PATH`** compiles a magic file to an attacker-chosen path.
  Confirmed writing.
- **`date`** sets the system clock from a flag (GNU `-s`/`--set`) or from
  a bare **positional** (BSD `date MMDDhhmmYYYY`). Privileged, so it fails
  for an unprivileged verifier, but it reaches `clock_settime`. The
  positional form is the important shape: a flag table is structurally
  blind to an operand.

The same round found that `sort`'s deny entry is incomplete in a way that
generalizes: getopt accepts any unambiguous **long-option abbreviation**,
so `sort --out=FILE` writes and `sort --com=PROG` executes (GNU) while the
table lists `--output` and `--compress-program`. The lesson is not "add
two more spellings": the deny table enumerates spellings and getopt
generates them. Exact -> glued -> clustered -> abbreviated is a sequence
with no last element.

Nineteen entries — grep, ls, stat, cat, head, tail, wc, cut, tr, jq, diff,
comm, echo, printf, realpath, test, [, basename, dirname — plus the three
checksum tools and `find` (whose channels the deny table does cover) were
confirmed CLEAN in both GNU and BSD form. That negative coverage is the
real product of the audit and is what justifies the new default.

## Decision

**1. Cut the shipped default to the audited-clean set.** `rg`, `file` and
`date` leave `.truth/evidence-allow`. Empirical cost: zero. This repo's
ledger is the only one (the template ships no ledger of its own) and has
ever carried 116 distinct command strings — 114 evidence commands plus 2
acceptance oracles. The programs they actually use are `grep`, `echo`,
`test`, `ls`, `head` (and the deliberately-unlisted `bash` of the P0
canary claim); `rg`, `file` and `date` appear **zero** times, not even in
argument position.

They are NOT added to the ADR-022 deny baseline. That file is reserved,
by its own charter, for programs whose *sole job* is running other
programs, where refusal has zero false-positive cost. `rg` is a search
tool and `file` a type prober; only particular flags are dangerous. Hard-
denying them would re-import the over-blocking ADR-022 explicitly rejected.

**2. Add them to `DOCTOR_GREY_ZONE` — the propagating half.** Removal
alone protects only *new* consumers: `.truth/evidence-allow` is consumer-
owned and `copier update` never reverts it (ADR-022's "you own what you
ALLOW"). The grey zone is code-owned, so it ships with the CLI and reaches
every existing deployment, warning any consumer whose own list still
carries `rg`, `file` or `date`. This is ADR-022 part 2 used exactly as
designed: surface the accident where it would matter, leave the policy
with the operator, never fail the doctor for it.

**3. Record what is still open, by measurement.** See Residuals. This ADR
closes three program-level channels and claims nothing more.

## Consequences

- Locked mechanically: canary FAULT AL1 (the shipped default carries no
  removed program), AL2a (the shipped default earns NO grey-zone warning
  — negative control), AL2b (a consumer keeping one IS warned), AL3 (the
  warning is advisory — doctor still exits 0); core
  test_grey_zone_covers_adr040_removals. AL2a/AL2b assert on the `WARN`
  line specifically: doctor prints an `OK ... grey-zone` line when the
  list is clean, so a bare grep for "grey-zone" would match either way —
  an arm that can never MISS. The first draft of AL2 had exactly that
  defect and was caught in independent review, which is the same lesson
  the FAULT G restoration above encodes.
- `truth doctor` in this repo: 0 failures, 0 warnings, after the same
  three entries were removed from its own consumer allowlist.
- Canary FAULT G and FAULT R7 re-add `date` to the sandbox allowlist
  before use. They test the **determinism** gate, and an unlisted program
  refuses one gate earlier — the arms would have kept reporting CAUGHT
  while testing nothing. A canary arm that passes for the wrong reason is
  the failure mode this suite exists to prevent, so the restoration is
  explicit and commented at the site.
- The shipped allowlist comment claiming the `sort` deny entry is
  "complete as far as is known" was FALSE and is corrected in place.

## Residuals (measured 2026-08-01, all still OPEN after this ADR)

Program-level, needing a screen patch (drafted, deliberately not landed —
the draft closed R2/R3 but was falsified on R4 by adversarial review):

- **R1** `sort --out=FILE` (write, GNU+BSD) and `sort --com=PROG` (exec,
  GNU) — long-option abbreviation. Fix: match denied long options as
  prefixes, which closes getopt's documented rule rather than one spelling.
- **R2** `sort -oFILE`, `sort -nroFILE` — glued and clustered short
  options. Note the cluster form: the denied letter may sit anywhere in
  the run, so a prefix test is not sufficient.
- **R3** `uniq IN OUT` — an output **positional**, invisible to a flag
  table. Needs a per-program positional cap in which a bare `-` counts as
  a word.

Shell-level, which **no allowlist and no argument screen can close**,
because they are properties of the executor rather than of the program:

- **R4a** `uniq *` — the glob is one word to shlex and N words to
  `/bin/sh`, so any positional cap can be stepped around by expansion.
  Confirmed overwriting a file.
- **R4b** `cat <>FILE` — `<>` opens read-**write** and creates the target;
  the screen classifies every `<` as read-only input. Confirmed creating.
- **R4c** `grep -c x f >1` — a bare digit redirect target is a file named
  `1`, not an fd dup.

R4 is the reason this ADR makes no closure claim. Its closure is ADR-041
(shell-free evidence execution), where the screen's own token stream
becomes the execution, and these channels cease to exist by construction
rather than by enumeration.

## Non-goals

Not claiming the evidence screen is now a write/exec boundary — R1-R4 are
open and measured. Not adding `rg`/`file`/`date` to the deny baseline
(wrong instrument; see Decision 1). Not fixing R1-R3 here: they are code
changes to the screen and belong with ADR-041's rework, where a single
adversarial pass can cover both. Not removing `sort` or `uniq` from the
default despite R1-R3 — both are load-bearing for existing canary arms
(RC1b, E5), and removal would gut those arms the way an unlisted `date`
would have gutted FAULT G.
