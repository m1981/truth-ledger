# Ściąga architekta — prawda na złym poziomie

Status: **rekonstrukcja, nie norma.** Zrekonstruowane z sesji 2026-08-25/26
nad tym repozytorium. Instancje są prawdziwe i wszystkie pochodzą stąd.
Kolejność szczebli 1–8 jest **hipotezą** o tym, gdzie błąd poziomu chowa
się najskuteczniej — nie pomiarem. Dokument operatorski: wolno go skracać,
skreślać i poprawiać bez ceremonii, i nic go nie bramkuje.

Po polsku celowo, jak `docs/books/books.md` — to zapis rozmowy operatora,
nie materiał, na którym pracuje agent.

> Każda awaria w tym systemie miała ten sam kształt: **prawdziwe zdanie
> wypowiedziane na złym poziomie.** Zdanie nie niesie własnego zakresu — i
> stąd bierze się wszystko poniżej.

---

## Dlaczego to boli, i dlaczego to nie jest wina architekta

**Robisz dwie prace, które wszędzie indziej są rozdzielone.** Inżynier IV&V
w lotnictwie *nigdy nie decyduje, co jest w zakresie* — DO-178C zdecydowało
dwadzieścia lat temu, a cały jego wysiłek idzie w stosowanie. Tutaj jedna
osoba jest jednocześnie komitetem normalizacyjnym i praktykiem: ustala, co
ma być mierzone, i to mierzy. Stąd wrażenie braku dna — bo dna faktycznie
nie ma, dopóki ktoś go nie zadeklaruje. Od 2026-08-26 deklaruje je
`docs/scope.md`.

**Filozofia jest rekonstrukcją, nie przygotowaniem.** Nikt, kto buduje
narzędzia IV&V, nie czytał wcześniej Arystotelesa. Najpierw robi się ruch,
potem odkrywa, że ma nazwę. Odwrotna kolejność produkuje ludzi, którzy
potrafią zacytować Poppera i nie potrafią napisać bramki.

**Tego nie trzeba mieścić w głowie.** Rejestry, `docs/registers.md` i
`docs/map.txt` istnieją dokładnie po to, żeby nie musieć. Dyskomfort to
standard rzemieślnika — *powinienem rozumieć cały swój warsztat* —
przyłożony do czegoś, co ten rozmiar przekroczyło.

---

## Procedura: osiem pytań, w kolejności

Kolejność nie jest według ważności ani ogólności. Jest według tego, **jak
dobrze błąd poziomu potrafi się na danej warstwie ukryć**. Zaczyna się od
góry, bo tam koszt niezauważenia jest największy.

| | pytanie | chowa się |
|---|---|---|
| 1 | Czy to jest normatywne czy opisowe? | najlepiej |
| 2 | Jaka jest populacja? | najlepiej |
| 3 | Szukanie czy podział? | dobrze |
| 4 | Co by mnie obaliło? | dobrze |
| 5 | Czy bramkę zapalono na czerwono? | słabo |
| 6 | Jaką wiązkę potępia ta czerwień? | słabo |
| 7 | Instancja czy kształt? | najgorzej |
| 8 | Kto może o tym rozstrzygnąć? | najgorzej |

**Szew.** Pytania 5 i 6 są **mierzalne** — instrument potrafi je zadać. 2 i 3
też, ale dopiero gdy populacja jest już zadeklarowana. **Pytanie 2 w swojej
mocnej postaci — *nad czym* ten podział jest — jest deklarowalne i niemierzalne:
granicy nie da się zmierzyć od środka.** 1, 7 i 8 są normatywne.

Aparat tego repozytorium mieszka w całości po mierzalnej stronie i jest tam
bardzo dobry. Katalog złapań pokazuje to liczbą: **każde zapisane złapanie
dotyczy struktury, każde chybienie — treści.** To nie jest zaległość do
nadrobienia, tylko sufit, i lepiej go znać niż o niego uderzać.

### 1. Czy to jest normatywne czy opisowe?

