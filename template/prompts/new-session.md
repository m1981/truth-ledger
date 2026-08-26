You are working on ~/PycharmProjects/truth-ledger.

ROUTE: <execution | record>          <- the operator fills this in

ORIENTATION -- read exactly one document

  docs/scope.md  (105 lines). It says what this system is, what it REFUSES,
  and what it cannot detect by construction. Nothing else is required
  reading before you start. If you find yourself opening the paper, the
  registers or the decisions "to get oriented", stop -- that is the failure
  this file exists to prevent, and it costs six figures of tokens.

RETRIEVAL -- query, never read

  docs/map.txt is generated: one line per navigable artifact, with the
  artifact's OWN first line as its description. 218 rows.

    grep <thing-you-are-touching> docs/map.txt
    python3 instruments/map.py --for <path>     kind, route, what governs it

  `--for` splits GOVERNED BY (norms, registers, the charter -- these bind
  you) from MENTIONED IN (briefs and docs -- history, not governance). Read
  the first list. Count the second and move on.

  If the map disagrees with the tree, the tree wins: `map.py --write`.

YOUR ROUTE, AND WHY IT IS ASSIGNED

  Every artifact is on one of two routes. `execution` is what runs --
  instruments, scripts, hooks, kernel code, the ledger and the policy files
  under .truth/. `record` is what is written -- decisions, registers,
  briefs, the paper.

  On 2026-08-25 two competent reviewers audited this repository on the same
  day. One entered from `record` and found five defects; one entered from
  `execution` and found three. The overlap was ZERO. Neither read too
  little; they came in through different doors.

  So the route is assigned, not chosen. Enter through yours. If you finish
  and want to widen, say so and ask for the other route to be dispatched
  separately -- do not widen inside one session, because then nobody knows
  which door found what.

HOW WORK IS JUDGED HERE

  A check that has never been observed to fail is not evidence that
  anything holds. Break it, watch for red, restore byte-identically, verify
  with sha256 (ADR-061). Measuring nothing has not passed (ADR-042 rule 2).

  Before reporting a finding, state the observation that would prove you
  wrong and go look for it. Report the ones that died too -- a killed
  hypothesis of your own is the only evidence that you could have been
  wrong.

  Do not commit; the operator commits (ADR-062). Do not write to
  .truth/claims.jsonl by any route except `scripts/truth`.
