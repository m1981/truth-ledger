# Ustalenia — APPEND-ONLY

Każdy wpis to **pomiar**, nie opinia: data, komenda, wynik, tripwire.

**Nigdy nie edytuj wpisu w miejscu.** Wniosek odwrócony dodaje się jako nowy
z `zastępuje: F-xx`. Inaczej nie da się odróżnić „zmiana na podstawie dowodów"
od „ktoś przepisał zdanie" — czyli dokładnie tego dryfu, przed którym broni
ten projekt.

Odtworzenie wszystkiego: `bash docs/diagnosis-2026-08/diagnose.sh`

Legenda statusu: **AKTUALNE** · **NIEAKTUALNE** (tripwire zadziałał, wymaga
przemierzenia) · **ZASTĄPIONE przez F-xx**

---

## F-01 · Oracle jest zielony i szybki · AKTUALNE
**2026-08-15**, HEAD `fa2e85b`

```
python3 template/scripts/test-truth-core.py     → 394 testy,  10,3 s, OK
python3 template/scripts/test-integrations.py   →  28 testów, 13,9 s, OK
bash    template/scripts/truth-canary.sh        → 283 caught, 0 missed
```
Wymagane `PYTHONPATH=$HOME/.cache/truth-ledger-pylib`. **Bez tego 3 testy
schematu są cicho pomijane, a suita nadal pisze `OK`.**

> **Werdykt:** ryzyko przepisania dowolnego modułu jest już zneutralizowane.
> To unieważnia klasyczną alternatywę „big rewrite vs incremental".

Tripwire: `template/truthlib/**`, `template/scripts/test-*.py`, `template/scripts/truth-canary.sh`

## F-02 · Złożoność jest SKONCENTROWANA, nie rozproszona · AKTUALNE
**2026-08-15**

```
CC=129   333 lin  kernel.py:447   validate_events()   ← jedyny prawdziwy potwór
CC= 45   187 lin  cli.py:229      cmd_verdict()
CC= 38   234 lin  cli.py:1329     cmd_doctor()
CC= 36   137 lin  cli.py:720      cmd_done()
CC= 32   127 lin  evidence.py:178 screen_evidence_command()
razem 6245 loc / 173 funkcji / MEDIANA CC = 4
```

> **Werdykt:** mediana 4 przy maksimum 129 oznacza, że 168 ze 173 funkcji jest
> w porządku. To profil kodu do **naprawy punktowej**, nie do przepisania.

Tripwire: `template/truthlib/**`

## F-03 · Graf importów jest czystym DAG-iem · AKTUALNE
**2026-08-15**

```
registry ← kernel ← {policy, evidence, shellio}
                  ← {gates, advisory, reports, contract} ← cli
CYKLE: brak
```
`registry` to czysty sink (0 importów), `cli` to jedyny root (9 importów).

> **Werdykt:** warstwy trzymają. Do **zamrożenia** kontraktem (import-linter),
> nie do naprawy.

Tripwire: `template/truthlib/*.py`

## F-04 · Masa dokumentacji: 3,5× kodu · AKTUALNE
**2026-08-15**

```
kod biblioteki    6 245 linii
dokumentacja     21 846 linii w 107 plikach
ADR-y                54
```

> **Werdykt:** to jest największe ryzyko strukturalne projektu — nie jakość
> kodu. Aparat zarządczy cięższy od mechanizmu, którym zarządza. Wymaga
> analizy 1.2 (czy ADR-y są kiedykolwiek wycofywane), bo rośnie liniowo.

Tripwire: `docs/**`, `template/docs/**`

## F-05 · Realne cykle konceptualne ADR — dwa, oba zweryfikowane w źródle · AKTUALNE
**2026-08-14**, narzędzie: `labels-deps` (`~/PycharmProjects/labels-deps`)

Graf ADR-only: 48 węzłów, 85 krawędzi, **nie jest DAG-iem**. Po odcięciu
krawędzi wagi 1 przeżywa jeden cykl:

- `ADR-009 ⇄ ADR-014` (w=3/4) — `screen_command` i `screen_accept_command`
  cytują się wzajemnie w docstringach: *„a second screen implementation is
  forbidden"*. Sprzężenie **celowe**, ale realne.
- `ADR-016 ⇄ ADR-031` (w=1/6) — `fold_key` ↔ `order_check`.

> **Werdykt:** nie anty-wzorzec, ale dowód, że tych decyzji nie da się zmieniać
> niezależnie. Do odnotowania przy każdym refaktorze `evidence.py`/`kernel.py`.

