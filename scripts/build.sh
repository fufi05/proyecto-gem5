#!/bin/bash
set -e
GEM5_ROOT=${GEM5_ROOT:-$HOME/Documentos/Arqui/Practica_cache_gem5/gem5}
CC=aarch64-linux-gnu-gcc
# una sola vez: libm5 para arm64
(cd $GEM5_ROOT/util/m5 && scons arm64.CROSS_COMPILE=aarch64-linux-gnu- build/arm64/out/m5)
M5="-I$GEM5_ROOT/include $GEM5_ROOT/util/m5/build/arm64/out/libm5.a"
mkdir -p bin bin/qemu
# escalar SIN +sve y sin autovectorizar: garantiza que no hay instrucciones SVE
$CC -O2 -static -fno-tree-vectorize -march=armv8-a src/gemm_scalar.c -o bin/qemu/gemm_scalar
$CC -O2 -static -fno-tree-vectorize -march=armv8-a -DGEM5 $M5 src/gemm_scalar.c -o bin/gemm_scalar
$CC -O2 -static -march=armv8-a+sve src/gemm_sve.c -o bin/qemu/gemm_sve
$CC -O2 -static -march=armv8-a+sve -DGEM5 $M5 src/gemm_sve.c -o bin/gemm_sve
$CC -O2 -static src/hello.c -o bin/hello
$CC -O2 -static -march=armv8-a+sve src/sve_probe.c -o bin/sve_probe
