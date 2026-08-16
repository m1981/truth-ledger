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

---

## J-008 · WYTYCZNE: skrypt identyfikacji claimów ADR zwraca CICHE ZERO · 2026-08-16

Skrypt z wytycznych wykonawczych, uruchomiony dosłownie:

```
Znaleziono 0 aktywnych claimów ADR:
```

Przyczyna — `truth list --json` **nie niesie `evidence_paths`**:

```
python3 template/scripts/truth list --json | (klucze wiersza)
→ ['age_days', 'class', 'id', 'status', 'text', 'tier']
→ 'evidence_paths' in row: False
```

`list` jest projekcją, nie surowym rekordem. Ten sam fakt jest już udokumentowany
w `instruments/concern-tag.py`: *"the tags come from a raw ledger read, because
`list` rows do not carry payload concerns"*.

**Wniosek:** gdyby ten skrypt został użyty jako podstawa decyzji, dałby odczyt
„0 claimów do obsłużenia" i przepuścił prosto do `git mv` — po którym 14 claimów
stałoby się `unexecutable`. To jest **dokładnie tryb awarii, przed którym broni
ten projekt**: sensor zwracający zero, brany za „czysto".

**Korekta (w runbooku, krok 1.2):** status z `list --json`, ścieżki z surowego
`.truth/claims.jsonl`. Wynik poprawnego odczytu: **14 claimów** — 13 `live`
+ 1 `unverified` (`tr-6207afe1`). Wcześniej raportowane „13" liczyło tylko `live`.

---

## J-009 · WYTYCZNE: `--cause expired` jest niezgodne z ADR-049 i skasowałoby 14 żywych faktów · 2026-08-16

```
grep RETRACTION_CAUSES template/truthlib/registry.py
→ RETRACTION_CAUSES = ("restated", "expired", "wrong")

template/truthlib/policy.py:66
→ "  --cause expired   it WAS true and the world moved past it"
```

**Dwa niezależne problemy.**

**(a) Przyczyna jest fałszywa.** Przeniesienie pliku ADR nie sprawia, że fakt
przestaje być prawdziwy — świat się nie ruszył, artefakt zmienił ścieżkę.
Wpisanie 14× `expired` zatrułoby dokładnie tę metrykę, którą
`instruments/retraction-causes.py` istnieje żeby mierzyć.

**(b) Operacja jest zbyt szeroka.** 13 z 14 claimów jest **mieszanych** —
obserwują plik ADR **oraz** kod/testy, a ich treść dotyczy działającego
zachowania:

```
tr-3ce7c0c9 [live] ['template/scripts/truth', 'truth-canary.sh',
                    'docs/adr/truth/014-acceptance-oracles.md', '.truth/accept-allow']
tr-75070d09 [live] ['docs/adr/truth/013-premise-supersede.md',
                    'template/scripts/test-truth-core.py']
tr-552d0fb0 [live] ['template/truthlib/kernel.py', 'truth-canary.sh',
                    'claims.schema.json', 'docs/adr/truth/015-canonical-timestamp-profile.md']
... (11 kolejnych o tym samym kształcie)
```

Wycofanie ich zabrałoby żywy ledger z **61 → 47 (−23%)** i skasowało fakty
o kodzie, który się nie zmienia.

**Korekta:** operacja to **przekierowanie**, nie wycofanie — re-file
z zawężonym zbiorem obserwacji (ścieżka ADR usunięta, kod/testy zostają),
potem `--cause restated --successor <NOWY_ID>`. To jedyna z trzech przyczyn
opisująca stan faktyczny i przy okazji realizuje cel Fazy 3 (mniej ścieżek →
precyzja 12,6% zamiast 1,9%).

Wyjątek: `tr-6207afe1` obserwuje wyłącznie glob `docs/adr/truth/*.md` — nie ma
czego zawężać, ten jeden wycofać bez następcy.

---

## J-010 · WYTYCZNE: `git mv` z `template/` to usunięcie artefaktu z produktu, nie archiwizacja · 2026-08-16

Wytyczna: `git mv template/docs/adr/truth/*.md docs/archive/adr/`.

`template/` jest tym, co copier wysyła konsumentowi. Przeniesienie do
meta-repo `docs/` oznacza, że **konsument przestaje dostawać ADR-y w ogóle**.
To może być zamierzone, ale jest decyzją produktową, nie porządkami.

Pomiar ryzyka linków:

```
linków markdown na adr/ w template/           → 0
plików template/ z referencją prozą na adr/   → 5
  template/.truth/README.md
  template/CHANGELOG.md
  template/docs/structure.md
  template/docs/truth-ledger-machinery.md
  template/docs/adr/truth/README.md
```

**Ryzyko zerwanych linków jest ZEROWE** (referencje są prozą, nie linkami), więc
`doc-health.sh` nie zaprotestuje — ale 5 plików będzie wskazywać ścieżkę, której
nie ma. `doc-health.sh` i tak wyłącza ze sweepu każdą ścieżkę z segmentem `adr/`
oraz `archive/`, a `fact-health.sh` wyłącza `docs/archive/` — oba warianty są dla
tych bramek neutralne.

