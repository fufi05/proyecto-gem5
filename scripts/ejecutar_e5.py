#!/usr/bin/env python3
"""Prepara o ejecuta corridas de E5 a partir de corridas_E5.csv."""

import argparse
import csv
from os import X_OK, access, environ
from pathlib import Path
import shlex
import subprocess
import sys


PROTOCOLS = ("MESI_Two_Level", "MOESI_CMP_directory")
BENCHMARKS = ("false_sharing", "gemm_paralelo")
HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def path_at(root, value):
    return (root / value).resolve()


def plan(args):
    config = path_at(args.gem5_root, args.config)
    stats_paths = set()
    run_ids = set()
    runs = []

    with args.csv.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            run_id = row["corrida_id"]
            if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
                raise ValueError(f"Identificador inválido: {run_id!r}")
            if run_id in run_ids:
                raise ValueError(f"Identificador repetido: {run_id}")
            run_ids.add(run_id)
            if args.corrida and run_id not in args.corrida:
                continue
            if args.piloto and row["nucleos"] != "2":
                continue

            protocol = row["protocolo"]
            benchmark = row["benchmark"]
            if args.protocolo and protocol != args.protocolo:
                continue
            if args.benchmark and benchmark != args.benchmark:
                continue
            cores = row["nucleos"]
            if protocol not in PROTOCOLS or cores not in {"2", "4", "8"}:
                raise ValueError(f"{run_id}: protocolo o núcleos inválidos")
            if row["hilos"] != cores or row["linea_cache_bytes"] != "64":
                raise ValueError(f"{run_id}: se requiere un hilo por núcleo y líneas de 64 bytes")

            gem5_override = args.mesi if protocol == PROTOCOLS[0] else args.moesi
            gem5 = path_at(args.gem5_root, gem5_override or row["binario_gem5_referencia"])
            if benchmark == "false_sharing":
                variant = row["variante"]
                iterations = int(row["incrementos_por_hilo"])
                if variant not in {"pad", "nopad"} or iterations < 1:
                    raise ValueError(f"{run_id}: variante o incrementos inválidos")
                recorded = f"{cores} {variant} {iterations}"
                workload = path_at(args.trabajo, args.micro or row["binario_benchmark_referencia"])
                if args.piloto:
                    iterations = min(iterations, 1000)
                workload_args = f"{cores} {variant} {iterations}"
                expected = [f"{variant} hilos={cores} esperado={iterations}"]
                expected.extend(f"contador[{idx}]={iterations}" for idx in range(int(cores)))
                expected.append("Verificación: OK")
            elif benchmark == "gemm_paralelo":
                size = int(row["gemm_n"])
                if size < 1:
                    raise ValueError(f"{run_id}: dimensión GEMM inválida")
                recorded = f"{size} {cores}"
                workload = path_at(args.trabajo, args.gemm or row["binario_benchmark_referencia"])
                workload_args = f"{min(size, 16) if args.piloto else size} {cores}"
                expected = []
            else:
                raise ValueError(f"{run_id}: benchmark desconocido: {benchmark}")

            if shlex.split(recorded) != shlex.split(row["argumentos_benchmark"]):
                raise ValueError(f"{run_id}: los argumentos contradicen los parámetros del CSV")
            stats = path_at(args.trabajo, row["stats_txt"])
            if not stats.is_relative_to(args.trabajo) or stats.name != "stats.txt":
                raise ValueError(f"{run_id}: stats.txt debe estar dentro del directorio de trabajo")
            if args.piloto:
                stats = args.trabajo / "results/e5_piloto" / run_id / "stats.txt"
            if stats in stats_paths:
                raise ValueError(f"{run_id}: ruta de estadísticas repetida: {stats}")
            stats_paths.add(stats)

            command = [
                str(gem5), "-d", str(stats.parent), str(config), "-n", cores, "--ruby",
                f"--cpu-type={row['modelo_cpu']}", "--cacheline_size", "64",
                "-c", str(workload), "-o", workload_args,
            ]
            runs.append((command, stats, workload, expected, protocol))

    unknown = set(args.corrida) - run_ids
    if unknown:
        raise ValueError(f"Corridas desconocidas: {', '.join(sorted(unknown))}")
    if not runs:
        raise ValueError("No hay corridas seleccionadas")
    return config, runs


