#!/usr/bin/env python3
"""Regenera el CSV y los gráficos de falso compartido del E5."""

import argparse
from configparser import Error as ConfigError
import csv
from decimal import InvalidOperation
from pathlib import Path

from ejecutar_e5 import PROTOCOLS
from registrar_e5 import HERE, register, write_csv


CORES = (2, 4, 8)
VARIANTS = ("nopad", "pad")
METRICS = (
    ("invalidaciones", "Invalidaciones explícitas de L1"),
    ("mensajes_coherencia", "Pasos de mensajes por conmutador"),
    ("latencia_media_fallo", "Latencia media de fallo (ciclos Ruby)"),
    ("traspasos_linea_modificada", "Traspasos de líneas modificadas"),
)


def load_runs(plan, workdir):
    with plan.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = list(reader.fieldnames or [])
        rows = [row for row in reader if row["benchmark"] == "false_sharing"]

    expected = {(protocol, variant, cores) for protocol in PROTOCOLS
                for variant in VARIANTS for cores in CORES}
    planned = {(row["protocolo"], row["variante"], int(row["nucleos"])) for row in rows}
    if planned != expected or len(rows) != len(expected):
        raise ValueError("Se requieren las 12 combinaciones únicas de protocolo, relleno y núcleos")

    for row in rows:
        stats = workdir / row["stats_txt"]
        values = register(row, stats, stats.parent, 1, require_false_sharing_roi=True)
        if values["estado"] != "stats_y_evidencia_revisadas":
            raise ValueError(f"{row['corrida_id']}: {values['observaciones']}")
        row.update(values)
        columns.extend(field for field in values if field not in columns)
    return rows, columns


def plot(rows, target):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.patches import Patch

    by_case = {(row["protocolo"], row["variante"], int(row["nucleos"])): row for row in rows}
    series = (
        (PROTOCOLS[0], "nopad", "MESI · sin relleno", "#174A73"),
        (PROTOCOLS[0], "pad", "MESI · con relleno", "#75A8C9"),
        (PROTOCOLS[1], "nopad", "MOESI · sin relleno", "#A84B1B"),
        (PROTOCOLS[1], "pad", "MOESI · con relleno", "#F0AB73"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    fig.suptitle("E5 · Falso compartido con Ruby", fontsize=16)
    fig.legend(handles=[Patch(facecolor=color, label=label) for _, _, label, color in series],
               loc="upper center", bbox_to_anchor=(0.5, 0.93), ncol=4, frameon=False)
    positions = range(len(CORES))
    width = 0.18
    for ax, (metric, title) in zip(axes.flat, METRICS):
        for index, (protocol, variant, _, color) in enumerate(series):
            offset = (index - 1.5) * width
            heights = [float(by_case[protocol, variant, count][metric]) for count in CORES]
            ax.bar([x + offset for x in positions], heights, width, color=color)
        ax.set_title(title)
        ax.set_xticks(positions, labels=CORES)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 5), useMathText=True)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
    for ax in axes[-1]:
        ax.set_xlabel("Núcleos")
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    fig.savefig(target, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=HERE / "corridas_E5.csv", help="CSV de corridas")
    parser.add_argument("--trabajo", type=Path, default=HERE.parent,
                        help="Raíz de las rutas de estadísticas del CSV")
    parser.add_argument("--salida", type=Path, help="Carpeta de salida (por defecto, results/e5/resumen)")
    args = parser.parse_args()
    destination = args.salida or args.trabajo / "results/e5/resumen"
    csv_output = destination / "metricas_falso_compartido.csv"
    chart = destination / "falso_compartido.png"
    if csv_output.resolve() == args.csv.resolve():
        parser.error("El CSV de salida debe ser distinto del CSV de corridas")

    try:
        rows, columns = load_runs(args.csv, args.trabajo)
        destination.mkdir(parents=True, exist_ok=True)
        plot(rows, chart)
        write_csv(csv_output, columns, rows)
    except ImportError as exc:
        parser.exit(1, f"Error al importar Matplotlib: {exc}\n")
    except (OSError, ValueError, KeyError, InvalidOperation, ConfigError) as exc:
        parser.exit(1, f"Error: {exc}\n")

    print(f"{len(rows)} corridas verificadas\n{csv_output}\n{chart}")


if __name__ == "__main__":
    main()
