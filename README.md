# Proyecto gem5: Multiplicación de Matrices (GEMM)

Repositorio para la evaluación de arquitecturas paralelas para inferencia en el borde usando gem5 (ARMv8 + SVE).

## Esqueleto del repositorio
├─ src/        # gemm_scalar.c, gemm_sve.c, gemm_omp.c, false_sharing.c
├─ configs/    # scripts de configuración de gem5
├─ scripts/    # run_e1.sh … run_e6.sh, parse_stats.py
├─ results/    # m5out por corrida + CSV
└─ report/

## Requisitos (Ubuntu)
- gem5 (compilado para ARM con protocolos MESI_Two_Level y MOESI_CMP_directory)
- `aarch64-linux-gnu-gcc` (Toolchain cruzado)
- Python 3 + pandas + matplotlib

## Reproducibilidad
Los detalles para regenerar cada experimento se encuentran en el directorio `scripts/`.