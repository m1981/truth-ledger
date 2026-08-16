# RUNBOOK — refaktor "Reproduce-on-Read"

> **To jest jedyne źródło prawdy o postępie.** Status zadania żyje TU, nie w
> pamięci sesji. Notatki empiryczne idą do `01-JOURNAL.md`.
> Jedno zadanie naraz. Po każdym: weryfikacja → status → wpis w JOURNAL → commit.

Gałąź robocza: `claude/git-hooks-architecture-zc97y3`
Commit bazowy: `fa2e85b`

---

## Teza refaktoru

Zestalenie (`stale`) to zmienna **zastępcza** o wartości predykcyjnej 3,6%,
używana jako zmienna **decyzyjna**, przy dostępnym pomiarze **bezpośrednim**
(`truth reproduce`) o koszcie 0,53 s na cały żywy ledger.

Kierunek: **nie przechowywać kotwic ani stanu `stale`; liczyć odtwarzalność
przy odczycie.** Precedens jest w tym repo — ADR-046 zrobił dokładnie to
z `blast_forecast` ("computed on read, not stored").

Czego refaktor **nie** rozstrzyga: czy produkt tworzy wartość. To zostaje przy
eksperymencie na obcym repozytorium (patrz §Poza zakresem).

---

## Bramka regresji — po KAŻDYM kroku

```bash
cd /home/user/truth-ledger
python3 template/scripts/test-truth-core.py   2>&1 | tail -3
python3 template/scripts/test-truth-v04.py    2>&1 | tail -3
python3 template/scripts/test-integrations.py 2>&1 | tail -3
(cd template/scripts && bash truth-canary.sh  2>&1 | tail -2)
```

**Wartości bazowe (2026-08-16, `fa2e85b`) — każde odchylenie wymaga wpisu
w JOURNAL PRZED commitem:**

| suita | wynik bazowy | uwaga |
|---|---|---|
| test-truth-core | `Ran 394`, **1 failure, 3 skipped** | porażka i skipy **środowiskowe** — brak `jsonschema` (J-002) |
| test-truth-v04 | `Ran 13`, OK | — |
| test-integrations | `Ran 28`, **1 failure** | porażka **środowiskowa** — klon shallow (J-003) |
| truth-canary | **283 caught, 0 missed** | pełna zieleń; 44,8 s |

Reguła F1 stosowana do tego runbooka: **wzrost liczby skipów albo spadek
liczby ramion canary to PORAŻKA**, nawet gdy suita pisze OK.

---

## Metryki, które refaktor ma poruszyć

Pomiar bazowy 2026-08-16 — cel jest po prawej. Mierzone tą samą komendą po
każdej fazie.

| metryka | baseline | cel po Fazie 2 |
|---|---:|---:|
| rekordy w ledgerze | 4 555 | bez wzrostu z tytułu szumu |
| `invalidation` | 1 971 | brak nowych |
| `reaffirm_cleared` | 1 283 (28% ledgera) | brak nowych |
| PPV zestalenia | 3,6% | n/d — sygnał znika |
| koszt `reproduce` (61 żywych) | 0,53 s | ≤ 2 s |
| ADR-y / wycofane | 54 / **0** | 54 / ≥1 (Faza 5) |

```bash
# odtworzenie metryk
python3 template/scripts/truth reproduce | tail -2
wc -l .truth/claims.jsonl
```

---

## FAZA 1 — Audyt bezpieczeństwa (BLOKUJE Fazę 2.4)

Powód: Faza 2 przenosi wykonanie receptur z komendy ręcznej do automatycznego
wyzwalacza. To zmiana modelu zagrożeń — receptury to komendy powłoki zapisane
w pliku danych, który może przyjść z cudzej gałęzi.

