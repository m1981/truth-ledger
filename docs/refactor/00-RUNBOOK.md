# RUNBOOK — refaktor "Reproduce-on-Read"

> **To jest jedyne źródło prawdy o postępie.** Status zadania żyje TU, nie w
> pamięci sesji. Notatki empiryczne idą do `01-JOURNAL.md`.
> Jedno zadanie naraz. Po każdym: weryfikacja → status → wpis w JOURNAL → commit.

Gałąź robocza: `claude/git-hooks-architecture-zc97y3`
Commit bazowy: `fa2e85b` · rewizja runbooka: `r18` (2026-08-17, tabela statusow zsynchronizowana; 3.1 format liniowy, 3.2 twarda odmowa, 4.3 bez nowych ADR-ow)

---

## Teza refaktoru

Zestalenie (`stale`) to zmienna **zastępcza** o wartości predykcyjnej 3,6%,
używana jako zmienna **decyzyjna**, przy dostępnym pomiarze **bezpośrednim**
(`truth reproduce`) o koszcie 0,53 s na cały żywy ledger.

Kierunek: **nie przechowywać kotwic ani stanu `stale`; liczyć odtwarzalność
przy odczycie.** Precedens w tym repo — ADR-046 zrobił to z `blast_forecast`
("computed on read, not stored").

---

## Bramka regresji — po KAŻDYM kroku

```bash
cd /home/user/truth-ledger
python3 template/scripts/test-truth-core.py   2>&1 | tail -3
python3 template/scripts/test-truth-v04.py    2>&1 | tail -3
python3 template/scripts/test-integrations.py 2>&1 | tail -3
(cd template/scripts && bash truth-canary.sh  2>&1 | tail -2)
```

**Wartości bazowe (2026-08-16, `fa2e85b`):**

| suita | wynik bazowy | uwaga |
|---|---|---|
| test-truth-core | `Ran 396`, **OK** | J-002 zamknięte przez instalację jsonschema (J-024) |
| test-truth-v04 | `Ran 13`, OK | — |
| test-integrations | `Ran 28`, **OK** | J-003 rozwiązane przez `fetch --unshallow` (J-016) |
| truth-canary | **283 caught, 0 missed** | 44,8 s |

**Reguła F1:** wzrost liczby skipów albo spadek liczby ramion canary to
**PORAŻKA**, nawet gdy suita pisze OK — **chyba że delta była zadeklarowana
z góry w runbooku** (patrz 2.6).

**Od J-024 baseline jest w pełni zielony: żadna porażka ani skip nie ma już
wyjaśnienia środowiskowego.** Reżim mocniejszy niż na starcie sesji.

---

## Metryki docelowe

| metryka | baseline | cel |
|---|---:|---:|
| rekordy w ledgerze | 4 555 | bez przyrostu z tytułu szumu |
| `invalidation` | 1 971 | brak nowych |
| `reaffirm_cleared` | 1 283 (28%) | brak nowych |
| PPV zestalenia | 3,6% | n/d — sygnał znika |
| `reproduce` (61 żywych) | 0,53 s | ≤ 2 s |
| żywych claimów | 61 | **≥ 61** (patrz 1.2 — nie wolno stracić) |
| `unexecutable` | 0 | **0** |
| ADR-y / wycofane | 54 / 0 | **54 zarchiwizowane, 0 w szablonie** ✔ |

---

# FAZA 0 — BLOKADA (wykryta 2026-08-16, J-018)

### [x] 0.1 Naprawić przekazywanie ledgera do bramek zdrowia — **ZROBIONE** (J-020)

`truth list --json` = **145 576 B** > `MAX_ARG_STRLEN` = **131 072 B**.
Dwie bramki są MARTWE (`Argument list too long`):

| plik | tier |
|---|---|
| `scripts/fact-health.sh` | meta-repo |
| `template/scripts/spec-health.sh` | **Tier A — ships do konsumenta** |

Korekta: JSON plikiem tymczasowym zamiast zmienną środowiskową
(`mktemp` + `trap` + `json.load(open(os.environ["CLAIMS_FILE"]))`).

**Weryfikacja:**
```bash
bash scripts/fact-health.sh | tail -1              # niezerowa liczba cytowań
bash template/scripts/spec-health.sh | tail -1
git push                                            # bateria przechodzi
```
**Zaliczone gdy:** obie bramki raportują **niezerową** liczbę zbadanych
pozycji (sweep pusty = sweep ciemny), a push przechodzi bez `--no-verify`.

