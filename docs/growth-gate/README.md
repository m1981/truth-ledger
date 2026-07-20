# Growth-gate archive: the fork-permanent hash-tree successor

What this is: the falsified-then-repaired hash-TREE redesign of the ledger's
ordering primitive (TLR-002/013/014 and dependents, two adversarial review
rounds deep), archived with its executable spec `test-tlr-fold.py` — 18/18
checks including negative controls (re-run 2026-07-20 from this location).

Status: growth-gated FUTURE work, NOT the current architecture. The linear
prev-hash chain was falsified for this regime (concurrent O_APPEND appenders
fork it; union merge breaks it both ways); the tree design is the named
successor. Already adopted from it: ADR-031 (TLR-013's one-rule duplicate-id
refusal). Trigger: the first forged timestamp found in the wild (paper §10).
