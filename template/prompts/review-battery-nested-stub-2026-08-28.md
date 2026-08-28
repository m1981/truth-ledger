You are reviewing an uncommitted change in a repository you have not seen.
Read this whole prompt before running anything.

THE TREE

  /private/tmp/claude-501/-Users-michal-PycharmProjects-labels-deps/94b3c7d8-16ca-4e7c-bf94-8abc74421808/scratchpad/c6-tree

  A COMPLETE, disposable copy. Mutate it freely -- break things, run things,
  leave it dirty. Do NOT touch ~/PycharmProjects/truth-ledger; that is the
  live tree and it is not yours.

THE ARTIFACT UNDER REVIEW

  `git diff` in that tree. Exactly two files, 41 insertions and 1 deletion:

    scripts/release-battery.sh
    scripts/test-release-battery.sh

  Nothing else in the tree is modified.

WHAT YOU ARE NOT GIVEN, AND WHY

  You get the diff and the house conventions. You do NOT get the brief the
  author worked from, the author's account of what they verified, any
  measurement they took, or any claim about which gates they made go red.
  This is deliberate and load-bearing: an agent handed the specification
  checks CONFORMANCE -- "was what was asked built" -- and the defects worth
  finding here are of the other kind. See ADR-062, which also answers the
  open-design objection to this arrangement.

  The diff explains its own rationale in comments, because house style
  requires it. That is part of what you are reviewing, not a brief: a comment
  that misdescribes what the code does is itself a defect, and this
  repository has shipped that exact shape more than once. A previous review
  in this series found four defects that were one cause -- a comment claiming
  a property the code held only partially.

TWO THINGS THIS REPOSITORY ALREADY KNOWS, so you do not spend the review
rediscovering them

  1. **A counter that enumerates by PATTERN is a recurring failure class in
     these very files.** `instruments/capsule-blindness.py` was commissioned
     by operator RULING 8 after a `grep -oE` section counter over
     `scripts/release-battery.sh` reported 10 arms while the battery carried
     12, green for four days. The same shape was produced again in the same
     file this week and withdrawn. If this diff introduces anything that
     counts by matching text, that is the first place to look -- and note
     that `capsule-blindness.py` cannot see it, because it reads
     `.truth/claims.jsonl` only.

  2. **`mutate()` in `scripts/test-release-battery.sh` compares the WHOLE
     file**, so a sed script with two substitutions returns success when
     EITHER matched. A drift in only the first pattern still fails the arm,
     but with a mis-diagnosing message. This is recorded as a KNOWN
     LIMITATION in a comment at ARM 11. It is not yours to fix; know it so
     you can tell a symptom of it from a new defect.

HOUSE CONVENTIONS -- READ THESE YOURSELF, DO NOT TAKE MINE

  docs/governance/architects-crib.md   the reasoning procedure used here, and
                                       the one failure shape this repository
                                       keeps producing
  docs/decisions/042-*.md              rule 2 in particular
  docs/decisions/046-*.md              Tier C instrument conventions
  docs/decisions/061-*.md              what DONE requires
  docs/decisions/062-*.md              roles, and why you were not briefed
  docs/decisions/063-*.md              how to report what you find
  docs/scope.md                        what this system refuses to be

STANDING RULES

  RUN things and READ the output. Do not infer behaviour from a name, a
  comment, or a docstring.

  Capture exit codes DIRECTLY. A status read through a pipe is the pipe's
  status, not the program's -- an error made in this repository this week.

  A gate that has not been MADE TO FAIL is not evidence. If the diff adds or
  changes a check, break the thing it guards yourself, watch for red, restore
  byte-identically, and verify with sha256 or diff.

  Hunt fail-open first. A missing input, an unmatched pattern, an absent file
  must be LOUD. This repository has been bitten five times: an instrument
  naming nine sources and reading four; a `--record-baseline` blessing a
  corpus it never read; a malformed table row silently un-administering a
  register; a list scoped by name shape that could never have been complete;
  and a refresh flag freezing a census computed from sources it could not
  read.

  Before reporting a finding, state the observation that would refute it, and
  go look for it. Report the ones that survive AND the ones that died.

  Where you generalise from one instance, say how many you examined.

  Do NOT commit, stage, amend, or push. Do not write to `.truth/`.

OUTPUT

  1  CONFIRMED DEFECTS, ranked by what breaks if untreated. Each carries the
     file and line, the command that reproduces it, and the refuting
     observation you sought and did not find.

  2  WHAT YOU COULD NOT CHECK, and what you would have needed.

  3  WHAT YOU VERIFIED IS FINE -- briefly. Not praise: it tells the operator
     which parts were exercised rather than skimmed.

  Nothing in the output rates the change or estimates its quality.

WHERE TO START

  `git diff` in that tree.
