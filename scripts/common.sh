# common.sh - funcion run compartida por run_e*.sh (usar con: source scripts/common.sh)
GEM5_ROOT=${GEM5_ROOT:-$HOME/Documentos/Arqui/Practica_cache_gem5/gem5}
GEM5=${GEM5:-$GEM5_ROOT/build/ARM/gem5.opt}

# run <impl> <N> <width> <rob> <vl> <outdir>
run() {
  local impl=$1 N=$2 w=$3 rob=$4 vl=$5 out=$6
  [ -f "$out/meta.txt" ] && return            # ya terminada: reanudable
  mkdir -p "$out"
  "$GEM5" -d "$out" configs/arm_se.py --bin "bin/gemm_$impl" --args "$N" \
          --width "$w" --rob "$rob" --vl "$vl" > "$out/run.log" 2>&1
  echo "impl=$impl N=$N width=$w rob=$rob vl=$vl" > "$out/meta.txt"
}