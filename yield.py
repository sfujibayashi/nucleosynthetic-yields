#!/usr/bin/env python3

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path


DESCRIPTION = "Create nucleosynthesis tables and plots."
VERSION = "1.01"
CREATED = "2026-09-09"
AUTHOR = "S. Wanajo"


def print_banner():
    print("yield.py  version %s  %s  %s" % (VERSION, CREATED, AUTHOR))


def parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION,
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("-h", "--h", "--help", action="help", help="show this help message")
    p.add_argument("--input", default="yield.dat",
                   help="input isotope-mass file (default: yield.dat)")
    p.add_argument(
        "--table",
        choices=("isotope", "isobar", "element", "all"),
        help="write the selected table(s)",
    )
    p.add_argument(
        "--plot",
        choices=("isotope", "isobar", "element", "all"),
        help="write the selected abundance plot",
    )
    p.add_argument(
        "--solar",
        default=None,
        metavar="REF|no",
        help="solar-r normalization point (default: A=151 or Z=63; 'no' disables solar-r)",
    )
    p.add_argument(
        "--mass",
        action="store_true",
        help="print the total ejecta mass",
    )
    p.add_argument(
        "--output_dir",
        default=".",
        help="output directory (default: current directory)",
    )
    return p


def read_isotope_masses(path):
    masses = defaultdict(float)
    with path.open() as f:
        for line_number, line in enumerate(f, 1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            fields = text.split()
            if len(fields) < 3:
                raise ValueError(f"{path}:{line_number}: expected Z, A, and M_ej/M_sun")
            try:
                z = int(fields[0])
                a = int(fields[1])
                mass = float(fields[2].replace("D", "E").replace("d", "e"))
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: invalid data") from exc
            if z < 0 or a <= 0 or not math.isfinite(mass) or mass < 0.0:
                raise ValueError(f"{path}:{line_number}: invalid Z, A, or mass")
            masses[(z, a)] += mass
    if not masses:
        raise ValueError(f"no isotope data found in {path}")
    total = sum(masses.values())
    if total <= 0.0:
        raise ValueError("total ejecta mass must be positive")
    return dict(sorted(masses.items())), total


def aggregate(masses, key_index):
    mass_sum = defaultdict(float)
    abundance_sum = defaultdict(float)
    for (z, a), mass in masses.items():
        key = (z, a)[key_index]
        mass_sum[key] += mass
        abundance_sum[key] += mass / a
    return dict(sorted(mass_sum.items())), dict(sorted(abundance_sum.items()))


def output_name(input_path, kind, suffix):
    return f"{kind}_{input_path.stem}{suffix}"


def write_isotope_table(path, masses, total):
    with path.open("w") as f:
        f.write("# M_ej,total/M_sun=%12.3e\n" % total)
        f.write("#   Z    A  M_ej/M_sun           X           Y\n")
        for (z, a), mass in masses.items():
            x = mass / total
            f.write("%5d%5d%12.3e%12.3e%12.3e\n" % (z, a, mass, x, x / a))


def write_grouped_table(path, symbol, mass_sum, abundance_sum, total):
    with path.open("w") as f:
        f.write("# M_ej,total/M_sun=%12.3e\n" % total)
        f.write("#   %s  M_ej/M_sun           X           Y\n" % symbol)
        for key, mass in mass_sum.items():
            f.write(
                "%5d%12.3e%12.3e%12.3e\n"
                % (key, mass, mass / total, abundance_sum[key] / total)
            )


def read_solar_mass_fractions(path):
    isotope_weights = defaultdict(float)
    with path.open() as f:
        for line_number, line in enumerate(f, 1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            fields = text.split()
            if len(fields) < 3:
                raise ValueError(f"{path}:{line_number}: expected Z, A, and N")
            try:
                z = int(fields[0])
                a = int(fields[1])
                number = float(fields[2].replace("D", "E").replace("d", "e"))
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: invalid data") from exc
            if z < 0 or a <= 0 or not math.isfinite(number) or number < 0.0:
                raise ValueError(f"{path}:{line_number}: invalid Z, A, or N")
            isotope_weights[(z, a)] += a * number
    total = sum(isotope_weights.values())
    if total <= 0.0:
        raise ValueError(f"no solar-r data found in {path}")

    isotopes = {key: weight / total for key, weight in isotope_weights.items()}
    isobars = defaultdict(float)
    elements = defaultdict(float)
    for (z, a), x in isotopes.items():
        isobars[a] += x
        elements[z] += x
    return (
        dict(sorted(isotopes.items())),
        dict(sorted(isobars.items())),
        dict(sorted(elements.items())),
    )


def solar_reference(option, default):
    if option is None:
        return default
    if option.lower() == "no":
        return None
    try:
        return int(option)
    except ValueError as exc:
        raise ValueError("--solar must be an integer or 'no'") from exc


def x_upper_limit(kind, values):
    step = 20 if kind in ("isotope", "isobar") else 10
    return int(math.ceil(max(values) / step) * step)


def make_plot(path, kind, data, total, solar_option):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.legend_handler import HandlerTuple
    from matplotlib.lines import Line2D

    plt.rcParams.update({
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "font.size": 16,
        "axes.labelsize": 18,
        "legend.fontsize": 14,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
    })

    fig, ax = plt.subplots(figsize=(6.2, 4.6))

    if kind == "isotope":
        items = sorted(data.items(), key=lambda item: (item[0][1], item[0][0]))
        x = [key[1] for key, mass in items]
        y = [mass / total for key, mass in items]
        z_values = [key[0] for key, mass in items]
        norm = matplotlib.colors.Normalize(vmin=min(z_values), vmax=max(z_values))
        cmap = plt.get_cmap("turbo")
        marker_cycle = ("*", "s", "^", "D", "x")
        marker_sizes = {"*": 18, "s": 9, "^": 12, "D": 9, "x": 10}
        result_legend_handle = tuple(
            Line2D(
                [],
                [],
                linestyle="none",
                marker=marker,
                color="0.25",
                markerfacecolor="0.25",
                markeredgecolor="0.25",
                markeredgewidth=0.8 if marker == "x" else 0,
                markersize=math.sqrt(marker_sizes[marker]),
            )
            for marker in marker_cycle
        )
        isotope_chains = defaultdict(list)
        for (z, a), mass in data.items():
            isotope_chains[z].append((a, mass / total))
        result_plot = None
        for z, points in sorted(isotope_chains.items()):
            points.sort()
            color = cmap(norm(z))
            ax.plot(
                [point[0] for point in points],
                [point[1] for point in points],
                color=color,
                lw=0.5,
                alpha=0.45,
                zorder=1,
            )
            marker = marker_cycle[(z - 1) % len(marker_cycle)]
            result_plot = ax.scatter(
                [point[0] for point in points],
                [point[1] for point in points],
                c=[z] * len(points),
                cmap=cmap,
                norm=norm,
                marker=marker,
                s=marker_sizes[marker],
                linewidths=0.8 if marker == "x" else 0,
                zorder=2,
            )
        colorbar = fig.colorbar(result_plot, ax=ax, pad=0.02)
        colorbar.set_label("$Z$")
        colorbar.ax.tick_params(which="both", direction="in")
    else:
        x = list(data)
        y = [data[i] / total for i in x]
        ax.plot(x, y, color="blue", lw=1.5, label="result")

    x_extent = list(x)

    script_dir = Path(__file__).resolve().parent
    if kind in ("isotope", "isobar"):
        default_ref = 151
        xlabel = "$A$"
        ylabel = "$X(Z,A)$" if kind == "isotope" else "$X(A)$"
    else:
        default_ref = 63
        xlabel, ylabel = "$Z$", "$X(Z)$"

    ref = solar_reference(solar_option, default_ref)
    solar_plot = None
    if ref is not None:
        solar_file = script_dir / "solar-r-isotope-prantzos.dat"
        solar_isotopes, solar_isobars, solar_elements = read_solar_mass_fractions(solar_file)
        if kind == "isotope":
            solar = solar_isotopes
            model_at_ref = sum(
                mass / total for (z, a), mass in data.items() if a == ref
            )
            solar_at_ref = sum(
                x_solar for (z, a), x_solar in solar.items() if a == ref
            )
        else:
            solar = solar_isobars if kind == "isobar" else solar_elements
            model_at_ref = data.get(ref, 0.0) / total
            solar_at_ref = solar.get(ref, 0.0)
        if model_at_ref <= 0.0:
            raise ValueError(f"no positive {kind} abundance at the solar-r normalization point {ref}")
        if solar_at_ref <= 0.0:
            raise ValueError(f"no positive solar-r abundance at the normalization point {ref}")
        scale = model_at_ref / solar_at_ref
        if kind == "isotope":
            solar_items = sorted(solar.items(), key=lambda item: (item[0][1], item[0][0]))
            sx = [key[1] for key, x_solar in solar_items]
            sy = [x_solar * scale for key, x_solar in solar_items]
        else:
            sx = list(solar)
            sy = [solar[i] * scale for i in sx]
        x_extent.extend(sx)
        solar_plot, = ax.plot(
            sx,
            sy,
            color="black",
            marker="o",
            linestyle="none",
            markersize=3,
            markeredgewidth=0,
            label="solar-r",
        )

    ax.set_xlim(0, x_upper_limit(kind, x_extent))
    ax.set_ylim(1.0e-6, 1.0)
    ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if kind == "isotope":
        handles = [result_legend_handle]
        labels = ["result"]
        if solar_plot is not None:
            handles.append(solar_plot)
            labels.append("solar-r")
        ax.legend(
            handles,
            labels,
            handler_map={tuple: HandlerTuple(ndivide=None, pad=0)},
            handlelength=1.35,
        )
    else:
        ax.legend()
    ax.minorticks_on()
    ax.tick_params(which="both", direction="in", top=True, right=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main(argv=None):
    print_banner()
    p = parser()
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        p.print_help()
        return 0
    args = p.parse_args(argv)
    if args.table is None and args.plot is None and not args.mass:
        p.error("specify --table, --plot, or --mass")

    input_path = Path(args.input)
    masses, total = read_isotope_masses(input_path)
    if args.mass:
        print("M_ej,total/M_sun=%12.3e" % total)
    if args.table is None and args.plot is None:
        return 0

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    isobars, isobar_y = aggregate(masses, 1)
    elements, element_y = aggregate(masses, 0)

    outputs = []
    table_kinds = ("isotope", "isobar", "element") if args.table == "all" else (args.table,)
    for kind in table_kinds:
        if kind is None:
            continue
        path = output_dir / output_name(input_path, kind, ".dat")
        if kind == "isotope":
            write_isotope_table(path, masses, total)
        elif kind == "isobar":
            write_grouped_table(path, "A", isobars, isobar_y, total)
        else:
            write_grouped_table(path, "Z", elements, element_y, total)
        outputs.append(path)

    plot_kinds = ("isotope", "isobar", "element") if args.plot == "all" else (args.plot,)
    for kind in plot_kinds:
        if kind is None:
            continue
        path = output_dir / output_name(input_path, kind, ".pdf")
        data = masses if kind == "isotope" else isobars if kind == "isobar" else elements
        make_plot(path, kind, data, total, args.solar)
        outputs.append(path)

    for path in outputs:
        print(f"[done] wrote: {path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"error: {exc}")