Rozstrzyga, czy pomiar ma tu cokolwiek do powiedzenia. Groźny przypadek:
zdanie **opisowe przemycone do dokumentu normatywnego** — dziedziczy jego
immunitet, bo „to przecież decyzja", i nikt go nie sprawdza.

- *Instancja:* sekcja `Context` w ADR-059, obalona pomiarem.
- *Tradycja:* gilotyna Hume'a, reguły konstytutywne Searle'a, reguła
  uznania Harta.

### 2. Jaka jest populacja?

Zawsze przed klasyfikacją. **Podział nad złym zbiorem to nadal kompletny
podział — i nadal raportuje zero niesklasyfikowanych.**

- *Instancja:* `scripts/gate-reachability.sh` — jedenaście globów zamiast
  zbioru checków. I `instruments/map.py` w pierwszej wersji: indeks git
  zamiast drzewa, więc spis piętnastu rodzajów bez wiersza `charter`.
- *Tradycja:* zarządzanie konfiguracją — identyfikacja poprzedza kontrolę.

### 3. Szukanie czy podział?

Heurystyka to świat otwarty: znajduje to, co pasuje do kształtu, i **milczy
o reszcie**. Podział to świat zamknięty: wyczerpujący, rozłączny, z bramką
na `niesklasyfikowane = 0`.

- *Instancja:* heurystyka `--*-ok` przegapiła dwie flagi; klasyfikacja
  totalna złapała dziesiątą bez niczyjej czujności.
- *Tradycja:* założenie świata zamkniętego (Reiter), reguły podziału u
  Arystotelesa, bilans próbny z podwójnego zapisu.

### 4. Co by mnie obaliło?

Powiedz to *zanim* zgłosisz, i idź tego poszukać. Zgłaszaj też własne
przegrane — zabita hipoteza jest jedynym dowodem, że mogłeś się mylić.

- *Instancja:* przepowiednia fail-openu w czytniku `options:` — obalona
  przez cross-check usage↔options i zgłoszona jako przegrana.
- *Tradycja:* Popper. I **Lakatos jako lustro**, bo pokusa jest zawsze ta
  sama: zwęzić tezę pod ciosem tak, żeby przeżyła (*monster-barring*).

### 5. Czy bramkę zapalono na czerwono?

Kontrola, która nigdy nie była czerwona, nie jest świadectwem — może być
**prawdziwa pusto**. Zepsuj, zobacz czerwień, przywróć bajt-w-bajt,
zweryfikuj `sha256`. Kontrola negatywna też: zielone na czystym drzewie.

- *Instancja:* jedenaście kontroli skasowanych, pakiet nadal zielony.
- *Tradycja:* Dijkstra 1969, testowanie mutacyjne, surowość u Mayo.

### 6. Jaką wiązkę potępia ta czerwień?

Nigdy jedno zdanie. Czerwień potępia hipotezę *plus* jej założenia
pomocnicze. Nazwij wiązkę, zanim wskażesz winnego.

- *Instancja:* nie sam `gate-reachability.sh`, tylko koniunkcja rostera,
  odczytu pustego opt-outu jako „uzbrojone" i delegacji z `registers.md`.
- *Tradycja:* Duhem–Quine.

### 7. Instancja czy kształt?

Reguła stosowana przez dopasowanie przykładów **nie da się dokończyć
dopisywaniem przykładów**. Jeśli następny przypadek zawsze będzie poza
listą — to kształt, nie defekt.

- *Instancja:* czarna lista w `purpose()` w `instruments/map.py` — dwie
  znane instancje zamknięte, kształt otwarty i tak zapisany.
- *Tradycja:* Wittgenstein, *Dociekania* §§143–242.

### 8. Kto może o tym rozstrzygnąć?

Recenzent nie dostaje specyfikacji — ze specyfikacją sprawdza zgodność, nie
poprawność. Granicy nie deklaruje agent. Rejestr zapisuje operator.

- *Instancja:* dwa audyty tego samego repozytorium w jeden dzień, część
  wspólna **zero**.
