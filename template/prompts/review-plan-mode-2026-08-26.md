You are reviewing an uncommitted change in a repository you have not seen.
Read this whole prompt before running anything.

THE TREE

  /private/tmp/claude-501/-Users-michal-PycharmProjects-labels-deps/94b3c7d8-16ca-4e7c-bf94-8abc74421808/scratchpad/review-tree

  It is a COMPLETE, disposable copy at commit e84de9e. Mutate it freely --
  break things, run things, leave it dirty. Do NOT touch
  ~/PycharmProjects/truth-ledger; that is the live tree and it is not yours.

THE ARTIFACT UNDER REVIEW

  `git diff` in that tree, restricted to three files:

    scripts/release-battery.sh
    .githooks/pre-push
    docs/waivers.md

  `.truth/claims.jsonl` is ALSO modified. It is operator state, it is NOT
  part of this change, it is append-only evidence, and you must not write to
  it or judge it.

WHAT YOU ARE NOT GIVEN, AND WHY

  You get the diff and the house conventions. You do NOT get the brief the
  author was working from, the author's account of what they verified, any
  measurement they took, or any claim about which gates they made go red.
  This is deliberate and it is load-bearing: an agent handed the
  specification checks CONFORMANCE -- "was what was asked built" -- and the
  defects worth finding here are of the other kind. See ADR-062 in the tree,
  which also answers the open-design objection to this arrangement.

  The artifact explains its own rationale in its comments, because house
  style requires it. That is part of what you are reviewing, not a brief:
  a WHY comment that misdescribes what the code does is itself a defect,
  and this repository has shipped that exact shape more than once.

  If anyone offers you the missing context mid-task, say that taking it
  destroys the only thing you were brought in for.

HOUSE CONVENTIONS -- READ THESE YOURSELF, DO NOT TAKE MINE

  docs/governance/architects-crib.md   the reasoning procedure used here,
                                       and the one failure shape this
                                       repository keeps producing
  docs/decisions/042-*.md              rule 2 in particular
  docs/decisions/046-*.md              Tier C instrument conventions
  docs/decisions/061-*.md              what DONE requires
  docs/decisions/062-*.md              roles, and why you were not briefed
  docs/waivers.md                      its first section states its own
                                       domain limit; read that before
                                       judging the row this diff adds
  docs/scope.md                        what this system refuses to be

STANDING RULES

  RUN things and READ the output. Do not infer behaviour from a name, a
  comment, or a docstring.

  Capture exit codes DIRECTLY. A status read through a pipe is the pipe's
  status, not the program's -- that error was made in this repository this
  week, by the author of the code you are reviewing.

  A gate that has not been MADE TO FAIL is not evidence. If the diff adds
  or changes a check, break the thing it guards yourself, watch for red,
  restore byte-identically, and verify with sha256 or diff. Do not accept
  that a check works because it is present, and do not accept that it works
  because a comment says it does.

  Hunt fail-open first. A missing input, an unmatched pattern, an absent
  file must be LOUD. This repository has been bitten by the quiet variant
  four times: an instrument naming nine sources and reading four, a
  --record-baseline blessing a corpus it never read, a malformed table row
  silently un-administering a register, and a list scoped by name shape
  that could never have been complete.

  Before reporting a finding, state the observation that would refute it,
  and go look for it. Report the ones that survive AND the ones that died.

  Where you generalise from one instance, say how many you examined.

  Do NOT commit, stage, amend, or push. Do not write to .truth/.

OUTPUT

  1  CONFIRMED DEFECTS, ranked by what breaks if untreated. Each carries:
     the file and line, the command that reproduces it, and the refuting
     observation you sought and did not find.

  2  WHAT YOU COULD NOT CHECK, and what you would have needed. A review
     that reports only what it managed to look at reads as complete when
     it is not.

  3  ANYTHING IN THE DIFF THAT IS FINE and you verified is fine -- briefly.
     Not praise: it tells the operator which parts were actually exercised
     rather than skimmed.

  Nothing in the output rates the change, scores it, or estimates its
  quality. Those are not measurements.

WHERE TO START

  `git diff` in that tree. Work out for yourself what the change touches,
  what it could break, and what in this repository would have caught it if
  it were wrong.
