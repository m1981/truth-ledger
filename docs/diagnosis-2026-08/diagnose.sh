#!/usr/bin/env bash
# Regeneruje WSZYSTKIE pomiary diagnozy. Dossier nie jest zbiorem twierdzeń
# do uwierzenia, tylko do odtworzenia -- jedna komenda i wiadomo, co się
# posypało od ostatniego razu.
#
#   bash docs/diagnosis-2026-08/diagnose.sh            # do raw/
#   bash docs/diagnosis-2026-08/diagnose.sh --stdout   # na ekran
#
# Wyjścia lądują w raw/ i są REGENEROWALNE -- nigdy nie są watched path
# żadnego twierdzenia (ADR-037: artefakt generowany nie jest faktem).
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
RAW="$HERE/raw"
cd "$ROOT"

# --- środowisko: PYTHONPATH, nigdy waiver (patrz .local/machine.md) --------
: "${PYTHONPATH:=$HOME/.cache/truth-ledger-pylib}"
export PYTHONPATH
if ! python3 -c "import jsonschema" 2>/dev/null; then
  echo "STOP: brak jsonschema. export PYTHONPATH=\$HOME/.cache/truth-ledger-pylib" >&2
  echo "      NIE używaj TRUTH_ALLOW_NO_JSONSCHEMA=1 -- wyłącza połowę kontraktu." >&2
  exit 2
fi
if [ -n "${TRUTH_ALLOW_NO_JSONSCHEMA:-}" ]; then
  echo "STOP: TRUTH_ALLOW_NO_JSONSCHEMA jest ustawione. Odstaw waiver." >&2
  exit 2
fi

run() { printf '\n===== %s =====\n' "$1"; shift; "$@" 2>&1; }

report() {
  echo "diagnoza truth-ledger -- $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "HEAD: $(git rev-parse --short HEAD 2>/dev/null) $(git log -1 --format=%s 2>/dev/null)"
  echo "brudne pliki: $(git status --short 2>/dev/null | grep -cv '^??')"

  run "ROZMIAR" bash -c '
    for d in template/truthlib template/scripts scripts instruments; do
      [ -d "$d" ] || continue
      printf "%-20s %3s plików %7s linii\n" "$d" \
        "$(find $d -type f \( -name "*.py" -o -name "*.sh" \) | wc -l | tr -d " ")" \
        "$(find $d -type f \( -name "*.py" -o -name "*.sh" \) -exec cat {} + | wc -l | tr -d " ")"
    done
    printf "%-20s %3s plików %7s linii\n" "dokumentacja" \
      "$(find docs template/docs -name "*.md" | wc -l | tr -d " ")" \
      "$(find docs template/docs -name "*.md" -exec cat {} + | wc -l | tr -d " ")"
    printf "%-20s %3s\n" "ADR-y" "$(ls template/docs/adr/truth/*.md 2>/dev/null | wc -l | tr -d " ")"'

  run "ZŁOŻONOŚĆ (top 10 wg CC)" python3 - <<'PY'
import ast, pathlib
out=[]; loc=0; nfn=0
for p in sorted(pathlib.Path("template/truthlib").glob("*.py")):
    src=p.read_text(); loc+=len(src.splitlines())
    for n in ast.walk(ast.parse(src)):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            nfn+=1
            cc=1+sum(isinstance(x,(ast.If,ast.For,ast.While,ast.ExceptHandler,
                                   ast.BoolOp,ast.IfExp,ast.Assert)) for x in ast.walk(n))
            out.append((cc, n.end_lineno-n.lineno+1, p.name, n.name, n.lineno))
for cc,ln,f,name,line in sorted(out, reverse=True)[:10]:
    print(f"CC={cc:>4}  {ln:>4} lin  {f}:{line}  {name}()")
print(f"\nrazem {loc} loc / {nfn} funkcji / mediana CC "
      f"{sorted(c for c,*_ in out)[len(out)//2]}")
PY

  run "GRAF IMPORTÓW truthlib" python3 - <<'PY'
import ast, pathlib
root=pathlib.Path("template/truthlib")
mods={p.stem:p for p in root.glob("*.py") if p.stem!="__init__"}
edges={}
for m,p in mods.items():
    tgt=set()
    for n in ast.walk(ast.parse(p.read_text())):
        if isinstance(n,ast.ImportFrom) and n.module:
            t=n.module.split(".")[-1]
            if t in mods and t!=m: tgt.add(t)
    edges[m]=tgt
    print(f"{m:<12} -> {', '.join(sorted(tgt)) or '-'}")
# cykl?
seen,stack,cyc=set(),[],[]
def go(m):
    if m in stack: cyc.append(stack[stack.index(m):]+[m]); return
    if m in seen: return
    seen.add(m); stack.append(m)
    for t in edges[m]: go(t)
    stack.pop()
for m in mods: go(m)
print("\nCYKLE:", cyc or "brak -- DAG")
PY

  run "SUITA: test-truth-core.py" python3 template/scripts/test-truth-core.py
  run "SUITA: test-integrations.py" python3 template/scripts/test-integrations.py
  run "CANARY" bash template/scripts/truth-canary.sh
  [ -f instruments/arm-index.py ] && run "ARM-INDEX" python3 instruments/arm-index.py

  run "GIT" bash -c '
    echo "commity: $(git log --oneline | wc -l | tr -d " ")"
    echo "pierwszy: $(git log --format=%ci | tail -1)"
    echo "ostatni:  $(git log -1 --format=%ci)"
    echo "--- churn top 10 (py/sh) ---"
    git log --name-only --format= | grep -E "\.(py|sh)$" | sort | uniq -c | sort -rn | head -10'
}

if [ "${1:-}" = "--stdout" ]; then
  report
else
  mkdir -p "$RAW"
  STAMP="$(date -u '+%Y%m%dT%H%M%SZ')"
  OUT="$RAW/diagnose-$STAMP.txt"
  report > "$OUT"
  ln -sf "$(basename "$OUT")" "$RAW/latest.txt"
  echo "zapisano $OUT"
  grep -E '^(Ran |OK|FAILED|canary result|arm-index|CYKLE|razem )' "$OUT" || true
fi
