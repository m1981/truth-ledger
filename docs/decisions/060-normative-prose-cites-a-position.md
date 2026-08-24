# ADR-060: Proza normatywna cytuje pozycję, a cytowanie podlega kontroli świeżości

Status: **PROPOSED** (2026-08-24, agent-authored). Reguła sortująca jest do
zastosowania w punkcie bólu, nie wstecz; druga połowa (kontrola świeżości
cytowań w prozie) nie jest jeszcze zaimplementowana.

Amends: ADR-057 (nie w treści, lecz w tym, czego jego wdrożenie dowiodło)

## Kontekst

`kernel.py` pod ADR-057 wyprowadza wygaśnięcie z `now_dt`. Paper §1 mówi:

> The clock's effect is **frozen into a record, never recomputed on read**
> (ADR-019).

Zdanie jest dziś nieprawdziwe. Wersja robocza tej decyzji zakładała, że
przyczyną jest brak adresu — że proza normatywna nie wskazuje pozycji, więc
nie da się jej sprawdzić. **Pomiar to obalił:**

```
§1: 18 akapitów | z modalnością normatywną: 13 | BEZ cytowania pozycji: 3
```

Zdanie o zegarze **cytuje ADR-019**. Adres istniał i był poprawny w chwili
pisania. Rozjazd powstał, bo ADR-057 zmienił semantykę cytowanej pozycji, a
**nic nie oznaczyło prozy, która ją cytuje**.

To jest ta sama klasa, którą suspect links (834b210) zamknęły dla dowiązań
wiersz↔ramię: dowiązanie, które się rozwiązuje, nie musi być świeże.

## Decyzja

Dwie połowy, i druga jest tą wiążącą.

**1. Reguła sortująca.** Zdanie, które ma falsyfikator, jest **artykułem** —
należy do pozycji z `Gate`. Zdanie bez falsyfikatora jest **motywem** i zostaje
prozą, której nikt nie pilnuje. Stosowana **w punkcie bólu**: gdy zdanie
normatywne okaże się nieprawdziwe, nie poprawia się go w prozie — promuje się
je do pozycji. Nie wstecz, nie jako projekt przepisania.

**2. Kontrola świeżości cytowań.** Cytowanie pozycji z prozy normatywnej
podlega tej samej regule co dowiązanie wiersz↔ramię: zmiana treści cytowanej
pozycji czyni **cytujący akapit SUSPECT**, do czasu ludzkiego potwierdzenia.
Mechanicznie to rozszerzenie `suspect_links` z tabeli na akapity: klucz
`plik:akapit -> pozycja`, hash treści pozycji.

## Odrzucone

- **Detektor znaczeniowy.** Rozpoznawanie „zdań normatywnych" modelem łamie
  regułę, którą to repo już ma: *„No NLP, by design -- the moment a gate needs
  a model to fire, it is a review, not a refusal"* (ADR o `contradicts`).
  Modalność (`must`, `never`, `only`) plus obecność cytowania to lint
  powierzchniowy, nadreportujący z konstrukcji i bramkowany baseline'em.
- **Przepisanie §1 na tabelę pozycji.** 13 z 18 akapitów już cytuje; koszt
  przepisania jest wysoki, a zysk pokrywa 3 akapity. §8 item 2 mierzy churn
  jako koszt dominujący — to by go dołożyło bez proporcjonalnego zwrotu.
- **Sama reguła sortująca.** Nie złapałaby zdania o zegarze, bo ono adres ma.
  Reguła bez połowy drugiej byłaby normą wyglądającą na mechanizm.

## Konsekwencje

- Trzy akapity §1 bez cytowania są kandydatami do promocji, nie defektem.
- Zdanie o zegarze wymaga rozstrzygnięcia niezależnego od tej decyzji: ADR-057
  jest `PROPOSED` i nierecenzowany, więc **kod może wyprzedzać rekord**, a nie
  rekord kod. Naprawa prozy przed rozstrzygnięciem statusu utrwaliłaby stan
  nieprzyjęty.
- Residuum R1/R2 z `.local/warstwy-mechanizmow.md` kurczy się dopiero po
  wdrożeniu połowy drugiej. Do tego czasu proza↔kod pozostaje niepokryta i
  jest to stan zadeklarowany, nie przeoczony.

**Falsyfikator:** jeśli po wdrożeniu połowy drugiej akapit prozy normatywnej
znów przeżyje zmianę pozycji, którą cytuje, ta decyzja jest błędna — rozjazd
nie siedzi w świeżości cytowania.
