#!/usr/bin/env python3
"""Registra estadísticas y revisa la evidencia de corridas de E5."""

import argparse
from configparser import ConfigParser, Error as ConfigError
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import shlex
import sys
from tempfile import NamedTemporaryFile


HERE = Path(__file__).resolve().parent
BEGIN = "---------- Begin Simulation Statistics ----------"
END = "---------- End Simulation Statistics   ----------"
RUBY = "system.ruby."
L1_STATS = RUBY + "L1Cache_Controller."
NETWORK_COUNTS = RUBY + "network.msg_count."
DIRTY_STATES = {
    "MESI_Two_Level": ("M",),
    "MOESI_CMP_directory": ("M", "MM", "O"),
}
FIELDS = {
    "latencia_media_fallo": RUBY + "m_missLatencyHistSeqr::mean",
    "fallos_ruby": RUBY + "m_missLatencyHistSeqr::samples",
    "fallos_escritura_ruby": RUBY + "RequestType.ST.miss_latency_hist_seqr::samples",
    "sim_ticks": "simTicks",
    "instrucciones_simuladas": "simInsts",
}
CPU_SECTION = re.compile(r"system\.cpu\d*")
BUILD_TRUE = {"true", "1", "y"}


def read_stats(path, number):
    blocks = path.read_text(encoding="utf-8").split(BEGIN)[1:]
    if not blocks:
        raise ValueError(f"{path}: no contiene bloques de estadísticas")
    if number is None and len(blocks) > 1:
        raise ValueError(f"{path}: hay {len(blocks)} bloques. Indique --bloque según la corrida")
    number = number or 1
    if not 1 <= number <= len(blocks) or END not in blocks[number - 1]:
        raise ValueError(f"{path}: el bloque {number} está ausente o incompleto")
    raw, _, _ = blocks[number - 1].partition(END)
    stats = {}
    for line in raw.splitlines():
        columns = line.split(maxsplit=2)
        if len(columns) >= 2:
            stats[columns[0]] = columns[1]
    if not any(key.startswith(RUBY) for key in stats):
        raise ValueError(f"{path}: el bloque {number} carece de estadísticas Ruby")
    return stats, number


def metric(stats, key, integer=True):
    value = stats.get(key, "")
    if value.lower() in {"", "nan", "-nan", "+nan"}:
        return ""
    number = Decimal(value)
    if not number.is_finite() or number < 0 or (integer and number != int(number)):
        raise ValueError(f"valor inválido para {key}: {value}")
    return str(int(number)) if integer else value


def review_build(build_path, command_path, expected_protocol):
    if not build_path.is_file():
        return "gem5_build_info.txt"

    build = dict(re.findall(r"^[ \t]*(\w+)[ \t]*=[ \t]*(\S+)",
                            build_path.read_text(encoding="utf-8"), re.M))
    if "PROTOCOL" not in build or "USE_ARM_ISA" not in build:
        return "confirmar ARM y protocolo en gem5_build_info.txt"
    if build["USE_ARM_ISA"].lower() not in BUILD_TRUE:
        raise ValueError(f"{build_path}: el build carece de soporte ARM")
    protocol = build["PROTOCOL"]
    if protocol != "MULTIPLE":
        if protocol != expected_protocol:
            raise ValueError(f"{build_path}: se esperaba {expected_protocol}, se encontró {protocol}")
        return ""

    enabled = build.get(f"RUBY_PROTOCOL_{expected_protocol}", "").lower()
    if enabled not in BUILD_TRUE:
        raise ValueError(f"{build_path}: el build MULTIPLE no declara soporte para {expected_protocol}")
    if not command_path.is_file():
        return ""

    args = shlex.split(command_path.read_text(encoding="utf-8"))
    selected = []
    for index, arg in enumerate(args):
        name, equals, value = arg.partition("=")
        if name == "--protocol":
            if not equals and index + 1 < len(args):
                value = args[index + 1]
            selected.append(value)
    if selected != [expected_protocol]:
        raise ValueError(f"{command_path}: se requiere una sola selección --protocol={expected_protocol}")
    return ""


