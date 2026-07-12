# Field notes — second-deployment session (temporal-go-agent-sdk)

> Reader: the operator/author, reviewing whether to fold these into the paper/ADRs | Enables: deciding which findings from a second deployment are worth adopting | Update-trigger: findings adopted into an ADR/paper section, or superseded

Review artifact, not a decision. Generated 2026-07-12 from a second deployment
of the truth-ledger: repo `temporal-go-agent-sdk`, a Fable-5 agent session
(distinct agent, distinct repo; **same operator**, so the §8.1 conflict-of-
interest caveat still applies — these strengthen, they do not resolve it).
Nothing in the existing docs was edited. Each item is a drop-in proposal.

Confirmations already shipped in v0.6.0 (no action — logged for completeness):
a scope-overreach divergence ("5 sites" → actually 6) reconfirming ADR-007's
dominant shape from a different agent; a mechanical divergence (an evidence
grep matched prose in the session's own spec `.md`) that is exactly ADR-012;
cross-session no-self-verify honored manually (ADR-010). None need changes.

---

## 1. (HIGHEST VALUE) ADR-010 conflicts with the single-writer coordination convention

**Home:** `hardening-proposals-solo-regime.md`, ADR-010 → append to *Consequences*.

**What happened.** Two concurrent sessions coordinated with (i) a single
ledger-writer convention (append-race safety) and (ii) the verifier peer in
`--permission-mode plan` (read-only). The plan-mode verifier could not file, so
the writer **scribed** its `agree` verdicts — and the verdict then carried the
*scribe's* `session`, which was also the claim's author-session. Under ADR-010
(`agree` refused when filing session == claim session) this independent verdict
is indistinguishable from self-verification: it **blocks a legitimate
independent verdict**, and symmetrically **lets a real self-verdict pass through
a courier**. ADR-010 enforces on the record's `session`; the single-writer
pattern makes the record's session the wrong one.

**Proposed text:**
> **Interaction with multi-session coordination (field note, 2026-07-12).** When
> concurrent sessions adopt a single-ledger-writer convention and route
> verification to a read-only (`--permission-mode plan`) peer, the peer cannot
> file its own verdict — a courier files it, and the verdict then carries the
> courier's `session`. If the courier authored the claim, this gate refuses a
> genuinely-independent `agree`; conversely it lets a true self-verdict pass as
> another's. The record's `session` must be the *verifier's*, not the courier's.
> Resolution: either verifiers write their own verdicts (verifiers must not be
> plan-mode), or `verdict` gains a `--verifier-session <id>` the courier sets and
> the gate checks. Until then: do not scribe `agree` — have the verifier session
> file it directly.

Why first: a real contradiction between two *shipped* disciplines in exactly the
multi-session regime the ops-guide recommends — not a nicety.

---

## 2. (NEW) A diverged/stale premise HOLDs work forever — no detach path

**Home:** `hardening-proposals-solo-regime.md`, Traceability table (new row) + an
FS-5 stub.

**What happened.** A premise diverged; a *corrected* claim was filed under a new
id and added as a premise — but the work item stayed HELD, because the diverged
original cannot be detached (append-only + issue first-wins, ADR-006). The only
exit was re-filing the whole work item under a new id (`wk-dcc7a92d` →
`wk-0eaee8d9`), which broke every reference to the old id (specs, RESUME, an ADR).

**Proposed traceability row:**
> | 11 | A diverged/stale premise HOLDs its work item permanently; correcting the
> fact under a new id doesn't release it — no detach/supersede verb (append-only
> + issue first-wins, ADR-006) | second deployment (wk-dcc7a92d re-file) |
> **FS-5** `truth premise --supersede <old-tr> <new-tr>` on an issue: appends a
> premise-redirect event the ready-fold honors | Released by an auditable event,
> no id churn |

---

## 3. (NEW) Onboarding trap: template ADR namespace collides with the consumer's

**Home:** paper `truth-ledger-paper-v2.md` §9 "Adopting this" (and/or the shipped
ADR README).

**What happened.** The template ships `docs/adr/001-012` and grows it on update.
This project numbered its *own* ADRs in the same series (007-011); a `copier
update` collided them, and immutable ledger references to the project ADRs made
renumbering impossible. Any consumer who writes their own ADRs hits this.

**Proposed text (§9):**
> **Reserve an ADR namespace before writing your own.** The template owns
> `docs/adr/NNN` and extends it on update; number *your project's* ADRs in a
> disjoint space (e.g. `docs/adr/ledger/` for the template's, or a `P###` range
> for yours) from day one. Ledger claims cite ADRs by number immutably, so a
> collision found after the fact cannot be renumbered away — only namespaced
> going forward.

---

## 4. (NEW angle) Sharpen "scope to the evidence" with a second reason: blast radius

**Home:** operations-guide §Summary authoring-discipline line (or paper §9).

**What happened.** One commit to a hot shared file (`fsguard.go`) re-staled 8
claims at once — 2 genuinely fixed, 6 still-true — cascading verification debt
across the file's whole claim neighborhood. §9 currently justifies narrow
`--paths` by correctness only.

**Proposed text (append to the discipline note):**
> Scope evidence `--paths` to the narrowest set that actually backs the claim —
> not only for correctness, but for *blast radius*: every claim anchored to a
> file re-stales when any commit touches it, so a broadly-scoped path drags
> unrelated-but-true claims into the verification queue on every edit to a hot
> file.

---

## Suggested order
1 (a shipped-discipline contradiction) → 2 (a work-kernel gap with a concrete
fix) → 3 (an install-time trap every consumer meets) → 4 (a one-line sharpening).

---

## Adoption status (2026-07-13, all four adopted)

1. → `Amended by:` line in `template/docs/adr/010-session-separation.md`
   status block, plus the attribution caveat in the ops guide §3 rung 3.
   One deviation from the proposal: no `--verifier-session` flag — the
   CLI already honors `TRUTH_SESSION=<verifier-session>` on the scribe's
   command, so the fix is the documented convention, not new surface.
   The scribe hazard also joined the loophole map §D.
2. → filed as ledger work item **wk-8d966a5b** (FS-5 design in its
   text) rather than a row in the hardening doc, which is a closed
   review artifact ("Accepted and implemented as v0.6.0"); the ADR
   lands with the implementation.
3. → paper §9, new "Reserve an ADR namespace" convention (adapted).
4. → paper §9, new blast-radius bullet (adopted there rather than the
   ops guide — the guide already delegates authoring discipline to one
   home, and a second restatement would rot).
