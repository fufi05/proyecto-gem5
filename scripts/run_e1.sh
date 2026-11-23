#!/bin/bash
# E1: linea base de un nucleo (ancho 8, ROB 192, VL 512), N = 64 y 128
cd "$(dirname "$0")/.."
source scripts/common.sh
mkdir -p results
for N in 64 128; do
  run scalar $N 8 192 4 results/e1/scalar_N$N
  run sve    $N 8 192 4 results/e1/sve_vl512_N$N
done
python3 scripts/parse_stats.py results/e1 > results/e1.csv
echo "Listo: results/e1.csv"