Tripwire: `template/truthlib/evidence.py`, `template/truthlib/kernel.py`

## F-06 · Decyzje są niemal wyłącznie przekrojowe · AKTUALNE
**2026-08-14**, narzędzie: `labels-deps`

**48 z 49 ADR-ów dotyka ≥2 plików kodu.** Tylko jeden jest zamknięty w jednym
pliku. Rekordziści: ADR-046 (16 plików), ADR-003/007/037 (po 11).

> **Werdykt:** wymierne *shotgun surgery*. Każda zmiana decyzji to zmiana
> wieloplikowa. Wyjaśnia, dlaczego churn idzie w testy, nie w kod.

Tripwire: `template/truthlib/**`, `template/scripts/**`

## F-07 · Ukryte sprzężenia modułów · NIEAKTUALNE
**2026-08-14** — tripwire zadziałał: `advisory.py` zostało wypatroszone
(−732 linie → `reports.py` + `contract.py`) w commicie po pomiarze.

Pomiar był: `advisory ~ gates` (J=0,28, 8 wspólnych ADR, zero importu),
`evidence ~ policy` (J=0,40, 10 wspólnych ADR, zero importu). Korelacja grafu
etykiet z grafem importów wynosiła 22/28 par.

> **Wymaga przemierzenia** po ustabilizowaniu podziału `advisory`/`reports`.

Tripwire: `template/truthlib/*.py` — **zadziałał 2026-08-15**

## F-08 · Aparat wykrył realny dryf w praktyce · AKTUALNE
**2026-08-14**, źródło: `.local/machine.md` (zmierzone przez właściciela)

`core.hooksPath` było **nieustawione przez co najmniej dwa wydania**
(v0.9.36, v0.9.37) — bramka commitowa, bramka pchnięcia i skan po commicie nie
działały. Pierwszy skan po uzbrojeniu **nadrobił 13 zaległych zestaleń**.

> **Werdykt dwustronny:** (a) mechanizm wykrywa realny dryf — to najmocniejszy
> dowód wartości produktu, jaki mamy; (b) **cicha nieuzbrojona instalacja jest
> realnym trybem awarii** i zasługuje na osobną pozycję w portfelu.

Tripwire: `.githooks/**`, `template/scripts/install-hooks.sh`

## F-09 · Naprawa już trwa i idzie we właściwym kierunku · AKTUALNE
**2026-08-15**, zakres `ea9f542..fa2e85b`

```
36 plików, +2 551 / −3 319  (netto −768 linii)
A1  refusals return, the shell exits
A3  retire the entry-point monkeypatch mirror
A4  cli: main() becomes a verb table
A6  the arm index -- 1221 arms answer what they guard
    5 plików scaffoldingu bash (−922 lin) → test-integrations.py (+795)
    advisory.py (−732) → reports.py (+663) + contract.py (+74)
```

> **Werdykt:** właściciel wykonuje ścieżkę „naprawiać", z issue'ami w ledgerze,
> i **redukuje** masę. To falsyfikuje hipotezę „projekt utknął".

Tripwire: `git log` (nie ma ścieżki — odświeżać przy każdej sesji)

## F-10 · Instrument `arm-index` pokrywa połowę analizy 1.1 · AKTUALNE
**2026-08-15**, `python3 instruments/arm-index.py`

```
1 000 ramion w 195 rodzinach nad 9 instrumentami — 2 failure(s)
  seeded-fault  593 · unit-test 407 · 77 odrębnych subjectów
  2 rodziny w canary nie deklarują subjectu
  45 rodzin ostrzeżonych (species REPORTED, nieegzekwowany)
```

> **Werdykt:** kierunek test→ADR jest już zbudowany i egzekwowany. **Brakuje
> kierunku odwrotnego**: ADR bez ani jednego ramienia = decyzja nieegzekwowana.
> To domyka `labels-deps` (ADR→kod) + arm-index (ADR→test). Patrz portfel 1.1.

Tripwire: `instruments/arm-index.py`, `template/scripts/test-*.py`, `template/scripts/truth-canary.sh`

## F-11 · Allowlista dowodowa ogranicza, co da się śledzić jako claim · AKTUALNE
**2026-08-15**, `.truth/evidence-allow`

Dozwolone są wyłącznie deterministyczne komendy odczytu (`grep ls cat head
tail wc find sort uniq cut tr diff comm echo printf test basename dirname
realpath stat sha256sum shasum md5sum jq`). Brak `python3`, brak `bash`
(ADR-021/022: generyczny wykonawca nie przechodzi).

