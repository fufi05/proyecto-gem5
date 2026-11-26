#!/bin/bash
# E1: linea base de un nucleo, GEMM escalar, TimingSimple / Minor / O3 (ancho 8, ROB 192)
cd "$(dirname "$0")/.."
source scripts/common.sh
mkdir -p results
for N in 64 128; do
  for cpu in timing minor o3; do
    run scalar $N 8 192 4 results/e1/scalar_${cpu}_N$N $cpu
  done
done
python3 scripts/parse_stats.py results/e1 > results/e1.csv
echo "Listo: results/e1.csv"