def review_evidence(directory, row):
    pending = []
    network_type = ""
    log = directory / "simulacion.log"
    version = ""
    if log.is_file():
        content = log.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^gem5 version\s+(\S+)", content, re.M)
        if match:
            version = match[1]
        else:
            pending.append("versión de gem5")
        if row["benchmark"] == "false_sharing":
            variant = row["variante"]
            threads = row["hilos"]
            count = row["incrementos_por_hilo"]
            expected = {
                f"{variant} hilos={threads} esperado={count}",
                "Verificación: OK",
            }
            expected.update(f"contador[{i}]={count}" for i in range(int(threads)))
            lines = set(content.splitlines())
            if not expected <= lines or "Verificación: ERROR" in lines:
                raise ValueError(f"{log}: no valida los contadores esperados de esta corrida")
    else:
        pending.extend(("simulacion.log", "versión de gem5"))

config_path = directory / "config.ini"
    if config_path.is_file():
        config = ConfigParser(interpolation=None)
        with config_path.open(encoding="utf-8") as stream:
            config.read_file(stream)
        cpus = [section for section in config.sections() if CPU_SECTION.fullmatch(section)]
        if not config.has_section("system.ruby"):
            raise ValueError(f"{config_path}: falta system.ruby")
        network_type = config.get("system.ruby.network", "type", fallback="")
        if config.get("system", "cache_line_size", fallback="") != row["linea_cache_bytes"]:
            raise ValueError(f"{config_path}: tamaño de línea distinto al del plan")
        if len(cpus) != int(row["nucleos"]):
            raise ValueError(f"{config_path}: cantidad de CPU distinta a la del plan")
        expected_model = row["modelo_cpu"]
        model_names = {expected_model, "Arm" + expected_model, "Base" + expected_model}
        for cpu in cpus:
            model = config.get(cpu, "type", fallback="")
            if model not in model_names:
                raise ValueError(f"{config_path}: modelo de CPU inesperado en {cpu}: {model}")
    else:
        pending.append("config.ini")

    command_path = directory / "comando.txt"
    build_pending = review_build(directory / "gem5_build_info.txt", command_path, row["protocolo"])
    if build_pending:
        pending.append(build_pending)
    if not command_path.is_file():
        pending.append("comando.txt")
    if row["benchmark"] == "gemm_paralelo":
        pending.append("validación numérica de GEMM")

    return version, pending, network_type


def coherence_metrics(stats, protocol, network_type):
    values = {
        "invalidaciones": "",
        "estadistica_invalidaciones": "",
        "mensajes_coherencia": "",
        "estadistica_mensajes": "",
        "traspasos_linea_modificada": "",
        "estadistica_traspasos": "",
    }
    l1_events = any(key.startswith(L1_STATS) and key.endswith("::total") for key in stats)
    if l1_events and protocol in DIRTY_STATES:
        # SLICC omite los contadores de eventos y transiciones con valor cero.
        inv_key = L1_STATS + "Inv::total"
        values["invalidaciones"] = metric(stats, inv_key) if inv_key in stats else "0"
        values["estadistica_invalidaciones"] = inv_key

        # Estos estados pierden la copia modificada al aceptar un GETX ajeno.
        keys = [L1_STATS + f"{state}.Fwd_GETX::total" for state in DIRTY_STATES[protocol]]
        counts = [metric(stats, key) if key in stats else "0" for key in keys]
        if all(counts):
            values["traspasos_linea_modificada"] = str(sum(map(int, counts)))
            values["estadistica_traspasos"] = " + ".join(keys)

    if network_type == "SimpleNetwork":
        # Solo los totales de red por clase. Cada uno ya agrega los conmutadores.
        counts = [metric(stats, key) for key in stats if key.startswith(NETWORK_COUNTS)]
        if counts and all(counts):
            values["mensajes_coherencia"] = str(sum(map(int, counts)))
            values["estadistica_mensajes"] = "suma de " + NETWORK_COUNTS + "* (SimpleNetwork)"
    return values


