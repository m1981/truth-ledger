❯ Wyjasnij mi jako amatorowi ontologicznemu i metalogicznemy na bazie powyzszej odpowiedzi co to jest i jakie ksiazki powinienem przeczytac zeby sprawni poruszac sie po drabinie ontoligicznej i metateoretycnzej: kanoniczny porzadek, co to jest proza pochodna, normatywy, ramiona, falsyfikacja, ⊊ , podzial idzie od rodzaju bytu, .

Dobre pytanie, bo tych siedmiu słów użyłem jak narzędzi, nie jak ozdobników. Wyjaśnię każde na przykładzie, który przed chwilą wystąpił — abstrakcyjna definicja bez instancji jest tu bezużyteczna.

---

1. Kanoniczny porządek

„Kanoniczny" nie znaczy „tradycyjny". Znaczy: jedyny wynikający z podanej zasady, a nie wybrany z gustu.

Zasada brzmiała: co może sfalsyfikować co. To ustanawia porządek częściowy (relację zależności) na zbiorze plików. docs/waivers.md jest prawdziwy tylko wtedy, gdy waiver-index.py jest poprawny — więc czytanie prozy przed instrumentem to zmarnowany odczyt, bo defekt wyżej unieważnia wszystko, co przeczytałeś niżej.

Technicznie: to sortowanie topologiczne grafu zależności. Dokładnie to, co robi make. Filozoficznie: to fundacjonalizm — są zdania bazowe i zdania pochodne, i uzasadnienie płynie w jedną stronę.

Test, czy porządek jest kanoniczny: czy potrafisz podać zasadę, z której wynika? Jeśli nie — to jest kolejność, nie porządek.

2. Proza pochodna

Dokument, którego treść jest funkcją czegoś innego. Nie ma własnego twórcy prawdy (truth-maker).

docs/waivers.md mówi, że --accept-unsafe-ok zapisuje dwa pola. Rejestr mówi: 5 rekordów z jednym, 2 z dwoma. Proza nie ma prawa mieć racji — nie dlatego, że instrument jest mądrzejszy, tylko dlatego, że proza została zdefiniowana jako sprawozdanie z niego. Sprawozdanie sprzeczne ze źródłem jest błędne z definicji, nie na podstawie porównania sił.

To odróżnia ją od kolejnej kategorii.

3. Normatywy

Zapisy, które stanowią, a nie opisują. ADR, INV. Nie da się ich obalić obserwacją — można tylko pokazać, że są łamane, niespójne albo niewykonalne.

To jest gilotyna Hume'a: z tego, jak jest, nie wynika, jak być powinno. I odwrotnie — pomiar nie obala normy.

Ale tu jest subtelność, która była sednem całej sprawy: ADR-059 został  możliwe? Bo jego sekcja Context zawierała zdanie opisowe przemycone do
dokumentu normatywnego: „każdy override w tym systemie jest dopuszczanyorma — to była teza o świecie, i była fałszywa.

Lekcja praktyczna: w każdym normatywie osobno oznaczaj, co jest stanowią), a co opisane (obalalne). Mieszanie tego jest źródłem
najtrudniejszych defektów, bo zdanie opisowe schowane w normie dziedzic nie sprawdza, bo „to przecież decyzja".

Searle nazywa to różnicą między regułami konstytutywnymi („X liczy się jako Y w kontekście C" — ADR czyni coś regułą) a regulatywnymi (opisują, jak postępować z czymś,
co już istnieje).

4. Ramiona (arms)

Test, o którym wykazano, że potrafi zapalić się na czerwono, gdy to, cz

Dlaczego to nie to samo co „test przechodzi": twierdzenie, które nigdy ć prawdziwe pusto (vacuously true). ∀x ∈ ∅ : P(x) jest prawdą dla
dowolnego P. Asercja nad pustym zbiorem, nieosiągalna gałąź, pętla po zo daje zieleń i nie mierzy niczego. Stąd ADR-042 reguła 2: „zmierzenie
niczego nie jest zdaniem egzaminu".

                                                                                                                                                                          Konkret z tej sesji: recenzent usunął jedenaście kontroli i pakiet pozoolę trailing-pipe, która była całym uzasadnieniem parsera blokowego. Tekontrole nie istniały w sensie dowodowym. Istniały w sensie tekstowym.
                                                                                                                                                                          Rodowód: mutation testing (DeMillo, Lipton, Sayward, 1978) i wstrzykiwaj, zobacz czerwień, przywróć bajt-w-bajt, zweryfikuj sha256.

