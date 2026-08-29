# Field notes — sesja 2026-08-28: cięcie ceremonii, backfill ogona, kolizja dwóch bramek

> Reader: operator i przyszłe sesje agentów wracające do pytania "co
> postanowiliśmy i dlaczego" | Enables: podjęcie wątków bez ponownego
> wyprowadzania werdyktów; wiedza, które daty są uzbrojone | Update-trigger:
> przegląd 2026-09-28 (metryka ogona prozy) lub kwartalne odczytanie
> zdobyczy meta-bramki

Tekstem wiążącym dla orzeczeń jest
`docs/governance/operator-actions-2026-08-28.md` — ten plik to narracja
i werdykty analityczne sesji, nie drugi dom dla reguł.

## Co się wydarzyło (skrót)

1. Martwe wskaźniki `Gate: scripts/test-instruments.sh` w pięciu nagłówkach
   instrumentów Tier C (plus proza canary/core/README) zastąpione żywą
   bramką `TestTierCInstruments`; przypięte claimem, zweryfikowanym
   niezależnie przed wejściem orzeczeń w życie.
2. Operator przyjął sześć orzeczeń ("rytuał wyłączony, mechanika zostaje")
   i zostały wykonane w tej samej sesji: dyspozycje weryfikatorów tylko
   P0/diverged/punkt-użycia, P2 bez ceremonii, whisper P0-only z agregacją
   P1/P2 (zamknięło bramkę zmęczeniową ADR-005), zamrożenie meta-aparatury,
   backfill selektywny, labels-deps jako warstwa orientacji i nigdy bramka.
3. Backfill: zwiad siedmiu agentów read-only nad ADR-054..061, kapsuły
   przeliczone przez sesję filującą, siedem claimów. Metryka ogona prozy:
   z siedmiu zer do zera zer w ADR-054..063.
4. Push zablokowany przez baterię i odblokowany naprawą: dopełnienie sweepa
   (`83cd6c2`) złapało fixture własnej meta-bramki (`.skip-stub.py`) jako
   plik osiągnięty-nienazwany; fixture wyprowadzona do `mktemp -d`
   (wpis `not-a-check` nie mógł tego naprawić — byt przejściowy łamie
   regułę lustra, gdy nie istnieje). ARM 13 czerwony-potem-zielony.

## Werdykty analityczne warte pamiętania

**IV&V.** Rdzeniem wartości tego systemu jest część mechaniczna (kapsuły,
tripwire'y, bramki intake, fold, reproduce) — nie "niezależny agent".
Świeży weryfikator daje niezależność KONTEKSTU (realną: autor jest
najgorszym weryfikatorem własnej pracy), ale nie niezależność AWARII:
dwie instancje tego samego modelu mylą się skorelowanie i "agree" tego
nie wykryje. Osi organizacyjnej IV&V (IEEE 1012) nie ma wcale. Najuczciwsza
liczba systemu: hit rate weryfikacji ~1,5% — stąd całe cięcie ceremonii.

**Dla kogo to narzędzie.** Rozwiązuje trzy realne problemy pracy
wielosesyjnej z agentami: dryf przekonań między sesjami, nadmiarowy
kwantyfikator nad zawężonym dowodem (zmierzony dominujący defekt),
dokumentację kłamiącą w czasie teraźniejszym. Bez wielu sesji agentowych
na jednym repo nie rozwiązuje niczego, czego nie robi taniej review + CI.

**Bateria push (pomiar 2026-08-28: 10:52 w wariancie maksymalnym).**
Trzy warstwy o różnym rachunku:

- 13 ramion zawsze-włączonych (~2 min) — potrzebne, z dowodami
  (audyt 2026-08-01: core suite czerwona na HEAD i nikt nie wiedział;
  zdobycze reproduce/fact-health w catch-logu).
- canary 290 ramion — ciężki, ale strzeżony zakresem (płaci się przy
  zmianach CLI/truthlib/canary). Zostawić.
- meta-bramka (17 ramion, ~6-7 min) — strzeżona zakresem (zmiany baterii);
  jedyna warstwa, której znane zdobycze są defektami samej aparatury
  (przypadek `.skip-stub.py` włącznie). KRYTERIUM UZBROJONE: jeśli do
  ~2026-11 nadal łapie wyłącznie samą siebie, jest pierwszym kandydatem
  do przeniesienia na granicę taga (konsumenci resolwują z tagów — mówi
  to nagłówek samej baterii).

**labels-deps (zewnętrzne repo użytkownika).** Skan z `74e8aab` pierwszy
pokazał ogon prozy (50 etykiet bez rekordu); re-weryfikacja na HEAD
potwierdziła nośny podzbiór. Wzorzec narzędzia właściwy: pull, read-only,
zawsze exit 0, głośne mianowniki. Mapa poznawcza, nie dowodowa — 57%
krawędzi z wnioskowania.

## Wątki otwarte

- [ ] 2026-09-28: ponowne odczytanie metryki ogona prozy (komenda w pliku
      orzeczeń); decyzje przyjęte po 2026-08-28 mają dostawać rekord w
      tydzień od przyjęcia.
- [ ] ~2026-11: kwartalne odczytanie zdobyczy meta-bramki (kryterium wyżej).
- [ ] catch-log (plik operatora — decyzja operatora): dwa kandydaty z
      2026-08-28: sweep łapiący fixture własnej meta-bramki, oraz fałszywy
      pomiar sesji "stub niewinny" (`$?` po pipe zmierzył `tail`, nie
      sweep; złapane zinstrumentowanym rerunem).
- [ ] labels_deps: renderer mermaid pada na dwukropku w `title:` (trzy z
      trzech renderów w demo) — naprawa w tamtym repo, poza tym.
- [ ] Rek. z przeglądu labels-deps: linia onboardingowa jest w AGENTS.md;
      głębsza integracja (np. artefakt skanu w .local/) nieurządzona,
      celowo — najpierw niech pull-model się przyjmie.

## Identyfikatory sesji (do wglądu, nie do cytowania w prozie normatywnej)

```
tr-87641e5b  nagłówki Tier C wskazują żywą bramkę (live, zweryfikowany)
tr-dcc1210c  whisper agreguje poniżej P0 (claim-at-death wk-5473af07)
tr-1819c0cc  ADR-054  tr-663c336c ADR-055  tr-503345de ADR-056
tr-68fa5f13  ADR-058 (ciemna bramka)  tr-a4520bb3 ADR-059
tr-3a35dc57  ADR-060  tr-7355a77e ADR-061 (status NORM)
```