def register(row, stats_path, evidence_dir, requested_block):
    stats, block = read_stats(stats_path, requested_block)
    cores = {key.removesuffix(".numCycles") for key in stats if key.endswith(".numCycles")
             and CPU_SECTION.fullmatch(key.removesuffix(".numCycles"))}
    if cores and len(cores) != int(row["nucleos"]):
        raise ValueError(f"{stats_path}: cantidad de CPU distinta a la del plan")

    version, pending, network_type = review_evidence(evidence_dir, row)
    values = {
        field: metric(stats, key, integer=field != "latencia_media_fallo")
        for field, key in FIELDS.items()
    }
    values.update(coherence_metrics(stats, row["protocolo"], network_type))
    values["estadistica_latencia"] = FIELDS["latencia_media_fallo"] if values["latencia_media_fallo"] else ""

    freq = metric(stats, "simFreq")
    if not values["sim_ticks"] or not freq or int(freq) == 0:
        raise ValueError(f"{stats_path}: faltan simTicks o una simFreq positiva")
    milliseconds = Decimal(values["sim_ticks"]) * 1000 / Decimal(freq)
    notes = [f"Bloque {block}. Se registran los eventos explícitos Inv de L1."]
    if values["mensajes_coherencia"]:
        notes.append("SimpleNetwork cuenta cada paso de un mensaje por un conmutador.")
    if values["invalidaciones"] == "0" and L1_STATS + "Inv::total" not in stats:
        notes.append("SLICC omite el contador Inv cuando vale cero.")
    required_fields = (*FIELDS, "invalidaciones", "mensajes_coherencia", "traspasos_linea_modificada")
    missing = [field for field in required_fields if not values[field]]
    if missing:
        notes.append("Sin dato en el bloque: " + ", ".join(missing) + ".")
    if pending:
        notes.append("Evidencia pendiente: " + ", ".join(pending) + ".")
    values.update(
        estado="stats_registradas" if pending or missing else "stats_y_evidencia_revisadas",
        tiempo_simulado_ms=format(milliseconds, ".7f"),
        bloque_stats=str(block),
        archivo_evidencia=stats_path.name,
        unidad_latencia="ciclos del secuenciador Ruby" if values["latencia_media_fallo"] else "",
        version_gem5=version,
        observaciones=" ".join(notes),
    )
    return values


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                            delete=False) as stream:
        temp = Path(stream.name)
        try:
            writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            stream.flush()
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=HERE / "corridas_E5.csv")
    parser.add_argument("--trabajo", type=Path, default=HERE.parent,
                        help="Raíz del proyecto para resolver las rutas stats_txt")
    parser.add_argument("--corrida", action="append", required=True, help="ID del CSV, repetible")
    parser.add_argument("--stats", type=Path, help="Archivo alternativo para una sola corrida")
    parser.add_argument("--evidencia", type=Path, help="Carpeta de evidencia para una sola corrida")
    parser.add_argument("--bloque", type=int, help="Número del bloque, empezando en 1")
    parser.add_argument("--salida", type=Path, required=True, help="Ruta de la copia actualizada")
    args = parser.parse_args()
    if len(args.corrida) != 1 and (args.stats or args.evidencia):
        parser.error("--stats y --evidencia requieren una sola --corrida")
    if args.bloque is not None and args.bloque < 1:
        parser.error("--bloque debe ser positivo")
    if args.salida.resolve() == args.csv.resolve():
        parser.error("--salida debe ser distinta del CSV de entrada")

    try:
        with args.csv.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            columns = list(reader.fieldnames or [])
        by_id = {row["corrida_id"]: row for row in rows}
        if len(by_id) != len(rows):
            raise ValueError("Hay IDs de corrida repetidos en el CSV")
        for run_id in dict.fromkeys(args.corrida):
            if run_id not in by_id:
                raise ValueError(f"Corrida desconocida: {run_id}")
            row = by_id[run_id]
            stats_path = args.stats or args.trabajo / row["stats_txt"]
            values = register(row, stats_path, args.evidencia or stats_path.parent, args.bloque)
            row.update(values)
            columns.extend(field for field in values if field not in columns)
            print(f"{run_id}: {row['estado']}. {row['observaciones']}", file=sys.stderr)
        write_csv(args.salida, columns, rows)
    except (OSError, ValueError, InvalidOperation, KeyError, ConfigError) as exc:
        parser.exit(1, f"Error: {exc}\n")