**Korekta:** runbook 1.3 stawia jawny wybór **A** (literalnie wg wytycznych —
ADR-y opuszczają produkt) albo **B** (`template/docs/archive/adr/` — konsument
dostaje je jako archiwum). Nie wykonuję żadnego wariantu bez decyzji właściciela.

---

## J-011 · WYTYCZNE: mapowanie kodów wyjścia pre-push pomija exit 8 · 2026-08-16

Wytyczna: *„jeśli exit 7 → blokuj; jeśli exit 0 → przepuszczaj"*.

`truth reproduce` ma trzeci kod: **8 = zbadano 0 claimów** (potwierdzone
w baseline J-006 — komenda raportuje `61 live claim(s)` i kończy 0; przy pustym
zbiorze kończyłaby 8).

Bez arm'a na 8 pusty albo uszkodzony ledger przechodzi przez bramkę pchnięcia
**po cichu** — ADR-042 reguła 2 i reguła F1 mówią, że sweep, który nic nie
zbadał, jest porażką, nie sukcesem.

**Korekta:** runbook 2.3 blokuje na 7 **i** na 8.

---

## J-012 · WYTYCZNE: „usuń kod komend" musi rozróżnić zapis od odczytu · 2026-08-16

Wytyczna: *„Usuń kod komend `invalidate-scan` oraz `reaffirm`"*.

Ledger jest append-only i zawiera **1 971** rekordów `invalidation` oraz
**1 283** pól `reaffirm_cleared`. Usunięcie obsługi **odczytu** złamałoby fold
na własnej historii.

**Korekta:** usuwamy werby CLI (ścieżka zapisu); zostawiamy parsowanie rekordów
(ścieżka odczytu); pole zamykamy wzorcem ADR-046 (*legacy-admitted, closed to
new records*) + wpis w `.truth/field-consumer-opt-out`.

**Delta canary zadeklarowana Z GÓRY** — 15 rodzin FAULT dotyka tych komend:

```
10x  FAULT RA (ADR-030)      6x  FAULT ST (ADR-050)     4x  FAULT SD-decay (ADR-032)
 4x  FAULT EF (ADR-051)      2x  FAULT L                 2x  FAULT DG (ADR-025)
 2x  FAULT C5 (issue #4)     1x each: B, D, T, E, R10, RX, LK, PA
```

Spadek ramion canary w kroku 2.6 jest **oczekiwany i wolno go zaliczyć** tylko
z wyliczeniem w JOURNAL, które ramię zniknęło i dlaczego jego przedmiot
przestał istnieć. Ramię, którego przedmiot **nadal istnieje**, musi zostać
przepisane, nie skasowane.

---

## J-013 · WYTYCZNE: szablon ARCHITECTURE.md przyjęty; rygor treści zaostrzony · 2026-08-16

Szablon 4-rozdziałowy przyjęty **bez zmian** — jest dobrze podzielony i
odwzorowuje realne osie systemu. Wyrywkowa kontrola dwóch faktów z szablonu
przeciwko kodowi:

```
template/truthlib/kernel.py:29  def fold_key(ne)  — "ADR-016: the fold's TOTAL
                                order… third key is canon()"     ZGADZA SIĘ
template/truthlib/registry.py:150  DUPLICATE_THRESHOLD = 0.6     ZGADZA SIĘ
```

**Zaostrzenie:** każdy fakt w ARCHITECTURE.md ma być **odczytany z kodu**, nie
przepisany z ADR-a — wzorzec nagłówka `template/docs/structure.md`
(*„STATUS: OBSERVED… where this document and an ADR disagree, this document is
reporting the code and the ADR is reporting the intent"*). Inaczej konsolidacja
54 ADR-ów wyprodukuje jeden plik dryfu zamiast pięćdziesięciu czterech.

---

## J-014 · Runbook zrewidowany do r2 · 2026-08-16

Wytyczne wykonawcze wprowadzone. Przyjęte bez zmian: kolejność (korpus ADR przed
Reproduce-on-Read), szablon ARCHITECTURE.md, kierunek 2.5 (stan z logu:
`unverified` → `live` → `diverged`/`retracted`), rozwiązanie pre-push
(`reproduce`, brak zapisu przy sukcesie).

Skorygowane: J-008 (odczyt), J-009 (przyczyna + zakres), J-010 (tier),
J-011 (exit 8), J-012 (zapis vs odczyt).

Numeracja uzgodniona: kroki z wytycznych 1.2/1.3 wchodzą do Fazy 1 obok audytu
screenera (1.1); dawna Faza 5 rozpuszczona. Dawny krok 1.2 („decyzja o
automatycznym wykonaniu") wchłonięty jako kryterium wyjścia z 1.1 — GO/NO-GO
JEST tą decyzją.

**Żaden plik produkcyjny nadal nie został dotknięty.**
Następny krok: **1.1 — audyt screenera dowodowego (read-only)**.