---

# FAZA 1 — Korpus decyzji i audyt bezpieczeństwa

### [x] 1.1 Audyt screenera dowodowego — ZROBIONE · WERDYKT **GO** (J-017)

Czy allowlista zamyka metaznaki powłoki: `;`, `&&`, `|`, `` ` ``, `$()`, `>`,
`<`, glob? Powód: Faza 2 przenosi wykonanie receptur z komendy ręcznej na
automatyczny wyzwalacz. Receptury to komendy powłoki w pliku danych, który może
przyjść z cudzej gałęzi.

Zero zmian w kodzie. Próby wyłącznie w `mktemp -d`.

**Wynik:** 19 wektorów w sandboxie, tabela w J-017. Screener zamyka podstawienia,
wstrzyknięcie przez separator (`;`/`&&`/`&` — screening **per segment**), potok do
powłoki, znaki sterujące (ADR-021), ścieżki w pozycji programu i denylist.

**USTALENIE SEC-1:** `cat f.txt >2` przechodzi i TWORZY plik `2`. Kanał zapisu
ograniczony do nazw złożonych z samych cyfr, w cwd (`>2a` i `>.git/x` odrzucone).
Preegzystujący, udokumentowany w ADR-040. Poprawka: rozróżnić token `>&` od `>`.

**Korekta etykiety:** bramka GO/NO-GO warunkuje **2.3** (`reproduce` na pre-push —
to on wprowadza automatyczne wykonanie), nie 2.4. r2 miał tu błąd.

**WERDYKT: GO**, pod warunkiem zamknięcia SEC-1 **przed** krokiem 2.3.

---

### [x] 1.2 Przekierowanie claimów obserwujących ADR-y — **ZROBIONE 14/14** (J-022, J-025)

> **KOREKTA WYTYCZNYCH — patrz J-008 i J-009.** Skrypt z wytycznych zwraca **0**
> (`truth list --json` nie niesie `evidence_paths`) i wycofanie przez
> `--cause expired` jest **niezgodne z ADR-049**.

**Poprawny odczyt** (status z CLI + ścieżki z surowego ledgera):

```bash
python3 - <<'PY'
import json, subprocess
status={r["id"]:r["status"] for r in json.loads(subprocess.run(
    ["python3","template/scripts/truth","list","--json"],
    capture_output=True,text=True).stdout)}
for l in open(".truth/claims.jsonl",encoding="utf-8"):
    if not l.strip(): continue
    e=json.loads(l)
    if e.get("kind")!="claim": continue
    p=e["payload"]; st=status.get(e["id"])
    if st in ("live","unverified") and any(
            "adr" in x.lower() for x in (p.get("evidence_paths") or [])):
        print(f"{e['id']} [{st}] {p.get('evidence_paths')}")