def execute(config, runs, cwd):
    missing = {str(config)} if not config.is_file() else set()
    occupied = set()
    required_protocols = {}
    for command, stats, workload, _, protocol in runs:
        gem5 = Path(command[0])
        if gem5 in required_protocols and required_protocols[gem5] != protocol:
            raise ValueError(f"Se requieren builds con protocolos distintos: {gem5}")
        required_protocols[gem5] = protocol
        for binary in (gem5, workload):
            if not binary.is_file() or not access(binary, X_OK):
                missing.add(f"{binary} (ejecutable)")
        if stats.parent.exists():
            occupied.add(str(stats.parent))
    if missing or occupied:
        problems = [f"Falta {entry}" for entry in sorted(missing)]
        problems.extend(f"La carpeta ya existe: {entry}" for entry in sorted(occupied))
        raise ValueError("\n".join(problems))

    build_info = {}
    for gem5, protocol in required_protocols.items():
        result = subprocess.run([str(gem5), "--build-info"], cwd=cwd,
                                capture_output=True, text=True)
        if result.returncode:
            raise ValueError(f"No se pudo consultar --build-info de {gem5}: {result.stderr.strip()}")
        options = {}
        for line in result.stdout.splitlines():
            key, separator, value = line.partition(" = ")
            if separator:
                options[key.strip()] = value.strip()
        if options.get("USE_ARM_ISA", "").lower() not in {"true", "1", "y"}:
            raise ValueError(f"{gem5} no indica soporte ARM en --build-info")
        if options.get("PROTOCOL") != protocol:
            found = options.get("PROTOCOL", "(sin identificar)")
            raise ValueError(f"{gem5}: se esperaba {protocol}, se encontró {found}")
        build_info[str(gem5)] = result.stdout

    for command, stats, _, expected, _ in runs:
        out = stats.parent
        out.mkdir(parents=True, exist_ok=False)
        (out / "comando.txt").write_text(shlex.join(command) + "\n", encoding="utf-8")
        (out / "gem5_build_info.txt").write_text(build_info[command[0]], encoding="utf-8")
        print(shlex.join(command), flush=True)
        log = out / "simulacion.log"
        with log.open("wb") as stream:
            result = subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            raise ValueError(f"gem5 terminó con código {result.returncode}. Revisar {log}")
        if not stats.is_file():
            raise ValueError(f"Faltan las estadísticas de {out.name}. Revisar {log}")
        blocks = stats.read_text(encoding="utf-8", errors="replace")
        begin = blocks.find("Begin Simulation Statistics")
        if begin < 0 or blocks.find("End Simulation Statistics", begin) < 0:
            raise ValueError(f"No hay un bloque de estadísticas completo en {stats}")
        if expected:
            lines = set(log.read_text(encoding="utf-8", errors="replace").splitlines())
            if not set(expected).issubset(lines):
                raise ValueError(f"Falta la verificación de algún contador. Revisar {log}")
        else:
            print(f"Verificar el resultado numérico de GEMM en {log}", flush=True)
        print(f"Estadísticas guardadas en {stats}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=HERE / "corridas_E5.csv")
    parser.add_argument("--gem5-root", type=Path,
                        default=Path(environ.get("GEM5_ROOT") or REPO / "gem5"),
                        help="Raíz de gem5 (por defecto, GEM5_ROOT o gem5/ dentro del repo)")
    parser.add_argument("--trabajo", type=Path, default=REPO,
                        help="Raíz del proyecto para rutas de binarios y resultados")
    parser.add_argument("--config", default="configs/deprecated/example/se.py")
    parser.add_argument("--mesi", help="Ruta alternativa a gem5 para MESI")
    parser.add_argument("--moesi", help="Ruta alternativa a gem5 para MOESI")
    parser.add_argument("--micro", help="Ruta alternativa al binario false_sharing")
    parser.add_argument("--gemm", help="Ruta alternativa al binario GEMM paralelo")
    parser.add_argument("--benchmark", choices=BENCHMARKS, help="Filtra la carga de trabajo")
    parser.add_argument("--protocolo", choices=PROTOCOLS, help="Filtra el protocolo Ruby")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--piloto", action="store_true", help="Selecciona corridas cortas con 2 núcleos")
    selection.add_argument("--corrida", action="append", default=[], help="ID del CSV, repetible")
    parser.add_argument("--ejecutar", action="store_true", help="Lanza gem5. Por defecto muestra comandos")
    args = parser.parse_args()
    args.gem5_root = args.gem5_root.resolve()
    args.trabajo = args.trabajo.resolve()
    try:
        config, runs = plan(args)
        if args.ejecutar:
            execute(config, runs, args.trabajo)
        else:
            for command, _, _, _, _ in runs:
                print(shlex.join(command))
        if len(runs) == 1:
            summary = "1 corrida ejecutada" if args.ejecutar else "1 corrida planificada"
        else:
            action = "ejecutadas" if args.ejecutar else "planificadas"
            summary = f"{len(runs)} corridas {action}"
        print(summary, file=sys.stderr)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
