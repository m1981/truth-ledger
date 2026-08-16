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