PY
```

**Stan faktyczny: 14 claimów** (13 `live` + 1 `unverified`), nie 13.

**Operacja NIE jest wycofaniem.** 13 z 14 to claimy **mieszane** — obserwują
plik ADR **oraz** kod/testy, a ich treść dotyczy **zachowania, które nadal
działa** (np. „truth v0.6.4 ships ADR-013 premise supersede"). Wycofanie ich
z powodu przeniesienia dokumentu skasowałoby 14 żywych faktów o działającym
kodzie — żywy ledger spadłby z 61 do 47 (**−23%**).

**Dla każdego z 14 claimów, po kolei:**

1. Re-file z **zawężonym** zbiorem obserwacji — ścieżka ADR usunięta, ścieżki
   kodu/testów zachowane. To realizuje przy okazji cel Fazy 3 (1 ścieżka →
   precyzja 12,6% zamiast 1,9%).
2. Wycofaj stary, wskazując następcę:

```bash
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=<STARY_ID> python3 template/scripts/truth \
  verdict <STARY_ID> retracted --cause restated --successor <NOWY_ID> \
  --basis "watch set narrowed: ADR path archived to docs/archive/adr/; \
the behaviour this claim asserts is unchanged and stays evidenced by code/tests"
```

`--cause restated` jest jedyną poprawną przyczyną z trzech dostępnych
(`restated`, `expired`, `wrong`). CLI definiuje `expired` jako *„it WAS true and
the world moved past it"* (`policy.py:66`) — fakt nadal jest prawdziwy, więc
`expired` byłby zapisem fałszywym w polu, które `retraction-causes.py` mierzy.

**Szczególny przypadek:** metryka korpusu ADR (`unverified`) obserwowała wyłącznie glob
`template/docs/adr/truth/*.md` — nie ma czego zawężać. Ten jeden wycofać bez
następcy, `--cause expired`, z uzasadnieniem odnoszącym się do archiwizacji.

**Weryfikacja:**
```bash
python3 template/scripts/truth reproduce | tail -2   # unexecutable = 0
python3 template/scripts/truth list --live | grep -c '^tr-'   # >= 61
```
**Zaliczone gdy:** `unexecutable = 0`, liczba żywych **nie spadła**, a powyższy
skrypt odczytu zwraca **0** aktywnych claimów ADR.

---

### [x] 1.3 — `ARCHITECTURE.md` + archiwizacja 54 ADR-ów — **ZROBIONE** (J-027 · J-028, zgoda człowieka) (decyzja właściciela 2026-08-16)

> **KOREKTA WYTYCZNYCH — patrz J-010.** `git mv template/docs/adr/truth/*.md
> docs/archive/adr/` to **nie archiwizacja, tylko usunięcie artefaktu
> z produktu**: `template/` jest tym, co copier wysyła konsumentowi.

**WARIANT A wybrany.** ADR-y opuszczają szablon: `git mv template/docs/adr/truth/*.md
docs/archive/adr/`. Konsument otrzymuje wyłącznie `template/docs/ARCHITECTURE.md`.
Konsekwencja przyjęta świadomie: ADR-y są historią rozwoju maszynerii, nie
dokumentacją produktu.

Pomiar ryzyka linków: **0 linków markdown** na `adr/` w `template/` (sprawdzone),
ale **5 plików** niesie referencje prozą: `template/.truth/README.md`,
`template/CHANGELOG.md`, `template/docs/structure.md`,
`template/docs/truth-ledger-machinery.md`, `template/docs/adr/truth/README.md`.
Każdy wymaga aktualizacji ścieżki.

**`docs/ARCHITECTURE.md` — szablon 4 rozdziałów przyjęty bez zmian:**

1. **Model Danych i Zbieżność** — `.truth/claims.jsonl` (append-only,
   `merge=union`); klucz sortowania `(ts, id, canon(payload))`; profil znacznika
   czasu z clock-push; `retracted` jako stan pochłaniający.
2. **Kaskada Bramek Wejściowych i Bezpieczeństwo** — `INTAKE_GATES`, SI-1..SI-4,
   G8 (`DUPLICATE_THRESHOLD = 0.6`), ADR-007, `evidence-allow`/`evidence-deny`,
   ADR-035.
3. **Cykl Życia Prawdy i Zadań** — ADR-010, ADR-001, ADR-013/017, ADR-014,
   ADR-049 (`restated` wymaga `--successor`).
4. **Reproduce-on-Read i Samoregulacja** — `truth reproduce` na pre-push,
   ADR-051, `field-consumers.py`, `truth health`.

**Rygor treści (J-013):** każdy fakt w ARCHITECTURE.md ma być **ODCZYTANY
Z KODU**, nie przepisany z ADR-a — wzorzec nagłówka `template/docs/structure.md`
(*„STATUS: OBSERVED… where this document and an ADR disagree, this document is
reporting the code"*). Inaczej powstanie 54-ADR-owy dryf w jednym pliku.
Wyrywkowo potwierdzone: `fold_key` (ADR-016) i `DUPLICATE_THRESHOLD = 0.6`
zgadzają się z szablonem.

**Weryfikacja:**
```bash
bash scripts/fact-health.sh      # docs/archive/ już wyłączone ze sweepu
(cd template && bash scripts/doc-health.sh)
```
**Zaliczone gdy:** oba przechodzą, a `fact-health` raportuje **niezerową** liczbę
cytowań (sweep pusty = sweep ciemny, nie sukces).

---

# FAZA 2 — Reproduce-on-Read (rdzeń)

### [x] 2.1 Inwentarz powierzchni — **ZROBIONE** (J-029)
Kto pisze i czyta: `anchor_commit`, `stale`, `reaffirm_cleared`, `invalidation`.
```bash
python3 instruments/field-consumers.py
```

### [x] 2.2 Testy charakteryzujące `reproduce` — **JUŻ ISTNIAŁY**, zweryfikowane (J-030)
Przypiąć obecne zachowanie **przed** zmianą: 4 klasy wyniku
(`reproduces`/`capsule-stale`/`unexecutable`/`no-capsule`) + kody 7 i 8.

### [x] 2.3 `reproduce` jako arm baterii pchnięcia — **ZROBIONE** (J-032)

**SEC-0 (warunek wstępny):** rozróżnić `>&` od `>` w `evidence.py`, gałąź `redir == "out"`; `tok.isdigit()` dopuszczalne wyłącznie po `>&`. Zamyka SEC-1 bez ruszania `2>&1`.

Mapowanie kodów wyjścia — **rozszerzone wobec wytycznych (J-011)**:

| exit | znaczenie | decyzja |
|---|---|---|
| 0 | wszystko się odtwarza | przepuść, **nic nie zapisuj** |
| 7 | rozbieżność dowodu | **BLOKUJ**, pokaż które claimy |
| **8** | **zbadano 0 claimów** | **BLOKUJ** — ADR-042 reguła 2: sweep, który nic nie zbadał, nie jest sukcesem |

Wytyczne opisywały tylko 0 i 7. Bez arm'a na 8 pusty lub uszkodzony ledger
przechodziłby przez bramkę po cichu.

**Weryfikacja:** `bash .githooks/pre-push` w sandboxie; czas < 2 s.

### [x] 2.4 Wygaszenie `invalidate-scan` — **ZROBIONE**, dwa hooki nie jeden (J-033)

### [x] 2.5 Zwężenie stanu `stale` w foldzie — **ZROBIONE** (J-035)
Zrealizowane jako **reguła podwójnego invalidation**, nie jako pełne usunięcie
`stale`: unieważnienia ścieżkowe są inertne, unieważnienia zegarowe TTL
(ADR-019) nadal zestalają. Powód, dla którego `stale` nie znika w całości, jest
w J-034 USTALENIE 1: TTL to fakt zegarowy, którego `reproduce` nie zastąpi —
claim z wygasającym dziś TTL odtwarza się dziś idealnie.

Żywa ścieżka folda: `unverified` → `live` → `diverged`/`retracted`, ze `stale`
zawężonym do ramienia zegarowego. Dyskryminator: `kernel.ttl_invalidation`,
wołany przez fold, replay w `reports` i `staling_report` — jedna implementacja.

Metryka półokresu przekierowana na `live -> diverge` (decyzja operatora,
opcja 2 z J-034). Pomiar: 1963 obserwacje → 58, mediana P1 0,04 d → 0,81 d.

**Pomiar, który uzasadnia krok:** na 1997 rekordów `invalidation` w tym ledgerze
**zero** niesie sygnał TTL. Cała masa to proxy ścieżkowe.

### [x] 2.6 Wycofanie komend `invalidate-scan` i `reaffirm` — **ZROBIONE** (J-035)

**KOREKTA WYTYCZNYCH, wykryta przed wykonaniem.** `cmd_invalidate_scan` było
jedynym wywołaniem `decide_invalidation`, a `_ttl_expired` jedynym producentem
rekordów TTL. Dosłowne wycofanie werbu zostawiłoby ADR-019 z czytnikiem i bez
pisarza — czyli cofnęłoby to, co 2.5 właśnie postanowiło zachować. Decyzja
operatora: **zwęzić werb, nie kasować**.

* `INVALIDATORS = (_ttl_expired,)` — `_anchor_unreachable` i
  `_evidence_paths_touched` usunięte.
* `truth invalidate-scan` → **`truth ttl-scan`** („ttl-scan: N claim(s) expired").
* `truth reaffirm` — **usunięty w całości**. Po 2.5 jego jedynym możliwym
  wejściem był claim TTL-stale, który triage odrzucał z kontraktu.
* Ścieżka odczytu nietknięta: `REAFFIRM_BASIS`, `latest_invalidation_reason`,
  `ttl_staleness`, pole `reaffirm_cleared` (1283 rekordy) — `staling_report`
  nadal je klasyfikuje.
* Bonus wykryty po drodze (J-035 USTALENIE 2): wiersz INV-C w `doctor` grepował
  za `invalidate-scan` i **trafiał w komentarz o wycofaniu** w wygaszonym hooku
  — przechodził nad hookiem, który nic nie robi. Przecelowany na `pre-push` +
  `reproduce`; `install-hooks.sh` pisze teraz ten hook (u konsumenta nie istniał).

### [x] Domkniecie po 2.6 — kolejka werdyktow rozstrzygnieta (J-036)

Piec claimow, nie trzy: obsluga dwoch pierwszych odslonila dwa kolejne z tej
samej siodemki, ktore siedzialy za nimi w cieniu `stale`. Trzy nazwane przez
operatora wycofane z `--cause restated --successor`; dwa odkryte po drodze
dostaly `diverge` z rekomendowana komenda tombstone w `basis` — ADR-011 mowi
agentowi konczyc na `diverge`, a bramka odblokowuje sie tak samo. Pelna tabela
"stary -> nastepca" jest w J-036; NIE jest przepisana tutaj, bo ten runbook
stoi w zasiegu `fact-health` i cytowanie w nim wycofanego id jest defektem, a
nie notatka (sweep zlapal dokladnie to na bramce pre-push).

**Odstepstwo od wytycznej (b), z pomiarem:** nowe claimy sa NIEZALEZNE OD
WERSJI — ani zdanie, ani receptura nie nazywa `v0.9.38`. W tym ledgerze
receptura z literalem wersji ma **96% smiertelnosci** (24 z 25 martwe), a trzy
osadzane rodziny mialy juz po 3-5 pokolen umierajacych na tym samym bumpie.
Uzyty wzorzec pochodzi z tego repo: wyciagnij wersje z linii 2 CLI i sprawdz
jej obecnosc w drugiej powierzchni, w obie strony, wiec twierdzeniem jest
*zgadzaja sie*, a nie *obie mowia X*.

**DO ZROBIENIA — trzy tombstone'y u operatora.** Sa to decyzje terminalne
(ADR-011), wiec agent ich nie wykonuje; komendy z konkretnymi id sa w J-036,
sekcje "Co z czym zrobione" i "DO DECYZJI". Jedna z nich usuwa podwojny claim
o nagłowku Scope: ledger niesie dzis dwa zywe claimy o jednym fakcie, jeden
przypiety do biezacej wersji, jeden od niej niezalezny.

**Bramka:** `reproduce` 66/66, 0 capsule-stale, exit 0; bateria wszystkie 10
ramion zielone; push bez `--no-verify`.

**DELTA CANARY — ZERO, wbrew prognozie niżej:** 283 → 283, żadne ramię nie
zostało skasowane. Zgodnie z regułą J-012 każde ramię o wciąż istniejącym
przedmiocie zostało **odwrócone albo przecelowane**, nie usunięte. Wyliczenie
per rodzina: J-035, sekcja „Delta ramion canary".

<details><summary>Oryginalne wytyczne kroku (zachowane dla porównania)</summary>

> **KOREKTA WYTYCZNYCH — patrz J-012.** „Usuń kod komend" musi rozróżnić
> **ścieżkę zapisu** od **ścieżki odczytu**.

* **Usuwamy:** werby CLI `invalidate-scan` i `reaffirm` (ścieżka zapisu).
* **ZOSTAWIAMY:** obsługę odczytu rekordów `invalidation` (1 971 w historii)
  i pola `reaffirm_cleared` (1 283). Ledger jest append-only — fold musi nadal
  czytać historię, inaczej pęknie na własnych danych.
* Pole zamykamy dla nowych rekordów wzorcem ADR-046 (*legacy-admitted, closed
  to new records*) + wpis w `.truth/field-consumer-opt-out`.

**ZADEKLAROWANA Z GÓRY DELTA CANARY:** **15 rodzin FAULT** dotyka
`invalidate-scan`/`reaffirm` — m.in. `FAULT RA (ADR-030)` (10 wzmianek),
`FAULT ST (ADR-050)` (6), `FAULT SD-decay (ADR-032)` (4), `FAULT EF (ADR-051)` (4),
`FAULT L` (2), `FAULT DG/C5` (po 2). Spadek liczby ramion canary w tym kroku
jest **oczekiwany**; wymagane jest wyliczenie w JOURNAL, które ramię zniknęło
i dlaczego jego przedmiot przestał istnieć. Ramię, którego przedmiot **nadal
istnieje**, musi zostać przepisane, nie skasowane.

</details>

---

# FAZA 3 — Polityki obserwacji (defekt D-A)

Dane: 1 ścieżka → 12,6% precyzji; 2–3 ścieżki → 1,9%. Trzy pliki-agregatory
(`template/scripts/truth`, `truth-canary.sh`, `test-truth-core.py`) = 75% zestaleń.

> **PRZELICZENIE PO FAZIE 2 (J-037).** Liczby powyżej mierzyły **fałszywe
> zestalenia**, których po kroku 2.5 nie ma — wniosek się nie zmienia, ale
> dowód pod nim tak. Ocalały koszt zbyt szerokiej obserwacji to **uwaga**:
>
> ```
> 75 aktywnych claimow ze zbiorem obserwacji  ->  60 ROZNYCH zbiorow
> 200 commitow = 1670 linii whispera, srednio 22,6 CLAIMU NAZYWANEGO PRZY
>   JEDNEJ EDYCJI
>   (SPROSTOWANE w J-040: pierwsza wersja podawala 2329 linii i 6,8 na edycje --
>    sumowala po plikach, a whisper emituje jedna linie na CLAIM. Wniosek sie
>    nie zmienil, jest mocniejszy.)
> jedno dotkniecie truth-canary.sh nazywa 31 claimow naraz
> ```
>
> Reużywalność bliska zeru — to jest D-A wyrażone liczbą dla świata po
> Reproduce-on-Read, i to jest podstawa danych dla twardej odmowy w 3.2.

### [x] 3.1 `.truth/watch-policies` + walidator — **ZROBIONE** (J-037)

**Format liniowy, nie YAML** (decyzja 2026-08-17). Jedna polityka na linię:

```
name -- path,path,path
```

Powód: README obiecuje *„no dependencies beyond Python 3 and git"*. YAML
kosztowałby albo zależność (złamanie obietnicy), albo własny parser. Format
liniowy jest zgodny z **wszystkimi pięcioma** istniejącymi plikami polityk
(`evidence-allow`, `evidence-deny`, `generated-paths`, `citation-scope`,
`arm-subject-opt-out`) i z kontraktem ich loaderów: **stdlib-only, SI-4,
R14a — loader ZWRACA błąd, wołający decyduje.**

**Wykonane dokładnie w tym kontrakcie:** `load_watch_policies()` w `shellio.py`
zwraca `(policies, state, err)`; czyste `watch_policy_error` /
`watch_policy_conflict_error` w `policy.py` (DAG ADR-044: `shellio` nie może
importować `policy`, więc czyta bajty, a decyduje `policy` — składa `cli`).
Flagi: `claim --watch-policy NAME` (polityka **rozwiązuje** zbiór przed tabelą
`INTAKE_GATES`, więc INV-M sądzi jej globy jak listę z ręki) oraz
`list --watch-policy NAME` — czytelnik pola wymagany przez ADR-046, a przy tym
widok migracji (`-` wypisuje backlog).

Payload niesie **nazwę i rozwiązane globy**: ledger jest append-only, więc
późniejsza edycja pliku polityk nie może przepisać tego, co przeszłe claimy
uważa się za obserwujące. Nazwa to proweniencja, globy to zapis.

Siedem odmów, każda głośna: nieznana nazwa (wylicza istniejące — typo nie może
po cichu złożyć claimu obserwującego NIC, defekt INV-M), `--watch-policy`
razem z `--paths`, pathspec magic w linii i w globie, brak separatora, zła
nazwa, duplikat nazwy, polityka bez globów.

**ABSENT jest łagodny**, inaczej niż u sióstr: polityki są opt-in, brak pliku to
stan spoczynku, nie ciemna bramka — więc bez wiersza atestacji i bez wiersza w
`doctor` (koszt ADR-053 nieopłacony po raz trzeci).
### [x] 3.2 Bramka `max_paths` jako wiersz w `INTAKE_GATES` — **ZROBIONE** (J-038)

**Twarda odmowa** (decyzja 2026-08-17), nie advisory: claim z więcej niż jedną
ścieżką podaną z palca jest odrzucany i zmuszony do `--watch-policy <name>`
albo do uzasadnienia. Podstawa danych: 1 ścieżka → 12,6% precyzji, 2–3 ścieżki
→ 1,9%.

> Wiersz dokłada się do tabeli, a `TestIntakeGateFunctions` czyta ją **przez
> `INTAKE_GATES`**, nie po nazwach — nowy wiersz nie wymaga zmiany testów,
> a wiersz usunięty z tabeli wywali `test_gate_table_pre_execution_order_is_pinned`.

**Wykonane.** `MAX_FREEHAND_WATCH_PATHS = 1`; wiersz `paths-budget-max` zaraz po
`paths-inv-m` i **przed** `scope-decay-adr032` (bo `--paths-ok` jest jedną z
trzech podstaw, które ten wiersz wygasza). Flaga `--paths-ok "<zdanie>"` zapisuje
`paths_basis`, wygasa po 30 dniach z `ttl_default=True` i liczy się jako
`paths_basis_filings` w `override_report()`.

Odmowy symetryczne wg precedensu ADR-035: `--paths-ok` przy jednej ścieżce i
`--paths-ok` obok `--watch-policy` są odrzucane — podstawa, która niczego nie
usprawiedliwia, to szum schematu, a tutaj gorzej, bo wygaszałaby osąd,
którego nikt nie musiał podjąć.

Pin kolejności **padł, jak przewidziano**, i został zaktualizowany. Canary
zablokował baterię na trzech ramionach filujących po dwie ścieżki (`FAULT T`,
`FAULT RA`, `DW6`) — przedmiot każdego nadal istnieje, więc każde dostało
`--paths-ok`, nie kasację (J-012). `DW6` jest wzorcowym przypadkiem użycia
flagi: arm **musi** obserwować nazwę sprzed i po `git mv`, bo bada sam wpis
rename, i żadna polityka takiego zbioru nie nazwie.
### [ ] 3.3 Migracja pozostałych claimów na polityki

**Skala zmierzona przed wykonaniem (J-038):**

```
backlog freehand ze sciezkami:                        78
  SZEROKIE (>1 sciezka, dzis odrzucone przez bramke): 46
  w budzecie (1 sciezka, legalne jak sa):             32
z 46 szerokich: 13 pasuje DOKLADNIE do jednej z 9 polityk
                33 nie pasuje do zadnej -- w 32 ROZNYCH zbiorach
```

Liczba **32** rozstrzyga kształt kroku: nazwanie 32 kolejnych polityk byłoby tym
samym defektem z nową etykietą — polityka użyta raz to lista ścieżek z nazwą.

**Koszt jest asymetryczny:** claim jest niezmienny, więc migracja = re-file +
weryfikacja z osobnej sesji + **retrakcja bramkowana człowiekiem**. 46 claimów
to ~138 nowych rekordów i 46 ceremonii tombstone, żeby zmienić pole metadanych
w faktach, które są prawdziwe i poprawnie obserwowane. Zakres — decyzja
operatora.

---

# FAZA 4 — `truth health` (defekt D-B)

### [x] 4.1 Model odczytu — jedna projekcja nad `fold()` — **ZROBIONE** (J-041)
### [x] 4.2 Werb `truth health [--json]` — **ZROBIONE** (J-041)
### [x] 4.3 Zwinięcie 5 instrumentów Tier C + **odwrócenie ADR-046** — **ZROBIONE** (J-042)

> **Obiekcja O4:** `truth health` **ships do konsumenta**, a zwijane instrumenty
> są celowo meta-repo-only. To odwrócenie podziału tierów — uzasadnione
> (`structure.md` nazywa tę asymetrię „największym pojedynczym ryzykiem
> systemu"), ale **musi być zapisane jako decyzja.**

**Rozstrzygnięte (J-041/J-042).** Odwrócenie zapisane w
`template/docs/ARCHITECTURE.md` rozdz. 4, bez nowych ADR-ów (r18), wraz z
powodem: `instruments/` **nie jest szablonowane**, więc konsument nie widział
pięciu pomiarów **wcale** — ani prędkości nadużyć, ani separacji weryfikatora,
ani churnu, ani przyczyn retrakcji, ani rozbicia zestaleń.

Pomiar zmienił kształt kroku 4.3: cztery z pięciu instrumentów **już wołały te
same czyste funkcje**, które komponuje `health_report()`, więc duplikacji logiki
nigdy nie było — zwinięcie dostarczył 4.2. Pliki **zostały**, oznaczone
nagłówkiem („widok meta-repo na sekcję, którą `health` wysyła; obie ścieżki
wołają tę samą funkcję"), bo ich skasowanie to zamiatanie governance'u:
`docs/governance/gate-metrics.md` deklaruje je jako ŹRÓDŁO metryk adopcji
ADR-047, a przepisanie tego rejestru należy do jego właściciela.

Granica nazwana: `field-consumers.py` i `arm-index.py` **zostają na zawsze** —
skanują kod źródłowy, nie ledger.
>
> **Gdzie zapisać** (decyzja 2026-08-17): bezpośrednio w
> `template/docs/ARCHITECTURE.md`, rozdział 4, oraz w `01-JOURNAL.md`.
> **Nie tworzymy nowych plików ADR w produkcie** — 54 ADR-y wyjechały do
> `docs/archive/adr/` w kroku 1.3, a dopisanie tam nowego rekordu przestałoby
> czynić z archiwum archiwum.

---

## Poza zakresem

1. **Kontrfakt produktu** — czy `diverge` łapie rzeczy, których nie złapałby
   test/CI/review. Nierozstrzygalne w tym repo. Obce repo, 10–20 claimów
   dziedzinowych, 4–6 tyg., próg ≥3 trafienia unikalne.
2. **Jakość receptur** — 78% to sprawdzenia kształtu; hash nie wykrywa zmiany
   wartości. Znana granica zasięgu, **nie do zaklejenia automatyzacją** (O2).
3. **Mutation score** — nie blokuje: przy każdym wyniku akcja jest ta sama.

---

## Dziennik statusów

> Tabela była nieaktualna do r18 (pokazywała 1.1 „GOTOWE DO STARTU", gdy Fazy
> 1 i 2 były dawno zamknięte) — a to jest plik, który deklaruje się jako
> **jedyne źródło prawdy o postępie**. Odtąd aktualizowana razem z nagłówkiem.

| krok | status | commit |
|---|---|---|
| 0 — runbook + journal | **[x] ZROBIONE** | `b98bf00` |
| r2 — wytyczne wykonawcze + 6 korekt | **[x] ZROBIONE** | `441ddd6` |
| **FAZA 0** | **[x] ZAMKNIĘTA** | |
| 0.1 + SEC-0 — martwe bramki zdrowia, kanał zapisu | **[x] ZROBIONE** (J-020) | `8970f5d` |
| **FAZA 1** | **[x] ZAMKNIĘTA** (J-028) | |
| 1.1 — audyt screenera, werdykt GO | **[x] ZROBIONE** (J-017) | `72a0099` |
| 1.2 — przekierowanie claimów ADR, 14/14 | **[x] ZROBIONE** (J-022, J-025) | `739d697`, `020b3ef` |
| 1.3 — `ARCHITECTURE.md` + archiwizacja 54 ADR-ów | **[x] ZROBIONE** (J-027, J-028) | `0e3112d`, `687dbdc` |
| **FAZA 2** | **[x] ZAMKNIĘTA** (J-035, J-036) | |
| 2.1 — inwentarz powierzchni | **[x] ZROBIONE** (J-029) | `f405eed` |
| 2.2 — testy charakteryzujące `reproduce` | **[x] JUŻ ISTNIAŁY**, zweryfikowane (J-030) | — |
| 2.3 — `reproduce` jako arm baterii pchnięcia | **[x] ZROBIONE** (J-032) | `49588e6` |
| 2.4 — wygaszenie `invalidate-scan` w dwóch hookach | **[x] ZROBIONE** (J-033) | `1858e7a` |
| 2.5 — zwężenie stanu `stale` w foldzie | **[x] ZROBIONE** (J-034 stop, J-035 wznowione) | `95fe01f`, `c0ff7f3` |
| 2.6 — wycofanie `invalidate-scan` i `reaffirm` | **[x] ZROBIONE** (J-035) | `c0ff7f3` |
| domknięcie po 2.6 — kolejka werdyktów | **[x] ZROBIONE** (J-036) | `de3c0a7`, `c43bfe7` |
| — oracle `gates.py` przed Fazą 3 | **[x] ZROBIONE** (dossier F-18/F-20) | `cc3aef0` |
| **FAZA 3 — polityki obserwacji** | **[x] ZAMKNIĘTA** | |
| 3.1 — `.truth/watch-policies` (format liniowy) + walidator | **[x] ZROBIONE** (J-037) | |
| 3.2 — bramka `max_paths` + `churn_budget` (twarda odmowa) | **[x]** (J-038, J-039) | `79750ed`, `0dbfc87` |
| 3.3 — migracja celowana pomiarem (2. tura odrzucona) | **[x]** (J-040) | `f4039b3` |
| **FAZA 4 — `truth health`** | **[x] ZAMKNIĘTA** | `0131a92`, `7f7ffbd` |
| 4.1 — model odczytu, jedna projekcja nad `fold()` | **[x]** (J-041) | `0131a92` |
| 4.2 — werb `truth health [--json]` | **[x]** (J-041) | `0131a92` |
| 4.3 — inwariant w ARCHITECTURE + odwrócenie ADR-046 | **[x]** (J-042) | `7f7ffbd` |
