# Maszyneria truth-ledger — rysunki struktury (migawka 2026-08-29)

> Reader: każdy, kto chce zobaczyć całość maszynerii meta-repo pod jednym
> kątem, zanim dotknie kodu | Enables: orientację bez czytania 30 plików;
> wiedzę, które krawędzie są bramkowane mechanicznie, a które tylko
> narysowane | Update-trigger: zmiana wiringu hooków, ramion baterii lub
> granicy tieringu — a przy każdej wątpliwości DRZEWO WYGRYWA z rysunkiem

Ten plik jest RYSUNKIEM, nie rejestrem. Trzy figury poniżej mają
mechanicznych strażników i tam należy sprawdzać stan faktyczny:
osiągalność bramek — `bash scripts/gate-reachability.sh` (dopełnienie
orzekane od `83cd6c2`); układ truthlib — `template/docs/structure.md`
przypięty testem `TestStructureDocMatchesDisk`; skład baterii —
`scripts/release-battery.sh` jest źródłem prawdy o własnych ramionach.
Reszta jest prozą narysowaną z drzewa dnia 2026-08-29.

## 1. Pierścienie obronne i korzenie

Trzy pierścienie o rosnącym zasięgu (commit → push → sesja) plus dwa
hooki harnessu agenta. Wszystkie drogi prowadzą do jednego CLI.

```mermaid
flowchart LR
  subgraph ROOTS["korzenie"]
    PC[".githooks/pre-commit"]
    PP[".githooks/pre-push"]
    SS["SessionStart<br/>(digest)"]
    PT["PreToolUse<br/>(Edit/Write)"]
    SE["koniec sesji<br/>agenta"]
  end
  PC --> CT["scripts/check-truth.sh<br/>(bramka commitu)"]
  PP --> TAG["tag-check"] & RB["scripts/release-battery.sh<br/>(15 ramion)"]
  SS --> DIG["truth-session-digest.py"]
  PT --> WH["truth-whisper.py<br/>deny: fail-closed<br/>whisper: fail-open, P0 pelne,<br/>P1/P2 jedna linia (ruling 2026-08-28)"]
  SE --> SC["session-close.sh<br/>+ session-gates.d/*.sh"]
  CT --> T["scripts/truth<br/>(CLI, symlink do template)"]
  DIG --> T
  WH --> T
  SC --> T
  RB --> T
```

## 2. Bateria push — trzy warstwy, dwa strażniki zakresu

Pomiar 2026-08-28: wariant maksymalny 10:52; zwykly push placi tylko
warstwe 1 (~2 min). Werdykt trzywarstwowy:
`docs/field-notes-2026-08-28-ceremony-cut-session.md`.

```mermaid
flowchart TD
  RB["release-battery.sh (pre-push)"] --> W1
  subgraph W1["warstwa 1 — zawsze, ~2 min"]
    direction LR
    A1["lockstep 7 powierzchni"]
    A2["fact-health"]
    A3["retracted-figures"]
    A4["doc-health (korpus szablonu)"]
    A5["core 538 t."]
    A6["v04"]
    A7["structural 116 t."]
    A8["integrations 64 t."]
    A9["field-consumers"]
    A10["label-coupling"]
    A11["arm-index (1280 ramion)"]
    A12["gate-reachability (19 checkow<br/>+ dopelnienie puste)"]
    A13["reproduce (65 kapsul, ~0.5 s)"]
  end
  RB -->|"scope dotyka:<br/>template CLI / truthlib / canary"| W2["warstwa 2 — canary<br/>290 zasianych usterek"]
  RB -->|"scope dotyka:<br/>baterii / sweepa / pre-push"| W3["warstwa 3 — meta-bramka<br/>test-release-battery, 17 ramion<br/>(bateria przez sama siebie;<br/>fixture poza drzewem od 2026-08-28)"]
```

## 3. Import-DAG truthlib (functional core / imperative shell)

Zrodlem przypietym testem jest `template/docs/structure.md`. Krawedz
A --> B czytaj "A importuje B". Dla czytelnosci pominieto krawedzie,
ktore kazdy modul i tak ma do `registry`/`kernel` — pelny obraz w
strukturze przypietej.

```mermaid
flowchart TD
  cli --> gates & advisory & contract & reports & shellio
  gates --> evidence & policy & reports & shellio
  advisory --> evidence & policy & reports
  contract --> policy
  reports --> evidence
  evidence --> kernel
  policy --> kernel
  shellio --> kernel & structural
  kernel --> registry & structural
  classDef pure fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20;
  classDef shell fill:#fff3e0,stroke:#ef6c00,color:#e65100;
  class registry,kernel,structural,policy,evidence,reports,contract,advisory,gates pure;
  class shellio,cli shell;
```

`shellio` jest jedynym modulem z `subprocess` (pilnuje `TestModulePurity`);
`registry` czystym dnem, `cli` jedynym korzeniem. Fold w `kernel` jest
czysta funkcja — status nigdy nie jest przechowywany.

## 4. Granica tieringu (ADR-046): co jedzie do konsumenta, co zostaje

```mermaid
flowchart LR
  subgraph TPL["template/ — Tier A/B (kopiowane przez copier)"]
    TT["scripts/truth + truthlib/"]
    TG["check-truth / spec-health /<br/>doc-health / session-close /<br/>install-hooks"]
    TS["suity: core, v04,<br/>structural, integrations"]
    TC["truth-canary.sh"]
  end
  subgraph MET27["meta-repo — Tier C (nigdy nie szablonowane)"]
    IN["instruments/*.py<br/>(arm-index, waiver-index,<br/>blast, separation, ...)"]
    MB["release-battery +<br/>test-release-battery +<br/>gate-reachability"]
    MH["fact-health, whisper,<br/>digest, retracted-figures"]
    GOV["docs/governance/<br/>(orzeczenia, gate-metrics,<br/>catch-log)"]
  end
  IN -->|import| TT
  MB --> TS & TC
  TC -.->|"wyjatek udokumentowany:<br/>3 instrumenty SD"| IN
  MH --> TT
```

Kierunek jest czysty w jedna strone: nic z `template/` nie wola meta-strony
(poza narysowanym wyjatkiem canary); meta swobodnie importuje truthlib.

## 5. Cykl zycia claimu (fold, ADR-016/057)

```mermaid
stateDiagram-v2
  [*] --> unverified: claim (rodzi sie niezweryfikowany)
  unverified --> live: verdict agree
  live --> diverged: verdict diverge (kolejka)
  live --> stale: invalidation / TTL z zegara odczytu
  live --> disputed: contradicts, obie strony live
  diverged --> live: pozniejszy agree
  stale --> live: pozniejszy agree
  unverified --> cannot_verify: verdict cannot_verify
  cannot_verify --> live: pozniejszy agree
  live --> retracted: verdict retracted (TRUTH_HUMAN=1)
  unverified --> retracted: verdict retracted (TRUTH_HUMAN=1)
  retracted --> [*]: terminalny — pozniejsze zdarzenia ignorowane
```

Status jest zawsze projekcja `fold(events, now_dt)` — `stale` z TTL liczy
sie w chwili odczytu (ADR-057), `disputed` jest post-passem po statusach
bazowych, `retracted` absorbuje. Zadnego przechowywanego stanu.
