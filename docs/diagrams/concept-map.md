# Truth Ledger — Concept Map

Six views of the system: components, data model, status machine, lifecycle,
fold semantics, and the theory-to-mechanism map (annotated with the
novelty-review verdicts).

---

## 1. Components & responsibilities

Who does what. The system owns no process — all reactivity is borrowed from
git hooks / CI ("the borrowed event loop").

```mermaid
flowchart TB
  subgraph ACTORS["Actors (identity self-attested)"]
    AA["Author agent session<br/><i>files claims, declares premises</i>"]
    VS["Verifier session<br/><i>independent recheck + judgment<br/>cannot retract</i>"]
    HU["Human operator<br/><i>sole retraction authority<br/>TRUTH_HUMAN + exact-id ack</i>"]
  end

  subgraph FILES[".truth/ — plain files, synced by git"]
    LEDGER[("claims.jsonl<br/>append-only JSONL event log<br/><b>the single source of truth</b>")]
    SCHEMA["claims.schema.json<br/><i>record contract</i>"]
    ALLOW["evidence-allow<br/><i>read-only command allowlist</i>"]
    PROMPT["verifier prompt<br/><i>fixed dispatch text</i>"]
  end

  subgraph CLI["scripts/truth — dependency-free Python CLI"]
    INTAKE["Intake gates<br/><i>refuse before writing:</i><br/>empty text · near-duplicate (Jaccard)<br/>quantifier vs scope · dead tripwires<br/>safety screen · determinism double-run"]
    CORE["Pure core (fold)<br/><i>no I/O, no clock, no env</i><br/>status = fold(log)"]
    SCAN["invalidate-scan<br/><i>the only clock reader</i><br/>TTL · anchor lost · paths touched<br/>→ writes invalidation records"]
    DISP["dispatch<br/><i>claim record + fixed prompt only<br/>never author reasoning</i>"]
    POLICY["ready<br/><i>issues × premise validity<br/>tier-sensitive blocking</i>"]
    VAL["validate + order_check<br/><i>schema mirror · backdated /<br/>equal-ts duplicate detection</i>"]
  end

  subgraph HOST["Borrowed event loop — git hooks / CI (must be installed; doctor checks)"]
    GATE["check-truth.sh<br/><b>commit gate</b>: byte prefix check<br/>(INV-A append-only) + validate"]
    PM["post-merge / CI hook<br/>→ runs invalidate-scan"]
  end

  AA -- "truth claim" --> INTAKE
  INTAKE -- "append (O_APPEND)" --> LEDGER
  AA -- "truth issue / premise" --> INTAKE
  HU -- "retract (human gate)" --> LEDGER
  VS -- "verdict agree/diverge/cannot_verify" --> LEDGER
  DISP -- "fixed prompt + record" --> VS
  PROMPT --> DISP
  LEDGER --> CORE
  CORE --> POLICY
  CORE --> SCAN
  SCAN -- "invalidation records" --> LEDGER
  SCHEMA --> VAL
  ALLOW --> INTAKE
  GATE --> VAL
  PM --> SCAN
  LEDGER -.-> GATE
```

---

## 2. Record kinds (the data model)

Six-plus-one kinds share one envelope; everything else is derived, never stored.

```mermaid
classDiagram
  class Envelope {
    id  ~hash of payload+ts+actor~
    kind
    actor  ~self-attested~
    session  ~self-attested~
    ts  ~self-chosen: forgery accepted~
  }
  class claim {
    text
    evidence_class VERIFIED|INFERRED|UNVERIFIED
    cost_tier P0|P1|P2
    evidence_cmd + output SHA-256 + exit code
    anchor_commit
    evidence_paths OR ttl_days
    scope_basis / basis
  }
  class verdict {
    claim → id
    verdict agree|diverge|cannot_verify|retracted
    basis (required)
    subtype: mechanical (ADR-012)
    anchor_commit (agree re-anchors)
  }
  class invalidation {
    claim → id
    reason: paths touched | ttl expired | anchor unreachable
    ~the ONLY path to stale~
  }
  class premise {
    issue → wk-id
    claim → tr-id
    supersedes (ADR-013 redirect)
  }
  class issue {
    wk- envelope
    premises[] declared at birth
  }
  class issue_event {
    issue → wk-id
    event claimed|released|closed|reopened|cancelled
  }
  class contradicts {
    a → id, b → id
    ~v0.9.0 — absent from paper §1/§6.3 (review Minor 6)~
  }
  Envelope <|-- claim
  Envelope <|-- verdict
  Envelope <|-- invalidation
  Envelope <|-- premise
  Envelope <|-- issue
  Envelope <|-- issue_event
  Envelope <|-- contradicts
  verdict --> claim : judges
  invalidation --> claim : demotes
  premise --> issue : blocks/enables
  premise --> claim : depends on
  issue_event --> issue : transitions
  contradicts --> claim : disputes pair
```

---

## 3. Claim status machine (derived, never stored)

Recoverable vs terminal is the core asymmetry: machine judgments can be
revisited; only a human retraction is a dead end.

```mermaid
stateDiagram-v2
    [*] --> unverified : claim filed (any class —<br/>evidence at filing ≠ verification)
    unverified --> live : verdict agree
    live --> diverged : verdict diverge<br/>(genuine or --mechanical)
    live --> cannot_verify : verdict cannot_verify
    live --> stale : invalidation record<br/>(paths / TTL / anchor lost)
    unverified --> stale : invalidation record
    live --> disputed : contradicts edge fires<br/>(both sides live)
    diverged --> live : agree (recoverable)
    cannot_verify --> live : agree (recoverable)
    stale --> live : agree — re-anchors<br/>⚠ TTL claims re-stale next scan<br/>(review Major 2)
    unverified --> retracted : human retraction
    live --> retracted : human retraction
    diverged --> retracted : human retraction
    stale --> retracted : human retraction
    retracted --> [*] : TERMINAL — absorbs all later events<br/>(2P-set tombstone; readiness release<br/>also human-gated, ADR-017)
```

