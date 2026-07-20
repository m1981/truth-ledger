> STATUS: historical session artifact (2026-07-20). The antipattern/redesign content here was subsequently ADJUDICATED — most structural fixes were falsified by red-team review; see docs/roadmap-v3.md (do-not-do list) and docs/growth-gate/ for the settled outcomes. Kept for the reasoning record.

# Truth Ledger — Target Design (post-peer-review)

The expected design after the remediation plan. Marking convention:
🟦 **NEW** (the seven actions) · ⬜ unchanged — settled correct, do not touch ·
❌ removed / struck · every 🟦 is S/M effort; nothing large by design.

---

## 1. Target architecture — the deltas in context

```mermaid
flowchart TB
  subgraph CLI["scripts/truth (single file — stays single file)"]
    CORE["⬜ Pure fold core<br/>(ts,id,canon) order · FWW/LWW/tombstone ·<br/>8 statuses (minimal quotient — keep)"]
    INTAKE["⬜ Intake gates (all 10 kept, per-gate flags kept)"]
    WARN["🟦 A3: exit-code warning<br/>VERIFIED filing with exit≠0 prints<br/>'usually demonstrates with a passing command'<br/><i>non-blocking — kills hollow-VERIFIED silently-green channel</i>"]
    SCAN["⬜ invalidate-scan (demote-only, no exec in hooks)"]
    REAFFIRM["🟦 A2: truth reaffirm (batch verb)<br/>verifier session walks stale queue:<br/>hash-match → auto-agree 'reaffirm: hash-match' + re-anchor<br/>mismatch → real dispatch · TTL-staled → re-file path<br/><i>automates the 98.5% that finds nothing;<br/>judgment stays human/LLM where it found the 1.5%</i>"]
    BANNER["🟦 A4: doctor banner<br/>write verbs print loud warning when<br/>commit gate unwired — fail-open WITH NOISE<br/><i>never fail-closed</i>"]
    DOCTOR["⬜ doctor (ADR-025) — now feeds the banner"]
    CHLOG["🟦 A6b: 444-line docstring changelog →<br/>CHANGELOG.md (15-line header stays)"]
  end

  subgraph TESTS["Self-checks"]
    VERTEST["🟦 A6a: ADR-026 version test extended to<br/>loophole-map · ops-guide · check-truth.sh headers<br/><i>project eats its own dogfood</i>"]
    CANARY["⬜ canary suite (166 faults)"]
    ORACLE["🟦 A5: canary-coverage claim re-homed as<br/>ADR-014 acceptance oracle (oracles may run bash)<br/><i>deny baseline stays intact</i>"]
  end

  subgraph GONE["Struck from the plan"]
    HL["❌ §10 prev_hash chain (unsound under<br/>O_APPEND races + union merge) →<br/>replaced by one sentence: git's commit DAG<br/>over the INV-A-gated file already binds sequence"]
    ORTHO["❌ all falsified redesigns: Lamport order ·<br/>sandbox · status collapse · kernel extraction ·<br/>mirror generation · unified override"]
  end

  INTAKE --> WARN
  DOCTOR --> BANNER
  SCAN -->|stale queue| REAFFIRM
```

---

## 2. Verification economics — the pipeline before → after

The measured problem: 597 agrees vs 9 diverges (1.5% hit rate), half-life
0.02 days, ~9.5 agrees/claim. The fix reprices re-affirmation without
touching first-verification independence.

```mermaid
flowchart LR
  subgraph BEFORE["TODAY — every re-check priced like first verification"]
    Q1["stale queue<br/>(hot-file commit → 8 claims stale,<br/>6 still true)"] --> D1["per-id dispatch<br/>full independent judgment<br/>× 597"]
    D1 --> R1["98.5% agree<br/>(labor found nothing)"]
  end
  subgraph AFTER["TARGET — triage by what actually changed"]
    Q2["stale queue"] --> T{"🟦 reaffirm triage"}
    T -->|"output hash matches<br/>(evidence unchanged)"| AUTO["auto-agree<br/>'reaffirm: hash-match'<br/>re-anchor, seconds, no judgment"]
    T -->|"hash mismatch<br/>(something really moved)"| FULL["⬜ full dispatch<br/>independent semantic judgment<br/>— where the 1.5% lives"]
    T -->|"TTL-staled"| REFILE["⬜ re-file claim<br/>(ADR-019: TTL never<br/>resets by re-verify)"]
    T -->|"screened:false"| MANUAL["⬜ manual only<br/>(never execute)"]
  end
  BEFORE -.->|"one M-effort verb"| AFTER
```

---

## 3. Three planes → root causes → actions

