# Aprendizaje continuo Proyecto GEM5

## Integrantes del equipo
- Integrante 1: Felipe Sánchez Segura (2023083272)
- Integrante 2: Anthony Villalta
- Integrante 3: Saul Quesada
- Integrante 4: Jorge Pérez

## AC1
## Matriz de competencias

Cada integrante se califica de forma individual con la escala al final. En "Evidencia" se registra una tarea, resultado o aporte que sustente la valoración.

| Competencia | Desempeño observable | Felipe (0–3) | Anthony (0–3) | Saul (0–3) | Jorge (0–3) | Evidencia |
|---|---|:-:|:-:|:-:|:-:|---|
| Comprensión del problema y modelo de costo | Identifica la pregunta del proyecto (mejor combinación de núcleos, ancho, VL y protocolo con presupuesto de 32 unidades), la fórmula de costo y el rol de E1–E6. | 1 | | | | |
| Fundamentos de arquitectura | Explica cómo el ancho de emisión, el ROB, la IQ, la longitud vectorial SVE y la coherencia (MESI/MOESI) afectan el rendimiento de GEMM. | 2 | | | | |
| Configuración de gem5 | Configura gem5 en modo SE para ARMv8 + SVE: tipo de CPU (TimingSimple, Minor, O3), ancho, ROB, VL, jerarquía clásica o Ruby y número de núcleos. | 1 | | | | |
| Preparación del entorno | Compila gem5 (contenedor Docker con MESI_Two_Level y MOESI_CMP_directory) y cross-compila binarios AArch64 estáticos. | 1 | | | | |
| Ejecución de simulaciones | Ejecuta los barridos de E1–E5 y verifica que cada corrida termine con `stats.txt` válido. | 0 | | | | |
| Programación de cargas de trabajo (GEMM y SVE) | Escribe y valida GEMM (N = 64 y 128) escalar y con SVE, delimita la ROI con `m5_reset_stats()` y `m5_dump_stats()`, y prepara el microbenchmark de falso compartido. | 0 | | | | |
| Diseño experimental | Varía una variable a la vez (ancho, ROB, VL, núcleos, protocolo, relleno), justifica el barrido y respeta el límite de costo en E6. | 0 | | | | |
| Recolección de resultados | Extrae de `stats.txt` solo las métricas de la ROI y las organiza en CSV por experimento. | 0 | | | | |
| Análisis de métricas | Interpreta IPC, CPI, speedup, eficiencia, fallos de caché e invalidaciones, y explica las tendencias con conceptos de arquitectura y la ley de Amdahl. | 0 | | | | |
| Diagnóstico y resolución de problemas | Identifica y corrige fallos típicos: errores de build, instrucciones SVE no soportadas, estadísticas contaminadas por la inicialización, errores de Ruby. |0 | | | | |
| Reproducibilidad y gestión del trabajo | Mantiene repositorio Git, scripts y README de modo que un comando regenere CSV y gráficos de cada experimento. |2 |3| | | |
| Colaboración y comunicación técnica | Lidera su experimento (E2–E5), cumple acuerdos, documenta en la bitácora y expone con dominio su parte del video. |2|3| | | |

### Escala

| Nivel | Descripción |
|:-:|---|
| 0 | No lo ha hecho ni lo conoce |
| 1 | Lo conoce, pero necesita guía para aplicarlo |
| 2 | Lo aplica con autonomía en casos conocidos |
| 3 | Lo aplica con dominio, resuelve imprevistos y puede enseñarlo |

## Brechas prioritarias

### Felipe
1. **Configurar y compilar el entorno gem5 ARM + SVE.** Es la brecha más urgente porque sin el entorno no se puede correr ningún experimento y es parte del entregable de la semana 1. Para cerrarla, investigaré entre la documentación de gem5 y buscaré guía para configurar el docker y el entorno en mi máquina. Para evaluar el cumplimiento de esta brecha, ejecutaré un "hola mundo" en modo SE.

2. **Escribir y validar GEMM escalar y con SVE.** Sin este kernel no se pueden hacer E1, E3 ni E6. Para cerrarla, escribiré GEMM con N = 64 compilado de forma estática para AArch64, delimitaré la región de interés con `m5_reset_stats()` y `m5_dump_stats()`, y comprobaré que el resultado coincida con la versión escalar. La evidencia será el código fuente y la comparación de salidas.

3. **Ejecutar simulaciones y diseñar barridos controlados.** Esta brecha habilita E1 y, después, E2 a E5. Para cerrarla, completaré E1 con TimingSimple, Minor y O3, y exportaré a un CSV con las métricas relevantes. La evidencia será el CSV y el script de extracción.

### Anthony

_Por completar._

### Saul

_Por completar._

### Jorge

_Por completar._