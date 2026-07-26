# V&V per spec archetype — pairings, standards map, and the mechanization design

> Reader: anyone deciding how a component of a given archetype should be
> tested, or whether to build the V&V section into the archetype blanks |
> Enables: picking the historically-proven verification technique per
> archetype without re-deriving the lineage, and building the V&V blank
> section from an already-red-teamed design | Update-trigger: the
> archetype set changes, a recipe here is falsified, or the operator
> green-lights the build

Status: **BUILD-WITH-AMENDMENTS, demand-gated** — the design below
survived an adversarial round against the live harness (2026-07-26,
twelve findings, three recipes killed or rewritten) but is NOT built.
Trigger: the operator deciding the archetype blanks (template
docs/templates/, shipped v0.9.15) should carry a V&V section — a
docs-only change riding any future release.

## Part 1 — the pairings (why each archetype tests the way it does)

Each spec tradition acquired its matching verification technique
because a specific 1980s–2000s failure mode made the unpaired spec
worthless; the fix always had the same shape: make the spec executable,
or make the test the spec. Boehm's split runs through all of it:
verification = building the product right (code ↔ spec), validation =
building the right product (spec ↔ need). A perfectly verified
component can be a perfectly implemented mistake.

| Archetype | Verification (code ↔ spec) + origin | Validation (spec ↔ world) | Residual no instrument closes |
|---|---|---|---|
| A Domain / Core Library | Property-based tests + contract assertions (Meyer DbC '86-88; Claessen & Hughes QuickCheck '00; the Ariane-5 unstated-precondition parable) | Domain-expert language walkthrough; the model survives the next requirement change (Evans '03) | Wrong abstraction — revealed only by change |
| B Data / Persistence | Schema/contract tests per endpoint, migration + round-trip tests (IEEE 830 prose → OpenAPI lineage: prose describes, schema binds) | Pilot consumer; production data-quality monitoring (Great Expectations lineage) | World's semantics drifting under a conformant schema |
| C Interactive GUI | Executable Given/When/Then scenarios + state/visual regression (Cunningham FIT '02, North BDD '03-06, Adzic Spec-by-Example '11 — the cure for sign-off-then-drift) | Usability tests, A/B, beta, task-completion analytics (Nielsen '90s) | Job-fit over time; trust and feel |
| D Integration / Adapter | Consumer-driven contract tests (Robinson '06, Pact '13 — the provider learns pre-merge which consumer it breaks); degraded form: compatibility probes | Runs against the real system; translation-error monitoring; the provider relationship | The third party's future — detection, never prevention (Hyrum's Law on undeclared dependencies) |
| E Pipeline / Batch | Golden master + run-twice determinism contract (batch-era diff testing; Feathers characterization tests '04; approval testing '08). Pins everything, understands nothing — re-blessing demands review | Expert sign-off on fixtures (the blessing IS the validation event); parallel/shadow run; downstream acceptance | Inputs the fixture corpus never sampled |
| F Cross-cutting / Infra | Fitness functions / CI gates per ATAM scenario (SEI '98-'00 → Ford/Parsons/Kua '17; ArchUnit '17, chaos '11) | SLO monitoring + error budgets (SRE '16), game days, incident review feeding new scenarios | Unknown-unknowns — incidents are the universe's pull requests against the scenario table |

