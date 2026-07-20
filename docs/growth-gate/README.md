# Growth-gate archive: gated successor designs

Designs that survived adversarial review but are deliberately NOT built —
each waits behind a named trigger, so the answer is never re-derived and
never ships ahead of its demand signal.

## 1. Fork-permanent hash-tree ordering (TLR)

`tlr-target-architecture-and-adrs.md` + executable spec `test-tlr-fold.py`
— 18/18 checks including negative controls (re-run 2026-07-20 from this
location). The falsified-then-repaired hash-TREE redesign of the ledger's
ordering primitive (TLR-002/013/014 and dependents, two adversarial review
rounds deep). The linear prev-hash chain was falsified for this regime
(concurrent O_APPEND appenders fork it; union merge breaks it both ways);
the tree design is the named successor. Already adopted from it: ADR-031
(TLR-013's one-rule duplicate-id refusal).
**Trigger: the first forged timestamp found in the wild (paper §10).**

## 2. Obligation Ledger — three-tier standards enforcement

`obligation-ledger-design.md` — mechanical gates + LLM tribunal
(judge/adversary roles, calibrated by sampled human audit) + human
quantifier-closure ceremonies with decaying attestations, decomposing
each §6.4 standards obligation (29148/24765/12207/10007/25010/29119/42010)
into its three jobs. Claims the achievable ceiling only: "accountably
searched and freshly signed", never "proven complete"; no executable
oracle exists yet (§6 of the doc lists what one must pin first).
**Trigger: a real team adopting the ledger against a real compliance
regime and asking for obligation-level enforcement.**
