#!/bin/bash
# E3: escalar (ancho 1,2,4,8 x ROB 32,64,192) vs SVE (VL 128..1024), N = 64 y 128
cd "$(dirname "$0")/.."
source scripts/common.sh
export -f run; export GEM5
mkdir -p results
{
  for N in 64 128; do
    for w in 1 2 4 8; do for r in 32 64 192; do
      echo "scalar $N $w $r 4 results/e3/scalar_w${w}_rob${r}_N$N"
    done; done
    for vl in 1 2 4 8; do
      echo "sve $N 8 192 $vl results/e3/sve_vl$((vl*128))_N$N"
    done
  done
} | xargs -P${JOBS:-4} -L1 bash -c 'run "$@"' _
python3 scripts/parse_stats.py results/e3 > results/e3.csv
echo "Listo: results/e3.csv"