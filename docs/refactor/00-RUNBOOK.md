# RUNBOOK — refaktor "Reproduce-on-Read"

> **To jest jedyne źródło prawdy o postępie.** Status zadania żyje TU, nie w
> pamięci sesji. Notatki empiryczne idą do `01-JOURNAL.md`.
> Jedno zadanie naraz. Po każdym: weryfikacja → status → wpis w JOURNAL → commit.

Gałąź robocza: `claude/git-hooks-architecture-zc97y3`
Commit bazowy: `fa2e85b` · rewizja runbooka: `r11` (2026-08-16, FAZA 1 ZAMKNIĘTA)

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

### [ ] 2.1 Inwentarz powierzchni — READ-ONLY
Kto pisze i czyta: `anchor_commit`, `stale`, `reaffirm_cleared`, `invalidation`.
```bash
python3 instruments/field-consumers.py
```

### [ ] 2.2 Testy charakteryzujące `reproduce`
Przypiąć obecne zachowanie **przed** zmianą: 4 klasy wyniku
(`reproduces`/`capsule-stale`/`unexecutable`/`no-capsule`) + kody 7 i 8.

### [ ] 2.3 `reproduce` jako autorytet na pre-push — WYMAGA zamknięcia SEC-1 (J-017)

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

### [ ] 2.4 Wyłączenie `invalidate-scan` z post-merge

### [ ] 2.5 Usunięcie stanu `stale` z folda
Stan wyliczany z logu: `unverified` → `live` → `diverged`/`retracted`.
Dotyka `kernel.fold`, `registry`, oraz `spec-health.sh`/`fact-health.sh`
(pobierają `citation_bad` z `truth vocab --json` — zmiana wokabularza propaguje
się do nich automatycznie, ale wymaga sprawdzenia).

### [ ] 2.6 Wycofanie komend `invalidate-scan` i `reaffirm`

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

---

# FAZA 3 — Polityki obserwacji (defekt D-A)

Dane: 1 ścieżka → 12,6% precyzji; 2–3 ścieżki → 1,9%. Trzy pliki-agregatory
(`template/scripts/truth`, `truth-canary.sh`, `test-truth-core.py`) = 75% zestaleń.

### [ ] 3.1 `.truth/watch-policies.yml` + walidator
### [ ] 3.2 Bramka `max_paths` jako wiersz w `INTAKE_GATES`
### [ ] 3.3 Migracja pozostałych claimów na polityki

---

# FAZA 4 — `truth health` (defekt D-B)

### [ ] 4.1 Model odczytu — jedna projekcja nad `fold()`
### [ ] 4.2 Werb `truth health [--json]`
### [ ] 4.3 Zwinięcie 5 instrumentów Tier C + **ADR odwracający ADR-046**

> **Obiekcja O4:** `truth health` **ships do konsumenta**, a zwijane instrumenty
> są celowo meta-repo-only. To odwrócenie podziału tierów — uzasadnione
> (`structure.md` nazywa tę asymetrię „największym pojedynczym ryzykiem
> systemu"), ale **musi być zapisane jako decyzja.**

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

| krok | status | commit |
|---|---|---|
| 0 — runbook + journal | ZROBIONE | `b98bf00` |
| r2 — wytyczne wykonawcze + 6 korekt | **ZROBIONE** | (ten commit) |
| 1.1 — audyt screenera | GOTOWE DO STARTU | — |
| 1.2 — przekierowanie 14 claimów ADR | czeka | — |
| 1.3 — archiwizacja + ARCHITECTURE.md | czeka na decyzję A/B | — |
