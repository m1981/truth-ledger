Trzy poziomy pewności, oznaczone przy każdej pozycji:
  [S] standard — twierdzenie ustalonej dyscypliny, źródło nazwane
  [M] zmierzone — wyprowadzone z pomiaru w tym repo, liczba podana
  [I] interpretacja — moje uogólnienie bez falsyfikatora; motyw, nie artykuł

## L0 · ONTOLOGIA — co istnieje i czy przeżywa

[S] Identyfikator musi być oddzielony od lokalizacji.
    Źródło: PURL / DOI / Handle; W3C "Cool URIs don't change" (1998); HTTP 301.

[S] Rejestr sam jest pozycją rejestrowaną.
    Źródło: ISO/IEC 11179 — administered item ma identyfikator, stewarda,
    status; rejestr podlega tym samym regułom co jego wpisy.

[S] Pozycja musi móc umrzeć: status rejestracyjny i dowiązanie supersesji.
    Źródło: ISO/IEC 11179 (Recorded→Standardized→Superseded→Retired);
    Nygard, ADR "Status: superseded by ADR-XXX".

[M] Relokacja bije nową nazwę i porzuca starą.
    FAULT B (INV-C) → FAULT B (step 2.5); FAULT OV → test-instruments.sh →
    test_override_velocity_...; pięć plików → jeden runner, bez przekierowania.

[M] Odwołania po wzorcu nie gniją, po nazwie gniją.
    gate-reachability: 12 globów + 8 nazw wprost → 0 martwych.
    ADR-046: 6 nazw wprost → 2 martwe. Korpus: 20 z 183 (11%).

[I] Wiersz, który przeżył swój mechanizm, czyta się jak działające
    zabezpieczenie. Wiersz brakujący jest widoczny w przeglądzie — martwy nie.

## L1 · EPISTEMOLOGIA — skąd wiemy i czy to jeszcze prawda

[S] Śladowalność musi być dwukierunkowa.
    Źródło: DO-178C, ISO 26262, IEC 62304 — wymaganie↔projekt↔kod↔test.

[S] Zmiana któregokolwiek końca dowiązania czyni je PODEJRZANYM, nie zepsutym,
    do czasu ludzkiego potwierdzenia.
    Źródło: suspect links, DOORS / Polarion.

[S] Niezależność weryfikatora jest własnością organizacyjną dowodzoną zapisami
    spoza artefaktu — nigdy samoopisem.
    Źródło: DO-178C independence.

[M] Dowiązanie, które się rozwiązuje, nie musi być świeże.
    FAULT B i E przetrwały inwersję jako w pełni rozwiązywalne; zmieniło się
    znaczenie, a to niesie wyłącznie tekst celu.

[M] Cytowanie poprawne w chwili pisania może zostać unieważnione z zewnątrz.
    Zdanie §1 cytuje ADR-019 prawidłowo; ADR-057 unieważnił je, nie edytując
    ADR-019. Hash musi obejmować pozycję PLUS zbiór jej amendujących.

[M] Warstwa samoopisowa deklaruje ~3% własnych relacji.
    44 zadeklarowane z 1433; 818 (57%) stoi wyłącznie na dziedziczeniu.

[I] Mechanizm łapie tylko to, co ma adres. Proza normatywna bez adresu jest
    poza zasięgiem każdej z tych warstw.

## L2 · SEMIOTYKA / LOGIKA — w jakim języku i z jaką mocą

[S] Akt prawny rozdziela artykuły (wiążące) od motywów (wyjaśniających).
    Źródło: technika legislacyjna UE — recitals vs articles.

[S] Nowelizacja przez instrument; tekst jednolity jest DERYWATEM i jest datowany.
    Źródło: EUR-Lex. Wniosek: artefakt nie może być jednocześnie utrzymywany

[S] Cytowanie wymaga stabilnego, drobnoziarnistego adresu (artykuł/ustęp/punkt).

[I] Zdanie z falsyfikatorem jest artykułem; bez falsyfikatora jest motywem.
    (ADR-060 połowa pierwsza. Sama nie wystarcza — patrz [M] wyżej.)

[M] Dominująca usterka tego systemu jest semiotyczna, nie epistemiczna.
    Zero halucynacji w 32 wysyłkach; dominuje scope overreach — rozjazd między
    kwantyfikatorem języka naturalnego a ekstensją komendy. BFT nie ma na to
    wiersza. Źródło: paper v3 §6.1.