```mermaid
flowchart LR
  subgraph PAIN["Pain points by plane"]
    direction TB
    RP["📄 READER<br/>P2 correction sediment (24 annotations)<br/>P3 best data buried in §8.2<br/>P5 unsound §10 plan<br/>P6 defect record lags 4 versions<br/>P10 unverified refs"]
    OP["⚙️ OPERATOR<br/>P1 1.5% verification hit rate<br/>P4 hollow VERIFIED<br/>P7 opt-in enforcement, silent<br/>P12 canary/deny collision"]
    AD["📦 ADOPTER<br/>P8 stale satellite docs (v0.4/v0.6.4/v0.9.0 vs v0.9.10)<br/>P9 efficacy unproven, costs unfavorable<br/>P11 changelog-in-code"]
  end
  subgraph RC["Root causes"]
    RC1["RC1 append-only discipline<br/>applied to the prose"]
    RC2["RC2 re-affirmation priced<br/>like first verification"]
    RC3["RC3 VERIFIED = determinism,<br/>not demonstration;<br/>enforcement silent when unwired"]
    RC4["RC4 dogfood not pointed<br/>at own docs"]
    RC5["RC5 single observer"]
  end
  subgraph ACT["Actions (all S/M)"]
    A1["🟦 A1 paper v3 consolidation<br/>≤10k words, §2 from repo snapshot,<br/>strike hash-linking, verify refs"]
    A2["🟦 A2 truth reaffirm"]
    A3["🟦 A3 exit-code warning"]
    A4["🟦 A4 doctor banner"]
    A5["🟦 A5 re-home canary claim"]
    A6["🟦 A6 version tests + CHANGELOG.md"]
    A7["🟦 A7 external referee run,<br/>published verbatim"]
  end
  RP --> RC1 --> A1
  OP --> RC2 --> A2
  OP --> RC3 --> A3 & A4 & A5
  AD --> RC4 --> A6
  AD --> RC5 --> A7
  RC1 -.P5 P6 P10.- A1
```

---

## 4. Paper v3 — target structure

```mermaid
flowchart TB
  subgraph V2["v2 today — 14,710 words"]
    S1["mechanism §1 + 24 dated<br/>in-place corrections"]
    S2["§2 frozen at 24–48h window, n=2 headline"]
    S3["§8.2 aside: the 11-day / 597-verdict<br/>longitudinal data (the best evidence, buried)"]
    S4["§10 incl. unsound hash-linking"]
    S5["refs 20–25 [unverified]"]
  end
  subgraph V3["v3 target — ≤10,000 words"]
    T1["clean current-state mechanism<br/>+ Revision History appendix<br/>(sediment moved, not deleted)"]
    T2["§2 dual-window: pilot snapshot AND<br/>longitudinal churn — regenerated from<br/>committed truth stats --json<br/><i>reproducible from the repo</i>"]
    T3["§4 + two missing rows<br/>(ADR-028 seam · hollow-VERIFIED)<br/>+ one §8 sentence: audit scope = v0.4,<br/>HEAD covered by canary/unit gates only"]
    T4["§10 hash-linking struck →<br/>git-DAG sentence; trial design promoted<br/>to the section's head"]
    T5["all refs verified or dropped"]
    T6["⬜ §6.4 standards motivation (stays)"]
  end
  S1 --> T1
  S2 & S3 --> T2
  S4 --> T4
  S5 --> T5
```

---

## 5. Roadmap — sequenced, trial-first logic

```mermaid
gantt
  dateFormat YYYY-MM-DD
  title Sequence: hardening week → trial clock starts → paper v3 during accrual
  section Hardening (pre-trial, ~1 week)
    A2 reaffirm verb (M)            :a2, 2026-07-21, 3d
    A3 exit-code warning (S)        :a3, 2026-07-21, 1d
    A4 doctor banner (S)            :a4, 2026-07-22, 1d
    A5 re-home canary claim (S)     :a5, 2026-07-23, 1d
    A6 version tests + CHANGELOG (S):a6, 2026-07-24, 2d
  section Efficacy trial (the primary move)
    Trial clock starts (churn now honest)   :milestone, m1, 2026-07-27, 0d
    Control-arm design + accrual            :t1, 2026-07-27, 60d
    First monthly hand-audit (§8.2 due)     :milestone, m2, 2026-08-08, 0d
  section Paper (during accrual)
    A1 v3 consolidation (M)         :p1, 2026-07-28, 7d
    A7 external referee run (M)     :p2, 2026-08-04, 7d
    v3 + trial numbers = submission :milestone, m3, 2026-09-28, 0d
```

**Why this order** (the review's core argument): running the trial today
divides benefit by a churn cost with a known one-week fix — guaranteeing
an unfavorable, unrepresentative denominator. Land A2–A4 first, *then*
start the clock; consolidate the paper while data accrues; submit with
the trial's number as the new headline. Both alternative orderings
terminate in the trial anyway — polish tops out at an experience report
(§7 disclaims the central claim), and deeper hardening is a proven trap
(every large mechanism on the do-not-do list).