Konsekwencja dla tej diagnozy: twierdzenia **policzalne** (LOC, liczby testów,
liczby ramion) idą jako `--class VERIFIED` z recepturą; wnioski **analityczne**
(CC, acykliczność, rekomendacja) idą jako `--class INFERRED --basis`, bo ich
receptura nie jest wyrażalna. Wciskanie ich jako VERIFIED byłoby dokładnie tym
pustym VERIFIED, które ADR-035 odrzuca.

> **Werdykt:** świadomy kompromis (determinizm > wyrazistość), nie wada. Ale
> to realna granica zasięgu aparatu i należy ją nazwać w ocenie produktu.

Tripwire: `.truth/evidence-allow`, `template/truthlib/evidence.py`

---

# Runda 2 — 2026-08-17, HEAD `dc330c1` (25 commitów od `fa2e85b`)

## F-12 · Mutation score: 88,5% na rdzeniu · AKTUALNE
**2026-08-17**, `python3 scripts/mutation-report.py` (cache z 2026-08-15)

```
kernel.py     342/374   91,4%
contract.py    14/18    77,8%
gates.py       14/26    53,8%   ← słaby punkt
RAZEM         370/418   88,5%
```

> **Werdykt: analiza 0.1 odpowiedziana dla rdzenia i próg 80% przekroczony.**
> To domyka ostatni otwarty warunek reguły decyzyjnej. **Rekomendacja NAPRAWIAĆ
> przestaje być wstępna.**
>
> **Ale:** przebieg objął 3 z 11 modułów (418 mutantów). `cli.py`, `evidence.py`,
> `policy.py`, `reports.py`, `shellio.py`, `advisory.py` są **niezmierzone**.

Tripwire: `.mutmut-cache`, `template/truthlib/**`

## F-13 · Ryzyko z F-04 zaadresowane: dokumentacja produktu zapadła się o 74% · ZASTĘPUJE F-04
**2026-08-17**

```
template/docs (DYSTRYBUOWANE)   64 pliki / 8 041 lin  →  11 plików / 2 096 lin
ADR-y w produkcie                            54  →  0  (docs/archive/adr/, 6 168 lin)
zastąpione przez                 template/docs/ARCHITECTURE.md, 217 linii
docs/ (meta-repo, warsztat)                 102 pliki / 22 203 lin  (rosło)
```
Stosunek docs:kod **dla produktu**: 1,29× → **0,33×**.

> **Werdykt:** właściciel zaadresował dokładnie to, co F-04 wskazywało jako
> największe ryzyko strukturalne — i zrobił to poprawnie: archiwum zamiast
> kasowania (uzasadnienia przeżyły), synteza zamiast serii.
>
> **Korekta mojego pomiaru:** F-04 liczyło `docs` + `template/docs` razem,
> mieszając **warsztat** z **produktem**. To był błąd metryki. Masa warsztatu
> rośnie i to jest w porządku; masa produktu spadła i to było ryzyko.

Tripwire: `template/docs/**`, `docs/archive/adr/**`

## F-14 · Teza refaktoru unieważnia interpretację F-08 · AKTUALNE
**2026-08-17**, źródło: `docs/refactor/00-RUNBOOK.md`

> „Zestalenie (`stale`) to zmienna **zastępcza** o wartości predykcyjnej
> **3,6%**, używana jako zmienna **decyzyjna**, przy dostępnym pomiarze
> bezpośrednim (`truth reproduce`) o koszcie **0,53 s** na cały żywy ledger."

> **Werdykt dwustronny i ważniejszy niż F-08:**
> (a) F-08 czytałem jako „mechanizm wykrywa realny dryf — 13 zaległych
> zestaleń". Przy 3,6% trafności **~12 z tych 13 to szum**. Moja interpretacja
> była zbyt łaskawa.
> (b) Ale wniosek o produkcie jest **mocniejszy**, nie słabszy: pomiar
> bezpośredni kosztuje pół sekundy. Wartościowa jest *teza* (fakty gniją wraz
> z dowodem), a nie jej konkretna implementacja przez kotwice i stan `stale`.
> **To jest dokładnie „wyłuskać substancję" — wykonane wewnątrz projektu.**

Tripwire: `docs/refactor/00-RUNBOOK.md`, `template/truthlib/kernel.py`