Scope note (the two-axes point): unit / integration / e2e / acceptance
classify tests by SCOPE and audience (V-model levels, Cohn's pyramid
'09, Marick's quadrants '03); the table above classifies by TECHNIQUE.
Every test has coordinates on both axes, and the technique implies the
natural scope (property tests → unit; CDC → isolated integration; BDD
scenarios → acceptance, mostly NOT e2e; golden master → any scope;
fitness functions → system/build). A spec that names the technique
never needs to say "write unit tests" — the level falls out.

## Part 2 — what the standards actually give (honest map)

- **12207/15288**: the verification-vs-validation split as two named
  processes; otherwise pure process shells. No technique.
- **29148**: every requirement SHALL be verifiable, with a bound method
  from Inspection / Analysis / Demonstration / Test (MIL-STD lineage).
  Forces the fit-criterion question at writing time; stops at the
  method CATEGORY.
- **29119-4**: the only ISO technique catalog (equivalence, boundary,
  decision tables, state-transition, scenario testing…). Archetype C
  genuinely served; A approximated (PBT's ancestors, no properties/
  generators/shrinking); **D, E, F essentially absent** — no CDC, no
  golden masters, no fitness functions. A competent 1990s unit-test
  curriculum, frozen.
- **IEEE 1012**: integrity levels + a task-per-phase matrix — answers
  what activities, when, at what rigor; still not which technique.
- **25010/25023**: quality vocabulary + actual measure formulas — the
  standardized form of "fit criteria → measurable tests"; lags SRE
  practice on operational qualities.
- **DO-178C / ISO 26262**: the only full answers, at the strict end:
  every test derives from a requirement; structural coverage is an
  ADEQUACY CHECK, not a target (a gap = missing requirement, dead code,
  or unintended function — each must be resolved); bidirectional
  traceability mandatory; 26262 Part 6 has literal technique tables per
  ASIL incl. fault injection and back-to-back comparison. Even DO-178C
  buys only "the code implements the requirements, all of them, nothing
  else" — requirement RIGHTNESS is pushed up and out.

The pairing knowledge in Part 1 lives in practitioner literature
(Meyer, Cockburn, Adzic, Robinson, Feathers, Ford), not in any
standard — which is why the archetype field guide has to exist: it is
the missing middle between "there shall be a procedure" and a failing
test. The through-line: verification became nearly free once each spec
tradition acquired its executable pairing (1986–2017); validation never
became free, because its subject does not hold still. Mechanize
verification completely, so human attention goes to the half only
humans can do.

## Part 3 — the mechanization design (red-teamed, not built)

Proposed: a V&V section in each archetype blank
(template/docs/templates/archetype-*.md), post-amendment shape:

```markdown
## Verification & Validation
Verification: <technique per archetype pairing> — oracle carried by
  `wk-XXXXXXXX` (--accept-cmd) or standing sentinel `tr-XXXXXXXX`
  <!-- cite the id that CARRIES the command; never restate the command -->
Validation: <instrument, who, date> — attestation `tr-XXXXXXXX`
  (UNVERIFIED, --ttl-days N; expiry means re-walkthrough + re-file + edit this line)
Residual (accepted, not closable): <name by TITLE only — an id here is a
  live tripwire that fails this spec when it dies>
```

Plus a recipes appendix in the field guide. The red-team round (twelve
findings, sandbox-reproduced against CLI v0.9.15) rewrote the draft:

- **F1/F2 (the worst): the layer-rule recipe was a trap twice.**
  `! grep …` is dead at the evidence screen (`!` tokenizes as a program
  name). The obvious rewrite `grep -rl 'import os' src/ | wc -l |
  grep -qx 0` FILES but is BLIND on macOS — `wc -l` pads with spaces,
  so output is empty and exit 1 in the clean AND violated state; after
  seeding a real violation, recheck reported "hash matches" and invited
  an agree. Canonical form (reproduced both ways):
  `grep -rl 'import os' src/ | wc -l | tr -d ' ' | grep -qx 0 && echo LAYER-CLEAN`.
  Filing over the exit-1 warning produces a hollow VERIFIED.
- **F3: ADR-007 taxes the honest wording.** "No I/O imports" fires the
  quantifier gate; `--scope-ok` without explicit `--ttl-days` silently
  takes ADR-032's 30-day decay. Discipline: fire the gate honestly, pay
  the scope sentence, pass a deliberate long TTL.
- **F4: every inline determinism form for archetype E is dead**
  (process substitution, chained `sh`, temp files, path-form scripts —
  each refused). E's run-twice check survives only as a wrapper script
  wired as an ADR-014 accept-cmd (that screen is deliberately looser:
  no deny baseline, exact repo-relative paths via .truth/accept-allow).
  Structural gap: an oracle runs once at `done` — no standing
  determinism claim exists, and faking one is refused.
- **F5: schema hash-pins are divergence generators** — every
  legitimate schema evolution burns the claim and fails citing specs.
  Use path-tripwired output-stable sentinels
  (`jq -e 'has("x")' schema.json >/dev/null && echo SCHEMA-OK`);
  reserve hash pins for genuinely frozen contracts.
- **F6: ids in a Residual line are live tripwires** (spec-health
  regex-matches ids anywhere) — a section meaning "accepted, not
  closable" must never stand on a dying id: titles only.
- **F8: the original draft violated the house restate-nothing rule**
  by asking for the oracle COMMAND in prose — amended to citing the id
  that carries it. This also dissolves overlap with the Acceptance
  section (Acceptance holds claim-texts-to-be; V&V holds pairing +
  validation instrument + residual).
- **F9: TTL'd validation attestations work end-to-end today.** No
  HUMAN class exists (`EVIDENCE_CLASSES = VERIFIED/INFERRED/UNVERIFIED`);
  the vehicle is UNVERIFIED + `--ttl-days N` + a cross-session agree.
  Reproduced: expiry → ADR-019 re-file-not-re-verify → spec-health
  flags citing specs until the new id is swapped in. Disclosed costs:
  each expiry is a human re-walkthrough + re-file + spec edit + a
  commit passing the full spec surface; and `verdict --recheck` on an
  attestation files `cannot_verify` — verifier protocol needs one line:
  judge attestations manually, recheck-first does not apply.
- **F7/F12: consumer-convention precedence** — a repo carrying its own
  spec-convention doc outranks the blanks (kuchnie's codifies five
  sections); shipping the V&V section requires a consumer note to
  update that doc, or the section is a dead letter there. And the
  F-archetype's "the gate passes" is enforced by session-close /
  session-gates.d, not by the ledger — say so instead of implying a
  ledger oracle.
- Survived clean: sixth section breaks nothing mechanical; blanks'
  15-line governance header window unaffected; shipping churn = one
  reaffirm sweep per repo (coverage-claim sentinels are
  content-independent).

## Named residuals (consolidated)

- Per-archetype residuals in the Part 1 table's last column — none is
  closable by any instrument; they are what validation loops watch for.
- The E-archetype standing gap (F4): an oracle runs once at `done`;
  there is no standing "tests are green" or "pipeline deterministic"
  claim, and faking one via evidence is refused by design.
- Attestation costs (F9): each TTL expiry is a human re-walkthrough +
  re-file + spec edit + a full-surface commit; recheck-first does not
  apply to attestations (files `cannot_verify`) — judge manually.
- Consumer-convention precedence (F7): a repo's own spec-convention doc
  outranks the shipped blanks; without updating it the V&V section is a
  dead letter there.

Related shipped mechanism: spec-coverage manifests
(spec-coverage-manifests.md) — the traceability half (which assertion
has a named test) is live in the pilot; this design is the authoring
half (which technique and which validation instrument the spec commits
to). They compose: the V&V section's oracle id and the spec's SC
manifest cover the same spec from two sides.
