# DZIENNIK — refaktor "Reproduce-on-Read"

> **APPEND-ONLY.** Nigdy nie edytuj wpisu w miejscu. Wniosek odwrócony dodaje się
> jako nowy wpis z `zastępuje: J-xxx`. Inaczej nie da się odróżnić "zmiana na
> podstawie dowodów" od "ktoś przepisał zdanie" — czyli dokładnie tego dryfu,
> przed którym broni ten projekt.
>
> Każdy wpis: data, komenda, **surowy wynik**, wniosek. Wniosek bez komendy
> nie jest wpisem.

---

## J-001 · Commit bazowy i stan gałęzi · 2026-08-16

```
git branch --show-current   → claude/git-hooks-architecture-zc97y3
git log -1 --format='%H %s' → fa2e85b14f6de82cd99fb61af0cb01d93d908155
                              chore: record post-commit invalidation scan
git status --porcelain      → (czysto)
```

Gałąź robocza była już utworzona i aktywna. Drzewo czyste.

---

## J-002 · ŚRODOWISKO: brak `jsonschema` — jedna porażka baseline jest oczekiwana · 2026-08-16

```
python3 -c "import jsonschema"  → ModuleNotFoundError
PYTHONPATH                      → (puste)
ls ~/.cache/truth-ledger-pylib  → brak
```

Konsekwencja w suicie core:

```
FAIL: test_drift_detector_armed (TestJsonschemaPresent)
AssertionError: jsonschema not installed: the JSON Schema half of the
contract is UNCHECKED.
skipped: TestConformanceSchema.test_both_representations_agree_everywhere
skipped: TestConformanceSchema.test_corpus_against_json_schema
skipped: TestGeneratedMutantsAgree.test_every_mutant_of_every_valid_seed_agrees
```

**Wniosek:** to nie jest defekt kodu — to **arm F1 działający poprawnie**. Suita
odmawia udawania zieleni, gdy połowa kontraktu rekordu jest niesprawdzana.

**Decyzja: NIE ustawiam `TRUTH_ALLOW_NO_JSONSCHEMA=1`** — zgodnie z regułą
właściciela z `.local/machine.md`. Waiver wyłączyłby te 3 testy po cichu, a suita
i tak pisałaby OK. Ten kontener nie ma cache'u `~/.cache/truth-ledger-pylib`,
który jest na maszynie właściciela.

**Skutek dla refaktoru:** kroki dotykające schematu rekordu (**2.5**, **2.6**)
mają tu **niepełne pokrycie**. Muszą zostać przewalidowane na maszynie
z `jsonschema` przed uznaniem za zamknięte. Odnotowane jako ryzyko, nie obejście.

---

## J-003 · ŚRODOWISKO: klon shallow — druga porażka baseline jest oczekiwana · 2026-08-16

```
git rev-parse --is-shallow-repository → true
git log --oneline | wc -l             → 50
```

```
FAIL: test_blast_report_real_and_sandbox (TestTierCInstruments)
AssertionError: 'shallow' != 'ok'   (data["history_state"])
```

**Wniosek:** porażka środowiskowa. `blast-report` poprawnie degraduje się głośno
przy płytkiej historii — zachowanie zgodne z projektem (ADR-039).

**Skutek:** wszystkie pomiary oparte na `git log` (churn, F-09 z dossier)
są w tym kontenerze **niewiarygodne**. Pomiary z ledgera są wiarygodne —
ledger jest kompletny (4 555 rekordów, 2026-07-10 → 2026-08-15).

---

## J-004 · ŚRODOWISKO: `core.hooksPath` NIEUSTAWIONE — bramki nie działają · 2026-08-16

```
git config core.hooksPath   → (nieustawione)
ls .githooks/               → post-commit post-merge pre-commit
                              pre-merge-commit pre-push
```

Katalog `.githooks/` istnieje i jest kompletny, ale **nic go nie wskazuje**.
Commity w tym kontenerze **nie przechodzą przez `check-truth.sh`**, a push
**nie przechodzi przez `release-battery.sh`**.

**Wniosek:** to jest dokładnie tryb awarii F-08 z dossier — cicha nieuzbrojona
instalacja — **występujący na żywo, teraz.** Dossier opisywał go jako zdarzenie
historyczne (v0.9.36–37). Jest bieżący.

**Nie uzbrajam go jednostronnie** — uzbrojenie zmieni zachowanie każdego commitu
w tym refaktorze i może zablokować na stanie zastanym. Decyzja należy do
właściciela; do czasu jej podjęcia **bramka regresji z runbooka jest uruchamiana
ręcznie po każdym kroku** i to jest jedyna ochrona tego refaktoru.

---

## J-005 · Baseline suit testowych · 2026-08-16, `fa2e85b`

| suita | komenda | wynik | czas |
|---|---|---|---|
| core | `python3 template/scripts/test-truth-core.py` | `Ran 394` — 1 failure, 3 skipped | 11,7 s |
| v04 | `python3 template/scripts/test-truth-v04.py` | `Ran 13` — OK | 0,002 s |
| integrations | `python3 template/scripts/test-integrations.py` | `Ran 28` — 1 failure | 13,7 s |
| canary | `bash truth-canary.sh` | **283 caught, 0 missed** | 44,8 s |

Obie porażki wyjaśnione: J-002 (jsonschema) i J-003 (shallow). **Żadna nie jest
regresją.** Canary — jedyna suita niezależna od obu tych czynników — jest
w pełnej zieleni.

**Definicja zieleni na czas refaktoru:** dokładnie te liczby. Każde odchylenie
— w tym **wzrost liczby skipów** — jest porażką wymagającą wpisu przed commitem.

---

## J-006 · Baseline metryk, które refaktor ma poruszyć · 2026-08-16

```
python3 template/scripts/truth reproduce
→ reproduce: 61 live claim(s) -- 60 reproduces, 1 capsule-stale,
             0 unexecutable, 0 no-capsule
→ 3 przebiegi: 539 / 514 / 530 ms

wc -l .truth/claims.jsonl → 4555
```

| rekordy | liczba |
|---|---:|
| `verdict` | 2 185 |
| `invalidation` | 1 971 |
| `claim` | 223 |
| `issue_event` | 102 |
| `issue` | 74 |
| — z tego `reaffirm_cleared` | **1 283 (28,2% ledgera)** |

```
ls template/docs/adr/truth/*.md | wc -l                          → 54
grep -lriE '^\s*status:.*(superseded|retired|rejected)' ... | wc -l → 0
```

**Wniosek:** `unexecutable = 0` jest punktem odniesienia dla Fazy 5 — po
przeniesieniu ADR-ów ta liczba musi wrócić do zera, a nie do 13.

---

## J-007 · Krok 0 zamknięty · 2026-08-16

Utworzone: `docs/refactor/00-RUNBOOK.md`, `docs/refactor/01-JOURNAL.md`.
**Żaden plik produkcyjny nie został dotknięty** — `git status` pokazuje wyłącznie
dwa nowe pliki pod `docs/refactor/`.

Trzy fakty środowiskowe (J-002, J-003, J-004) zostały znalezione przy okazji
i są **odnotowane jako fakty empiryczne**, nie obejścia. J-004 jest z nich
najpoważniejszy i wymaga decyzji właściciela przed Fazą 2.

Następny krok: **1.1 — audyt screenera dowodowego (read-only)**.
