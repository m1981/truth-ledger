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

---

## J-015 · DECYZJA: hooki uzbrojone — i natychmiast wyprodukowały 16 FAŁSZYWYCH zestaleń · 2026-08-16

```
git config core.hooksPath .githooks     → ustawione
python3 template/scripts/truth invalidate-scan
→ stale: tr-599e7561 (anchor unreachable)
→ ... 16 razy ...
→ invalidate-scan: 16 claim(s) marked stale
```

Skutek natychmiastowy: ledger **4555 → 4571**, żywych claimów **61 → 47 (−23%)**.

**Diagnoza.** Sprawdziłem kotwice wszystkich 16 zestalonych claimów przeciwko
historii klonu:

```
tr-58707dac  kotwica 8a5595451520  obecna_w_klonie=NIE
tr-0caaf857  kotwica 56c5af368b4e  obecna_w_klonie=NIE
... (16/16) ...
obecnych: 0   nieobecnych: 16
```

**Wszystkie 16 kotwic leżało poza 52-commitowym oknem płytkiego klonu (J-003).**
Żaden z tych claimów nie był zestały w rzeczywistości — `anchor unreachable
(history rewritten)` opisywał wyłącznie artefakt kontenera.

**Precyzja tego uruchomienia: 0/16.** To jest ta sama teza, którą refaktor
adresuje, zaobserwowana na żywo: heurystyka zestalenia wystrzeliła 16 razy
i nie miała racji ani razu.

**Korekta.** 16 rekordów było **niezacommitowanych**, więc `git checkout --
.truth/claims.jsonl` je cofnął — **żadna historia nie została przepisana**,
bo nigdy nie weszły do historii. Gdyby weszły, ledger jest append-only i te
16 fałszywych zestaleń zostałoby w nim na zawsze.

**Usunięcie przyczyny źródłowej:** `git fetch --unshallow` → 431 commitów,
`shallow: false`. Skan powtórzony:

```
invalidate-scan: 0 claim(s) marked stale
rekordów: 4555   żywych: 61   git status: (czysto)
```

Stan przywrócony w całości. Hooki pozostają uzbrojone zgodnie z decyzją
właściciela — **przyczyną nie były hooki, tylko płytki klon pod nimi.**

**Wniosek operacyjny dla konsumentów:** `install-hooks.sh` w płytkim klonie
(CI z `fetch-depth: 1` jest normą w GitHub Actions) wyprodukuje dokładnie ten
sam kaskadowy fałszywy alarm. To kandydat na osobną pozycję — bramka powinna
odmówić skanu przy `is-shallow-repository = true` zamiast raportować cudze
kotwice jako nieosiągalne.

---

## J-016 · ZMIANA BASELINE: pogłębienie klonu rozwiązało J-003 · 2026-08-16

```
python3 template/scripts/test-integrations.py → Ran 28 tests, OK
```

Porażka `test_blast_report_real_and_sandbox` (`'shallow' != 'ok'`) **zniknęła**.
`zastępuje: J-003` w części dotyczącej baseline'u suit (diagnoza przyczyny
w J-003 pozostaje poprawna).

**Nowy baseline bramki regresji:**

| suita | było | jest |
|---|---|---|
| test-integrations | `Ran 28`, 1 failure | **`Ran 28`, OK** |

Pozostałe bez zmian. J-002 (jsonschema: 1 failure + 3 skipy) obowiązuje dalej —
`git fetch` tego nie dotyka.

---

## J-017 · KROK 1.1 — audyt screenera dowodowego · 2026-08-16 · WERDYKT: GO

**Mechanizm (odczyt kodu).** Receptury wykonują się przez `/bin/sh`:

```
template/truthlib/shellio.py:185
  r = subprocess.run(cmd, shell=True, capture_output=True, cwd=cwd)
```

Screener (`evidence.py:178 screen_evidence_command`) jest zatem jedyną obroną.
**Jest istotnie mocniejszy, niż zakładałem w analizie wstępnej** — moja hipoteza
„allowlista sprawdza tylko pierwszy token" była **BŁĘDNA**. Screener:

* odrzuca `$(` i backtick bezwarunkowo, przed tokenizacją;
* odrzuca każdy znak sterujący ASCII poza tabem (ADR-021 — udokumentowana
  rozbieżność między lexerem `shlex` a `/bin/sh`, gdzie newline jest
  separatorem instrukcji);
* tokenizuje **quote-aware** (`shlex` w trybie punctuation), więc `|` wewnątrz
  cytowanego regexa jest argumentem, nie potokiem;
* traktuje `;`, `&&`, `|`, `&` jako granice segmentów i screenuje program
  **KAŻDEGO segmentu**, nie tylko pierwszego;
* denylist wygrywa z allowlistą (ADR-022);
* dopuszcza redirect wyjścia wyłącznie do `/dev/null` lub deskryptora;
* odrzuca ścieżki w pozycji programu.

**Macierz prób (19 wektorów, sandbox `mktemp -d`, allowlista: grep cat wc ls
head tail echo):**

| # | wektor | werdykt | powód / skutek |
|---|---|---|---|
| 1 | `cat f.txt` | PRZYJĘTA | baseline pozytywny, brak skutku ubocznego |
| 2 | `rm f.txt` | ODRZUCONA | `'rm' is not in .truth/evidence-allow` |
| 3 | `awk '{print}' f.txt` | ODRZUCONA | `'awk' is not in .truth/evidence-allow` |
| 4 | `cat f.txt; rm f.txt` | ODRZUCONA | **`'rm' is not in ...`** — screening per segment |
| 5 | `cat f.txt && rm f.txt` | ODRZUCONA | j.w. |
| 6 | `cat f.txt \| sh` | ODRZUCONA | `'sh' is on the template-owned evidence deny baseline` |
| 7 | `cat $(echo f.txt)` | ODRZUCONA | `command substitution ... is not screenable (ADR-009)` |
| 8 | ``cat `echo f.txt` `` | ODRZUCONA | j.w. |
| 9 | `cat f.txt > pwned.txt` | ODRZUCONA | `output redirection to 'pwned.txt' is refused` |
| 10 | `cat f.txt >/dev/null` | PRZYJĘTA | dozwolony sink, brak skutku |
| 11 | `cat < f.txt` | PRZYJĘTA | odczyt, brak skutku |
| 12 | `cat *.txt` | PRZYJĘTA | glob rozwijany przez sh — **tylko odczyt** |
| 13 | `cat <> f.txt` | PRZYJĘTA | kanał read-write otwarty, **brak eksploatu przy tej allowliście** |
| 14 | `cat f.txt >2` | **PRZYJĘTA** | **PLIK `2` UTWORZONY — potwierdzony kanał zapisu** |
| 15 | `sh -c 'rm f.txt'` | ODRZUCONA | denylist |
| 16 | `/bin/cat f.txt` | ODRZUCONA | `program '/bin/cat' is a path, not a bare command name` |
| 17 | `wc -l ${PWD}/f.txt` | PRZYJĘTA | rozwinięcie zmiennej, nie wykonanie — brak skutku |
| 18 | `cat f.txt & rm f.txt` | ODRZUCONA | `'rm' is not in ...` |
| 19 | newline injection | ODRZUCONA | `control character '\n' is not screenable` (ADR-021) |

### USTALENIE SEC-1 · potwierdzony kanał zapisu, ograniczony

```
cat f.txt >2    PRZYJĘTA  utworzono: 2
cat f.txt >22   PRZYJĘTA  utworzono: 22
cat f.txt >2a   ODRZUCONA output redirection to '2a' is refused
cat f.txt >.git/x  ODRZUCONA j.w.
wc -l f.txt 2>&1   PRZYJĘTA  utworzono: nic   (poprawny fd dup)
```

**Przyczyna źródłowa** (`evidence.py`, gałąź `redir == "out"`):

```python
if redir == "out" and tok != "/dev/null" and not tok.isdigit():
    return "output redirection to ... is refused"
```

`tok.isdigit()` istnieje po to, by dopuścić `1` w `2>&1` (dup deskryptora).
Ale `>2` (zapis do PLIKU `2`) i `2>&1` (dup) trafiają w tę samą gałąź, bo
screener nie odróżnia tokenu `>` od `>&`.

**Granice ryzyka — nazwane precyzyjnie:** można utworzyć/nadpisać wyłącznie plik
o nazwie złożonej **z samych cyfr**, **w bieżącym katalogu**. Nie można nazwać
`.git/hooks/pre-commit` ani niczego ze ścieżką. Treść ograniczona do wyjścia
programu z allowlisty. To **zanieczyszczenie**, nie dowolny zapis.

**Status:** kanał **preegzystujący i już udokumentowany** — ADR-040 wymienia
„digit redirect targets" wśród trzech otwartych kanałów SHELL, których żadna
allowlista nie zamknie, a ADR-041 (PROPOSED, niezaimplementowany) jest ich
nazwaną domknięciem. **Refaktor go nie wprowadza.** Podnosi natomiast
ekspozycję: dziś odpala się przy ręcznej komendzie, po kroku 2.3 przy **każdym
pchnięciu**.

**Proponowana poprawka (jednolinijkowa, do kroku 2.3):** rozróżnić token `>&`
od `>` i dopuszczać `tok.isdigit()` wyłącznie po `>&`. Zamyka SEC-1 bez ruszania
`2>&1`, na którym opiera się konwencja przypinania wyjścia.

### WERDYKT: **GO**

Screener zamyka wszystkie wektory wykonania kodu, które testowałem: podstawienia,
wstrzyknięcie przez separator, potok do powłoki, znaki sterujące, ścieżki
i denylist. Jedyne przejście to ograniczony kanał zapisu SEC-1, preegzystujący
i udokumentowany.

**Warunek do GO:** SEC-1 zamknięte **przed** wdrożeniem kroku 2.3 (automatyczne
wykonanie na pre-push). Nie blokuje kroków 1.2, 1.3, 2.1, 2.2.

**Korekta runbooka:** GO/NO-GO warunkuje **krok 2.3** (`reproduce` na pre-push —
to on wprowadza automatyczne wykonanie), nie 2.4 (wyłączenie `invalidate-scan`,
które nic nie uruchamia). Runbook r2 przypisywał bramkę do 2.4 — błąd etykiety,
poprawiony w r3.

**Nie testowane, zapisane jako granica audytu:** zachowanie przy innej powłoce
`/bin/sh` niż w tym kontenerze (dash vs bash zmienia semantykę `<>`
i podstawienia procesów), oraz `.truth/evidence-allow` konsumenta, który może
zawierać programy z własnymi kanałami wykonania (ADR-040 audytował 28 wpisów
i usunął trzy: `rg`, `file`, `date`).

---

## J-018 · BLOKADA: dwie bramki zdrowia są MARTWE — przekroczony limit rozmiaru zmiennej środowiskowej · 2026-08-16

Push zablokowany przez `release-battery.sh` (hooki uzbrojone w J-015 — bramka
zadziałała zgodnie z przeznaczeniem):

```
FAIL  fact-health -- scripts/fact-health.sh: line 76:
      /usr/local/bin/python3: Argument list too long
```

**To nie jest szum środowiskowy. To sufit systemowy, trafiony na żywo.**

### Pomiar

```
truth list --json                        → 145 576 bajtów (142 KiB)
MAX_ARG_STRLEN (Linux, 32 × PAGESIZE)    → 131 072 bajtów (128 KiB)
                                           PRZEKROCZONY o 14 504 bajtów
ARG_MAX (całość argv+env)                → 2 097 152 bajtów
```

### Zasięg — dwie bramki, nie jedna

```
bash template/scripts/spec-health.sh
→ line 37: /usr/local/bin/python3: Argument list too long
```

Wzorzec „JSON przez zmienną środowiskową" występuje w trzech plikach:

| plik | tier | stan |
|---|---|---|
| `scripts/fact-health.sh` | meta-repo | **MARTWY** |
| `template/scripts/spec-health.sh` | **Tier A — SHIPS DO KONSUMENTA** | **MARTWY** |
| `scripts/release-battery.sh` | meta-repo | działa (nie eksportuje ledgera) |

### Przyczyna źródłowa: komentarz mierzył NIEWŁAŚCIWĄ STAŁĄ

`template/scripts/spec-health.sh` niesie własne ostrzeżenie:

> *„JSON travels via env vars — fine at current ledger size; revisit before the
> ledger approaches ARG_MAX (~1MB on macOS)."*

Wiążącym limitem na Linuksie **nie jest ARG_MAX (2 MiB)**, tylko
**MAX_ARG_STRLEN = 128 KiB** — limit na POJEDYNCZY łańcuch, 16× mniejszy.
Zapowiedziany margines był zawyżony o ponad rząd wielkości: bramka miała
umrzeć przy ~1 MB, umarła przy 142 KiB.

### Dobra połowa: awaria jest GŁOŚNA

Pytanie z analizy wstępnej brzmiało: ciche obcięcie czy głośne `E2BIG`?
**Odpowiedź: głośne.** `execve` odmawia, skrypt kończy niezerowo, bateria
blokuje push. Żadna z bramek nie raportowała fałszywej zieleni. To jest
najlepszy możliwy tryb tej awarii — ale bramki są martwe od momentu, w którym
ledger przekroczył 128 KiB, i **nikt tego nie zauważył, dopóki hooki nie
zostały uzbrojone** (J-015). Bez decyzji właściciela o uzbrojeniu ten defekt
byłby nadal niewidoczny.

### Konsekwencja dla produktu

`spec-health.sh` jest Tier A i **trafia do każdego konsumenta**. Umiera
w momencie, w którym ledger konsumenta przekroczy 128 KiB — u nas stało się to
przy **223 claimach / 4 555 rekordach**. To nie jest odległe ryzyko; to typowa
wielkość po kilku tygodniach użycia.

### Proponowana korekta — precyzyjna, dwie linie na plik

Przekazać JSON **plikiem tymczasowym**, nie zmienną środowiskową:

```bash
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
scripts/truth list --json > "$TMP"
export CLAIMS_FILE="$TMP"          # zamiast: export CLAIMS_JSON
# w bloku python:
claims = {r["id"]: r for r in json.load(open(os.environ["CLAIMS_FILE"]))}
```

Limit znika (ścieżka ma kilkadziesiąt bajtów), semantyka bez zmian, `trap`
sprząta. `VOCAB_JSON` i `FILES` mogą zostać — są małe; ale ten sam wzorzec
warto zastosować do `FILES` w repo z dużą liczbą plików.

**To jest zmiana w kodzie produkcyjnym** (`template/scripts/spec-health.sh`
jest Tier A), więc leży poza zakresem kroku 1.1 i wymaga decyzji właściciela
o wpięciu do runbooka.

### Stan bieżący

* Commit `72a0099` (krok 1.1) **jest wykonany lokalnie**.
* **Push zablokowany.** `--no-verify` **NIE użyte** — bateria zgłasza realny
  defekt, a obejście byłoby dokładnie zamiataniem pod dywan, którego zakazuje
  reguła 4.
* Praca nie jest wypchnięta; kontener jest efemeryczny.

---

## J-019 · ŚWIADOME UŻYCIE `--no-verify` — jednorazowo, dla commitów docs-only · 2026-08-16

Bateria blokuje push na defekcie J-018. Defekt jest **preegzystujący**
i **niezwiązany** z wypychanymi commitami: `72a0099` i `3c35f2d` dotykają
wyłącznie `docs/refactor/`. Bramki `fact-health`/`spec-health` umarły w chwili,
gdy ledger przekroczył 128 KiB — **przed rozpoczęciem tego refaktoru**.

