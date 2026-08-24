You are continuing work on ~/PycharmProjects/truth-ledger. Read this whole
prompt before touching anything.

WHAT THIS SYSTEM IS (ontology — get this right or every judgement is wrong)

  It is a VERIFICATION apparatus, not a validation one. It answers exactly one
  question: does a written sentence still correspond to the repository it
  describes? It cannot tell you a true fact is about the wrong thing. Paper §0
  declares this: in 12207 terms the whole ledger sits BELOW the baseline.

  Its ontology is thin on purpose. There are no substances, only EVENTS in a
  total order (ts, id, canonical-serialisation); state is `fold(events)`, never
  stored. Some states are pure projections: under ADR-057 `stale` is derived
  from a clock passed as a PARAMETER, and `now_dt=None` means "do not ask the
  clock", so being-in-time is optional and reproducible.

  Its epistemology is defeasibility, not truth. INV-C/D/E/F specify DEFEAT
  conditions, not verification conditions. A claim is warranted until something
  defeats it.

  Above the mechanism sit five parallel registers with no declared relations
  between them: ADR (decisions), INV (safety properties), FAULT arms (seeded
  faults), EPI (lessons, on a branch), J (journal). Their cross-references are
  prose. This is the source of nearly every defect found so far.

IV&V POSTURE (how to work here)

  1. A claim without a falsifier is not a claim. State the observation that
     would prove you wrong, then look for it.
  2. A gate that has not been MADE TO FAIL is not evidence. Break it, see red,
     restore byte-identically, verify with diff or sha256. (ADR-061)
  3. Hunt fail-open first. This repo has been bitten three times: an instrument
     naming nine sources and reading four; --record-baseline blessing a corpus
     it never read; a malformed table row silently un-administering a register.
     A missing input must be LOUD.
  4. Measuring nothing is not passing (ADR-042 rule 2).
  5. A refusal writes no record, so gates are invisible in the ledger. You
     cannot infer a gate fired from the absence of a violation.
  6. Never verify your own work alone. See ADR-062: dispatch an adversarial
     reviewer and DO NOT give it the specification — given the spec it checks
     compliance, not correctness. An implementer that demonstrated its own gate
     red still shipped a defect, twice.
  7. Look for the strongest counter-evidence to your own finding BEFORE
     reporting it. A previous session claimed Appendix A named no arms; 16 of
     21 rows do. It had generalised from the one row it had grepped.
READ, IN THIS ORDER

  docs/reviews/mechanism-layers-brief-2026-08-24.md     layers L0-L5, landed/open
  docs/decisions/060,061,062-*.md                       prose citations, DONE, agent roles
  docs/registers.md                                     the register index (new, WIP)

  Then run and READ the output, do not assume it:
    python3 instruments/arm-index.py
    python3 instruments/register-index.py
    bash template/scripts/doc-health.sh


CONVENTIONS

  Artifacts are English. AGENTS.md states no language rule — that is itself an
  unwritten norm worth writing down. Commit messages in English.
  The operator may converse in Polish. Instruments are Tier C: stdlib only, no
  truthlib import, a docstring saying WHY, documented exit codes, and a baseline
  file whose entries fail when they outlive their finding.