#!/usr/bin/env bash


set -u

PID="${1:-}"
LABEL="${2:-manual}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_ROOT="${DUMP_DIR:-$SCRIPT_DIR/dumps}"

if [[ -z "$PID" ]]; then
  echo "Usage: $0 <PID> [label]" >&2
  exit 2
fi
if ! kill -0 "$PID" 2>/dev/null; then
  echo "Процесс PID=$PID не найден или нет доступа" >&2
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$OUT_ROOT/${LABEL}_pid${PID}_${STAMP}"
mkdir -p "$OUT"

{
  echo "label=$LABEL"
  echo "pid=$PID"
  echo "time=$(date -Iseconds 2>/dev/null || date)"
  echo "uname=$(uname -a)"
  echo "cmd=$(ps -p "$PID" -o command= 2>/dev/null || true)"
} > "$OUT/meta.txt"

# снимок store, который UI кладёт рядом перед вызовом
if [[ -f "$OUT_ROOT/_last_store_snapshot.txt" ]]; then
  cp "$OUT_ROOT/_last_store_snapshot.txt" "$OUT/store_snapshot.txt"
fi

OS="$(uname -s)"
CORE="$OUT/core"
DUMP_OK=0

if [[ "$OS" == "Darwin" ]]; then
  # карта памяти (без root часто доступна)
  vmmap "$PID" > "$OUT/vmmap.txt" 2>"$OUT/vmmap.err" || true
  # полный core через lldb (может потребовать права отладчика / SIP)
  if command -v lldb >/dev/null 2>&1; then
    lldb -b -p "$PID" \
      -o "process save-core \"$CORE\"" \
      -o quit \
      >"$OUT/lldb.out" 2>"$OUT/lldb.err" || true
  fi
elif [[ "$OS" == "Linux" ]]; then
  if command -v gcore >/dev/null 2>&1; then
    gcore -o "$OUT/coreprefix" "$PID" >"$OUT/gcore.out" 2>"$OUT/gcore.err" || true
    # gcore пишет coreprefix.<pid>
    if ls "$OUT"/coreprefix.* >/dev/null 2>&1; then
      mv "$OUT"/coreprefix.* "$CORE" 2>/dev/null || true
    fi
  elif command -v gdb >/dev/null 2>&1; then
    gdb -batch -p "$PID" \
      -ex "generate-core-file $CORE" \
      -ex detach -ex quit \
      >"$OUT/gdb.out" 2>"$OUT/gdb.err" || true
  fi
  # maps
  cp "/proc/$PID/maps" "$OUT/maps.txt" 2>/dev/null || true
  ps -p "$PID" -o pid,rss,vsz,pcpu,pmem,etime,cmd > "$OUT/ps.txt" 2>/dev/null || true
fi

if [[ -f "$CORE" ]]; then
  DUMP_OK=1
  if command -v strings >/dev/null 2>&1; then
    strings -a "$CORE" 2>/dev/null | head -n 8000 > "$OUT/strings_head.txt" || true
  fi
  ls -lh "$CORE" > "$OUT/core_size.txt"
fi

# CPU/RAM на момент дампа
ps -p "$PID" -o pid=,rss=,vsz=,pcpu=,pmem= > "$OUT/resources.txt" 2>/dev/null || true

{
  echo "OUT=$OUT"
  if [[ "$DUMP_OK" -eq 1 ]]; then
    echo "CORE=ok ($CORE)"
  else
    echo "CORE=missing (нужны права отладчика / sudo / Linux gcore)"
    echo "Смотри vmmap.txt / maps.txt / store_snapshot.txt — для отчёта этого часто достаточно,"
    echo "а полный core сними вручную: sudo lldb -p $PID -o 'process save-core $OUT/core' -o quit"
  fi
} | tee "$OUT/RESULT.txt"

echo "$OUT"