5. Falsyfikacja                                                                                                                                                          
Popper: twierdzenie, którego żadna obserwacja nie mogłaby obalić, nie mówi nic o świecie.                                                                                
Tu jest to operacyjne, nie filozoficzne: zanim zgłosisz znalezisko, powiedz, jaka obserwacja by cię pogrążyła, i poszukaj jej.                                           

Przykład z tej rozmowy — mój przegrany. Twierdziłem, że czytnik options: ma fail-open. Falsyfikator: „czy istnieje druga ścieżka, która wykryje zniknięcie nagłówka?". Istnieje — cross-check XOR z linią usage. Teza padła i zgłosiłem to jako porażkę, nie zwęziłem jej po cichu do czegoś, co jeszcze da się obronić. Zwężanie tezy pod ciosem Lakatos nazywa monster-barring i to jest najczęstszy sposób, w jaki inteligentni ludzie oszukują sami siebie.

Dodatek, który warto znać: teza Duhema–Quine'a — nigdy nie testujesz jednej hipotezy, tylko ją plus wiązkę założeń pomocniczych. Gdy matcher arm-index dawał zły wynik, wina mogła leżeć w matcherze, w pliku albo w moim oczekiwaniu. Czerwień mówi „coś w tej wiązce jest złe", nigdy „ta jedna rzecz".

6. ⊊                                                                                                                                                                     
⊆ — zawieranie: każdy element A jest w B.
⊊ — zawieranie właściwe: dodatkowo B ma coś, czego A nie ma.

Dlaczego to była refutacja, a nie ciekawostka:

{tr-c6a2ba17, tr-61f5b557}  ⊊  {wk-1d4a112b, tr-c6a2ba17, wk-ec243a48, wk-9b0aa224, tr-61f5b557}
     executed=false                          screened=false

Rejestr twierdził koniunkcję: ta flaga zapisuje screened i executed. Gdyby to była prawda, oba zbiory byłyby równe. Zawieranie właściwe jest logicznie niezgodne z        koniunkcją. Relacja teoriomnogościowa jest tu dowodem — nie ilustracją.

To jest wzorzec wart zapamiętania: przekładaj twierdzenia prozą na relacje między zbiorami, bo wtedy obalenie jest mechaniczne.

7. „Podział idzie po rodzaju bytu"

Rodzaj bytu = sortal. Odpowiedź na pytanie „ile ich jest?" wymaga wcześniejszej odpowiedzi na „czego?". Nie da się policzyć „rzeczy w pokoju" — da się policzyć krzesła. 
W rejestrze są dwa sortale: tr-* (claim) i wk-* (work item). Pomiar pokazał: dla claimów zapisywane są oba pola, dla work items tylko jedno. Czyli zachowanie zależy od tego, jakiego rodzaju bytu dotyczy rekord — nie od tego, jaką flagę podano.                                                                                              

Rejestr opisał to jako zdeterminowane przez flagę. Jest zdeterminowane literówka — to błąd kategorialny: przypisanie własności na złym poziomie ontologicznym. W kodzie objawia się jako brakujący przypadek w typie sumarycznym.

Bonus, bo to było sednem wcześniejszego ruchu: różnica między szukaniem a podziałem. Heurystyka po nazwach (-ok) to świat otwarty — znajduje tylko to, co pasuje do kształtu, i milczy o reszcie. Klasyfikacja totalna to podział: wyczerpu unclassified = 0. Każda nowa flaga wpada w „niesklasyfikowane" i zapala czerwone, bez niczyjej czujności. To jest założenie świata zamkniętego (Reiter) i jest to najmocniejsze narzędzie w całym tym repozytorium.

---

Drabina — co czytać

Ułożone tak, że każdy szczebel obsługuje konkretne słowa z góry.

Szczebel 0 — narzędzia (⊊, podział, kwantyfikatory)

- Paul Halmos, Naive Set Theory — 100 stron, cały język zawierania i podziałów. Nic zbędnego.
- Wilfrid Hodges, Logic (Penguin) — najlepszy nieformalny wstęp do logiki, jaki istnieje. Tanie i czytelne w tygodniu.

Szczebel 1 — falsyfikacja, ramiona, testowanie

