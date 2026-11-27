# Aprendizaje continuo Proyecto GEM5

## Integrantes del equipo
- Integrante 1: Felipe Sánchez Segura (2023083272)
- Integrante 2: Anthony Villalta
- Integrante 3: Saul Quesada
- Integrante 4: Jorge Pérez Jimenez (2021061955)

## AC1
### Matriz de competencias

Cada integrante se califica de forma individual con la escala al final. En "Evidencia" se registra una tarea, resultado o aporte que sustente la valoración.

| Competencia | Desempeño observable | Felipe (0–3) | Anthony (0–3) | Saul (0–3) | Jorge (0–3) | Evidencia |
|---|---|:-:|:-:|:-:|:-:|---|
| Comprensión del problema y modelo de costo | Identifica la pregunta del proyecto (mejor combinación de núcleos, ancho, VL y protocolo con presupuesto de 32 unidades), la fórmula de costo y el rol de E1–E6. | 1 | | | 1 | |
| Fundamentos de arquitectura | Explica cómo el ancho de emisión, el ROB, la IQ, la longitud vectorial SVE y la coherencia (MESI/MOESI) afectan el rendimiento de GEMM. | 2 | | | 2 | |
| Configuración de gem5 | Configura gem5 en modo SE para ARMv8 + SVE: tipo de CPU (TimingSimple, Minor, O3), ancho, ROB, VL, jerarquía clásica o Ruby y número de núcleos. | 1 | | | 1 | |
| Preparación del entorno | Compila gem5 (contenedor Docker con MESI_Two_Level y MOESI_CMP_directory) y cross-compila binarios AArch64 estáticos. | 1 | | | 1 | |
| Ejecución de simulaciones | Ejecuta los barridos de E1–E5 y verifica que cada corrida termine con `stats.txt` válido. | 0 | | | 1 | |
| Programación de cargas de trabajo (GEMM y SVE) | Escribe y valida GEMM (N = 64 y 128) escalar y con SVE, delimita la ROI con `m5_reset_stats()` y `m5_dump_stats()`, y prepara el microbenchmark de falso compartido. | 0 | | | 0 | |
| Diseño experimental | Varía una variable a la vez (ancho, ROB, VL, núcleos, protocolo, relleno), justifica el barrido y respeta el límite de costo en E6. | 0 | | | 0 | |
| Recolección de resultados | Extrae de `stats.txt` solo las métricas de la ROI y las organiza en CSV por experimento. | 0 | | | 0 | |
| Análisis de métricas | Interpreta IPC, CPI, speedup, eficiencia, fallos de caché e invalidaciones, y explica las tendencias con conceptos de arquitectura y la ley de Amdahl. | 0 | | | 0 | |
| Diagnóstico y resolución de problemas | Identifica y corrige fallos típicos: errores de build, instrucciones SVE no soportadas, estadísticas contaminadas por la inicialización, errores de Ruby. |0 | | | 0 | |
| Reproducibilidad y gestión del trabajo | Mantiene repositorio Git, scripts y README de modo que un comando regenere CSV y gráficos de cada experimento. |2 | | | 2 | |
| Colaboración y comunicación técnica | Lidera su experimento (E2–E5), cumple acuerdos, documenta en la bitácora y expone con dominio su parte del video. |2| | | 2 | |

### Escala

| Nivel | Descripción |
|:-:|---|
| 0 | No lo ha hecho ni lo conoce |
| 1 | Lo conoce, pero necesita guía para aplicarlo |
| 2 | Lo aplica con autonomía en casos conocidos |
| 3 | Lo aplica con dominio, resuelve imprevistos y puede enseñarlo |

### Brechas prioritarias

#### Felipe
1. **Configurar y compilar el entorno gem5 ARM + SVE.** Es la brecha más urgente porque sin el entorno no se puede correr ningún experimento y es parte del entregable de la semana 1. Para cerrarla, investigaré entre la documentación de gem5 y buscaré guía para configurar el docker y el entorno en mi máquina. Para evaluar el cumplimiento de esta brecha, ejecutaré un "hola mundo" en modo SE.

2. **Escribir y validar GEMM escalar y con SVE.** Sin este kernel no se pueden hacer E1, E3 ni E6. Para cerrarla, escribiré GEMM con N = 64 compilado de forma estática para AArch64, delimitaré la región de interés con `m5_reset_stats()` y `m5_dump_stats()`, y comprobaré que el resultado coincida con la versión escalar. La evidencia será el código fuente y la comparación de salidas.

3. **Ejecutar simulaciones y diseñar barridos controlados.** Esta brecha habilita E1 y, después, E2 a E5. Para cerrarla, completaré E1 con TimingSimple, Minor y O3, y exportaré a un CSV con las métricas relevantes. La evidencia será el CSV y el script de extracción.

#### Anthony

_Por completar._

#### Saul

_Por completar._

#### Jorge

1. **Configurar gem5 para ARM con Ruby.** Esta es mi primera prioridad porque necesito verificar que el microbenchmark funcione con los dos protocolos antes de ejecutar el barrido completo. Para cerrarla, ejecutaré una prueba con 2 núcleos en `MESI_Two_Level` y otra en `MOESI_CMP_directory`. Confirmaré el protocolo en la configuración y comprobaré que ambas pruebas generen un `stats.txt` válido.