[S] Bramka wymagająca modelu do zadziałania jest przeglądem, nie odmową.
    Źródło: reguła własna repo ("No NLP, by design").

## L3 · TAKSONOMIA / MEREOLOGIA — porządek i podział

[S] Relacje MIĘDZY rejestrami są deklarowane, nie opisywane prozą.
    Źródło: SKOS (ConceptScheme, exactMatch/closeMatch/relatedMatch);
    GSN modular assurance cases z away-goals.

[S] Assurance case: claim → argument → evidence z jawnymi dowiązaniami.
    Źródło: ISO/IEC 15026-2, notacje GSN i CAE.
    Obserwacja: Appendix A JEST fragmentem assurance case zapisanym jako tabela.

[I] Etykieta to termin deklarowany raz i cytowany wiele razy. Identyfikator
    wskazujący unikalny rekord etykietą nie jest. (ADR-003.)

[I] Objętość prozy nie jest kosztem — pomieszanie gatunków jest.
    Uzasadnienie, narracja i norma mają różne obowiązki, jedno medium.

## L4 · CYBERNETYKA — sterowanie i diagnostyka

[S] Fail-safe defaults: brak wejścia to błąd, nie pominięcie.
    Źródło: Saltzer & Schroeder (1975); wejścia hermetyczne (Bazel, Nix).

[S] Diagnostic coverage + PROOF TEST INTERVAL: diagnostyka musi być dowodzona
    cyklicznie, bo detektor też się psuje.
    Źródło: IEC 61508 / ISO 26262.

[M] Instrument zbudowany do wykrywania ciemnych bramek był sam fail-open na
    własnym wejściu: 9 nazwanych źródeł, 4 czytane, przez 9 dni.

[M] Ten sam kształt awarii odtworzył się w NOWYM narzędziu pierwszego dnia:
    zniekształcony wiersz tabeli po cichu wyrejestrowywał rejestr.

[I] Instrument bez bramki jest normą. (Docstring arm-index: "Gate: NONE yet".)

[S] Odmowa musi zostawiać rekord; logowanie prób NIEUDANYCH, nie tylko udanych.
    Źródło: rodziny kontroli audytowych (NIST 800-53, rodzina AU).

[M] Odmowa nie zapisuje rekordu → cały aparat bramek jest z rejestru
    nieobserwowalny → INV-O pozostaje nierozstrzygalny.
    Źródło pomiaru: paper §8 item 1a — 133 pary, 14 zgód poniżej sekundy,
    najszybsza 0,282 s wobec 0,285 s kosztu samego procesu.

[I] Odmowa nie może uczyć własnego obejścia. Bramka na czasie jest pokonywana
    przez `sleep` i reklamuje to.


## L5 · METATEORIA — granice i domknięcie

[S] Demarkacja Poppera jako KRYTERIUM PRZYJĘCIA, nie deklaracja światopoglądowa:
    każde twierdzenie ma nazwany falsyfikator. Źródło: paper §7.

[S] Testowanie testów jest osobnym etapem — słaby falsyfikator, który przechodzi,
    nie dowodzi niczego. Źródło: paper §3.

[S] Zbieżność niezależna na wyniki sprzed dekad jest najbliższym dostępnym
    substytutem przeglądu zewnętrznego — i importuje ZNANE SŁABOŚCI oryginału
    jako sprawdzalne przewidywania. Źródło: paper §6.3.

[I] Instrument, który nic nie zmierzył, nie przeszedł — nie uruchomił się.
    (ADR-042 rule 2. Uogólnienie: pomiar zerowy musi być głośny.)

[I] Stos mechanizmów nie domyka się i nie może. Domyka się DO NAZWANEGO
    RESIDUUM plus jednego zaplanowanego aktu ludzkiego.
    Test: 6 z 8 znalezisk sesji pokrytych; 2 (proza↔kod, proza↔proza) nie.

[I] Pozycja jest skończona, gdy istnieje bramka mogąca się z jej powodu
    zaczerwienić I ktoś udowodnił, że się czerwieni. (ADR-061.)

[I] Weryfikator nie może być autorem. Implementator zademonstrował własną
    bramkę na czerwono na wszystkich kontrolach i zaraportował uczciwie —
    defekt #1 i tak przeszedł. Znalazł go dopiero niezależny recenzent.