## F-15 · Najsłabszy oracle pokrywa się z zakresem refaktoru · AKTUALNE
**2026-08-17**, złączenie F-12 z `docs/refactor/00-RUNBOOK.md`

`gates.py` ma **najniższy mutation score (53,8%)**, a wśród 12 ocalałych
mutantów są dokładnie te dotyczące `paths`:
```
#392 L86   paths = ctx["paths"]
#393 L87   if not paths:
#394 L124  if not ctx["paths"]:
#397 L177  if not ctx["paths"]:
```
Refaktor „Reproduce-on-Read" **usuwa kotwice i stan `stale`**, czyli zmienia
semantykę dokładnie tej logiki.

> **Werdykt — najważniejsze ryzyko operacyjne, jakie ta runda znalazła:**
> zmiana semantyki jest prowadzona w module, którego oracle przepuszcza prawie
> połowę mutantów. Sieć bezpieczeństwa jest najcieńsza dokładnie tam, gdzie
> spada się z liny.
>
> **Zalecenie: dobić `gates.py` do ≥80% ZANIM wznowi się krok 2.5.**

Tripwire: `template/truthlib/gates.py`, `.mutmut-cache`

## F-16 · Moje twierdzenia nie zestalały mimo unieważniających zmian · AKTUALNE
**2026-08-17**

Sześć twierdzeń z 2026-08-15 ma status `unverified`, **żadne nie jest `stale`**,
mimo że ich watched paths się zmieniły. `tr-a8bda1a1` („54 ADR-y…") jest
**faktycznie fałszywe**: `template/docs/adr/truth/` zawiera 0 plików.

Przyczyna: kotwica = `fa2e85b`, zmiany są w `fa2e85b..dc330c1`, ale
`invalidate-scan` nie był uruchomiony od zacommitowania claimów w `dc330c1`.

> **Werdykt:** poprawność ledgera zależy od **uruchomienia skanu**, nie od
> samego zapisania kotwicy. Dopóki hook nie odpali, fałszywe twierdzenie
> wygląda w `truth list` identycznie jak prawdziwe. To wzmacnia tezę refaktoru
> (F-14): stan przechowywany wymaga dyscypliny odświeżania, stan liczony przy
> odczycie nie.
>
> **Wymaga działania właściciela:** retrakcja jest human-only. `tr-a8bda1a1`
> do retrakcji z `--cause`, ewentualnie następca z poprawną liczbą.

Tripwire: `.truth/claims.jsonl`

## F-17 · Właściciel zbudował ten sam wzorzec dossier niezależnie · AKTUALNE
**2026-08-17**

`docs/refactor/00-RUNBOOK.md` („**To jest jedyne źródło prawdy o postępie.**
Status zadania żyje TU, nie w pamięci sesji") + `01-JOURNAL.md` (83 wpisy,
J-001…J-034) to dokładnie rozdzielenie metoda/stan ↔ dziennik append-only,
które zaprojektowałem w tym dossier.

> **Werdykt:** zbieżność projektowa potwierdza wzorzec, ale tworzy ryzyko
> **dwóch „jedynych źródeł prawdy"**. Rozgraniczenie przyjęte w `00-STATE.md`:
> RUNBOOK jest właścicielem *postępu refaktoru*; to dossier odpowiada wyłącznie
> na *pytanie decyzyjne* i nie zarządza pracą.

Tripwire: `docs/refactor/**`

---

# Runda 3 — 2026-08-17, działanie naprawcze

> Zadanie zlecało zapis jako „F-12". Ten numer jest zajęty (mutation score
> rdzenia, runda 2), a numery są append-only — nadpisanie F-12 zerwałoby
> właśnie tę własność, która pozwoliła wykryć zgniłe wnioski w rundzie 2.
> Wpis dostaje kolejny wolny numer.

## F-18 · `gates.py`: luka z F-15 zamknięta · AKTUALNE
**2026-08-17**, działanie na podstawie F-15

```
                     przed        po
pokrycie linii        29 %       86 %   (13 z 90 instrukcji niepokrytych)
mutation score      53,8 %     94,9 %   (14/26  ->  37/39)
testy w suicie         372        403   (+31, czas suity 4,2 s -> 7,1 s)
```

Nowe klasy w `template/scripts/test-truth-core.py`:
* `TestIntakeGateFunctions` (26) — każdy wiersz `INTAKE_GATES` osobno,
  osiągany **przez tabelę**, nie po nazwie: wiersz, który przestanie być
  podpięty, wywala test zamiast cicho zniknąć. Wszystkie czysto pamięciowe.