2. **Diseñar y ejecutar un barrido controlado de falso compartido.** Para medir el efecto del relleno, compararé `pad` y `nopad` con el mismo protocolo y número de núcleos. Para cerrarla, ejecutaré las 12 combinaciones de 2 protocolos, 2 variantes y 3 cantidades de núcleos (2, 4 y 8). Mantendré 100 000 incrementos por hilo y verificaré el valor final de cada contador. La evidencia será la matriz de corridas y los registros de ejecución. 

3. **Extraer e interpretar las métricas de la región de interés.** Necesito distinguir qué mide cada estadística para explicar el efecto del falso compartido. Para cerrarla, extraeré las invalidaciones explícitas de L1, los pasos de mensajes por los conmutadores de Ruby y la latencia media de fallo. Generaré un CSV con las 12 corridas y un gráfico comparativo. Usaré los traspasos de líneas modificadas para explicar por qué el contador de invalidaciones explícitas solo refleja parte del tráfico de coherencia.

## AC2
### Felipe 

| # | Tecnología emergente | Por qué importa para el proyecto | Recurso de aprendizaje | ¿Cómo lo usaré?|
|:-:|---|---|---|---|
| 1 | Biblioteca estándar de gem5, gem5 Resources, Suite y MultiSim | Permite armar configuraciones con componentes ya probados y lanzar varias simulaciones en paralelo desde un solo script | Tutorial de la biblioteca estándar de gem5 (CS 433, Illinois) | Escribiré los scripts necesarios para simular la arquitectura y responder a la pregunta del proyecto |
| 2 | Extensión matricial de Arm (SME) en gem5 | SME apunta a operaciones matriciales como GEMM y es la continuación natural de SVE | Notas de versión de gem5 y documentación de Arm sobre SME | Escribiré scripts usando esta extensión y mediré las métricas necesarias para su análisis|
| 3 | Agentes de IA para exploración del espacio de diseño | Automatizan la búsqueda de configuraciones bajo restricciones de costo, como el E6 |  Artículo "gem5 Co-Pilot" (arXiv 2510.19577) | Investigación y automatización de tareas |

**Fuentes.**
- Pai et al., "Toward Reproducible and Standardized Computer Architecture Simulation with gem5", ISPASS 2026: https://arch.cs.ucdavis.edu/simulation/2026/05/26/gem5-resources.html
- Versión en arXiv: https://arxiv.org/abs/2512.13479
- Documentación del módulo MultiSim: https://www.gem5.org/documentation/general_docs/stdlib_api/gem5.utils.multisim.multisim.html
- Tutorial de la biblioteca estándar (CS 433, Illinois): https://courses.grainger.illinois.edu/cs433/gem5/part1/cache_config
- Notas de versión de gem5 (sección de mejoras de la ISA Arm): https://gem5.googlesource.com/public/gem5/+show/refs/heads/master/RELEASE-NOTES.md
- Documentación de Arm sobre SME: https://developer.arm.com/documentation/ddi0616/latest
- Fu, Manley y Alian, "gem5 Co-Pilot: AI Assistant Agent for Architectural Design Space Exploration", 2025: https://arxiv.org/abs/2510.19577

  ### Jorge

| # | Tecnología emergente | Por qué importa para el proyecto | Recurso de aprendizaje | ¿Cómo lo usaré? |
|:-:|---|---|---|---|
| 1 | Extensión matricial de Arm (SME) | Permite acumular productos externos de vectores en bloques de la matriz de salida. Esto ayuda a entender cómo se puede acelerar GEMM dentro de un núcleo. En el E5 estudié otro aspecto del rendimiento: el tráfico de coherencia entre núcleos. | Tutorial introductorio de Arm sobre SME, con ejemplos de productos externos y almacenamiento matricial ZA. | Seguiré un ejemplo del tutorial para mostrar cómo dos vectores actualizan un bloque de la matriz de salida. Compararé ese procedimiento con el bucle interno de GEMM para identificar dónde se acumulan los resultados parciales. |
| 2 | Extensión vectorial de RISC-V (RVV) | Permite procesar una fila de GEMM en tramos de longitud variable. Compararla con Arm SVE ayuda a entender cómo se procesan los elementos restantes cuando la fila no cabe en un número exacto de vectores. | Especificación de la extensión V 1.0 y guía de intrínsecos vectoriales en C de RISC-V International. | Escribiré pseudocódigo para actualizar una fila de GEMM por tramos con `vsetvli`. Usaré una matriz pequeña que deje un tramo parcial y compararé el resultado con el de una implementación escalar. |

**Fuentes**

- [Arm, *Scalable Matrix Extension (SME) Introduction*](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/arm-scalable-matrix-extension-introduction)
- [RISC-V International, *V Standard Extension for Vector Operations*, versión 1.0](https://docs.riscv.org/reference/isa/unpriv/v-st-ext)
- [RISC-V International, *RISC-V Vector C Intrinsic Specification*](https://docs.riscv.org/reference/vector-c-intrinsics/rvv-intrinsic-spec.html)
