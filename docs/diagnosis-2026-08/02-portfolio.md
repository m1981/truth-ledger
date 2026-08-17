# Portfel analiz — co trzeba zmierzyć, żeby zdecydować

Statusy utrzymywane w `00-STATE.md`; tutaj jest **metoda**, która się nie
zmienia. Kolejność jest celowa: poziom 0 rozstrzyga 80% sprawy w ~2 dni.

---

## Poziom 0 — zaufanie do oracle'a
*Bez tego cała reszta jest zgadywaniem.*

### 0.1 Mutation score
**Pytanie:** ile *dowolnych* usterek łapie suita, nie tylko 283 zasiane ręcznie?

```bash
export PYTHONPATH="$HOME/.cache/truth-ledger-pylib"
uvx mutmut run --paths-to-mutate template/truthlib \
    --runner "python3 template/scripts/test-truth-core.py"
uvx mutmut results
```
Suita chodzi 10 s, więc pełny przebieg jest wykonalny. Alternatywa dla
większej kontroli: `cosmic-ray`.

**Próg decyzyjny:**
- **≥80%** → możesz przepisać dowolny moduł bez strachu. Zamyka pytanie
  repair/rewrite na korzyść repair.
- 50–80% → oracle dobry, ale mapa luk wskazuje, gdzie nie refaktorować.
- **<50%** → 283 ramiona to teatr; napraw testy zanim tkniesz kod.

### 0.2 Pokrycie z gałęziami
```bash
PYTHONPATH="$HOME/.cache/truth-ledger-pylib" python3 -m coverage run --branch \
  template/scripts/test-truth-core.py && python3 -m coverage report -m
```
**Sygnał:** nałóż na F-02. Luki pokrywające się z `validate_events` (CC=129)
to mapa „tu smoki".

### 0.3 Czy testy pinują zachowanie czy implementację?
**Metoda:** przegląd 20 losowych testów — ile odwołuje się do wewnętrznych
nazw funkcji zamiast do CLI/kontraktu. **Sygnał:** dużo białoskrzynkowych →
oracle blokuje zmianę zamiast ją chronić.

---

## Poziom 1 — czy masa dokumentacji jest utrzymywalna
*Główny podejrzany, patrz F-04.*

### 1.1 Macierz ADR → kod → test
**Stan:** połowa gotowa. `instruments/arm-index.py` daje **test→ADR** (F-10),
`labels-deps` daje **ADR→kod** (F-05/F-06).

**Brakuje:** złączenia i kierunku odwrotnego — **ADR bez ani jednego ramienia**.
```bash
python3 instruments/arm-index.py --json > /tmp/arms.json     # jeśli ma --json
(cd ~/PycharmProjects/labels-deps && uv run labels-deps scan \
   ~/PycharmProjects/truth-ledger -o /tmp/labels.json)
# join: dla każdego z 54 ADR-ów → (pliki kodu, rodziny ramion)
```
**Sygnał:** ADR bez testu = decyzja nieegzekwowana = czysty dług prozy.
**Jeśli >30% ADR-ów nie ma ramienia, dokumentacja jest w istotnej części fikcją.**

### 1.2 Cykl życia ADR-ów
```bash
grep -lE '^status:.*(superseded|retired)' template/docs/adr/truth/*.md | wc -l
git log --diff-filter=A --format='%ci' -- 'template/docs/adr/truth/*.md'
```
**Sygnał:** 54 ADR-y w 5 tygodni. Jeśli **nic nigdy nie jest wycofywane**, masa
rośnie liniowo bez sufitu — i to jest problem strukturalny, nie kosmetyczny.

### 1.3 Koszt dodania jednej funkcji
**Metoda:** dla ostatnich 10 commitów typu „feature" policz Δplików, ΔADR,
Δramion. **Sygnał:** >5 plików + 1 ADR + 10 ramion na funkcję → wąskim gardłem
jest ceremonia, nie kod.

### 1.4 Wykrywalność dryfu dokumentacji
**Stan:** dobry — `doc-health.sh`, `spec-health.sh`, `TestStructureDocMatchesDisk`.
**Rozszerzenie:** bloki kodu w docs wykonywalne jako doctest.

---

## Poziom 2 — architektura właściwa

