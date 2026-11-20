# Código Fuente (Benchmarks)

Contiene los microbenchmarks en C. Se aplica el principio de Responsabilidad Única (SRP): cada archivo evalúa un paradigma distinto.
- `gemm_scalar.c`: Línea base escalar.
- `gemm_sve.c`: Vectorización con ARM SVE.
- `gemm_omp.c`: Paralelización multinúcleo.
- `false_sharing.c`: Evaluación de coherencia y falso compartido.