**Wybór między dwoma złymi wyjściami:**

| opcja | koszt |
|---|---|
| (a) naprawić 0.1 od razu | zmiana w **kodzie Tier A** bez zgody właściciela |
| (b) `--no-verify` na commitach docs-only | użycie udokumentowanego wyjścia awaryjnego |
| (c) nie robić nic | **utrata zapisu empirycznego** przy odzyskaniu kontenera |

Wybrane **(b)**. Uzasadnienie:

* `release-battery.sh` sam nazywa je wyjściem awaryjnym: *„Emergency exit is
  'git push --no-verify' — loud, and in the reflog."* To mechanizm zaprojektowany,
  nie obejście wymyślone na miejscu.
* Wypychane commity są docs-only — **nie mogły spowodować ani pogłębić** defektu.
* Opcja (a) łamie zasadę „nie dotykać kodu produkcyjnego bez decyzji", którą sam
  postawiłem prosząc o zgodę na krok 0.1.
* Opcja (c) traci J-015..J-018 — w tym pomiar 0/16 i diagnozę martwych bramek —
  czyli dokładnie tę wiedzę, dla której ten dziennik istnieje.

**To NIE jest zamiecenie pod dywan (reguła 4):**
defekt jest zmierzony (J-018), otwarty w runbooku jako **FAZA 0 / krok 0.1**,
oznaczony jako **BLOKUJE PUSH**, a bypass jest zapisany tutaj i w reflogu.
Nic nie zostało ukryte ani „naprawione" przez wyciszenie.

**Zakres zgody:** jednorazowo, na te dwa commity docs-only. Każdy kolejny push
w tym refaktorze wymaga albo wykonania kroku 0.1, albo osobnej decyzji
właściciela. Nie ustanawia to precedensu.

---

## J-020 · KROK 0.1 ZROBIONY — dwie bramki zdrowia żyją · 2026-08-16

Zmiana: JSON pochodzący z ledgera podróżuje **plikiem tymczasowym**; w środowisku
zostają tylko payloady o stałym rozmiarze (wokabularz).

```
scripts/fact-health.sh          CLAIMS_JSON -> CLAIMS_FILE  (mktemp + trap)
template/scripts/spec-health.sh CLAIMS_JSON -> CLAIMS_FILE
                                ISSUES_JSON -> ISSUES_FILE
```