- *Tradycja:* niezależność w DO-178C, reguły wtórne Harta, ADR-062.

---

## Jeden kształt awarii

**Zdanie nie niesie własnego zakresu. Poziom, na którym coś jest prawdziwe,
jest w prozie niewidoczny.**

- Komentarz nad `gate-reachability.sh` był prawdziwy; kod pod nim stosował
  go o jedną pośredniość za płytko.
- ADR-059 był prawdziwy o flagach, które ekstraktor widział; fałszywy jako
  zdanie o wszystkich flagach.
- `instruments/map.py` klasyfikował bezbłędnie — nad indeksem git zamiast
  nad drzewem.
- `PURPOSE_REQUIRED` naprawdę testuje niepustość; *twierdzi*, że testuje
  cel.
- Wiersz indeksu opisywał rejestr waiverów prawdziwie — minus jego
  samoograniczenie.

To nie jest niechlujstwo. Dlatego wszystkie naprawy, które zadziałały, są
**mechanicznym wymuszaniem zakresu**, a nie apelem o staranność.

---

## Cztery ruchy, które naprawiają

1. **Roster → podział.** Populacja liczona z rzeczywistości (z parsera, z
   `git ls-files`, z systemu plików); lista mówi wyłącznie, *po której
   stronie* stoi element. Przeniesienie listy do pliku konfiguracyjnego
   niczego nie naprawia — to ten sam roster w innym katalogu.
2. **Sprawdzaj w obie strony.** Kontrola, która idzie z A do B i nie wraca,
   jest połową kontroli. To repozytorium przegrało z tym kształtem
   czterokrotnie.
3. **Zepsuj, zobacz czerwień, przywróć, zweryfikuj.** Bajt-w-bajt, z
   `sha256` przed i po.
4. **Każdy mechanizm nazywa awarię, która go kupiła.** A gdy umiera —
   zapisuje pomiar, który go uśmiercił. Wzorzec, który już tu jest:
   komentarz uśmiercający hook `post-commit`, z PPV 3,6% i wskazaniem
   następcy.

---

## Gdyby zaczynać na czystej kartce

Nie od ontologii. Od jednego zdarzenia szkody. I **na czystej kartce
wyszedłby mniej więcej ten sam system** — zdarzenia zamiast stanu,
defeasibility, rejestry, ramiona. Może trzydzieści procent mniej
maszynerii. Wartością tego pytania nie jest przepisanie, tylko kolejność.

1. **Skarga.** Jedno konkretne zdanie, które przestało być prawdziwe, i
   nikt nie zauważył. Zapisane. Nie wizja.
2. **Odmowa.** Czego to *nie* będzie robić — **przed** jakimkolwiek
   mechanizmem. To jest krok, którego brakowało przez dwieście dni: nie
   było podłogi, o którą mogłoby oprzeć się „nie".
3. **Jedna bramka, którą da się zapalić na czerwono**, na tym jednym
   przypadku. Nic więcej.
4. **Potem mechanizm — ale tylko z nazwaną awarią**, która go kupiła.

---

---

## Czego tu nie ma: dachu

Wszystko w tym repozytorium jest **dowodem bez twierdzenia nad sobą**. Stąd
bierze się to, że pytanie *„czy to robi wartościową pracę"* zawsze wraca ciszą:
nie ma zdania, którego dowód miałby być dowodem.

W praktyce IV&V ten dach ma nazwę i normę — **assurance case**, w notacji GSN
albo CAE, znormalizowany w ISO/IEC 15026-2. Jedno twierdzenie na szczycie,
rozłożone na cztery–sześć podtwierdzeń, każde kończące się na dowodzie.
Przykład twierdzenia szczytowego stąd: *każde normatywne zdanie w tym
repozytorium odpowiada stanowi repozytorium, albo jest oznaczone jako
nieodpowiadające.*

To jest dzień pracy, nie kwartał. Po jego napisaniu dwa uporczywe pytania
przestają być pytaniami o samopoczucie:

| pytanie | czym się staje |
|---|---|
| czy to robi wartościową pracę? | czy dowód wspiera twierdzenie szczytowe? |
| jaki to ma kształt? | to drzewo, na jednej stronie |

I każdy instrument dostaje test, którego dziś nie ma: **którego liścia jesteś
dowodem?** Instrument bez rodzica jest natychmiast widoczny jako
nieumotywowany — a dwanaście z piętnastu nie złapało dotąd niczego.

**Ostrzeżenie.** Assurance case bardzo łatwo staje się teatrem: diagramem
argumentującym za wnioskiem podjętym wcześniej. Zabezpieczenie jest to samo,
które już stosujesz — **każdy liść niesie warunek obalenia**. Nie „czym to jest
poparte", tylko „co by to zabiło". Bez tej kolumny dostaniesz ładne drzewo,
które niczego nie orzeka.

## Na czym naprawdę opierają się implementatorzy IV&V

- **Na normie jako liście skończonej.** Wartością DO-178C nie jest jego
  trafność — jest nią to, że ktoś inny już się o zakres pokłócił i
  skończył.
- **Na produktach pracy, nie na zasadach.** Szablon planu weryfikacji,
  macierz identyfikowalności, indeks konfiguracji. Ludzie wypełniają
  formularze, których nie zaprojektowali.
- **Na garstce zapamiętanych reguł.** Identyfikowalność w obie strony.
  Niezależność. Pokrycie jest konieczne, nie wystarczające. Test, który
  nigdy nie padł, niczego nie dowodzi. Cztery, może pięć — nie czterdzieści.
- **Na precedensie.** „Co zrobił poprzedni projekt, który przeszedł
  certyfikację." Największe źródło w praktyce i nikt się tym nie chwali.

---

## Słownik — objaw, nie program studiów

| gdy utkniesz na tym | ktoś to już nazwał |
|---|---|
| definicja pęka pod kontrprzykładem, a Ty czujesz pokusę, żeby ją zwęzić | **Lakatos**, *Dowody i refutacje* |
| rejestry rozjeżdżają się mimo staranności | **Hart**, *Pojęcie prawa* — reguła uznania |
| wszystko zielone i nie wiadomo, czy cokolwiek zmierzono | **Mayo**, *Severe Testing*; jedno zdanie **Dijkstry** z 1969 |
| pytanie „ile ich jest?" nie ma odpowiedzi | **Arystoteles**, *Kategorie*; **Strawson**, *Indywidua* — sortale |
| coś mierzy, rejestruje albo rządzi samo sobą | **Tarski** — język przedmiotowy i metajęzyk; **Franzén** jako *hamulec*, żeby nie wyciągać z tego wniosków o niezupełności |
| reguły nie da się dokończyć dopisywaniem przypadków | **Wittgenstein**, *Dociekania* §§143–242 |
| komponent spełnił specyfikację, a system i tak jest niebezpieczny | **Leveson**, *Engineering a Safer World* — PDF leży w `docs/books/` |
| opis rozjeżdża się z tym, gdzie rzecz naprawdę leży | archiwistyka, *respect des fonds* (1841) — proweniencja bije treść |

Pełniejsza lista z komentarzem: `docs/books/books.md`.

---

## Czego nie wygładzam

**Jesteś tu sam.** Rdzeniem IV&V jest niezależność — druga strona, która ma
inny interes. Symulowanie jej agentami działa lepiej niż nic i zostało to
zmierzone: dwa audyty tego samego repozytorium w jeden dzień, część wspólna
zero. Ale agent nie ma własnego interesu, nie ponosi konsekwencji i nie
pamięta. Tego nie da się naprawić narzędziem. Część zmęczenia bierze się
stąd, że jedna osoba odgrywa obie strony relacji, która ma mieć dwie.

**To nie jest norma.** Jeśli któryś szczebel przestanie się sprawdzać —
skreśl go. Cztery szczeble, które przyjmujesz, są warte nieskończenie
więcej niż osiem, których nie. Dokładnie jak z odmowami w `docs/scope.md`.