### [ ] 1.1 Audyt screenera dowodowego — READ-ONLY
Czy allowlista (`.truth/evidence-allow`) zamyka metaznaki powłoki: `;`, `&&`,
`|`, `` ` ``, `$()`, `>`, `<`, rozwinięcia glob?
Zero zmian w kodzie produkcyjnym. Próby wyłącznie w sandboxie `mktemp -d`.

**Weryfikacja:** tabela prób (komenda → werdykt screenera) w JOURNAL.
**Zaliczone gdy:** każda z ≥8 prób ma zapisany werdykt, a wniosek jest jawnym
**GO** albo **NO-GO** dla 2.4.

### [ ] 1.2 Decyzja o automatycznym wykonaniu receptur
Zapis decyzji w JOURNAL. Przy GO — ADR. Przy NO-GO — Faza 2 kończy się na 2.3
(`reproduce` pozostaje na pre-push, `invalidate-scan` zostaje wyłączony bez
zastępnika automatycznego).

**Zaliczone gdy:** decyzja zapisana z uzasadnieniem opartym na 1.1.

---

## FAZA 2 — Reproduce-on-Read (rdzeń)

### [ ] 2.1 Inwentarz powierzchni — READ-ONLY
Kto **pisze** i kto **czyta**: `anchor_commit`, status `stale`, `reaffirm_cleared`,
`invalidation`. Narzędzie już istnieje: `instruments/field-consumers.py`.

**Weryfikacja:** `python3 instruments/field-consumers.py`
**Zaliczone gdy:** lista wywołań (plik:linia) dla każdego z 4 pól w JOURNAL.

### [ ] 2.2 Testy charakteryzujące `reproduce`
Przypiąć OBECNE zachowanie zanim cokolwiek się ruszy: 4 klasy wyniku
(`reproduces` / `capsule-stale` / `unexecutable` / `no-capsule`) + kody wyjścia 7 i 8.

**Weryfikacja:** nowe testy przechodzą na niezmienionym kodzie.
**Zaliczone gdy:** bramka regresji bez zmian, liczba testów core rośnie.

### [ ] 2.3 `reproduce` jako autorytet na pre-push
**Weryfikacja:** `bash .githooks/pre-push` w sandboxie; czas < 2 s.

### [ ] 2.4 Wyłączenie `invalidate-scan` z post-merge — WYMAGA GO z 1.2
**Weryfikacja:** po scaleniu testowym `wc -l .truth/claims.jsonl` bez przyrostu.

### [ ] 2.5 Usunięcie stanu `stale` z folda
Największy pojedynczy krok. Dotyka `kernel.fold`, `registry` (wokabularz),
`spec-health.sh`, `fact-health.sh` (pobierają `citation_bad` z `truth vocab`).

**Weryfikacja:** bramka regresji + `python3 template/scripts/truth vocab --json`
**Zaliczone gdy:** canary 283/0 albo jawny opis, które ramię zmieniło sens i dlaczego.

### [ ] 2.6 Wycofanie `reaffirm` i `reaffirm_cleared`
Historia jest append-only — **stare rekordy zostają**. Zamykamy pole na nowe
(wzorzec ADR-046: legacy-admitted, closed to new records).

**Weryfikacja:** `python3 instruments/field-consumers.py` — pole zostaje z wpisem
w `.truth/field-consumer-opt-out` i uzasadnieniem.

---

## FAZA 3 — Polityki obserwacji (defekt D-A)

Dane: 1 ścieżka → 12,6% precyzji; 2–3 ścieżki → 1,9%. Trzy pliki-agregatory
(`template/scripts/truth`, `truth-canary.sh`, `test-truth-core.py`) odpowiadają
za 75% wszystkich zestaleń.

### [ ] 3.1 `.truth/watch-policies.yml` + walidator
### [ ] 3.2 Bramka `max_paths` jako wiersz w `INTAKE_GATES`
Mechanizm istnieje: `blast_forecast` już liczy churn obserwowanej ścieżki
i został zdegradowany do raportu. To promocja pomiaru do bramki, nie nowa maszyneria.
### [ ] 3.3 Migracja istniejących claimów na polityki

---

## FAZA 4 — `truth health` (defekt D-B, rozproszenie)

### [ ] 4.1 Model odczytu — jedna projekcja nad `fold()`
### [ ] 4.2 Werb `truth health [--json]`
### [ ] 4.3 Zwinięcie 5 instrumentów Tier C + **ADR odwracający ADR-046**

> **Uwaga architektoniczna (obiekcja O4):** `truth health` jako werb CLI
> **ships do konsumenta**, a zwijane instrumenty są celowo meta-repo-only.
> To odwrócenie podziału tierów z ADR-046 — uzasadnione (`structure.md` sam
> nazywa tę asymetrię "największym pojedynczym ryzykiem systemu"), ale
> **musi być zapisane jako decyzja, nie jako sprzątanie skryptów.**

---

## FAZA 5 — Korpus decyzji (defekt D-D)

**Pomiar (obiekcja O5):** 77 claimów obserwuje pliki ADR, z tego **13 żywych**
na 61 żywych w ogóle (21% żywego ledgera). 15 unikalnych `tr-` id jest
cytowanych wewnątrz korpusu ADR. `git mv` bez przygotowania zamieni te 13
claimów w `unexecutable`.

### [ ] 5.1 Przekierowanie lub wycofanie 13 żywych claimów — PRZED przenoszeniem
**Weryfikacja:** `python3 template/scripts/truth reproduce` — `unexecutable` = 0.
### [ ] 5.2 Przeniesienie wycofanych ADR-ów do `docs/archive/`
**Weryfikacja:** `bash scripts/fact-health.sh` (archive jest już wyłączone ze sweepu).
### [ ] 5.3 `docs/ARCHITECTURE.md` — ~10 żywych zasad

---

## Poza zakresem tego runbooka

1. **Kontrfakt produktu.** Czy `diverge` łapie rzeczy, których nie złapałby
   test/CI/review — nierozstrzygalne wewnątrz tego repozytorium. Wymaga obcego
   repo, 10–20 claimów o faktach dziedzinowych, 4–6 tyg., z polem
   "czy coś innego by to złapało". Próg: ≥3 trafienia unikalne → produkt ma rację bytu.
2. **Jakość receptur.** 78% receptur to sprawdzenia kształtu (`grep -c`, `ls`,
   `wc`) — hash nie wykrywa zmiany wartości. To znana granica zasięgu aparatu,
   zapisana jawnie, **nie do zaklejenia automatyzacją** (obiekcja O2).
3. **Mutation score.** Nie blokuje tego refaktoru: przy każdym wyniku akcja jest
   ta sama. Rozstrzyga kolejność prac, nie kierunek.

---

## Dziennik statusów

| krok | status | commit |
|---|---|---|
| 0 — runbook + journal | **ZROBIONE** | (ten commit) |
| 1.1 | GOTOWE DO STARTU | — |