Readiness policy (`truth ready`) reads this machine per premise:
`live` passes · `unverified` warns · `cannot_verify` blocks P0 only ·
`stale` / `diverged` / `retracted` / missing always block.

---

## 4. Claim lifecycle (sequence)

```mermaid
sequenceDiagram
    participant A as Author agent
    participant T as truth CLI
    participant L as claims.jsonl
    participant G as commit gate<br/>(check-truth.sh)
    participant S as invalidate-scan<br/>(post-merge/CI)
    participant V as Verifier session
    participant H as Human queue

    A->>T: truth claim "text" --evidence-cmd --paths/--ttl
    T->>T: intake gates (refuse-first)<br/>screen · dedupe · quantifier/scope ·<br/>dead-tripwire · determinism ×2
    T->>L: append claim (status: unverified)
    A->>G: git commit
    G->>G: byte prefix check (INV-A)<br/>+ schema + order_check
    Note over G: backdated / equal-ts duplicate ids refused here
    A->>T: truth dispatch tr-xxxx
    T->>V: fixed prompt + claim record only<br/>(no author reasoning)
    V->>V: deterministic recheck:<br/>re-run cmd, compare SHA-256
    V->>V: judge: does output support the TEXT?<br/>(the scope-overreach seam)
    V->>L: verdict agree → live (re-anchor)
    Note over S: later: merge / CI tick
    S->>S: git diff anchor..HEAD vs evidence_paths<br/>TTL elapsed? anchor reachable?
    S->>L: invalidation → stale (queued)
    H->>L: retract (TRUTH_HUMAN=1 + typed exact id)<br/>— terminal
```

---

## 5. Fold semantics (how status is derived)

```mermaid
flowchart LR
  RAW["Log lines<br/>(any file order —<br/>union merge may scramble)"]
  SORT["Total-order sort<br/><b>(ts, id, canon)</b><br/>canon = 3rd key: distinct records<br/>never tie (ADR-016)"]
  subgraph DISC["Per-field merge disciplines"]
    FWW["Claim CONTENT<br/>first-writer-wins<br/>(min key; write-once register)"]
    LWW["Claim STATUS<br/>last-writer-wins<br/>per verdict/invalidation"]
    TOMB["retracted<br/>absorbing / terminal<br/>(2P-set tombstone)"]
  end
  VIEWS["Derived views<br/>claim status · issue status ·<br/>premises + supersedes · disputed edges"]
  OUT["Consumers<br/>ready · queue · list · stats"]

  RAW --> SORT --> DISC --> VIEWS --> OUT
```

Confluence: any permutation of the same event set folds to one state
(exhaustive-permutation tested; 166/166 seeded faults green).
The real CRDT is the grow-only set of log lines under git union merge;
the fold is a deterministic query over it.

---

## 6. Theory → mechanism map (with review verdicts)

```mermaid
flowchart LR
  subgraph THEORY["Cited theory"]
    TMS["Doyle TMS 1979"]
    CRDT["Shapiro CRDTs 2011"]
    OCC["Kung-Robinson OCC 1981"]
    BFT["Lamport BFT 1982 /<br/>Castro-Liskov 1999"]
    CT["RFC 6962 Cert. Transparency"]
    BSC["Mokhov Build Systems 2018"]
    HARDY["Hardy Confused Deputy 1988"]
    DNS["Mockapetris DNS TTL 1987"]
    QC["QuickCheck 2000"]
    ES["Fowler / Helland<br/>event sourcing"]
  end
  subgraph MECH["Mechanism"]
    M1["status = fold(log), never stored"]
    M2["total-order fold; FWW/LWW/tombstone"]
    M3["never-block append +<br/>validate at commit"]
    M4["design stance only<br/>(no quorum, no signatures)"]
    M5["byte prefix commit gate (INV-A)"]
    M6["scan: content diff vs anchor<br/>(demote-only, no rebuild)"]
    M7["TRUTH_HUMAN_ACK = exact id<br/>(no ambient authority)"]
    M8["ttl_days decay"]
    M9["exhaustive-permutation<br/>confluence tests"]
    M10["append-only log as<br/>source of truth"]
  end
  TMS -- "SOUND (as annotated)" --> M1
  CRDT -- "SOUND (with own caveats)" --> M2
  OCC -- "PARTIAL — no abort phase" --> M3
  BFT -- "ORNAMENTAL — self-declared" --> M4
  CT -- "SOUND — first-party trust" --> M5
  BSC -- "PARTIAL — 'rebuilder' overstates" --> M6
  HARDY -- "SOUND — residual admitted" --> M7
  DNS -- "PARTIAL — re-verify ≠ TTL reset" --> M8
  QC -- "PARTIAL — exhaustive, not random" --> M9
  ES -- "SOUND" --> M10
```

Uncited nearest kin (review Major 1): Dynamic Safety Cases (2015),
Kelly & McDermid (1999), TUF `expires`, in-toto capsules,
Swimm / Dosu / Fiberplane doc-freshness, Panthaplackel JIT comment
invalidation (2021). The novelty is the **composition**, not any element.