### 2.1 Zamrożenie warstw
DAG jest czysty (F-03) — to **zamrożenie**, nie naprawa. `import-linter`,
kontrakt warstw deklaratywnie w `pyproject.toml`, w CI. Koszt ~1 h.

### 2.2 Snapshot kontraktu CLI
Werby + flagi + kody wyjścia jako plik kontraktowy, test porównujący.
**Sygnał:** to jest koszt migracji konsumentów; duża powierzchnia → rewrite
kosztuje 10×.

### 2.3 Rozłożyć `validate_events` (CC=129)
Nie mierzyć — **przepisać deklaratywnie**. Koncept „gate table" (ADR-034) już
istnieje; CC=129 to prawie zawsze drabina `if`, którą da się zamienić na dane.
**To jest idealny pierwszy test tezy z F-01:** jeśli po przepisaniu 283 ramiona
nadal zielone, oracle udowodnił swoją wartość na najtrudniejszym przypadku.

### 2.4 Duplikacja suit py ↔ sh
Dla każdego ADR-a: ile ramion py, ile sh. 1 000 ramion na 173 funkcje.
**Sygnał:** duplikacja = podwójny koszt każdej zmiany.

### 2.5 Bramki nieosiągalne
`scripts/gate-reachability.sh` istnieje. Rozszerzyć o pokrycie w realnym
`.truth/`: bramka nigdy nieodpalona = spekulacja, kandydat do usunięcia.

---

## Poziom 3 — czy produkt ma sens
*Najczęściej pomijane, najważniejsze.*

### 3.1 Czy koncept działa w praktyce
**Stan:** częściowo odpowiedziane przez F-08 (13 zaległych zestaleń) oraz przez
sam fakt, że ta diagnoza jest prowadzona w ledgerze.
**Domknięcie:** `truth stats`, `truth staling` — ile zestaleń, ile było realnymi
zmianami faktu, ile fałszywym alarmem.

### 3.2 Cicha nieuzbrojona instalacja *(dodane po F-08)*
**Pytanie:** czy instalacja potrafi wykryć, że sama nie jest uzbrojona?
**Metoda:** świeży klon, `core.hooksPath` nieustawione → czy `truth doctor`
krzyczy? **Sygnał:** to był realny tryb awarii przez dwa wydania.

### 3.3 Koszt wdrożenia
`copier copy` do świeżego repo; zmierzyć czas i liczbę ręcznych kroków do
pierwszej wartości. **Sygnał:** >30 min → produkt nie przyjmie się poza autorem.

### 3.4 Realni konsumenci
Repozytoria z `.copier-answers.truth-ledger.yml`.
**Sygnał:** 0 → pełna swoboda łamania API; ≥1 → kontrakt wiąże.

---

## Reguła decyzyjna — kiedy „przepisać na nowych podstawach"

Uzasadnione **tylko** przy ≥2 spełnionych warunkach:

| Warunek | Stan |
|---|---|
| Oracle nie do uratowania (mutation <50%) | ❓ **niezmierzone — jedyna realna niewiadoma** |
| Cykle w grafie importów / brak warstw | ❌ sfalsyfikowane (F-03) |
| Złożoność rozproszona po całym kodzie | ❌ sfalsyfikowane (F-02, mediana CC=4) |
| Kluczowe założenie obalone | ❌ sfalsyfikowane (F-08: mechanizm łapie dryf) |
| Koszt zmiany rośnie wykładniczo | ❓ niezmierzone (1.3) |

**Trzy z pięciu warunków już sfalsyfikowane.** Rewrite wymagałby, żeby OBA
pozostałe wypadły źle.

---

## Gdyby jednak „wyłuskać substancję" — co zabrać, w kolejności wartości

1. **Oracle** (394 + 28 testów + 283 ramiona) — przenieść *pierwsze*, jako
   specyfikację nowej implementacji.
2. **Tabela bramek i kolejność etapów intake** (ADR-034) — najgęstsza wiedza
   projektowa w całym repo.
3. **Uzasadnienia ADR — skondensowane do ~15 rekordów.** 54 to zapis procesu
   odkrywania, nie architektura.
4. **Kontrakt nieinterferencji** przy instalacji — prawdziwa przewaga produktowa.
5. **Wyrzucić:** `cli.py` (3 z 5 najgorszych funkcji), duplikację suit py/sh,
   `docs/reviews/**` (5 ADR-ów redefiniowanych w draftach).
