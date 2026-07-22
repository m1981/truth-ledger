# Symbol-level inverse tracing — validated design (build on demand)

Status: **demand-gated, validated at scale** — NOT current architecture.
Two review rounds (2026-07-22): a falsification round against this repo
and a validation round against the kuchnie monorepo (6 components,
212 py files, 2,397 symbols). Trigger: a consumer needing
24765/29119-grade code-element traceability, or the operator adopting
the kuchnie first wave sketched below. First adopted piece: the catalog
BOM pins (2 claims, kuchnie, 2026-07-22).

## The design (three parts, verdicts from review)

- **D1 — coarse-watch / fine-verify** (BUILD-WITH-AMENDMENTS): a claim
  watches the FILE; its evidence command extracts and hashes only the
  target function's definition text. File touch → stale (cheap dirty
  bit); `reaffirm`'s recheck auto-agrees when the extracted region is
  unchanged. Effective symbol granularity with zero new anchor
  machinery; churn absorbed by ADR-030.
- **D2 — dark-symbol sweep** (BUILD-WITH-AMENDMENTS): stdlib `ast`
  enumeration cross-referenced against active claims' evidence commands
  (word-boundary matching, `(?<![A-Za-z0-9_])name(?![A-Za-z0-9_])`) and
  watches. Three darkness grades: g0 lit (file watched + symbol named),
  g1 (file watched, symbol unnamed), g2 (file unwatched). Exclude
  RECORD-kind paths per the coverage policy.
- **D3 — contract-symbol manifests** (replaces a prose symbol table,
  which would rot): a tracked, **pre-sorted** manifest file + one
  sentinel claim. Adding/removing a contract symbol stales the claim —
  the staling is the review trigger (the tr-ebac6513 pattern at symbol
  scale).

## Tested recipes (verbatim — all pass the ADR-009 screen; rg is
## allowlisted in both this repo and kuchnie)

```
# top-level function pin (async- and decorator-aware; handles
# multi-line signatures closing at column 0):
rg -U -o '(?m)^(?:@.*\n)*(?:async )?def NAME\(.*(?:\n(?:[ \t].*|\).*)?)*' FILE

# method pin (4-space class body; async- and decorator-aware):
rg -U -o '(?m)^    (?:@.*\n    )*(?:async )?def NAME\(.*(?:\n(?:[ \t]{5,}.*|[ \t]*)?)*' FILE

# D3 manifest sentinel (-h REQUIRED for multi-file; manifest committed
# pre-sorted to match sort -u):
grep -whoFf MANIFEST FILES... | sort -u | diff - MANIFEST
```

**Forbidden recipes** (falsified): `grep -A N` and `head|tail` window
pins — an edit beyond the window hash-matches and reaffirm silently
auto-agrees a changed region; the determinism double-run cannot catch
it (under-extraction is deterministic).

## Amendments earned on real code (kuchnie round)

- **A1** `(?:async )?` and the `\).*` continuation alternative are
  mandatory — `async def` and column-0-closing multi-line signatures
  both defeated the original pattern.
- **A2** `rg -U -o` drops blank lines inside matches: claim wording
  must reference "the definition text as extracted by this command",
  never file bytes.
- **A3** repeated method names (protocol + implementations, 4× in one
  kuchnie file) produce multi-region pins — acceptable (any impl drift
  stales; arguably a feature) or class-scope the pattern.

## Named residuals (disclose in any ADR that ships this)

- **Text pins the artifact, not behavior**: rebinding
  (`name = lambda: ...` after the def), import-swap, and callee edits
  all hash-match and auto-agree. Rule: symbol claims assert DEFINITION
  TEXT ("the source contains the deny-wins check"), never behavior
  ("the screen refuses X") — behavior belongs to the canary /
  acceptance-oracle channel (ADR-014), kept separate by design. This is
  the industry lesson too: trace links pair with test references.
- Universal wording + regex metacharacters trip ADR-007; use
  existential wording or `--scope-ok` WITH an explicit `--ttl-days`
  (else ADR-032's 30-day default decays the claim on a timer reaffirm
  can never clear).
- `grep -woF` manifest matching also hits call sites: a deleted def
  still "present" while called. Accepted; the D2 sweep is the backstop.
- rg version/output-format coupling: a format change is a mechanical
  divergence (ADR-012 path), absorbed.

## Measured economics

- Meta-repo (hot single file): N=20 symbol claims ≈ +65% ledger growth.
- kuchnie (6 components): N=20 on kuchnie-core ≈ **+18%** (~50 stale
  events/wk in burst, one reaffirm batch clears hash-matchers; est.
  5–15 genuine dispatches/wk in burst, ~0 quiet). 91% of
  component-touching commits touch exactly one component → per-component
  claims give component-local blast radius by construction.
  Cross-component claims only at adapter boundaries; a claim watching
  all components is the anti-pattern (kuchnie's tr-076ed1ea).

## kuchnie dark-symbol census (2026-07-22 validation round)

2,397 symbols: 50 g0 (2%) / 823 g1 / 1,524 g2. Production highlights:
catalog BOM path (`get_bom`, `build_bom`) was **g2 — files wholly
unwatched** (closed by the first-wave pins); ERP price-import chain and
CAM drilling/DXF output symbol-dark (g1/g2); kuchnie-core formula
methods g1 (files watched, formulas unnamed).

## Adoption sketch (kuchnie first wave, ~12–15 claims)

1. catalog BOM pins (2 claims) — done 2026-07-22.
2. kuchnie-core: `docs/contract-symbols-core.txt` (~15 sorted symbols:
   `decompose_*` registry entries, panel/reveal/clearance formulas) +
   1 D3 sentinel + 6–8 D1 pins on `blum_drawers.py`/`construction.py`.
3. kitchen-erp pricing: manifest (~10: `import_price_file`,
   `validate_landing_rows`, `_last_known_price`,
   `assess_quote_freshness`, `record_offer`,
   `generate_cost_trace_lines`) + sentinel + 3–4 pins.

## Standards context

The fine-grained end of obligations already mapped in paper §6.4:
24765 backward traceability at symbol granularity, 29119-4 structural
coverage for the condition level, 25023's inverse count as the
dark-symbol measure. Granularity is *mandated* only by the
functional-safety family (DO-178C MC/DC, ISO 26262, IEC 61508) — the
demand signal that would justify building D2 as a shipped verb.