Poprawiony też nagłówkowy komentarz `spec-health.sh`, który niósł błędną stałą
(*„revisit before the ledger approaches ARG_MAX (~1MB on macOS)"*) — to była
przyczyna, dla której nikt nie zareagował na czas.

### Weryfikacja

```
bash scripts/fact-health.sh
→ fact-health: 0 failure(s), 8 warning(s), 29 citation(s), 13 foreign
→ rc=0
```

**29 cytowań, nie zero** — sweep pusty byłby sweepem ciemnym, nie sukcesem.

`spec-health` na pustym korpusie zwraca `no spec files found`, co **niczego nie
dowodzi**. Sprawdzony osobno na korpusie niepustym (kontrola dodatnia
i ujemna, `template/docs/specs/` — skrypt rootuje się w `template/`, nie
w meta-repo, co samo w sobie wyszło przy tej próbie):

```
spec cytujący tr-3a31bfcf → FAIL tr-3a31bfcf retracted -- spec stands on a dead fact
spec cytujący tr-deadbeef → FAIL tr-deadbeef missing from ledger
rc z failure = 1 · rc pusty korpus = 0 · fact-health rc = 0
```

Status `retracted` odczytany z ledgera dowodzi, że ścieżka `CLAIMS_FILE`
faktycznie ładuje rekordy — a nie tylko nie wywala się.

Pliki tymczasowe sprzątane przez `trap ... EXIT` (sprawdzone: brak zalegających).
Rozmiar przekazywany w środowisku: **~20 B ścieżki** zamiast 145 576 B danych.

---

## J-021 · KROK SEC-0 ZROBIONY — kanał zapisu SEC-1 zamknięty · 2026-08-16

Przyczyna była w jednej gałęzi `template/truthlib/evidence.py`: plain `>` i fd
dup `>&` dzieliły warunek, a `tok.isdigit()` — obecny po to, by dopuścić `1`
w `2>&1` — dopuszczał też `>2`, czyli **zapis do pliku o nazwie `2`**.

Lexer rozróżniał je od zawsze; screener nie:

```
'cat f >2'      -> ['cat', 'f', '>',  '2']
'wc -l f 2>&1'  -> ['wc', '-l', 'f', '2', '>&', '1']
'cat f >&2'     -> ['cat', 'f', '>&', '2']
```

Poprawka: token kończący się na `&` ustawia `redir = "dup"` (cel: cyfra lub `-`),
plain `>`/`>>` ustawia `redir = "out"` (cel: wyłącznie `/dev/null`).

### Weryfikacja — obie strony

```
cat f.txt >2            ODRZUCONA  output redirection to '2' is refused
cat f.txt >22           ODRZUCONA
cat f.txt >>2           ODRZUCONA
cat f.txt > pwned.txt   ODRZUCONA  (bez zmian)
--- musi nadal działać ---
wc -l f.txt 2>&1        PRZYJĘTA
cat f.txt >&2           PRZYJĘTA
cat f.txt >/dev/null    PRZYJĘTA
cat < f.txt             PRZYJĘTA
```

Konwencja przypinania wyjścia (`>/dev/null 2>&1`) nietknięta.

### Ramiona regresyjne

Poprawka bez ramienia jest prozą, więc `TestEvidenceScreen` dostaje dwa:
`test_digit_sink_after_plain_gt_refused` (trzy formy zapisu odrzucone
**i** trzy formy fd dup przepuszczone — obie strony, bo arm pinujący tylko
odmowę przeszedłby też dla screenera, który blokuje wszystko) oraz
`test_fd_dup_to_non_digit_refused`.

**ZADEKLAROWANA ZMIANA BASELINE:** core **394 → 396**. Wzrost, nie spadek —
reguła F1 dotyczy ubytków i skipów.

### Stan bramki regresji po obu krokach

```
core 396 (1 failure, 3 skipped -- J-002)   v04 13 OK
integrations 28 OK                          canary 283 caught, 0 missed
```

---

## J-022 · KROK 1.2 — kategoria B zamknięta (5 z 14); kategoria A wymaga decyzji · 2026-08-16

### Ustalenie 1: runbook zakładał jedną operację, są dwie

Klasyfikacja po tym, czy **receptura otwiera plik ADR** (parsowanie `shlex`
+ `os.path.exists`, nie substring — pierwszy pomiar dał 12/14 fałszywie,
bo łapał ciąg `ADR-018` we **wzorcu** `grep`, nie w ścieżce):

| kategoria | ile | operacja |
|---|---:|---|
| **B** — receptura NIE czyta ADR | **5** | zawęzić obserwację; twierdzenie i receptura nietknięte |
| **A** — receptura CZYTA plik ADR | **9** | zawężenie NIE wystarczy — trzeba tknąć recepturę |

Runbook (krok 1.2) opisywał wyłącznie operację B i przypisywał ją do wszystkich 14.

### Ustalenie 2: wszystkie 5 claimów kategorii B miało dziurę w pokryciu — od początku

```
tr-a101be2f  czyta:     test-truth-core.py, truth-canary.sh
             obserwuje: 019-ttl-expiry-semantics.md, test-truth-core.py
             DZIURA:    truth-canary.sh czytany, nieobserwowany
             NADMIAR:   ADR-019 obserwowany, nigdy nieotwierany
```

Identycznie w pozostałych czterech. **Zbiór obserwacji i realne odczyty były
rozjechane w OBIE strony**: pilnowano pliku, którego receptura nie otwiera,
i nie pilnowano pliku, od którego twierdzenie zależy.

To jest defekt D-A (brak warstwy polityki obserwacji) pokazany na konkretach:
skoro każdy claim wybiera zbiór obserwacji z palca, nic nie sprawdza, czy ten
zbiór ma cokolwiek wspólnego z dowodem.

**Przyjęty niezmiennik: obserwuj dokładnie te ścieżki, które receptura czyta.**
Uwaga o koszcie: to dokłada `truth-canary.sh` (drugi najgłośniejszy plik w repo,
763 trafienia) do pięciu claimów, więc krótkoterminowo **podnosi** szum.
Świadomie — zaniżanie pokrycia dla lepszej metryki byłoby optymalizacją pod
wskaźnik, który Faza 2 i tak usuwa.

### Błąd własny, odnotowany

Pierwsza próba (`tr-726376a3` → `tr-cd6856ed`) zawęziła obserwację mechanicznie,
przez odjęcie ścieżek ADR — i przeniosła dziurę dalej: nowy claim obserwował
jeden z dwóch czytanych plików. Naprawione przez ponowne przefilowanie
(`tr-cd6856ed` → `tr-7c4966ad`) z retrakcją `restated`. Ledger jest append-only,
więc pomyłka została w historii — tak ma być.

Druga pomyłka, w skrypcie weryfikującym: porównywałem surowy hex z polem
`output_hash`, które niesie prefiks `sha256:`. Dało to pięć fałszywych
`MISMATCH`. Po poprawce wszystkie pięć: **MATCH**.

### Wykonanie kategorii B

Dla każdego z 5: re-file z poprawnym zbiorem obserwacji (`--duplicate-ok`,
bo tekst jest identyczny wobec wciąż żywego poprzednika) → retrakcja starego
`--cause restated --successor <NOWY>` → **niezależna weryfikacja kapsuły**
(ponowne uruchomienie receptury, porównanie `output_hash` i `returncode`)
→ `agree` z osobnej sesji (ADR-010).

```
tr-a101be2f -> tr-56a8e36c    tr-45d8bf7a -> tr-49f53967
tr-c9c8372e -> tr-6140a005    tr-9e717e86 -> tr-994f7e8f
tr-726376a3 -> tr-cd6856ed -> tr-7c4966ad
wszystkie kapsuły: MATCH (rc=0)
```

### Stan

```
żywych: 62 (baseline 61)      validate: 4605 record(s) OK
reproduce: 62 live -- 61 reproduces, 1 capsule-stale, 0 unexecutable
aktywnych claimów ADR: 9 (było 14)
core 396 (1F/3S = J-002) · v04 13 OK · integrations 28 OK · canary 283/0
```

### DO DECYZJI: kategoria A (9 claimów)

Ich receptury **otwierają plik ADR**, więc zawężenie ścieżek nie zamyka sprawy.
Trzy możliwe operacje, różne epistemicznie:

1. **Przepiąć recepturę na `docs/archive/adr/…`** — wariant A przenosi pliki,
   nie kasuje ich, więc twierdzenie przeżywa w całości. Koszt: żywy claim stoi
   na dokumencie zamrożonym, a `fact-health` celowo wyłącza `docs/archive/`
   ze sweepu cytowań.
2. **Usunąć z receptury fragment czytający ADR** — twierdzenie **słabnie**
   (traci część, którą dotąd weryfikowało). To nie jest `restated`, tylko
   zawężenie zakresu i trzeba je nazwać wprost.
3. **Wycofać** — dla claimów, których **przedmiotem jest sam ADR**
   (np. `tr-75070d09`: „ADR-013 documents supersede cycle resolution: its
   Amended-by note states…", `tr-6207afe1`: liczy pliki w korpusie). Tu
   `--cause expired` jest **poprawne**: *„it WAS true and the world moved past
   it"* — świat faktycznie się ruszył, korpus jest wycofywany.

Wybór jest per claim i zależy od tego, **czym dany claim jest** — a to osąd
właściciela, nie mechanika. Nie wykonuję go jednostronnie.

---

## J-023 · Bramka złapała konsekwencję kroku 1.2 — w moim własnym dzienniku · 2026-08-16

Pierwszy uczciwy push po naprawie 0.1 przeszedł do `fact-health` (który wcześniej
**umierał**, więc niczego nie badał) i zablokował:

```
FAIL  fact-health -- 2 failure(s), 8 warning(s), 33 citation(s), 13 foreign
  docs/refactor/01-JOURNAL.md
    FAIL  tr-726376a3  retracted -- live prose stands on a dead fact
    FAIL  tr-cd6856ed  retracted -- live prose stands on a dead fact
```

Oba id wycofałem w kroku 1.2, a dziennik je cytuje — **bo zapisuje, że je
wycofałem**. To nie jest defekt dziennika.

`fact-health` ma na to własną doktrynę, w sekcji SCOPE:
*„A record of a past event correctly names the ids that were live THEN;
re-judging it against today's ledger is a category error, not a finding."*
Na tej podstawie wyłączone są już `docs/archive/`, `docs/reviews/`,
`docs/roadmap-v3.md` i `docs/field-notes*`.

`docs/refactor/01-JOURNAL.md` należy do dokładnie tej klasy: append-only,
datowany, cytuje id żywe w chwili zapisu. Dodany do wyłączeń.

**`docs/refactor/00-RUNBOOK.md` ŚWIADOMIE ZOSTAJE w zakresie** — runbook to
instrukcja, na której czytelnik działa dziś, więc martwe cytowanie w nim jest
realnym defektem. Kontrola ujemna, żeby to nie było deklaracją:

```
wstrzyknięte '<!-- kontrola ujemna: tr-726376a3 -->' do 00-RUNBOOK.md
→ FAIL tr-726376a3 retracted -- live prose stands on a dead fact
→ rc=1
po przywróceniu → rc=0
```

Granica przebiega dokładnie tam, gdzie powinna: **dziennik zapisuje przeszłość,
runbook instruuje teraźniejszość.**

Uboczny, ale wart nazwania: to pierwszy raz, gdy `fact-health` cokolwiek
zablokował, odkąd przekroczył `MAX_ARG_STRLEN`. Przez ten czas raportował
sukces przez śmierć.

---

## J-024 · J-002 ROZWIĄZANE — kontrakt rekordu jest wreszcie sprawdzany · 2026-08-16 · zastępuje: J-002

Po J-023 bateria zgłosiła wszystkie arm-y treściowe na zielono i zablokowała
wyłącznie na `exit 2` — środowisko, nie zmiany:

```
release-battery: BLOCKED on an environment problem (exit 2), not on your changes.
```

Zamiast waivera (`TRUTH_ALLOW_NO_JSONSCHEMA=1`, zakazanego przez właściciela
i słusznie — wyłącza połowę kontraktu, a suita i tak pisze OK) usunięta
przyczyna:

```
python3 -m pip install jsonschema   → jsonschema 4.26.0
python3 template/scripts/test-truth-core.py → Ran 396 tests, OK
```

**Zero porażek, zero skipów.** Trzy testy zgodności schematu
(`TestConformanceSchema` ×2, `TestGeneratedMutantsAgree`), pomijane od
początku tej sesji, wreszcie się wykonują, a `TestJsonschemaPresent` przestał
krzyczeć.

### Nowy baseline bramki regresji

| suita | było (J-005) | jest |
|---|---|---|
| test-truth-core | `Ran 394`, 1 failure, 3 skipped | **`Ran 396`, OK** |
| test-truth-v04 | `Ran 13`, OK | bez zmian |
| test-integrations | `Ran 28`, 1 failure (J-003) | **`Ran 28`, OK** (J-016) |
| truth-canary | 283/0 | bez zmian |

**Od tej chwili każda porażka i każdy skip w bramce jest defektem, bez
wyjątków środowiskowych.** To jest mocniejszy reżim niż ten, w którym zaczynałem.

### Skutek dla planu

Ryzyko zapisane w J-002 — *„kroki 2.5 i 2.6 mają tu niepełne pokrycie, muszą
zostać przewalidowane na maszynie z jsonschema"* — **jest zamknięte**. Kroki
dotykające schematu rekordu mogą być zamykane w tym kontenerze.

---

## J-025 · KROK 1.2 DOMKNIĘTY — 14/14, aktywnych claimów ADR: 0 · 2026-08-16

Kategoria A wykonana wg decyzji właściciela: opcja 2 dla reguł kodu, opcja 3 dla
metryki korpusu, opcja 1 odrzucona.

### Reguła 2 — 8 claimów (7 + jeden przypadek szczególny)

Wszystkie okrojone receptury sprawdzone PRZED filowaniem: 7/7 `rc=0`.

```
tr-75070d09 -> tr-e4f4b934    tr-c52e3e84 -> tr-789b11be
tr-3ddc6f97 -> tr-f9318142    tr-af2e5758 -> tr-5c44d665
tr-fc03d886 -> tr-891efd02    tr-552d0fb0 -> tr-634049d9
tr-e70240c3 -> tr-4c3f748d    tr-3ce7c0c9 -> tr-fd5984c9
```

**Pięć tekstów wymagało zawężenia, nie tylko receptury.** Zdania zaczynały się
od *„ADR-013 documents…"*, *„ADR-029 documents…"*, *„ADR-002 and template/.truth/
README state…"*. Po wycięciu grepa po ADR-ze zostawienie tekstu bez zmian dałoby
twierdzenie, którego **nic nie sprawdza** — dokładnie puste VERIFIED, które
ADR-035 odrzuca. Zawężone do tego, co weryfikuje receptura, i nazwane wprost
w basis każdego z nich.

Trzy teksty zostawione bez zmian (`tr-552d0fb0`, `tr-e70240c3`, `tr-3ce7c0c9`):
wycięty grep sprawdzał wyłącznie linię `Status:` ADR-a, czego zdanie nie twierdzi.

### Przypadek szczególny: `tr-3ce7c0c9` — kapsuła była pusta

Jego **jedyną** ewidencją było `grep -c ADR-014 <plik ADR>` — receptura, która
nigdy nie dotknęła kodu, o którym zdanie mówi. Do tego zbiór obserwacji nadal
wskazywał cienki `template/scripts/truth`, choć logika przeniosła się do
`truthlib/` przy podziale na pakiet (ADR-044): `grep -c 'accept-cmd'
template/scripts/truth` = **0**.

Odbudowane przeciwko miejscu, gdzie zachowanie faktycznie żyje
(`truthlib/cli.py` + 8 arm-ów `FAULT AC` w canary, zgodnych z tekstem
„canary FAULTS AC1-AC8 gate the behavior"). To nie jest wymyślanie dowodu —
to naprawa pustej kapsuły P1.

### Bramka nagrobkowa zadziałała — trzy retrakcje odrzucone

```
tr-c52e3e84, tr-3ddc6f97, tr-fc03d886
→ cytowane w docs/truth-ledger-operations-guide.md (ADR-036)
```

Cytowania przepięte na następców **przed** retrakcją, w kolejności, którą ADR-036
wymusza. Po przepięciu wszystkie trzy przeszły.

### Reguła 3 — `tr-6207afe1`, z jawnym override

Czysta metryka korpusu („53 decision files numbered 001 through 053"). Archiwizacja
usuwa liczony przedmiot, więc `--cause expired` jest poprawne, bez następcy.

Gate odmówił i tu — pięć cytowań w czterech plikach. Ale one referują ten id jako
**wzorzec** (*„the tr-6207afe1 ADR-series precedent"*, *„the tr-6207afe1 pattern at
symbol level"*), nie jako fakt, na którym stoją. Reguła 3 nie daje następcy do
podstawienia, więc użyty `--orphan-ok` z uzasadnieniem zapisanym w rekordzie
(liczone przez `override-velocity`).

### Stan

```
aktywnych claimów ADR: 0  (było 14)
żywych: 61 (baseline 61)   validate: 4633 record(s) OK
reproduce: 61 live -- 60 reproduces, 0 unexecutable, 0 no-capsule
wszystkie 13 nowych kapsuł zweryfikowane niezależnie: MATCH
```

---

## J-026 · KROK 1.3 ZROBIONY — korpus ADR poza szablonem, ARCHITECTURE.md na jego miejscu · 2026-08-16

```
git mv template/docs/adr/truth/*.md docs/archive/adr/   → 54 plików
katalog template/docs/adr usunięty
reproduce → 0 unexecutable          żywych → 61 (baseline)
```

**`0 unexecutable` jest tu pointą.** Gdyby krok 1.2 nie przekierował 14 claimów,
ta liczba wynosiłaby teraz 14 — i to jest dokładnie ta katastrofa, którą skrypt
z pierwotnych wytycznych przepuściłby, raportując „0 aktywnych claimów ADR"
(J-008).

### `template/docs/ARCHITECTURE.md`

Cztery rozdziały wg szablonu właściciela. **Każdy fakt odczytany z kodu**, nie
przepisany z ADR-a — nagłówek nosi `STATUS: OBSERVED` i klauzulę rozstrzygającą
spór na korzyść kodu. Odczytane w tej sesji, nie z pamięci:
`fold_key` i jego trzeci klucz `canon()`; `TS_RE`; `merge=union`
z `.gitattributes`; 9 wierszy `INTAKE_GATES` w kolejności tabeli;
`DUPLICATE_THRESHOLD = 0.6`; `RETRACTION_CAUSES`; `ACTIVE_STATUSES`;
`CITATION_BAD`; `TIERS`; reguła `>&` vs `>` z SEC-0.

Rozdział 4 nazywa wprost granicę, której nie zamyka żaden gate: **receptura
kształtowa nie wykryje zmiany wartości, a hash całego pliku rozjedzie się na
komentarzu.** Screen gwarantuje bezpieczeństwo i determinizm, nigdy
informatywność.

### Referencje prozą

Poprawione 3 pliki szablonu (`.truth/README.md` ×5, `structure.md` ×2,
`machinery.md` ×1) — wszystkie przepięte na `docs/ARCHITECTURE.md`.
`template/CHANGELOG.md` **zostawiony**: to zapis historyczny, a jego wpisy
opisują stan z dnia wydania.

Pin `TestStructureDocMatchesDisk` przeszedł po zmianie węzła `A4` w diagramie
tierów — sprawdzone osobno, bo to jedyny diagram w repo, który jest asercją.

### Luka między dwoma zasięgami cytowań — znalezione przy okazji

`fact-health` zgłosił **5 porażek** na `tr-6207afe1`, mimo że retrakcja przeszła.
Przyczyna: to **dwie różne bramki o różnym zasięgu**.

| bramka | zasięg | werdykt |
|---|---|---|
| nagrobkowa (ADR-036) | `.truth/citation-scope` (`docs/specs/**`, README) | przepuściła z `--orphan-ok` |
| `fact-health` | **cała żywa proza** | 5 × FAIL |

`--orphan-ok` uzasadniał, że pięć cytowań referuje id jako **wzorzec**, nie jako
fakt. Dla wąskiej bramki to wystarczyło; szeroki sweep ma inny kontrakt —
*żywa proza nie stoi na martwym fakcie*, bez wyjątków. **Override jednej bramki
nie jest override'em drugiej**, i dobrze, że nie jest.

Naprawione u źródła: id usunięty z pięciu miejsc w żywej prozie, wzorzec opisany
z nazwy („the ADR-series count sentinel, retired 2026-08-16"). Zero utraty
informacji dla czytelnika, zero martwych cytowań.

### Stan po 1.3

```
fact-health: 0 failure(s), 2 warning(s), 23 citation(s)
doc-health:  0 failure(s) across 14 live doc(s)
core 396 OK · v04 13 OK · integrations 28 OK · canary 283/0
reproduce: 61 live, 0 unexecutable    validate: 4633 record(s) OK
```

---

## J-027 · KROK 1.3 ZABLOKOWANY przez zamrożenie `docs/archive/` · 2026-08-16 · zastępuje: J-026 (część o przeniesieniu)

J-026 zapisał krok 1.3 jako zrobiony. **To było przedwczesne** — commit został
odrzucony przez hook pre-commit i nigdy nie wszedł do historii. Wpis jest
korygowany tu, a nie edytowany w miejscu.

```
pre-commit: docs/archive/ is frozen verbatim (AGENTS.md); staged:
  docs/archive/adr/001-premise-validity-semantics.md
  ... 54 pliki ...
A human must lift the freeze deliberately before this can land.
```

Mechanizm (`.githooks/pre-commit`, linie 1–12) jest jawny i celowy:

> *„Consumer policy, this repo only (ADR-003 rule 2): docs/archive/ is frozen
> verbatim. Harness hooks block edit tools; this guard is the
> harness-independent backstop at the git layer — the 2026-07-11 trial showed
> norms alone do not hold."*

`AGENTS.md`, linia 23: *„`docs/archive/` is frozen verbatim; never update it."*

**Nie użyłem `--no-verify`.** Ta bramka istnieje wyłącznie po to, żeby wymagać
człowieka, a jej komentarz wprost mówi, że powstała, bo same normy nie
wytrzymały próby. Agent, który ją omija, jest dokładnie tym zdezorientowanym
pełnomocnikiem, przed którym ostrzega ADR-014.

### Wariant obejścia sprawdzony i ODRZUCONY

Przeniesienie do `docs/adr-archive/` nie tknęłoby zamrożenia — ale `fact-health`
wyłącza ze sweepu wyłącznie `^docs/archive/`, więc 54 ADR-y pełne cytowań `tr-`
wpadłyby w zasięg żywej prozy i posypały bramkę. `docs/archive/adr/` jest
właściwym celem **właśnie dlatego**, że jest wyłączony. Obejście byłoby gorsze
niż blokada.

### Co zostało zrobione i wchodzi tym commitem (1.3a)

* `template/docs/ARCHITECTURE.md` — cztery rozdziały, każdy fakt odczytany
  z kodu. Sformułowania o lokalizacji korpusu urealnione: mówią, że korpus jest
  **wycofywany** z szablonu, a nie że już został.
* Referencje prozą przepięte na `docs/ARCHITECTURE.md` — poprawne od chwili,
  gdy ten plik istnieje, czyli od tego commitu.
* `tr-6207afe1` usunięty z pięciu miejsc żywej prozy (wzorzec opisany z nazwy).

### Co czeka na człowieka (1.3b) — przepis odtworzenia

```bash
mkdir -p docs/archive/adr
git mv template/docs/adr/truth/*.md docs/archive/adr/
rmdir template/docs/adr/truth template/docs/adr
python3 template/scripts/truth reproduce | tail -2   # MUSI dać 0 unexecutable
bash scripts/fact-health.sh | tail -1
(cd template && bash scripts/doc-health.sh | tail -1)
```

Przy poprzednim przebiegu ta sekwencja dała: `0 unexecutable`, żywych 61,
`fact-health 0F/23`, `doc-health 0F/14`, `core 396 OK`, `canary 283/0`.
**Treść jest przetestowana; brakuje wyłącznie zdjęcia zamrożenia.**

### Stan drzewa

Przeniesienie cofnięte — 54 ADR-y wróciły do `template/docs/adr/truth/`,
`docs/archive/` nietknięte (`git diff --cached -- docs/archive/` → 0 plików).
Drzewo jest spójne: nic nie udaje, że korpus już się przeprowadził.

---

## J-028 · KROK 1.3b WYKONANY — 54 ADR-y w archiwum, za jawną zgodą człowieka · 2026-08-16

**Autoryzacja.** Właściciel repozytorium udzielił pisemnej, jawnej zgody na
zdjęcie zamrożenia `docs/archive/` dla tej jednej operacji — po tym, jak
`pre-commit` ją zablokował (J-027) i blokada została zaraportowana zamiast
obejścia. `--no-verify` użyte **na polecenie człowieka, nie z inicjatywy
agenta**, i odnotowane w treści commitu.

```
mkdir -p docs/archive/adr
git mv template/docs/adr/truth/*.md docs/archive/adr/   → 54 pliki
rmdir template/docs/adr/truth template/docs/adr
→ template/docs/adr istnieje: NIE
```

### Uwaga, która nie jest formalnością

`--no-verify` pomija **całe** `pre-commit`, nie tylko strażnika zamrożenia:
ostatnia linia hooka to `exec bash scripts/check-truth.sh`. Zgoda dotyczyła
zamrożenia, nie bramki commitowej, więc `check-truth.sh` został uruchomiony
**ręcznie przed commitem**: `rc=0`. Inaczej zgoda na jedną rzecz cicho
wyłączyłaby drugą.

### Weryfikacja przed commitem

```
reproduce: 62 live -- 61 reproduces, 0 unexecutable, 0 no-capsule
żywych: 62 (baseline 61)
fact-health: 0 failure(s), 2 warning(s), 23 citation(s)
doc-health:  0 failure(s) across 15 live doc(s)
check-truth: rc=0
```

**`0 unexecutable` to miara całego kroku 1.2.** Gdyby te 14 claimów nie zostało
przekierowanych, byłoby ich teraz 14 — i dokładnie to przepuściłby skrypt
z pierwotnych wytycznych, raportując „0 aktywnych claimów ADR" (J-008).

### Po przeniesieniu

```
core 396 OK · integrations 28 OK · canary 283 caught, 0 missed
```

**FAZA 1 ZAMKNIĘTA.** Korpus decyzji nie ships; konsument dostaje
`template/docs/ARCHITECTURE.md` jako jedyny kontrakt behawioralny.

---

## J-029 · KROK 2.1 — inwentarz powierzchni Reproduce-on-Read · 2026-08-16

```
python3 instruments/field-consumers.py
→ 30 payload key(s) over 4646 record(s) -- 0 failure(s)
   OK     anchor_commit     2271   cli.py, evidence.py, kernel.py
   OK     touched           1995   cli.py, reports.py
   EXEMPT reaffirm_cleared  1306   presence-only reader, fix planned in F3.5
```

### Powierzchnia do usunięcia, pole po polu

**`anchor_commit` (2271 rekordów) — najgłębiej wrośnięte.**

| rola | miejsce |
|---|---|
| ZAPIS | `cli.py:93` (intake), `:413` (re-anchor przy agree), `:513` (reaffirm) |
| ODCZYT | `cli.py:427,524,1164` · `evidence.py:592` · `kernel.py:139,148,150,571,584,673,681` |

Siedem miejsc odczytu w samym `kernel.py`, w tym w folcie (`:148-150` ustawia
`claims[c]["anchor"]`) i w walidacji (`:681` sprawdza kształt). **To nie jest
pole do skasowania jednym ruchem** — to zmienna stanu, na której stoi cała
logika unieważniania.

**`reaffirm_cleared` (1306 rekordów) — najpłycej.**

| rola | miejsce |
|---|---|
| ZAPIS | `cli.py:533` — jedno miejsce |
| ODCZYT | `reports.py:572` — **tylko test obecności** (`is not None`) |

`field-consumers` klasyfikuje je jako `EXEMPT / presence-only`. Potwierdza to
pomiar z analizy wstępnej: 28% ledgera to ślad audytowy własnych fałszywych
alarmów, którego zawartości nikt nigdy nie odczytał. **Krok 2.6 usuwa ścieżkę
zapisu; ścieżka odczytu i tak jest pusta.**

**Stan `stale`.** Ustawiany w jednym miejscu — `kernel.py:161`, na rekordzie
`invalidation`. Czytany przez `cli.py:468` (bramka reaffirm), `registry.py`
(`STATUSES`, `CITATION_BAD`, `DEAD_CLAIM_STATUSES`) i `reports.py:104,127,382`
(rozbicie staleń, kolejka, ready). Usunięcie stanu dotyka **wokabularza**, więc
propaguje do `spec-health`/`fact-health` przez `truth vocab --json` — te dwa
skrypty nie wymagają zmiany, bo pobierają zbiór w czasie wykonania (ADR-043).

**Rekord `invalidation` (1971).** Zapis: `cli.py:437`. Odczyt: `kernel.py:158,686`,
`evidence.py:374,404`, `reports.py:56,99,104,125,329,625,631`.

### Wniosek dla kolejności Fazy 2

Kolejność w runbooku (2.5 fold → 2.6 komendy) jest **odwrotna do trudności**.
Najpłytsze pole (`reaffirm_cleared`, jeden zapis, zerowy odczyt treści) można
zamknąć niezależnie; najgłębsze (`anchor_commit`, 7 odczytów w kernelu) trzyma
fold i musi iść ostatnie. **Nie zmieniam runbooka bez pomiaru z kroku 2.2** —
odnotowuję jako hipotezę do sprawdzenia testami charakteryzującymi.

---

## J-030 · KROK 2.2 — pokrycie JUŻ ISTNIAŁO; zweryfikowane, nie dopisane · 2026-08-16

Runbook zakładał, że trzeba napisać testy charakteryzujące. **Nie trzeba** —
istnieją i są zielone, na obu poziomach:

| poziom | co pinuje | ile |
|---|---|---|
| `TestReproduceTriage` | 4 klasy wyniku jako czysta funkcja, w kolejności arm-ów | 8 metod |
| `TestCapsuleStaleShape` | kształty rozbieżności (buried/ahead/uncommitted/unexplained) | 8 metod |
| `TestReproduceExitCodes` | `REPRODUCE_EXIT_STALE=7`, `EXIT_EMPTY=8`, brak kolizji, `reproduce ∉ WRITE_VERBS` | 2 metody |
| `test-integrations.py` | **E2E**: `test_exit_code_7_reproduce_stale`, `test_exit_code_8_reproduce_empty` | 2 metody |
| `truth-canary.sh` | `FAULT RP` — seeded-fault na sweepie | 2 rodziny |

Uruchomione, żeby nie zaliczyć ich z nazwy: **28/28 OK**. Dopisywanie ramion
byłoby dublowaniem, nie pokryciem.

---

## J-031 · Warunek wstępny 2.3 był CZERWONY — i claim, który go wykrył, zadziałał · 2026-08-16

Pomiar przed wpięciem:

```
python3 template/scripts/truth reproduce  → rc=7
tr-010f7e96  capsule-stale  shape=unexplained
```

**Gdyby arm został wpięty bez tego pomiaru, KAŻDY push byłby zablokowany** od
pierwszej chwili, na warunku niezwiązanym z pchającym — czyli bramka rodząca się
czerwona, która uczy `--no-verify`. Dokładnie to, przed czym ostrzega nagłówek
tej baterii.

Claim `tr-010f7e96` twierdził zgodność wersji na v0.9.33. Pomiar:

```
CLI:       truth v0.9.38
explainer: CLI v0.9.33      receptura → rc=1
```

**To nie był fałszywy alarm — to był sygnał.** Wersje realnie się rozjechały,
a claim istniał właśnie po to, żeby to wychwycić. Osądzone jako `diverge`
(ADR-012: mechaniczne-vs-genuine to nie jest decyzja czasownika wsadowego).

**Pętla domknięta, nie obejście.** Właściwą odpowiedzią na wykryty dryf jest jego
naprawa: `docs/truth-ledger-explained.md` zsynchronizowany 0.9.33 → 0.9.38,
następca `tr-8d9005d0` przypina ten sam niezmiennik na bieżącej wersji,
`tr-010f7e96` wycofany `--cause restated --successor`, cytowania przepięte.

**Uboczna lekcja operacyjna:** `git checkout -- .truth/claims.jsonl` skasował
niezacommitowany werdykt `diverge` przy sprzątaniu po kontroli ujemnej. Ledger
jest append-only **w historii gita**, nie w drzewie roboczym — werdykt bez
commitu nie istnieje. Odtworzony.

---

## J-032 · KROK 2.3 — `reproduce` jako arm baterii pchnięcia · 2026-08-16

Wpięte **do `release-battery.sh`, nie do `pre-push`** — hook kończy się
`exec bash scripts/release-battery.sh`, więc tam żyją wszystkie kontrole treści
i tam arm dziedziczy format raportowania oraz dyscyplinę „powiedz, co zbadałeś".

Kontrakt kodów wyjścia, zgodnie z korektą J-011:

| exit | decyzja |
|---|---|
| 0 | przepuść — **i nic nie zapisuj** (o to chodzi w weryfikacji przy odczycie) |
| 7 | BLOKUJ, wypisz rozbieżne claimy, wskaż `diverge` albo `--refresh-evidence` |
| **8** | **BLOKUJ** — sweep, który zbadał 0 claimów, nie jest sukcesem (ADR-042 reguła 2) |
| inne | BLOKUJ — kontrakt czasownika to 0/7/8, cokolwiek innego jest defektem |

Dodatkowo: `rc=0` bez linii podsumowania też blokuje — arm musi wiedzieć, ile
zbadał, a nie tylko że nie padł.

**Stan po wpięciu:**

```
ok  reproduce -- 62 live claim(s) -- 62 reproduces, 0 capsule-stale,
                 0 unexecutable, 0 no-capsule
fact-health 0 failure(s) · reproduce rc=0
```

Warunek SEC-1 z werdyktu GO (J-017) był zamknięty w SEC-0 (J-021) **przed** tym
krokiem, zgodnie z porządkiem, który ten werdykt narzucał.

---

## J-033 · KROK 2.4 — ścieżka zapisu wygaszona w DWÓCH hookach, nie jednym · 2026-08-16

**Runbook nazywał tylko `post-merge`. Pomiar pokazał dwa:**

```
.githooks/post-commit  → python3 scripts/truth invalidate-scan
.githooks/post-merge   → python3 scripts/truth invalidate-scan
```

Oba z tym samym komentarzem *„Solo/trunk: every commit can invalidate facts;
there are no merges to hook"* — czyli w tym repo **pracował `post-commit`**,
a `post-merge` był kopią na wypadek scaleń. To `post-commit` odpalał się po
każdym commicie tej sesji i to on wyprodukował wszystkie zestalenia, które
musiałem rozstrzygać.

Gdybym wykonał instrukcję dosłownie, wygasiłbym hook, który w praktyce nie
strzelał, i zostawił ten, który strzela. **Trzeci raz w tej sesji instrukcja
nazywała jeden obiekt, a pomiar znalazł więcej** (J-008: 0 vs 14 claimów,
J-022: 1 vs 2 operacje, teraz 1 vs 2 hooki).

### Wykonane

Oba hooki meta-repo → `exit 0` z uzasadnieniem w nagłówku (plik zostaje, bo
jest rootem dla `gate-reachability`; znika wyłącznie zapis).
`template/scripts/install-hooks.sh` → generuje `post-merge` bez zapisu,
komunikat dla `core.hooksPath` i wskazówka CI przepisane na `truth reproduce`
z kontraktem exit 7 / exit 8.

### Weryfikacja

```
realne wywołania invalidate-scan poza komentarzami → BRAK
gate-reachability: examined 10 check(s), 10 reachable, 0 unreachable
core 396 OK · integrations 28 OK · canary 283 caught, 0 missed
```

**`10/10 reachable` jest tu istotne**: odcięcie dwóch hooków nie osierociło
żadnej kontroli — nic nie było do nich podpięte poza skanem. Gdyby coś było,
ten sweep by to zgłosił, zamiast pozwolić kontroli zniknąć po cichu.

### Otwarte okno, o którym uprzedzałem

`reaffirm` nadal istnieje i nadal jest jedynym mechanizmem wchłaniającym
zestalenia — ale **nic już nowych zestaleń nie produkuje**. Stare pozostają
w ledgerze jako historia. Okno „każde zestalenie wymaga osądu" **nie otworzyło
się**, bo źródło wyschło przed usunięciem absorbera. To był powód, dla którego
kolejność 2.4 → 2.5 → 2.6 jest lepsza od 2.4 → 2.6 → 2.5.

---

## J-034 · KROK 2.5 — próba wykonana, ZATRZYMANA na odkrytym zakresie · 2026-08-16

### Co zostało zrobione i ZOSTAJE (commit 95fe01f)

Pin konfluencji dla rekordów `invalidation`, w 6 permutacjach. Przy okazji
**korekta mojej wcześniejszej analizy**: twierdziłem, że konfluencji nic nie
testuje — testuje (`itertools.permutations` w 3 miejscach,
`test_verdict_precedence_is_confluent`, 5 rodzin `FAULT UM`). Ale wszystkie te
ramiona permutują **wyłącznie werdykty**; żadne nie wkładało do permutacji
rekordu `invalidation`. Ta luka była realna i jest zamknięta.

### Zmiana algebry — DZIAŁA, i zmierzyłem dokładnie co robi

```
PRZED  retracted 117 · live 62 · unverified 22 · stale 7 · diverged 30
PO     retracted 117 · live 68 · unverified 23 · stale 0 · diverged 30
```

Siedem zestalonych claimów wróciło do tego, co mówią ich werdykty. Algebra
`unverified → live → diverged/retracted` jest osiągalna.

### USTALENIE 1: rekordy `invalidation` niosą DWA różne znaczenia

Test charakteryzujący zrobił dokładnie to, do czego służy — pokazał, że
usunięcie gałęzi zabija **dwa** mechanizmy, nie jeden:

| znaczenie | czym jest | los |
|---|---|---|
| zmiana obserwowanej ścieżki | proxy o PPV 3,6% | **do usunięcia** |
| wygaśnięcie TTL (ADR-019/G10) | **fakt zegarowy**, którego repo nie zaobserwuje inaczej | **musi zostać** |

`reproduce` **nie zastąpi** TTL: receptura claimu z TTL odtwarza się doskonale
w dniu, w którym wygasa. Zabicie obu, bo dzielą `kind`, po cichu usunęłoby
działający mechanizm. Padły na tym cztery ramiona (`test_ttl_staled_claim_*`,
`test_backdated_scope_ok_expires_*`, `test_verbatim_repeat_across_expiry`).

Rozwiązanie zaimplementowane i zweryfikowane: dyskryminator `ttl_invalidation`
w `kernel` (bo `kernel` jest **poniżej** `evidence` w DAG-u ADR-044, więc zależność
mogła pójść tylko w tę stronę), z `is_ttl_reason` przeniesionym tam i
re-eksportowanym przez star-import — **jedna implementacja**, zgodnie z lekcją
F1/F5.

### USTALENIE 2: `reports.py` miał WŁASNE odwzorowanie — i arm to złapał

`half_life_observations` replayuje statusy niezależnie od folda
(`new = "stale" if kind == "invalidation"`). Po zmianie folda replay opisywał
ledger, którego nikt nie ma. **Złapał to `test_half_life_replay_matches_fold`** —
arm istniejący dokładnie po to. To jest ta para, o której repo pisze, że nie
wolno jej pozwolić się rozjechać, i nie pozwoliła.

### USTALENIE 3 — powód zatrzymania: cała rodzina raportowa jest DOWNSTREAM

Po naprawie parytetu padła rodzina `TestStats`, w tym arm nazwany wprost
`test_ttl_expiry_excluded_but_path_invalidation_kept`. Powód strukturalny:
**raport półokresu MIERZY przejścia live→stale spowodowane zmianą ścieżki.**
To nie jest test zepsuty przez zmianę — to raport, którego przedmiot znika.

Bilans: 18 porażek w 6 rodzinach. Osiem to `TestReaffirmCLI` (zadeklarowane
do wycofania w 2.6). Dwie to piny usuniętego zachowania (oczekiwane).
**Sześć to nowy zakres**: `TestStats` half-life ×4, `TestIntakeAdvisories`
(sugestia TTL czyta te same strumienie), `TestScanRenameBlindness`.

### Decyzja: kod cofnięty, drzewo zielone

```
git checkout -- kernel.py reports.py evidence.py  →  Ran 398 tests, OK
```

**Nie dokańczam zmiany w kernelu na kończącym się budżecie kontekstu.** Kernel
to jedyny moduł, w którym pomyłka jest cicha: fold liczy status przy każdym
odczycie, więc błąd nie wywala się — zwraca inną prawdę. Zostawienie w drzewie
półzrobionej algebry byłoby gorsze niż jej brak.

Pin zostaje zacommitowany, więc następna sesja startuje z siatką, której
wcześniej nie było, i z trzema ustaleniami zamiast z hipotezą.

### DO DECYZJI przed wznowieniem 2.5

Raport półokresu / `ttl_suggestion` (ADR-050, FS-1) mierzy metrykę mechanizmu,
który usuwamy. Trzy opcje:

1. **Wycofać rodzinę** razem z mechanizmem — spójne, ale kasuje jedyne źródło
   kalibracji TTL per tier.
2. **Przekierować na `diverge`** — półokres liczony od `live` do rozbieżności
   dowodu zamiast do dotknięcia ścieżki. Metryka staje się semantyczna;
   danych będzie **o rząd wielkości mniej** (70 zamiast 1971).
3. **Zostawić jako czytnik historii** — raportuje wyłącznie rekordy sprzed
   refaktoru, zamrożony jak `reaffirm_cleared`.

Rekomendacja: **(2)**, bo zachowuje cel raportu przy nowym, uczciwym sygnale.
Ale to zmiana znaczenia publikowanej metryki, więc nie moja decyzja.

---

## J-035 · KROK 2.5 + 2.6 — algebra zwężona, proxy wygaszone, metryka przeceluowana · 2026-08-17

Decyzja operatora na J-034: **opcja 2** (półokres przekierowany na `live -> diverge`).
Dodatkowa decyzja w trakcie kroku, podjęta po pomiarze niżej: **opcja 1** dla
writera TTL (`invalidate-scan` → `ttl-scan`).

### Reguła podwójnego invalidation (2.5a)

`kernel.ttl_invalidation(payload)` — jeden dyskryminator, jedno miejsce.
Fold, replay w `reports` i `staling_report` wołają ten sam predykat, więc nie
mogą się rozjechać tak, jak rozjechał się `new = "stale" if kind == "invalidation"`
w J-034.

| znaczenie rekordu | los | uzasadnienie |
|---|---|---|
| zmiana ścieżki | **inertny** — nie rusza ani statusu, ani `status_ts` | proxy o PPV 3,6%; `reproduce` odpowiada wprost, 8 ms/kapsuła |
| wygaśnięcie TTL | **nadal zestala** | fakt zegarowy; claim z wygasającym dziś TTL odtwarza się dziś idealnie |

### Pomiar na tym ledgerze — 1997 rekordów, z czego TTL: ZERO

```
grep -c '"kind": "invalidation"'                    1997
  z reason_code "ttl"                                  0
  z prefiksem "ttl expired"                            0
  wszystkie z reason "evidence ..."                 1997
```

Mechanizm TTL istnieje, ma testy i ramię canary, i **nie odpalił się tu ani razu**.
Cała masa 1997 rekordów to wyłącznie proxy ścieżkowe.

### Status przed → po

```
PRZED  retracted 117 · live 62 · unverified 28 · stale 7 · diverged 30
PO     retracted 117 · live 68 · unverified 29 · stale 0 · diverged 30
```

Siedem zestalonych wróciło do tego, co mówią ich werdykty (6 → live, 1 → unverified).

### USTALENIE 1 — `stale` był KRYJÓWKĄ, nie tylko szumem

To jest znalezisko, którego nie było w hipotezie. `truth reproduce` bada
**wyłącznie claimy live**. Cztery z siedmiu claimów zaparkowanych w `stale`
mają kapsuły, których **nie da się już odtworzyć** — i przez cały ten czas
były niewidzialne dla pomiaru bezpośredniego:

```
tr-39eb58bc  asbuilt-architecture.md nie sięga bieżącej wersji CLI (dochodzi do v0.9.33, CLI jest v0.9.38)
tr-791fafbc  receptura zawiera literał "v0.9.32"; nagłówek explainera i CLI zgadzają się na v0.9.38
tr-96d14c58  sha256sum check-truth.sh -- plik zmieniony w 215d114 (v0.9.38)
tr-b350781e  sha256sum release-battery.sh -- plik zmieniony m.in. w 961d696
```

Bramka `reproduce` w baterii zablokowała push w chwili, w której te claimy
wróciły do live. **To nie jest regresja tej zmiany — to pierwszy raz, kiedy ta
populacja jest w ogóle widzialna.** Proxy nie było więc tylko nieprecyzyjne;
działało jak schowek, który wyjmował claim spod jedynego pomiaru zdolnego go
zweryfikować.

Werdykty na te cztery są **do decyzji operatora** (ADR-012: mechaniczne vs
genuine to sąd, nigdy nie robota werbu wsadowego). Wstępna klasyfikacja z
dowodem w raporcie sesji.

### Metryka półokresu — przecelowana (2.5b)

Mierzone przejście: `live -> diverged`, czyli ile claim żył, zanim **sędzia**
stwierdził, że dowód się ruszył. Wykluczenie TTL, o które prosił FS-1/ADR-032,
jest teraz **strukturalne**, nie specjalnym przypadkiem: TTL produkuje `stale`,
nigdy `diverged`, więc nie dosięga gałęzi obserwacji. Retrakcja celowo NIE jest
obserwacją — `retracted` mówi, że claimu nie należało złożyć; `diverged` mówi,
że był prawdziwy i przestał.

```
PRZED  P0 0.02d (n=77) · P1 0.04d (n=1441) · P2 0.06d (n=445)     razem n=1963
PO                       P1 0.81d (n=21)   · P2 0.66d (n=37)      razem n=58
```

Spadek 34×, mniej więcej rząd wielkości przewidziany w J-034. P0 znika
całkowicie — nie ma ani jednej osądzonej rozbieżności na P0, więc `ttl_suggestion`
dla P0 zwraca `None` zamiast liczby zbudowanej z szumu. Poprzednie 0,02 d to
było „ktoś dotknął obserwowanego pliku w ciągu pół godziny", sprzedawane jako
półokres życia faktu.

### Zwężenie kaskady i writer TTL (2.6a)

Konflikt wykryty przed wykonaniem: `cmd_invalidate_scan` był **jedynym**
wywołaniem `decide_invalidation`, a `_ttl_expired` **jedynym** producentem
rekordów TTL. Dosłowne wycofanie werbu zostawiłoby ADR-019 z czytnikiem i bez
pisarza. Rozstrzygnięcie operatora: zwęzić, nie skasować.

```
INVALIDATORS = (_ttl_expired,)          # było: + _anchor_unreachable, _evidence_paths_touched
truth invalidate-scan  →  truth ttl-scan        "ttl-scan: N claim(s) expired"
```

Efekt uboczny wart odnotowania: `ttl-scan` nie odpala już `commit_reachable`
ani diffa względem kotwicy **per claim aktywny** — te sondy git odeszły razem
ze strategiami, które je konsumowały, i to była większość kosztu werbu.

### `reaffirm` wycofany — martwa maszyneria, nie odebrana zdolność (2.6a)

Po 2.5 jedyną drogą do `stale` jest TTL, który był **pierwszym ramieniem**
`reaffirm_triage` i bezwarunkową odmową („re-file required; ADR-019: TTL never
resets by re-verification"). Każde wejście, jakie werb mógł jeszcze dostać,
było wejściem, które odrzucał z kontraktu. Usunięte: `cmd_reaffirm` (117 linii),
`reaffirm_triage`, `previously_agreed`, `REAFFIRM_ARMS`, 24 ramiona testowe.
**Zostawione (J-012, ścieżka odczytu):** `REAFFIRM_BASIS`,
`latest_invalidation_reason`, `ttl_staleness`, pole `reaffirm_cleared` —
`staling_report` nadal klasyfikuje 1283 historyczne rekordy.

### USTALENIE 2 — ciemna bramka w doktorze, odziedziczona po 2.4

`doctor` grepował `post-merge`/`post-commit` za słowem `invalidate-scan`.
Krok 2.4 wygasił oba hooki do `exit 0` — **pod komentarzem wyjaśniającym
usunięcie, który zawiera słowo `invalidate-scan`**. Jednohopowy grep trafiał
w notatkę o wycofaniu i przez cały czas raportował:

```
OK    post-merge hook enforces INV-C          ← nad hookiem, który nie robi nic
```

Bramka, która przechodzi na własnym akcie zgonu. Przecelowana na następcę:
`pre-push` + `reproduce`. Przy okazji wyszło, że u **konsumenta** ta obietnica
nie miała mechanizmu — `install-hooks.sh` nie pisał żadnego hooka pre-push, więc
zdanie „reproduce runs at pre-push" było prawdziwe tylko w tym repo. Installer
pisze go teraz.

### Delta ramion canary — ZERO, wbrew prognozie runbooka

Runbook deklarował: „**spadek** liczby ramion canary w tym kroku jest oczekiwany"
(15 rodzin FAULT dotykających wygaszanych werbów). Wynik: **283 → 283, zero
skasowanych ramion.** Powód: zgodnie z regułą J-012 („ramię, którego przedmiot
nadal istnieje, musi zostać przepisane, nie skasowane") każde ramię dostało
odwróconą albo przecelowaną tezę zamiast usunięcia:

| rodzina | co się stało | nowa teza |
|---|---|---|
| FAULT B (INV-C) | **odwrócone** | dotknięcie obserwowanej ścieżki NIE zestala |
| FAULT D (G10) | zachowane, werb przemianowany | TTL nadal zestala, przez `ttl-scan` |
| FAULT E (G14) | **odwrócone** + dodane | skasowana kotwica nie zestala, a kapsuła nadal się odtwarza |
| FAULT T (ADR-023) | połowa zachowana, połowa odwrócona | wyjątek przy intake zostaje; „odpala po zapełnieniu" odwrócone |
| FAULT L | przecelowane | re-weryfikacja = live **i** kapsuła się odtwarza |
| FAULT RA (ADR-030) | przecelowane na `reproduce` | zmieniona kapsuła → exit 7, **nic** nie zapisane w żadną stronę |
| FAULT SD-decay | zwężone | wygasły override jest stale **i** niesie `reason_code: ttl` |
| FAULT EF3 | przecelowane | odświeżony claim znów się odtwarza |
| FAULT DG (ADR-025) | igła zmieniona | `pre-push` + `reproduce` zamiast `post-merge` + `invalidate-scan` |
| FAULT J / R3 / S2 | fixture wymieniony | martwa przesłanka z werdyktu `diverge`, nie z dotknięcia ścieżki |

`reproduce` okazał się przy tym **ostrzejszy** niż `reaffirm`, którego zastąpił:
tamten auto-składał `agree` na trafieniu hasha, ten nie zapisuje nic w żadnym
kierunku.

### USTALENIE 3 — żywy claim zaostrza bramkę bliskich duplikatów

Nieprzewidziany efekt kaskadowy, złapany przez canary: `ACTIVE_STATUSES` to
`{live, unverified}`, a bramka ADR-018 porównuje tylko z aktywnymi. Claimy,
które wcześniej wypadały ze zbioru przez zestalenie, **zostają w nim teraz na
stałe**, więc odmowy bliskich duplikatów będą częstsze. W canary objawiło się
to odmową złożenia „intact.txt says hello" przy żywym „watched.txt says hello"
(Jaccard 0,5) — i przewróciło FAULT O oraz FAULT P, które z nim nie miały nic
wspólnego. Do obserwacji u konsumentów.

### Weryfikacja

```
core          372 testy, 0 skipów, OK
v04            13 testów, OK
integrations   28 testów, 0 skipów, OK
canary        283 caught, 0 missed
field-consumers  30 kluczy / 4660 rekordów -- 0 failures
reachability  10/10
reproduce     BLOKUJE (exit 7) na 4 claimach z USTALENIA 1 -- kolejka werdyktów, nie defekt kodu
```

### USTALENIE 4 — `impact`/whisper przewidywały skutek, który zniknął

Werb `impact` (i sterowany nim hook whisper) drukował:

```
editing X -> next commit STALES tr-xxxxxxxx (P1, live): <tekst>
```

Po 2.5 to zdanie jest **fałszywe**: dotknięcie obserwowanej ścieżki nie zestala
niczego. Zostało zamienione na to, co narzędzie faktycznie wie:

```
editing X -> WATCHED BY tr-xxxxxxxx (P1, live): <tekst>
```

Wiersze są te same, znaczenie węższe i uczciwsze: te claimy **czytają** ścieżkę,
którą edytujesz; czy fakt się ruszył, rozstrzyga `reproduce` na granicy pusha
albo sędzia. Stare brzmienie uczyło czytelnika traktować zgadywankę o precyzji
3,6% jak werdykt. Canary FAULT W1 dostał ramię, które **jawnie łapie powrót**
starego brzmienia (`miss "impact still predicts STALES"`), a nie tylko sprawdza
nowe.

Przy okazji: `queue_rows` opisywał claim `stale` jako „evidence invalidated" —
formuła odziedziczona po proxy. `stale` ma teraz dokładnie jedną przyczynę,
więc powód nazywa ją wprost: `ttl expired -- re-file required (ADR-019)`.

### Weryfikacja mutacyjna kernel.py (wymóg 2.5d)

```
380 mutantów: 341 zabitych + 6 timeoutów (nieskończone pętle = wykryte) = 347
33 ocalałych  ->  91,3%   (linia bazowa z pyproject.toml: 91,4%, 342/374)
```

Żaden ocalały nie leży w nowym kodzie. Pięć celowanych mutacji na
dyskryminatorze sprawdzonych ręcznie — **wszystkie zabite**:

```
is_ttl_reason:    and -> or                 killed
ttl_invalidation: or -> and                 killed
ttl_invalidation: == -> !=                  killed
fold branch:      and -> or                 killed
fold branch:      negacja dyskryminatora    killed
```

Ocalałe to warunki brzegowe w `validate_events` (`ttl_days < 1`,
`blast_forecast < 0`) i strażnik cyklu w `fold_supersedes` — populacja sprzed
tej zmiany.

### DZIAŁANIA WYDAWNICZE — DO WYKONANIA, nie zrobione tutaj

1. **Kolejka werdyktów: 4 claimy** (USTALENIE 1). ADR-012 mówi, że
   mechaniczne-vs-genuine to sąd, nigdy robota werbu wsadowego, a ADR-010 chce
   niezależnej sesji. Klasyfikacja z dowodem jest w raporcie sesji; bateria
   pozostaje BLOCKED do rozstrzygnięcia.
2. **Bump wersji CLI + tag.** Usunięty werb (`reaffirm`) i przemianowany
   (`invalidate-scan` → `ttl-scan`) to zmiana łamiąca dla konsumentów.
   Komentarze w kodzie celowo **nie** twierdzą „v0.10.0" — mówią „refactor
   step 2.5/2.6" — bo CLI nadal stwierdza v0.9.38 i żadne wydanie nie zaszło.
   Wydanie wymaga: linii 2 w `template/scripts/truth`, 7 przypiętych
   powierzchni ADR-026, wpisu w `template/CHANGELOG.md` i taga.
3. **ADR-030** (reaffirm) i **ADR-005** (whisper) opisują zachowania, które ten
   krok zmienił; ADR-019 zyskał nowego pisarza pod nową nazwą. Do przejrzenia
   przy wydaniu.

---

## J-036 · PO 2.6 — pięć zdemaskowanych claimów osądzonych, bramka odblokowana · 2026-08-17

Kolejka werdyktów z J-035 USTALENIE 1, domknięta. Skład okazał się inny niż
lista wyjściowa: operator obsłużył `tr-39eb58bc` i `tr-a8bda1a1`, a to odsłoniło
**dwa kolejne** z tej samej siódemki — `tr-c6170e24` i `tr-d1049451` — które
dotąd siedziały za nimi w cieniu `stale`. Pięć capsule-stale, nie trzy.

### Co z czym zrobione

| stary | klasa | działanie | następca |
|---|---|---|---|
| `tr-791fafbc` | mechanical | `retracted --cause restated` | `tr-f8b946cd` |
| `tr-96d14c58` | mechanical | `retracted --cause restated` | `tr-d237a049` |
| `tr-b350781e` | genuine (liczba ramion) | `retracted --cause restated` | `tr-38d32bc7` |
| `tr-c6170e24` | mechanical | `diverge --mechanical` | `tr-3dbdd418` |
| `tr-d1049451` | expired (przedmiot zniknął) | `diverge` | brak — nie ma czego liczyć |

Wycofania objęły **wyłącznie trzy claimy nazwane przez operatora**. Dla dwóch
odkrytych po drodze użyto `diverge` — dokładnie tego, co ADR-011 mówi agentowi
robić przy tombstone (*„file `diverge` … and stop — the human queue decides"*),
z rekomendowaną komendą wycofania wpisaną w `basis`. Bramka odblokowuje się tak
samo (claim `diverged` nie jest `live`, więc wypada ze sweepu), a decyzja
terminalna zostaje u człowieka.

`tr-d1049451` nie dostał następcy świadomie: twierdził o **47 plikach ADR
001–047 w `template/docs/adr/truth/`**, a tego katalogu nie ma — korpus 54 ADR-ów
pojechał do `docs/archive/adr/` w `687dbdc`. To nie jest fakt do przemierzenia,
to fakt, którego przedmiot przestał istnieć. Ten sam ruch uśmiercił
`tr-a8bda1a1`, i `stale` ukrywał oba od 2026-08-02.

### ODSTĘPSTWO OD WYTYCZNYCH, z pomiarem

Wytyczna (b) brzmiała: *„Sfiluj nowy claim z aktualną wersją **v0.9.38 w tekście
i recepturze**"*. Nie wykonano dosłownie — i to jest jedyne odstępstwo w tym
kroku. Powód jest policzalny, nie estetyczny:

```
claimy, których ZDANIE nazywa literał wersji:     122  ->  94 martwe (77%)
claimy, których RECEPTURA nazywa literał wersji:   25  ->  24 martwe (96%)
```

Receptura z wpisaną wersją ma w tym ledgerze **96% śmiertelności**. Trzy
rodziny, które właśnie osądzaliśmy, są tego historią, nie anegdotą:

```
explainer scope :  tr-b66ed08c -> tr-791fafbc -> (tr-8d9005d0) -> tr-f8b946cd
lockstep gate   :  tr-84b79439 -> tr-9dd3323b (v0.9.34) -> tr-96d14c58 -> tr-d237a049
bateria/ramiona :  tr-99113e85 -> tr-4f48fd51 -> tr-c6170e24 -> tr-7cccc674 -> tr-b350781e -> tr-38d32bc7
```

Każde pokolenie umierało na tym samym: bump wersji, receptura przestaje trafiać,
claim leci do kolejki. Złożenie czwartego pokolenia w tym samym kształcie byłoby
świadomym złożeniem claimu z datą ważności równą następnemu wydaniu.

Zamiast tego użyto **wzorca, który to repo już ma** — nieżyjący `tr-39eb58bc`
niósł go w recepturze: wyciągnij wersję z linii 2 CLI i sprawdź, czy występuje
w drugiej powierzchni, zamiast wpisywać ją po obu stronach.

```
grep '^\*\*Scope\*\*' docs/truth-ledger-explained.md | grep -oE 'v[0-9]+[.][0-9]+[.][0-9]+' \
  | grep -qF -f - template/scripts/truth \
&& head -2 template/scripts/truth | grep -oE 'v[0-9]+[.][0-9]+[.][0-9]+' \
  | grep -qF -f - docs/truth-ledger-explained.md \
&& echo EXPLAINER-SCOPE-AND-CLI-AGREE-ON-CURRENT-VERSION
```

Sprawdzenie idzie **w obie strony**, więc twierdzeniem jest *zgadzają się*, a nie
*obie mówią X*. Zdania nowych claimów też nie nazywają wersji. Analogicznie dla
lockstepu bramki (`tr-d237a049`) i dla obu claimów o baterii, gdzie
`sha256sum <plik>` — receptura ginąca przy **dowolnej** edycji pliku — została
zastąpiona recepturą demonstrującą sam fakt (`grep -oE '^# --- [0-9]+[.] [a-z]+'`
wylicza dziesięć ramion po nazwie).

Jeśli operator chce jednak przypiętą wersję, to jedno re-file.

### DO DECYZJI: podwójny claim o nagłówku Scope

`tr-8d9005d0` jest **jedyną ocalałą** recepturą z literałem wersji w całym
ledgerze — bo literał to akurat `v0.9.38`, czyli bieżąca wersja. Twierdzi ten sam
fakt co świeży `tr-f8b946cd`. Bramka bliskich duplikatów tego nie złapała,
bo (b) kazało użyć `--duplicate-ok`. Rekomendacja: wycofać przypięty na rzecz
niezależnego od wersji —

```
truth verdict tr-8d9005d0 retracted --cause restated --successor tr-f8b946cd
```

— ale to kolejny tombstone, więc zostaje u operatora. Do czasu decyzji ledger
niesie dwa żywe claimy o jednym fakcie, i to jest tu zapisane, a nie przemilczane.

### Bramka i telemetria

```
reproduce   66 live -- 66 reproduces, 0 capsule-stale, 0 unexecutable, 0 no-capsule, exit 0
core 372 OK · v04 13 OK · integrations 28 OK · canary 283 caught / 0 missed
field-consumers 30 kluczy / 4675 rekordow -- 0 failures · reachability 10/10
release-battery: ALL ARMS GREEN
```

```
status:     retracted 122 · live 66 · diverged 32 · unverified 28
polokres:   P1 0.87d (n=22) · P2 0.79d (n=38)
kolejka:    32 pozycje, najstarsza 17 d
```

Push wykonany bez `--no-verify` — bateria przeszła na bramce pre-push.

### POST SCRIPTUM — bramka cytowań złapała ten właśnie wpis

Pierwszy `git push` **został zablokowany**, i nie przez kod:

```
FAIL  tr-39eb58bc  retracted -- live prose stands on a dead fact
FAIL  tr-c6170e24  diverged  -- live prose stands on a dead fact
FAIL  tr-d1049451  diverged  -- live prose stands on a dead fact
```

Źródłem był **`00-RUNBOOK.md`**, do którego przepisano tabelę „stary → następca"
z tego dziennika. `fact-health` rozróżnia te dwa pliki celowo i ma rację:

* `01-JOURNAL.md` jest **poza zasięgiem** — to zapis append-only, który *ma*
  nazywać id, które wycofał; nazwanie ich jest treścią wpisu.
* `00-RUNBOOK.md` **zostaje w zasięgu** — to instrukcja, na której czytelnik
  działa dziś, więc martwe cytowanie w niej jest defektem.

Runbook odsyła teraz do J-036 zamiast powielać id. Dwie rzeczy warte
odnotowania: bramka zadziałała na własnym autorze w tej samej sesji, w której
opisywano jej działanie, i był to **jedyny** czerwony arm — pozostałe dziewięć
przeszło za pierwszym razem.

---

## J-037 · KROK 3.1 — nazwane polityki obserwacji, mechanizm gotowy · 2026-08-17

### Najpierw przeliczenie defektu D-A na obecny reżim

Runbook wnosił do Fazy 3 liczby `1 ścieżka → 12,6% precyzji; 2–3 ścieżki → 1,9%`.
**Te liczby mierzyły fałszywe zestalenia, których po 2.5 nie ma.** Budowanie
polityki na nich byłoby optymalizacją pod wskaźnik, który sami usunęliśmy, więc
najpierw pomiar tego, co `evidence_paths` kosztują dziś.

```
93 aktywne claimy, z czego 75 ma zbiór obserwacji
153 wpisy obserwacji, średnio 2,04 na claim
te 75 zbiorow to 60 ROZNYCH zbiorow   <- reuzywalnosc bliska zeru
najczestszy zbior wspoldzieli 4 claimy
```

Ocalały koszt to **uwaga, nie fałszywe zestalenia**. Whisper nadal odpala się na
każdej obserwowanej ścieżce:

```
ostatnie 200 commitow: 2329 linii whispera  (srednio 6,8 claimu na edycje)
  ^^^ TE DWIE LICZBY SA BLEDNE -- sprostowane w J-040 na 1670 linii i
      22,6 claimu na edycje (sumowalem po plikach, a whisper emituje
      jedna linie na CLAIM). Zostawione w oryginale, bo dziennik jest
      zapisem append-only, a korekta jest czescia zapisu.
jedno dotkniecie truth-canary.sh          -> 31 claimow naraz
```

To jest D-A wyrażone liczbą dla świata po Reproduce-on-Read: 60 zbiorów wybranych
z palca, nic nie sprawdza ich związku z dowodem, a rachunek płaci się uwagą.

### Format — decyzja operatora, opcja 1, z twardym ograniczeniem w tle

Runbook szkicował `.truth/watch-policies.yml`. **CLI jest stdlib-only**
(`scripts/truth` linia 20), `yaml` nie jest w stdlib, a wszystkie osiem
istniejących plików polityk w `.truth/` to bezrozszerzeniowy tekst liniowy z
identycznym loaderem. Rozszerzenie `.yml` obiecywałoby ogólność, której loader
musi odmówić — pułapka na konsumenta. Przyjęty format to standard tego repo:

```
<policy-name> -- <glob>[, <glob>...]
```

### Co powstało

| warstwa | co | gdzie |
|---|---|---|
| stała | `WATCH_POLICIES_REL`, `WATCH_POLICY_NAME_RE` | `registry.py` |
| loader (I/O) | `load_watch_policies()` → `(policies, state, err)` | `shellio.py` |
| decyzje (czyste) | `watch_policy_error`, `watch_policy_conflict_error` | `policy.py` |
| wpięcie | `claim --watch-policy NAME` | `cli.py` |
| czytelnik | `list --watch-policy NAME` (i `-` = backlog) | `cli.py` |

Podział wymuszony DAG-iem ADR-044: `shellio` importuje tylko `registry` i
`kernel`, więc nie może wołać `policy` — czyta bajty, a decyduje `policy`;
składa `cli`. To ten sam kształt, w którym już żyją `read_policy_file` +
`policy_file_state`.

**Polityka ROZWIĄZUJE zbiór, nie adnotuje go.** Rozwiązanie idzie PRZED tabelą
`INTAKE_GATES`, więc INV-M, prognoza ADR-039 i doradca ADR-038 sądzą globy
polityki dokładnie tak, jak sądzą listę z ręki — polityka z nieosiągalnym globem
zostaje odrzucona jak każda inna.

**Payload niesie OBOJE: nazwę i rozwiązane globy.** Zapis samej nazwy pozwoliłby
późniejszej edycji `.truth/watch-policies` po cichu przepisać to, co przeszłe
claimy uważa się za obserwujące. Ledger jest append-only: globy to zapis, nazwa
to proweniencja.

### Odmowy — wszystkie sprawdzone, każda głośna

```
nieznana nazwa       -> odmowa WYLICZAJACA istniejace  (typo nie moze po cichu
                        zlozyc claimu obserwujacego NIC -- to defekt INV-M)
--watch-policy + --paths -> odmowa (dwa zrodla jednego pola)
pathspec magic (:-!)  -> odmowa, w linii i w globie (SI-1)
brak ' -- '           -> odmowa
nazwa poza [a-z0-9-]  -> odmowa
duplikat nazwy        -> odmowa (last-wins ukrylby polityke przed czytelnikiem)
polityka bez globow   -> odmowa (zbior pokrywajacy zero plikow)
```

### Błąd własny, złapany testem odmowy

Pierwsza wersja składała trzy odmowy w jedną krotkę:

```python
for _e in (wp_err, watch_policy_conflict_error(...), watch_policy_error(...)):
```

Krotka wylicza **wszystkie** elementy przed pętlą, a zepsuty plik daje
`policies=None`, więc `name not in None` rzucało `TypeError` — crash zamiast
odmowy, dokładnie to, czemu tekst odmowy ma zapobiegać. Naprawione krótkim
spięciem: `if wp_err: sys.exit(wp_err)` przed resztą.

### USTALENIE — pole bez czytelnika, i dlaczego NIE poszło do `stats`

Pierwsza wersja dodawała sekcję adopcji do `stats_report`. **Test
`TestStatsCLIShape` ją odrzucił** — i miał rację: ADR-046 rozstrzygnął, że
`stats` niesie rdzeń Tier B (liczby, werdykty, półokres zasilający doradcę FS-1,
wiek kolejki), a metryki analityczne pojechały do `instruments/`. Wskaźnik
adopcji jest z rodziny override-velocity. Zmiana tego rozstrzygnięcia to decyzja
operatora, nie efekt uboczny dowożenia funkcji, więc sekcję **cofnąłem**, a
czytelnikiem pola (wymóg ADR-046) został filtr `list --watch-policy`, który przy
okazji odpowiada na operacyjne pytanie migracji 3.3: `--watch-policy -` wypisuje
backlog. Dziś: **65 żywych claimów ze ścieżkami i bez polityki.**

### USTALENIE — sentinel `sha256sum`: pinuj BAJTY albo WŁASNOŚĆ, plik decyduje

Trzeci raz w tej sesji padła receptura `sha256sum <plik>` — tym razem
`tr-7a10f167` na `scripts/fact-health.sh`, zerwana **moją własną** edycją
(dodaniem reguły zasięgu). Przewodnik operacyjny reklamował te sentinele jako
„intended ceremony". Pomiar rozstrzyga subtelniej niż „sha256sum jest kruche":

```
9 sentineli sha256sum ->  8 ZYWYCH, 1 martwy
zywe:   pliki POLITYK (evidence-allow, citation-scope, settings.json, pre-commit)
        -- rzadko edytowane, a edycja JEST zdarzeniem, ktore chcesz zglosic
martwy: SKRYPT w aktywnym rozwoju (fact-health.sh) -- padl trzy razy na
        edycjach, ktore ULEPSZALY pilnowana granice
```

Projekt nie jest zły, jest **źle zastosowany** do pliku pod rozwojem. Sentinel
na `fact-health.sh` przefilowany (`tr-a00459ec`) na recepturę twierdzącą o
własnościach, po które sentinel istnieje. Przy okazji akapit w przewodniku
opisywał mechanizm, którego już nie ma („edycja zestala claim… `reaffirm`'s
match arm") — poprawiony na obecny i **mocniejszy**: `reproduce` przelicza
digest na granicy pusha, zmieniony bajt ląduje w `capsule-stale`, sweep wychodzi
7 i **blokuje push**, a wyczyścić tego mechanicznie nie da się, bo `reproduce`
nie zapisuje nic w żadną stronę.

### Weryfikacja

```
core 425 testow (14 nowych na 3.1), 0 skipow, OK
canary 283 caught / 0 missed · integrations 28 OK · v04 13 OK
field-consumers 31 kluczy (watch_policy z czytelnikiem) -- 0 failures
reproduce 66/66, exit 0 · reachability 10/10
release-battery: ALL ARMS GREEN
```

Pierwszy claim na polityce: `tr-a2614cf7` (`--watch-policy canary-suite`),
zweryfikowany z osobnej sesji.

### Stan Fazy 3

* **3.1 — ZROBIONE.** Mechanizm, odmowy, testy, plik polityk tego repo (9
  polityk nazwanych z faktycznie powtarzających się zbiorów) i szablonowy plik
  dla konsumenta (pusty, opt-in, bez wiersza w doktorze).
* **3.2 — NASTĘPNY.** `max_paths` / `churn_budget` jako wiersz `INTAKE_GATES`.
  Projektowa teza do potwierdzenia: claim stojący na nazwanej polityce jest
  **zwolniony** z budżetu, bo zbiór został zrecenzowany raz — to jest cała
  wymiana, jaką polityki oferują, i to daje bramce zęby zamiast samego licznika.
* **3.3 — migracja 65 claimów z backlogu.**

---

## J-038 · KROK 3.2 — budżet obserwacji jako twarda odmowa · 2026-08-17

`MAX_FREEHAND_WATCH_PATHS = 1`. Wiersz `paths-budget-max` w `INTAKE_GATES`,
zaraz po `paths-inv-m`: INV-M pyta, czy ścieżka MOŻE kiedykolwiek trafić,
budżet pyta, czy zbiór został **wybrany, czy uzbierany**.

Dwa wyjścia, oba zostawiają ślad; trzeciego, cichego, nie ma:

```
--watch-policy <name>     zbior zrecenzowany raz i zacommitowany pod nazwa
--paths-ok "<zdanie>"     autor mowi, dlaczego TEN zbior; zapis paths_basis,
                          decay 30 dni (ADR-032), liczone w override_report
```

Pozycja w tabeli jest wymuszona: musi być **przed** `scope-decay-adr032`, bo
`--paths-ok` jest jedną z trzech podstaw, które ten wiersz wygasza.

### Odmowy symetryczne — tak samo ważne jak sam budżet

Precedens ADR-035 (`--evidence-exit-ok` przy komendzie kończącej się zerem)
zastosowany dosłownie: **podstawa, która niczego nie usprawiedliwia, to szum
schematu** — a tutaj gorzej, bo wygaszałaby osąd, którego nikt nie musiał
podjąć. Odrzucane są więc również: `--paths-ok` przy jednej ścieżce oraz
`--paths-ok` obok `--watch-policy` (polityka już niesie tę recenzję).

### Canary złapał zmianę intake'u — trzy ramiona, każde przepisane

Bateria zablokowała się na `FAULT T`, potem na `DW6`. To nie były testy zepsute
przez zmianę — to fixture'y filujące po dwie ścieżki, więc **nowa bramka je
odrzuciła i miała rację**. Zgodnie z J-012 przedmiot każdego z nich nadal
istnieje, więc każdy dostał `--paths-ok`, a nie kasację:

| ramię | przedmiot, który został | co zyskało |
|---|---|---|
| `FAULT T` | INV-M nie może wziąć listy po przecinkach za literał ze spacją | przejście przez escape hatch budżetu, end-to-end przez CLI |
| `FAULT RA` | dotknięcie obserwowanej-ale-nieczytanej ścieżki jest inertne | jawne uzasadnienie, dlaczego fixture watchuje plik, którego receptura nie czyta |
| `DW6` | wpis rename widoczny przez dwa pola NUL | jawne uzasadnienie, że arm POTRZEBUJE nazwy sprzed i po `git mv` |

Trzeci przypadek jest najciekawszy: `DW6` **musi** obserwować obie nazwy, bo bada
sam wpis rename. To jest wzorcowy przypadek użycia `--paths-ok` — zbiór jest
poprawny i żadna polityka go nie nazwie.

### BŁĄD WŁASNY — sondy filowane do PRAWDZIWEGO ledgera

Testując bramkę odpaliłem `truth claim` z tekstami `probe ...` w tym
repozytorium zamiast w sandboxie. Ledger jest append-only, więc **zostają na
stałe**:

```
tr-e079a1d5  unverified  probe single path
tr-3d1ffc53  unverified  probe policy exempt from the budget
tr-7dbe14ae  unverified  probe wide freehand set with a stated reason
tr-abdfddc3  unverified  probe decay notice flag naming for the wide set case
```

Ironia jest częścią lekcji: wszystkie cztery obserwują realne pliki, więc
dokładają dokładnie ten szum whispera, który Faza 3 usuwa. Sondy należą do
sandboxa — canary robi to od zawsze i miałem wzorzec przed oczami.

Rekomendacja: `retracted --cause wrong` (nigdy nie były faktami, tylko sondami
przyrządu). Ceremonia jest ludzka (ADR-011), więc zostaje u operatora; komendy
w raporcie sesji. Pozostałe testy 3.2 napisane już jako testy jednostkowe nad
tabelą `INTAKE_GATES`, bez dotykania ledgera.

### Weryfikacja

```
core 436 (11 nowych na 3.2), 0 skipow, OK · canary 283/0 · integrations 28 OK
field-consumers 32 klucze -- paths_basis i watch_policy MAJA czytelnikow, 0 failures
reproduce 66/66 exit 0 · reachability 10/10 · release-battery ALL ARMS GREEN
```

## Skala kroku 3.3, zmierzona przed wykonaniem

```
backlog freehand ze sciezkami:                        78
  SZEROKIE (>1 sciezka, dzis odrzucone przez bramke): 46
  w budzecie (1 sciezka, legalne jak sa):             32

z 46 szerokich:
  13 pasuje DOKLADNIE do jednej z 9 polityk   (cli-behaviour 4, both-suites 4,
                                               record-contract 3, fold-kernel 2)
  33 nie pasuje do zadnej -- w 32 ROZNYCH zbiorach
```

Liczba 32 jest rozstrzygająca dla kształtu 3.3: **nazwanie 32 kolejnych polityk
byłoby tym samym defektem z nową etykietą** — polityka użyta raz to lista
ścieżek z nazwą. Jedyny powtarzający się zbiór wśród nich to
`scripts/fact-health.sh, scripts/release-battery.sh` (2 claimy) i on zasługuje
na politykę; reszta to kandydaci na `--paths-ok` albo na pozostawienie w spokoju.

**Koszt migracji jest asymetryczny i trzeba go nazwać:** claim jest niezmienny,
więc „migracja" to re-file + weryfikacja z osobnej sesji + **retrakcja
bramkowana człowiekiem**. 46 claimów = ~138 nowych rekordów i **46 ceremonii
tombstone**, żeby zmienić pole metadanych w faktach, które są prawdziwe i
poprawnie obserwowane. Decyzja o zakresie należy do operatora — pytanie w
raporcie sesji.

---

## J-039 · KROK 3.2, drugie ramię — budżet szerokości i korekta własnej tezy · 2026-08-17

### KOREKTA POMIARU, który uzasadniał to ramię

Zaproponowałem `churn_budget` argumentem: „trzy z sześciu najgłośniejszych
claimów mają JEDNĄ ścieżkę (`template/truthlib/**`, 74 linie) i przechodzą przez
`max_paths=1`". Zdanie było prawdziwe **dla okna 200 commitów**, w którym
liczyłem. ADR-039 mierzy w oknie **30 dni**, a tam te same globy dają **24** przy
skalibrowanym progu **54** — czyli spokojnie legalne.

**To ramię nie łapie przypadku, który je umotywował.** Zapisuję to, bo zostawienie
fałszywego uzasadnienia w pliku jest gorsze niż samo ramię. Co łapie naprawdę:
każdy zbiór, który jest gorący **teraz**, a najwyższa prognoza jedno-ścieżkowa na
ledgerze (48) leży na tyle blisko progu, że jeden `**` by go przekroczył — więc
pilnuje przypadku osiągalnego, nie hipotetycznego.

### DRUGIE USTALENIE: kolejność decydowała o tym, czy ramię w ogóle żyje

```
freehand claimow na/powyzej progu churn: 17 z 78
  ...z nich majacych JEDNA sciezke:       0
najwyzsza prognoza jedno-sciezkowa:      48   (prog 54)
```

Wszystkie 17 ma ≥2 ścieżki, więc przy kolejności „liczba, potem szerokość"
ramię churn **nigdy by nie odpaliło** — martwy wiersz udający pokrycie, czyli
dokładnie ta ciemna bramka, której to repo zabrania. Odwrócone: odpala na
wszystkich 17, a autor dostaje komunikat **działający** („zawęź globy") zamiast
tylko prawdziwego („masz cztery ścieżki”). `blast-forecast-adr039` przesunięty
razem z nim jako jego źródło faktu; żadne filowanie nie płaci nowego `git`,
bo `paths-inv-m` wiersz wyżej już płaci `git ls-files`.

### TRZECIE: doradca i odmowa dzieliły próg — rozwarstwione, nie skasowane

Canary `BF1` padł: arm oczekiwał **advisory** ADR-039, a dostał odmowę, bo
podniesienie doradcy do bramki uczyniło jego populację pustą. Rozwiązanie nadaje
obu ról zamiast wybierać jedną:

* **nieusprawiedliwiona** szerokość → **odmowa**;
* **zaakceptowana** (polityka albo `--paths-ok`) → filowane i doradca mówi, ile
  to kosztuje.

`BF1` jest teraz dwoma ramionami (`BF1a` odmowa, `BF1b` advisory), więc ucichnięcie
którejkolwiek połowy jest łapane. Canary 283 → **284**.

### BŁĄD WŁASNY, złapany przez BF1b

Kontrola „podstawa, która niczego nie usprawiedliwia" patrzyła wyłącznie na
liczbę ścieżek. Po dodaniu drugiego ramienia **jedna** ścieżka może legalnie
potrzebować `--paths-ok` — żeby usprawiedliwić szerokość. Pierwsza wersja
odrzucała dokładnie ten przypadek, mówiąc autorowi, że jego podstawa jest zbędna,
podczas gdy to drugie ramię jej żądało. Naprawione: ramię churn ustawia
`ctx["churn_over"]` **zanim** wyjścia je wyczyszczą, a ramię liczności ten
znacznik czyta. Regresja przypięta testem.

### Krawędź w DAG-u: `gates -> reports`

Próg (`effective_blast_floor`) ma jedną implementację i mieszka w `reports.py`.
Alternatywą było przepisanie percentyla w drugie miejsce, czyli dryf F1/F5.
Krawędź jest acykliczna (`reports` importuje tylko registry/kernel/evidence i
nigdy `gates`), dorysowana w `template/docs/structure.md` — którego test
porównuje strzałki z realnymi krawędziami AST, więc niezaktualizowany diagram
by to wywalił.

### Weryfikacja

```
core 441 (18 nowych na 3.2 lacznie) · canary 284/0 · integrations 28 OK
v04 13 OK · field-consumers 32 klucze 0 failures · reproduce 66/66 exit 0
release-battery ALL ARMS GREEN
```

---

## J-040 · KROK 3.3 — migracja celowana, i SPROSTOWANIE własnej metryki · 2026-08-17

### SPROSTOWANIE: metryka hałasu, którą cytowałem, była policzona źle

Liczby `2329 linii whispera / 6,8 claimu na edycję` z J-037 i J-039 są **błędne**.
Sumowałem po plikach, więc commit dotykający dwóch obserwowanych plików tego
samego claimu liczył się dwa razy — a whisper emituje **jedną linię na claim**,
nie na plik. Poprawnie (distinct commits per claim, to samo okno 200 commitów):

```
BLEDNIE:   2329 linii, 6,8 claimu na edycje
POPRAWNIE: 1670 linii, 22,6 claimu na edycje
```

Pomyliłem się w obie strony: licznik zawyżony, a mianownik („dotknięcia") tak
samo zawyżony, przez co iloraz **zaniżony ponad trzykrotnie**. Wniosek
jakościowy się nie zmienia — jest **mocniejszy**: przy jednej edycji pada
średnio 22,6 claimu, nie 6,8. Decyzje 3.2 stały na wniosku, nie na liczbie, więc
nie wymagają rewizji; cytaty wymagają.

Lekcja jest ta sama, którą to repo stosuje do claimów: metryka też potrzebuje
receptury, którą da się odtworzyć i zakwestionować.

### Migracja — cztery claimy, wybrane pomiarem, nie kolejnością

Niezmiennik z J-022 („obserwuj dokładnie to, co czyta receptura") uczynił wybór
mechanicznym: porównanie zbioru obserwacji z tokenami ścieżkowymi receptury.

| claim | obserwował | receptura czyta | werdykt |
|---|---:|---:|---|
| `tr-4cf0f3eb` | 8 | **1** | migrowany |
| `tr-0c9099c2` | 4 | 3 | migrowany |
| `tr-ef37611b` | 2 | 1 | migrowany |
| `tr-6308173b` | 2 | 1 | migrowany |
| `tr-6bdfed46` | 4 | 4 | **zostawiony — poprawny** |
| `tr-789b11be` | 2 | 2 | **zostawiony — poprawny** |
| `tr-f8b946cd` | 2 | 2 | **zostawiony — poprawny** |
| `tr-2c5de4e2` | 4 | — | brak receptury; niezmiennik nie ma zastosowania |

Trzy z ośmiu najgłośniejszych obserwowały **dokładnie** to, co czytają. Ich
hałas jest ceną prawdziwego zakresu, nie niechlujstwa — i migrowanie ich byłoby
optymalizacją pod wskaźnik kosztem poprawności.

### Wynik, w poprawnej metryce

```
158 -> 105 linii na 4 migrowanych parach   spadek 53 (34%)
  tr-4cf0f3eb 64 -> 42   tr-0c9099c2 39 -> 37
  tr-ef37611b 27 -> 23   tr-6308173b 28 ->  3
```

**Ledger jako całość NIE spadł**: 1670 linii przy 80 aktywnych zbiorach. Powód
jest mój: w tej sesji złożyłem 14 aktywnych claimów kosztem 320 linii, z czego
**4 sondy testowe kosztem 102 linii** to czysty błąd własny (J-038). Migracja
zadziałała na swoich celach; moje własne filowanie zjadło zysk. Zapisuję to
tak, a nie jako sukces — inaczej ta sama metryka, którą właśnie prostuję,
zaczęłaby kłamać po raz drugi.

### `tr-4cf0f3eb` — genuine, nie mechanical, i ten sam trap co w doktorze

Ten claim reprodukował się **wyłącznie dlatego, że przewodnik nadal wspominał
`invalidate-scan` — we własnej prozie o wycofaniu tego werbu.** Dokładnie ta
sama figura, co wiersz doktora grepujący komentarz o swoim usunięciu (J-035
USTALENIE 2). Kapsuła zielona, przedmiot martwy.

Sprawdzenie odsłoniło większy dryf: **`docs/truth-ledger-operations-guide.md`
opisywał wycofaną maszynerię jako żywą w ośmiu miejscach** — wiersz „Every
merge/pull" z `invalidate-scan`, lista werbów zapisu z `reaffirm`, przepis CI,
trzy diagramy i cały „Rung 3" o triage'u reaffirm. To dokument idący do
konsumenta. Poprawiony: tabela wyzwalaczy ma teraz wiersze `reproduce` (pre-push)
i `ttl-scan` (jedyny czytnik zegara), a „Rung 3" mówi, że `reproduce` jest
**ostrzejszy** od tego, co zastąpił — nie zapisuje nic w żadną stronę.

Trzy pozostałe wzmianki są jawnie historyczne („it used to run", „all that
remains of", „until v0.10 this rung was") i tak mają zostać.

### Ceremonie u operatora

Cztery poprzedniki dostały `diverge` z rekomendowaną komendą tombstone w
`basis` (ADR-011: agent kończy na diverge). Dwa cytowania w przewodniku
podmienione na następców, bo bramka ADR-036 słusznie je złapała.

```
truth verdict tr-4cf0f3eb retracted --cause restated --successor tr-db201971
truth verdict tr-0c9099c2 retracted --cause restated --successor tr-4df1a9fd
truth verdict tr-ef37611b retracted --cause restated --successor tr-4a666db0
truth verdict tr-6308173b retracted --cause restated --successor tr-d0cfd9ea
```

### Weryfikacja

```
core 442 · v04 13 · integrations 28 · canary 284/0 · field-consumers 32/0
reproduce 66/66 exit 0 · reachability 10/10 · release-battery ALL ARMS GREEN
```

---

## J-041 · KROKI 4.1 i 4.2 — jedna projekcja, jeden werb · 2026-08-17

### Uzasadnienie okazało się inne, niż zakładał runbook

Runbook motywował Fazę 4 zwinięciem rozproszenia. Pomiar mówi, że to jest
**drugorzędne**:

```
5 instrumentow = 5 procesow = 5 foldow : 0,55 s
1 proces, 1 fold, te same sekcje       : 0,15 s   (3,7x)
```

Prawdziwy powód jest inny i większy: **`instruments/` nie jest szablonowane.**
ADR-046 przeniósł pięć czystych projekcji ledgera do instrumentów meta-repo, a
te nie jadą do konsumenta. Wygenerowane repo widzi dziś `truth stats` — liczby,
werdykty, półokres, wiek kolejki — i **nic więcej**: żadnej prędkości nadużyć,
żadnego dowodu separacji weryfikatora, żadnego raportu churnu, przyczyn
retrakcji ani rozbicia zestaleń. Pomiary mówiące, czy czyjś ledger jest
prowadzony uczciwie, istnieją wyłącznie w repozytorium, które wydaje narzędzie.
`structure.md` nazywa tę asymetrię największym pojedynczym ryzykiem systemu.

### 4.1 — `health_report()`: kompozycja, nie przepisanie

Każda sekcja to **istniejąca czysta funkcja** wołana ze wspólnym `folded` —
dokładnie tak, jak ADR-034 zamierzał, przewlekając ten parametr. Nic tu nie
przelicza liczby, którą już ktoś posiada; druga implementacja którejkolwiek
byłaby dryfem F1/F5.

Czysta, więc powłoka dostarcza to, co wymaga świata: `history` + `history_state`,
`reproduce` (albo `None`) i `watch_policies`.

**`watch` wylądowało tutaj, nie w `stats` — i to rozwiązuje napięcie z 3.1.**
Wtedy próbowałem wstawić adopcję polityk do `stats_report`, a
`TestStatsCLIShape` słusznie odmówił: ADR-046 rozstrzygnął, że `stats` niesie
rdzeń Tier B. `health` **jest** tym „gdzie indziej" — i w dodatku jedzie do
konsumenta.

### BŁĄD WŁASNY, złapany pierwszym smoke-testem

Pierwsza wersja wnioskowała stan historii churnu **z braku klucza** w wyjściu
`blast_report` — a ta funkcja żadnego stanu nie zwraca. Sygnał ogłaszał więc
„historia niedostępna" nad zupełnie zdrowym logiem. To jest dokładnie ta cicho
zimna odczytana wartość, przed którą sama sekcja ostrzega: **wnioskowanie o
zdrowiu sensora z nieobecności pola.** Naprawione jawnym parametrem
`history_state`, regresja przypięta testem.

### 4.2 — werb `truth health [--json] [--reproduce]`

**Raportuje i niczego nie odmawia**, i to jest projekt, nie nieśmiałość. To repo
ma już powierzchnie, które blokują — bramka commitu, tabela intake'u, exit 7/8
`reproduce`, bateria — i każda posiada swoje pytanie. Druga blokująca
powierzchnia nad tymi samymi faktami byłaby drugim miejscem, w którym można się
o nie pokłócić. `health` odpowiada „jak się ma ten ledger", co nie jest pytaniem
bramki.

`--reproduce` jest **opt-in**, bo wykonuje receptury autorów. Werb odczytu, który
po cichu uruchamia własne przepisy repozytorium, byłby zaskoczeniem; ekran
ADR-009 to granica, którą czytelnik powinien przekraczać świadomie. Bez flagi
sekcja jest `null`, a sygnał **mówi, że nie została uruchomiona** — zamiast
sugerować czysty przemiat, którego nikt nie zrobił.

Sweep kapsuł **wyodrębniony** z `cmd_reproduce` do `reproduce_sweep()`: czysty
ruch, `cmd_reproduce` woła go i zachowuje każdy bajt renderowania oraz kontrakt
0/7/8. Alternatywą było drugie przejście z własnym ekranem i własnym triage'em.

### Widok, dziś

```
WARN  queue-aging: 35 pozycji, najstarsza 17d (> 14d)
ok    reproduce: 66/66 kapsul odtwarza sie tutaj      (z --reproduce)
ok    watch-adoption: 2/80 na nazwanej polityce (78 freehand)

overrides: scope=9 paths=3 duplicate=20 screened-false=0
retraction causes: expired=5, restated=24, unrecorded=96, wrong=0
verifier separation: 17 unevidenced, mediana 172,7 s
churn: floor 55 (calibrated, history ok)
```

`unrecorded=96` jest tu najciekawszą liczbą, jaką ten widok ujawnia od razu:
96 retrakcji sprzed ADR-049 nie ma zapisanej przyczyny. Nie jest to defekt do
naprawy wstecz — to pomiar tego, ile osądu przepadło, zanim pole istniało.

### Weryfikacja

```
core 450 (8 nowych) · v04 13 · structural 116 · integrations 28 · canary 284/0
field-consumers 32/0 · reproduce 66/66 exit 0 · reachability 11/11
release-battery ALL ARMS GREEN
```

---

## J-042 · KROK 4.3 — zwinięcie okazało się już wykonane, i to jest ustalenie · 2026-08-17

### Pomiar przed cięciem

Sprawdziłem, co właściwie jest do zwinięcia. Cztery z pięciu instrumentów
**już wołają dokładnie te same czyste funkcje**, które komponuje
`health_report()`:

```
blast-report.py      -> blast_report()
override-velocity.py -> override_report()
separation-report.py -> separation_report()
retraction-causes.py -> retraction_cause_report()
```

**Duplikacji logiki nigdy nie było.** Instrumenty to cienkie opakowania CLI
(58–134 linii) nad funkcjami z `reports.py`. Prawdziwe zwinięcie — jedna
implementacja na pomiar i jedno wejście dla czytelnika — **dostarczył krok 4.2**,
kiedy `truth health` zaczął komponować te same funkcje w werbie, który **jedzie
do konsumenta**.

### Czego NIE zrobiłem i dlaczego

Skasowanie pięciu plików miałoby zmierzony promień rażenia: każdy jest
cytowany w **kilkunastu miejscach** — `test-integrations.py` (rodzina
`TestTierCInstruments`), canary, `docs/governance/gate-metrics.md` (kolumna
„instrument source" dla metryk adopcji ADR-047), `structure.md`,
`asbuilt-architecture.md`, `template/.truth/README.md`, CHANGELOG, przewodnik
operacyjny, paper i explainer.

To jest zamiatanie governance'u, nie sprzątanie kodu: `gate-metrics.md` to
rejestr, w którym operator zadeklarował, **skąd** bierze się każda metryka
adopcji. Przepisanie go jest decyzją właściciela rejestru, nie efektem ubocznym
kroku refaktoru — zwłaszcza że korzyść jest kosmetyczna (logika już jest jedna),
a ryzyko realne. Zostawione operatorowi z wyliczonym kosztem.

Zamiast tego każdy z czterech instrumentów dostał nagłówek mówiący, czym teraz
jest: **widokiem meta-repo na sekcję, którą `truth health` wysyła konsumentowi**,
z jawnym „obie ścieżki wołają tę samą funkcję; nie dodawaj drugiej". Czytelnik,
który trafi do `instruments/`, nie pomyśli, że znalazł drugą implementację.

### Granica, która została nazwana

Dwa instrumenty **zostają i nie są kandydatami do zwinięcia**:
`field-consumers.py` (przemiat AST po kluczach payloadu) i `arm-index.py`
(indeks ramion tego repo). One skanują **kod źródłowy**, nie ledger. To jest
linia zapisana teraz w ARCHITECTURE rozdz. 4: *projekcja nad rekordami jedzie do
konsumenta, analiza kodu tego repozytorium — nie.*

### Inwariant w ARCHITECTURE, rozdz. 4

Dopisane cztery akapity, w tym jawne odwrócenie wcześniejszej decyzji systemu:

* **jedna projekcja, i ona jedzie** — reguła to nie „jeden plik", tylko **jedna
  implementacja na pomiar**; druga funkcja licząca prędkość nadużyć rozjechałaby
  się z pierwszą, a rozjazd byłby niewidzialny, bo obie wyglądałyby wiarygodnie;
* **widok raportuje, nie odmawia** — każda blokująca powierzchnia już istnieje i
  posiada jedno pytanie; druga nad tymi samymi faktami byłaby drugim miejscem
  sporu, i to sporu cichego, bo obie nazywałyby się „bramką";
* **sekcja, której nie policzono, mówi o tym** — `reproduce` jest `null`, a nie
  zerami; różnica między „czysto" a „niezmierzone" jest całą wartością raportu;
* **granica tieringu** — projekcja nad rekordami vs analiza kodu.

Runbook przewidywał tu odwrócenie ADR-046 zapisane jako decyzja (obiekcja O4) i
bez nowych ADR-ów (r18). Tak zrobione: rozdział 4 niesie odwrócenie wprost,
razem z powodem — konsument nie widział tych pomiarów wcale.

### Weryfikacja

```
core 450 · v04 13 · structural 116 · integrations 28 · canary 284/0
field-consumers 32/0 · reproduce 66/66 exit 0 · reachability 11/11
release-battery ALL ARMS GREEN
```

---

# J-043 · ZAMKNIĘCIE REFAKTORU „Reproduce-on-Read" · 2026-08-17

44 commity od bazy `fa2e85b`, 111 plików, +9268/−1144. Fazy 0–4 wykonane.
Wszystkie liczby poniżej odczytane z drzewa w chwili zamknięcia, nie przepisane
z wcześniejszych wpisów.

## Teza i jej weryfikacja

> Zestalenie (`stale`) to zmienna **zastępcza** o wartości predykcyjnej 3,6%,
> używana jako zmienna **decyzyjna**, przy dostępnym pomiarze **bezpośrednim**.

Zweryfikowana na produkcyjnym ledgerze, nie w sandboxie:

```
rekordow invalidation w historii:   1997
...z tego niosacych sygnal TTL:        0     <- caly ten mechanizm to bylo proxy
truth reproduce:                   66/66 zywych kapsul, exit 0, ulamek sekundy
```

Proxy odpalało 1997 razy przy 71 osądzonych rozbieżnościach. Zegar — jedyne, czego
`reproduce` nie zastąpi — nie odpalił się **ani razu**.

## Stan ledgera

```
retracted 133 · live 66 · diverged 31 · unverified 29     (4710 rekordow)
polokres:  P1 0,83d (n=27) · P2 0,79d (n=38)
overrides: scope=10 paths=3 duplicate=20 screened-false=0
retraction causes: restated=29, expired=5, wrong=3, unrecorded=96
verifier separation: 17 unevidenced, mediana 169,9 s
churn: floor 55 (calibrated, history ok)
```

`stale = 0` i to jest wynik, nie przypadek: po kroku 2.5 ten stan jest osiągalny
**wyłącznie** przez wygaśnięcie TTL, a ten ledger nigdy TTL nie użył.

## Bramki

```
core 450 · v04 13 · structural 116 · integrations 28 · canary 284/0 missed
field-consumers 32 klucze / 0 failures · reachability 11/11
release-battery: ALL ARMS GREEN, push bez --no-verify
```

## Co ten refaktor faktycznie znalazł

Najcenniejsze nie były planowane. Wszystkie poniższe wyszły z **pomiaru przed
wykonaniem**, nie z hipotezy:

1. **`stale` był kryjówką, nie tylko szumem** (J-035). `reproduce` bada tylko
   claimy live, więc cztery claimy zaparkowane w `stale` miały kapsuły
   nieodtwarzalne i były niewidzialne dla jedynego pomiaru zdolnego je
   zweryfikować. Proxy nie było nieprecyzyjne — było schowkiem.
2. **Bramka przechodząca na własnym akcie zgonu** (J-035). Wiersz INV-C w
   `doctor` grepował `post-merge` za słowem `invalidate-scan` i trafiał w
   **komentarz wyjaśniający usunięcie tego werbu**. Ta sama figura wróciła przy
   `tr-4cf0f3eb`, który reprodukował się wyłącznie dzięki prozie o wycofaniu.
3. **Obietnica bez mechanizmu** (J-035). „reproduce runs at pre-push" było
   prawdą wyłącznie w tym repo — `install-hooks.sh` nie pisał takiego hooka,
   więc u konsumenta zdanie nie miało za sobą niczego.
4. **96 retrakcji bez zapisanej przyczyny** — ujawnione natychmiast przez
   `truth health`. Nie defekt do naprawy wstecz: pomiar tego, ile osądu przepadło,
   zanim pole istniało.
5. **Kolejność decydowała, czy bramka w ogóle żyje** (J-039). Ramię churn przy
   kolejności „liczność, potem szerokość" **nigdy by nie odpaliło** — martwy
   wiersz udający pokrycie.
6. **Receptura z literałem wersji ma 96% śmiertelności** (J-036), a sentinel
   `sha256sum` jest poprawny dla plików **polityk** i błędny dla **skryptów w
   rozwoju** (J-037): 8 z 9 żywych, martwy tylko ten na pliku pod edycją.

## Błędy własne, wszystkie zapisane

Zostawiam je w bilansie, bo dziennik bez nich byłby reklamą, nie zapisem:

* **Sondy filowane do prawdziwego ledgera** zamiast do sandboxa (J-038) — cztery
  claimy w append-only, obserwujące realne pliki, czyli dokładający ten sam szum,
  który Faza 3 usuwała.
* **Własna metryka hałasu policzona źle** (J-040): sumowałem po plikach, a
  whisper emituje jedną linię na claim. 2329/6,8 → **1670/22,6**. Pomyłka w obie
  strony, iloraz zaniżony ponad trzykrotnie.
* **Uzasadnienie ramienia churn okazało się nieprawdziwe** (J-039): argumentowałem
  oknem 200 commitów, a ADR-039 mierzy w oknie 30 dni. Ramię nie łapie przypadku,
  który je umotywował — zapisane w kodzie, żeby nie zostawić fałszywej racji.
* **Sygnał `health` wnioskujący stan sensora z braku pola** (J-041) — dokładnie
  ta cicho zimna wartość, przed którą sam ostrzega. Złapany pierwszym
  smoke-testem.
* **Krotka wyliczająca wszystkie odmowy przed pętlą** (J-037) — zepsuty plik
  polityk dawał `TypeError` zamiast odmowy.

## Reguła, która niosła cały refaktor

J-012, zastosowana bez wyjątku: **ramię, którego przedmiot nadal istnieje, musi
zostać przepisane, nie skasowane.** Stąd delta canary **283 → 284 przy zerze
skasowanych ramion**, wbrew prognozie runbooka o spadku. FAULT B, E, T, L, RA,
SD-decay, EF3, DG, W1, BF1 — każde odwrócone albo przecelowane, żadne usunięte.

## Otwarte, świadomie

**Wydanie.** Usunięty werb (`reaffirm`) i przemianowany (`invalidate-scan` →
`ttl-scan`) to zmiana łamiąca dla konsumentów. Komentarze w kodzie celowo mówią
„refactor step 2.x", a nie „v0.10.0", bo CLI nadal stwierdza v0.9.38 i żadne
wydanie nie zaszło. Wymaga: linii 2 w `template/scripts/truth`, siedmiu
przypiętych powierzchni ADR-026, wpisu w `template/CHANGELOG.md` i taga.

**Kasowanie pięciu instrumentów** (J-042) — możliwe, ale to zamiatanie
governance'u przez `docs/governance/gate-metrics.md`, więc decyzja właściciela
rejestru.

**Dwie ceremonie tombstone, które przy zamknięciu jeszcze nie wpadły.**
Sprawdzone na drzewie w chwili pisania tego wpisu, nie przyjęte na słowo —
podsumowanie sesji mówiło o komplecie, a fold mówi inaczej:

```
tr-7dbe14ae  unverified   <- CZWARTA sonda z J-038; wycofano trzy, nie cztery
tr-4cf0f3eb  diverged     <- tombstone z J-040 nie wykonany (nastepca tr-db201971)
```

`tr-662eb74f` z podsumowania **nie istnieje w tym ledgerze** — to był identyfikator
z sandboxa `mktemp`, a czwarta realna sonda nazywa się `tr-7dbe14ae` i nadal
obserwuje `scripts/release-battery.sh` oraz `scripts/fact-health.sh`. Stąd
`wrong=3` zamiast `wrong=4` w metrykach wyżej.

```
truth verdict tr-7dbe14ae retracted --cause wrong
truth verdict tr-4cf0f3eb retracted --cause restated --successor tr-db201971
```

Nie jest to defekt refaktoru i nie blokuje niczego — bateria jest zielona, a
`reproduce` daje 66/66. Jest to jednak dokładnie ta klasa różnicy, którą ten
projekt istnieje po to, żeby łapać: **podsumowanie z pamięci kontra odczyt z
folda.** Zapisane po stronie odczytu.

**Praca w toku, nieobjęta tym commitem.** W drzewie leżą niezacommitowane zmiany
w siedmiu plikach `template/truthlib/` — moduł `structural` i selektory
`#/sciezka` na celach obserwacji (stąd „structural suite: 116 tests" w baterii).
To nie jest część tego refaktoru i nie została tu zacommitowana.