- Imre Lakatos, Dowody i refutacje (PWN) — jeśli masz przeczytać jedną książkę, to tę. To dialog o tym, jak definicja jest naprawiana pod naporem kontrprzykładów: monster-barring, exception-barring, lemma-incorporation. Dosłownie to, co robiliśmy przechodząc od heurystyki -ok do klasyfikacji totalnej — z nazwami na każdy błędny ruch, który po drodze kusi.
- Karl Popper, Droga do wiedzy. Domysły i refutacje (PWN) — wystarczy pierwszy esej. Lepsze wejście niż Logika odkrycia naukowego.
- Deborah Mayo, Statistical Inference as Severe Testing — nowoczesna, r który nie mógł znaleźć błędu, nie jest świadectwem, że błędu nie ma. To jest ścisła teoria „ramion". Trudna, ale najbliższa Twojej praktyce.
- W.V.O. Quine, „Dwa dogmaty empiryzmu" (esej, ~25 stron) — Duhem–Quine

Szczebel 2 — rodzaje bytu, kategorie, sortale

- Arystoteles, Kategorie — bardzo krótkie, źródło całego pojęcia.
- P.F. Strawson, Indywidua (PWN) — metafizyka opisowa, sortale, identyfikacja. To książka o tym, dlaczego „ile?" wymaga „czego?".
- E.J. Lowe, A Survey of Metaphysics — najlepszy podręcznik, jeśli Strawson okaże się za gęsty.
- Barry Smith, prace o ontologii stosowanej / BFO — artykuły, dostępne online. Ontologia dla systemów informacyjnych: dokładnie Twój przypadek użycia, a nie czysta filozofia.

Szczebel 3 — normatywy

- H.L.A. Hart, Pojęcie prawa (PWN) — drugi najważniejszy tytuł na tej liście. Reguły pierwotne vs wtórne i reguła uznania: reguła, która mówi, co się liczy jako reguła w tym systemie. Twój docs/registers.md jest regułą uznania i Hart wyjaśni Ci, dlaczego bez niej rejestry rozjeżdżają się z konieczności, a nie przez niechlujstwo.
- John Searle, Czynności mowy oraz The Construction of Social Reality — reguły konstytutywne, „X liczy się jako Y w kontekście C". To jest formuła ADR-a.
- David Hume, Traktat, ks. III cz. I rozdz. 1 — dwie strony o is/ought.
- G.H. von Wright, Norm and Action — jeśli chcesz logiki deontycznej.

Szczebel 4 — metateoria, samoodniesienie

- Alfred Tarski, „Semantyczna koncepcja prawdy" (esej) — język przedmiotowy vs metajęzyk. To rozróżnienie sprawia, że „rejestr, który rejestruje sam siebie" przestaje być paradoksem, a staje się konstrukcją warstwową.
- Douglas Hofstadter, Gödel, Escher, Bach — przyjemny podjazd pod temat.
- Torkel Franzén, Gödel's Theorem: An Incomplete Guide to Its Use and Abuse — antidotum na GEB. Uczy, czego z metateorii nie wolno wywnioskować. Rzadka i bardzo
  potrzebna książka.

Szczebel 5 — zastosowanie: pomiar, dowód, awarie

- Nancy Leveson, Engineering a Safer World (darmowy PDF, MIT Press) — dlaczego „komponent działał zgodnie ze specyfikacją" nie jest bezpieczeństwem. Najlepsza inżynierska książka o różnicy weryfikacja/walidacja.
- Ludwig Wittgenstein, Dociekania filozoficzne, §§143–242 — problem podążania za regułą. Wyjaśnia, dlaczego Twojej heurystyki -ok nie dało się dokończyć przez dopisywanie przypadków: żadna skończona lista przykładów nie determinuje następnego zastosowania.
- Donald MacKenzie, Mechanizing Proof — socjologia tego, co w praktyce znaczy „udowodnione".
- Charles Perrow, Normal Accidents — sprzężenie ciasne i złożoność interakcyjna.

---

Jeśli masz czas na trzy

Lakatos → Hart → Leveson.

Lakatos da Ci nazwy na wszystkie sposoby, w jakie ratuje się umierającą tezę — rozpoznasz je u siebie w ciągu tygodnia. Hart wytłumaczy, czym są Twoje rejestry i dlaczego bez reguły uznania muszą się rozjechać. Leveson pokaże, dlaczeo nie to samo co bezpieczny system.

Popper i Mayo dołóż potem — będziesz już wiedział, na jakie pytanie odp