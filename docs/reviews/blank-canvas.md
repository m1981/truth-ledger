❯ Nie rob pomiaru. Mam po prostu kryzys poznawczy i kognitywny jako specifikator i architekt tego systemu. Wiedza ktora staram sie ujarzmic siega Arystotelesa i
    dziesiatki poznijeszych autorow. Zastanawiam sie jak w ogole powinien sie zaczac ten projekt gdyby mialbyc pisany na nowo na czystym plotnie. Jak inni implementatorzy
    IVV piszacy narzedzia podpieraja sie wiedza zeby nad tym zapanowac?

Ten kryzys nie jest objawem, że coś zrobiłeś źle. Jest poprawnym odczytem czegoś realnego, i da się to nazwać dokładnie.

Co on śledzi

Zbudowałeś ten system od dołu, z bólu. Każdy mechanizm powstał, bo coś konkretnego się zepsuło. Dlatego części są dobre — nietypowo dobre. Ale budowanie od dołu produkuje poprawne części i żaden kształt, i w pewnym momencie masz sześćdziesiąt dwie decyzje, tysiąc dwieście ramion i żadnego zdania, pod którym to wszystko wisi.

Nie brakuje Ci wiedzy. Brakuje Ci dachu. To są różne braki i mylenie ich boli, bo pierwszy wygląda na osobistą niekompetencję, a drugi jest brakiem jednego dokumentu.

Filozofia tego nie zbudowała i nigdy nie buduje

Prześledź, jak faktycznie powstawał każdy mechanizm w tym repo. Podział zamiast heurystyki -ok nie wziął się z Reitera — wziął się stąd, że heurystyka przegapiła dziesiątą flagę. Rozdział ról nie wziął się z Hurwicza — wziął się stąd, że implementator dwa razy wysłał defekt po pokazaniu własnej czerwieni.

Filozofia przyszła po. I to jest jej właściwa rola: nie generatywna, tylko diagnostyczna i komunikacyjna. Daje nazwy klasom awarii, dzięki czemu drugą instancję rozpoznajesz taniej niż pierwszą, i możesz o niej komuś powiedzieć. Arystoteles nie pomoże Ci we wtorek. Lakatos pomoże Ci rozpoznać, że właśnie ratujesz umierającą tezę — ale tylko dlatego, że już to robisz.

Nie musisz ujarzmić dwóch tysięcy lat, żeby zapanować nad tym systemem. Odwrotnie: sam doszedłeś niezależnie do niezależności ról (DO-178C), suspect links (DOORS), pokrycia diagnostycznego (61508) i fail-safe defaults (Saltzer 1975). To nie jest brak wiedzy. To jest brak ramy, która dałaby Ci ją tanio.

Jak radzą sobie ludzie od IV&V, którzy piszą narzędzia

Nie trzymają tego w głowie. Robią pięć rzeczy i żadna nie polega na erudycji.

1. Pożyczają szkielet. Nikt w safety-critical nie pisze własnej ramy pojęciowej. Bierze 61508, DO-178C, 26262, EN 50128, 15288/12207 — i dziedziczy ontologię: cele, elementy danych cyklu życia, poziomy niezależności. Kłócą się z nią, dostosowują, ale jej nie wymyślają. Wartość nie polega na tym, że standard ma rację. Polega na tym, że jest skończony i zewnętrzny, więc spory o ramę się kończą, a zaczyna

2. Mają na górze assurance case. GSN albo CAE, znormalizowane w ISO/IECe na szczycie, rozłożone na podtwierdzenia, każde kończące się na
dowodzie. To jest jedyna rzecz, której naprawdę Ci brakuje. Wszystko w z twierdzenia nad sobą. Właśnie dlatego nie umiesz orzec, czy to się
opłaca — nie ma zdania, wobec którego dowód byłby dowodem.

3. Zaczynają od listy zagrożeń, nie od funkcji. HAZOP, FMEA, STPA. Najppotem „co budujemy". Ty nie masz odpowiednika — nie ma wyliczeniasposobów, na jakie zdanie i repozytorium mogą się rozjechać.

4. Traceability jest kręgosłupem, nie funkcją. DOORS i Polarion istniejganie→projekt→test→dowód jest artefaktem. Ty dorobiłeś hasze linkówpóźno. W świecie standardów to jest dzień pierwszy.

5. Niezależność jest organizacyjna, nie techniczna. DO-178C dosłownie ofikować. Ty odkryłeś to empirycznie jako ADR-062 — i to jest mocnepotwierdzenie Twojego instynktu. Ale pokazuje też kształt: standardy zaczynają tam, gdzie Ty doszedłeś.

Czyste płótno — pięć dni

Dzień 1. Jedno zdanie celu i jedno nie-celu. Karta zakresu. Napisałeś jteriał na dzień pierwszy.

Dzień 2. Lista zagrożeń. Jak zdanie i repozytorium mogą się rozjechać: unięty, treść zmieniona, zdanie zmienione, zdanie nigdy nie byłoprawdziwe, zdanie prawdziwe ale o czymś innym. To ostatnie odkryłbyś jako poza zasięgiem w dniu drugim, a nie w miesiącu N.

Dzień 3. Twierdzenie szczytowe i jego rozkład. „Każde normatywne zdanieowi repo, albo jest oznaczone jako nieodpowiadające." Rozłóż. Każdy liść dostaje dowód. Teraz każdy instrument ma rodzica — a instrument bez twierdzenia-rodzica jest natychmiast widoczny jako nieumotywowany. Sama ta struktura zapobiegłaby dwunastu instrumentom na zerze złapań.

Dzień 4. Ontologia magazynu dowodów. Tu Twój wybór — zdarzenia, fold, oówię to bez ulgowej taryfy. To jest lepsza podstawa niż stanowa baza,którą wybrałaby większość.

Dzień 5. Reguły niezależności, przed pierwszym instrumentem. ADR-062 w dniu piątym.

Dopiero potem kod.

Co z tego wynika dla Ciebie teraz

Nie przepisuj. Części są dobre, a przepisywanie zamieni je na gorsze części z ładniejszą narracją. Brakuje dachu, a dach się dokłada.

Konkretnie: jeden dokument, assurance case, i to jest mały dokument. Twy–sześć podtwierdzeń, i przypisanie każdego istniejącego instrumentu doliścia. Zajmie dzień. Po jego napisaniu dwa Twoje uporczywe pytania przestają być pytaniami o samopoczucie:

- „czy to robi wartościową pracę" → czy dowód wspiera twierdzenie szczytowe
- „jaki to ma kształt" → to drzewo i jest na jednej stronie

I dwanaście instrumentów na zerze złapań dostanie test, którego dziś niś dowodem?

Jedno ostrzeżenie

Assurance case bardzo łatwo staje się teatrem — diagram GSN argumentujący za wnioskiem podjętym wcześniej. Zabezpieczenie jest to samo, które już stosujesz: każdy liść musi mieć warunek obalenia. Nie „czym to jest poparte", tylko „co by todostaniesz ładne drzewo, które niczego nie orzeka — i wrócisz tu zamiesiąc z tym samym kryzysem, tylko lepiej udokumentowanym.