* `TestGeneratedPathsGate` (5) — korpus bramki ADR-037 przez jedyny wspierany
  seam (`truthlib.configure(repo_root=…)`, A3). Czyta jeden plik polityki:
  bez gita, bez zegara, bez podprocesu.

**Technika warta zapamiętania:** tam gdzie odwrócenie strażnika wpadłoby w I/O
gate'a, asercja jest na **braku klucza**, który to I/O stempluje w `ctx`
(`generated_source`, `blast_state`). Nieobecność klucza jest dowodem, że
early return zadziałał — to pinuje gałąź w obie strony, nie łamiąc kontraktu
„no git, no filesystem" tego pliku.

**2 ocalałe mutanty, oba zweryfikowane jako RÓWNOWAŻNE** (`mutate.sh show`):
* `#8 L50` `and`→`or` w `(similar and ctx["duplicate_ok"])` — gdy `similar`
  jest puste, generator daje `[]` niezależnie od operatora; gdy niepuste
  a `duplicate_ok` fałszywe, gate zwrócił już odmowę. Żaden osiągalny stan
  nie rozróżnia wariantów.
* `#15 L79` `flag = None` — `flag` trafia wyłącznie do komunikatu, który
  `override_decay` zwraca trzecim elementem, a gate odrzuca go przez `_`.
  Nieobserwowalne bez zmiany kodu produkcyjnego.

94,9 % to zatem **sufit dla obecnego kształtu `gates.py`**, nie plateau
testów.

**Niepokryte pozostają 100-119 i 180-185** — korpus odmów INV-M
(`tracked_files()` = `git ls-files`) i korpus prognozy blast
(`blast_history()` = `git log`). Oba wymagają gita, a `CONFIGURABLE` obejmuje
tylko `repo_root`/`ledger_path`. Domknięcie ich to decyzja o rozszerzeniu
seamu — poza zakresem tego zadania, odnotowane jako kandydat.

**Regresja po zmianie:** `test-truth-core` 403 OK · `test-truth-v04` 13 OK ·
`test-integrations` 28 OK · canary 283 caught / 0 missed. Zero pominięć
(`PYTHONPATH` ustawiony, waiver nietknięty).

> **Werdykt:** ryzyko operacyjne z F-15 — zmiana semantyki `paths` w module
> z najcieńszą siatką — **przestało istnieć**. `gates.py` jest teraz drugim
> najlepiej opancerzonym modułem po `kernel.py` (91,4 %). Krok 2.5 refaktoru
> „Reproduce-on-Read" może ruszyć.

Tripwire: `template/truthlib/gates.py`, `template/scripts/test-truth-core.py`

## F-19 · Cache mutmuta czyta „survived" ze starych wyników · AKTUALNE
**2026-08-17**, zaobserwowane podczas F-18

Po dopisaniu testów, które **udowodnienie** zabijały mutanty (ręczne
`mutate.sh apply 377` + przebieg suity = `FAILED`), `mutate.sh run` nadal
raportował je jako ocalałe. Ani regeneracja `.coverage`, ani `--rerun-all` nie
pomogły — dopiero `rm -f .mutmut-cache` dał prawdziwy wynik.

Kolejność, która działa:
```bash
bash scripts/mutmut-coverage.sh          # po KAŻDEJ zmianie suity
rm -f .mutmut-cache                      # inaczej stary werdykt przeżywa
./scripts/mutate.sh run --paths-to-mutate <plik>
```

> **Werdykt:** `mutmut_config.py` ostrzega, że nieświeży `.coverage`
> under-selects i że „an under-selected mutant reads as survived". To jest
> **druga, niezależna** pułapka tego samego kształtu: nieświeży `.mutmut-cache`
> daje ten sam fałszywy odczyt, mimo `--rerun-all`. Warta dopisania do
> nagłówka `mutate.sh`, bo kosztowała tu trzy przebiegi zanim się wydała.
>
> **Uwaga o stanie roboczym:** `.mutmut-cache` zawiera teraz wyłącznie wyniki
> `gates.py`; wpisy `kernel.py`/`contract.py` z F-12 zostały skasowane przez
> ten `rm`. Kopia sprzed: `mutmut-cache.backup` w katalogu scratch sesji.
> Liczby z F-12 są zapisane, więc odtworzenie jest przeliczeniem, nie stratą.

Tripwire: `scripts/mutate.sh`, `mutmut_config.py`
