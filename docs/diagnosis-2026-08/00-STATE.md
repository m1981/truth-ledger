# Diagnoza truth-ledger — STAN

> **Czytaj to najpierw.** Satelity: `01-findings.md` (pomiary, append-only),
> `02-portfolio.md` (metoda), `raw/` (surowe wyjścia, regenerowalne).
> Odtworzenie pomiarów: `bash docs/diagnosis-2026-08/diagnose.sh`

> **Rozgraniczenie ról.** `docs/refactor/00-RUNBOOK.md` jest jedynym źródłem
> prawdy o **postępie refaktoru**. To dossier odpowiada wyłącznie na **pytanie
> decyzyjne** i dostarcza dowodów. Nie zarządza pracą, nie duplikuje statusu.

**Pytanie decyzyjne:** naprawiać, czy wyłuskać substancję i napisać na nowo.
**Ostatni pomiar:** 2026-08-17, HEAD `dc330c1` (runda 2).

## ► ODPOWIEDŹ: NAPRAWIAĆ — rozstrzygnięte

Ostatni otwarty warunek (mutation score) został zmierzony: **88,5% na rdzeniu,
kernel.py 91,4%** (F-12). Cztery z pięciu warunków uzasadniających rewrite są
sfalsyfikowane; piąty (koszt zmiany rośnie wykładniczo) jest sfalsyfikowany
obserwacyjnie przez F-13 — właściciel zredukował dokumentację produktu o 74%
w dwa dni. **Pytanie decyzyjne jest zamknięte.**

## ► NASTĘPNY KROK

Dobić `gates.py` z 53,8% do ≥80% mutation score **zanim wznowi się krok 2.5
refaktoru** — 12 ocalałych mutantów siedzi dokładnie w logice `paths`, której
semantykę „Reproduce-on-Read" zmienia (F-15). Lista ocalałych:
`python3 scripts/mutation-report.py gates`.

## Status portfela

| # | Analiza | Status | Wynik |
|---|---|---|---|
| 0.1 | mutation score | **ZROBIONE (częściowo)** | F-12: 88,5% na 3 z 11 modułów; kernel 91,4%, gates 53,8% |
| 0.1b | mutation na pozostałych 8 modułach | **TODO** | cli/evidence/policy/reports/shellio/advisory niezmierzone |
| 0.2 | coverage --branch | TODO | — |
| 1.1 | macierz ADR→kod→test | **PRZEDAWNIONE** | ADR-ów w produkcie już nie ma (F-13); przeformułować na ARCHITECTURE.md→kod→test |
| 1.2 | cykl życia ADR-ów | **ZROBIONE** | F-13: 54 ADR-y zarchiwizowane, aktywnych claimów ADR: 0 |
| 1.3 | koszt dodania funkcji | TODO | — |
| 2.1 | import-linter (zamrożenie) | TODO | DAG nadal czysty (F-03) |
| 2.3 | rozłożyć `validate_events` | **TODO — nadal CC=129** | nietknięte przez refaktor; kernel ma 91,4% oracle, więc bezpieczne |
| 3.2 | cicha nieuzbrojona instalacja | TODO | realny tryb awarii (F-08) |
| 3.4 | realni konsumenci | TODO | — |
| — | oracle zielony | ZROBIONE | 398+28 testów, 283 ramiona, 1004 arms |
| — | profil złożoności | ZROBIONE | mediana CC=4, maks 129 — bez zmian |
| — | graf importów | ZROBIONE | czysty DAG |
| — | masa dokumentacji | **ZROBIONE** | F-13 zastępuje F-04 |

## Otwarte pytania

- **`tr-a8bda1a1` jest fałszywe** („54 ADR-y" — jest 0). Retrakcja jest
  human-only. Do decyzji właściciela: retrakcja z `--cause` czy następca (F-16).
- **`invalidate-scan` nie był uruchomiony** od `dc330c1` — 5 z 6 moich twierdzeń
  powinno zestaleć. Nie uruchamiam go jednostronnie na produkcyjnym ledgerze.
- F-07 (ukryte sprzężenia modułów) nadal wymaga przemierzenia po ustabilizowaniu
  podziału `advisory`/`reports`/`contract`.
- Decyzja z J-034 (rodzina `ttl_suggestion`) jest własnością właściciela —
  moja opinia w sekcji niżej, ale to nie jest decyzja tego dossier.

## Decyzje podjęte — NIE relitygować

- **2026-08-17 · REKOMENDACJA: NAPRAWIAĆ. Rozstrzygnięte, nie wstępne.**
  Podstawa: F-12 (88,5%/91,4%) domyka ostatni warunek reguły decyzyjnej.
- **2026-08-17 · Priorytet: oracle `gates.py` przed semantyką `paths`.** Powód:
  F-15 — najcieńsza siatka dokładnie pod miejscem, w którym się spada.
- **2026-08-17 · F-04 zastąpione przez F-13; metryka docs:kod musi rozdzielać
  produkt od warsztatu.** Powód: liczenie ich razem dało fałszywy alarm.
- **2026-08-17 · RUNBOOK jest właścicielem postępu; dossier tylko decyzji.**
  Powód: dwa „jedyne źródła prawdy" to gorzej niż żadne (F-17).
- **2026-08-15 · Pomiary policzalne → VERIFIED z recepturą; wnioski analityczne
  → INFERRED z `--basis`.** Allowlista nie ma `python3` (F-11).
- **2026-08-14 · NIGDY `TRUTH_ALLOW_NO_JSONSCHEMA=1`** — waiver wyłącza połowę
  kontraktu rekordu. Zawsze `PYTHONPATH=$HOME/.cache/truth-ledger-pylib`.
  Właściciel wpiął tę zasadę na stałe w `scripts/mutmut-runner.sh`.

## Opinia do decyzji z J-034 (rodzina `ttl_suggestion`)

Rekomendacja właściciela — opcja (2), przekierować półokres na `diverge` —
jest **słuszna**, z jednym zastrzeżeniem: spadek próbki z 1971 do 70 to nie
jest ta sama metryka o mniejszej mocy, tylko **inna metryka**. Przy n=70 per
tier przedziały ufności będą szerokie na tyle, że kalibracja TTL stanie się
iluzoryczna. Sugestia: opcja (2) **plus** publikowanie n i przedziału obok
wartości, żeby odbiorca widział, kiedy liczba jeszcze nic nie znaczy.
Opcja (1) kasuje jedyne źródło kalibracji; opcja (3) zostawia w produkcie
czytnik martwego formatu — obie gorsze.
