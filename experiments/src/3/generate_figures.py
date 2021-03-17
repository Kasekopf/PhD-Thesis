import collections
import math
import slurmqueen

import util

output = util.output_pdf()

BASE_EXPERIMENT_DIR = "../../data/3"
TIMEOUT = 1000


""""
Definition and analysis of experiments computing graph decomposition quality (for appendix).
"""


def vertex_cover_graph_analysis(*methods):
    return slurmqueen.Experiment(
        "python src/graph_analysis.py",
        [
            {
                "": [
                    "benchmarks/cubic_vertex_cover/cubic_vc_%d_%d.cnf" % (num_vars, i)
                ],
                "timeout": 1000,
                "method": m,
                "seed": 1234567,
                "|num_vars": num_vars,
                "|i": i,
            }
            for num_vars in range(50, 260, 10)
            for i in range(100)
            for m in methods
        ],
        output_argument="output",
        log_argument="&>",
    )


ga_vertex_cover_line = vertex_cover_graph_analysis(
    "line-Tamaki", "line-Flow", "line-htd"
).instance(BASE_EXPERIMENT_DIR + "/appendix_graph_analysis/cubic_vertex_cover/line")
ga_vertex_cover_factor = vertex_cover_graph_analysis(
    "factor-Tamaki", "factor-Flow", "factor-htd"
).instance(BASE_EXPERIMENT_DIR + "/appendix_graph_analysis/cubic_vertex_cover/factor")


def extract_best_decompositions_vertex_cover(instance):
    data = instance.query("SELECT [Carving], [Tree], [|num_vars], [|i] FROM data")

    # Take the best decomposition found across all solvers on each benchmark
    data = data.groupby(["|num_vars", "|i"], as_index=False).min()

    # Take the median runtime for each number of variables, across all 100 benchmarks
    data = data.groupby(["|num_vars"], as_index=False).median()

    if len(data) != 21:
        print(
            "Only {0}/21 options for the numbers of variables observed for {1}".format(
                len(data), instance
            )
        )

    return data.sort_values("|num_vars")


def plot_graph_analysis_vertex_cover(ax):
    line = extract_best_decompositions_vertex_cover(ga_vertex_cover_line)
    factor = extract_best_decompositions_vertex_cover(ga_vertex_cover_factor)

    DisplayInfo = collections.namedtuple(
        "DisplayInfo", ["name", "data", "color", "marker"]
    )
    lines_to_display = [
        DisplayInfo("Treewidth of $Line(G)$", line["Tree"], "#c11e96", "o"),
        DisplayInfo("Treewidth of $G$", factor["Tree"], "#023880", "v"),
        DisplayInfo(
            "Carving width of $G$ using \\textbf{FT}", factor["Carving"], "#a7e831", "s"
        ),
        DisplayInfo(
            "Carving width of $G$ using \\textbf{LG}", line["Carving"], "#86d7a9", "*"
        ),
    ]
    for exp_info in lines_to_display:
        ax.plot(
            line["|num_vars"],
            exp_info.data,
            color=exp_info.color,
            linewidth=1,
            markersize=5,
            markerfacecolor=exp_info.color,
            markeredgewidth=0.5,
            markeredgecolor="black",
            marker=exp_info.marker,
            label=exp_info.name,
        )

    ax.legend(
        borderaxespad=0,
        handletextpad=0.2,
        labelspacing=0.4,
        handlelength=2,
        frameon=False,
    )
    ax.set_xticks([50, 100, 150, 200, 250])
    ax.set_xlabel("$n$: Number of vertices")
    ax.set_ylabel("Width of decomposition")


def wmc_graph_analysis(*methods):
    return slurmqueen.Experiment(
        "python src/graph_analysis.py",
        [
            {
                "": [benchmark],
                "timeout": 1000,
                "method": m,
                "seed": 1234567,
                "|benchmark": benchmark,
                "|benchmark_class": benchmark_class,
            }
            for benchmark, benchmark_class in cachet_benchmarks()
            for m in methods
        ],
        output_argument="output",
        log_argument="&>",
    )


ga_wmc_line = wmc_graph_analysis("line-Tamaki", "line-Flow", "line-htd").instance(
    BASE_EXPERIMENT_DIR + "/appendix_graph_analysis/wmc/line"
)
ga_wmc_factor = wmc_graph_analysis(
    "factor-Tamaki", "factor-Flow", "factor-htd"
).instance(BASE_EXPERIMENT_DIR + "/appendix_graph_analysis/wmc/factor")


def extract_best_decompositions(instance):
    data = instance.query("SELECT [Carving], [Tree], [|benchmark], [output] FROM data")

    # Take the best decomposition found across all solvers on each benchmark
    data = data.groupby(["|benchmark"], as_index=False).min()

    if len(data) != 1091:
        print(
            "Only {0}/1091 options for the numbers of variables observed for {1}".format(
                len(data), instance
            )
        )
    return data.sort_values("|benchmark")


def plot_graph_analysis_lg_wmc(ax):
    line = extract_best_decompositions(ga_wmc_line)

    def cap_data(data, column):
        data = data.copy()
        data.loc[data[column] > 200, column] = 200
        return data[column]

    DisplayInfo = collections.namedtuple("DisplayInfo", ["name", "data", "color"])
    bars_to_display = [
        DisplayInfo("Treewidth of $Line(G)$", cap_data(line, "Tree"), "#c11e96"),
        DisplayInfo(
            "Carving width of $G$ using \\textbf{LG}",
            cap_data(line, "Carving"),
            "#86d7a9",
        ),
    ]

    ax.hist(
        [d.data for d in bars_to_display],
        bins=range(0, 210, 10),
        histtype="bar",
        color=[d.color for d in bars_to_display],
        label=[d.name for d in bars_to_display],
    )

    ax.legend(
        borderaxespad=0,
        handletextpad=0.2,
        labelspacing=0.4,
        handlelength=2,
        frameon=False,
    )
    ax.set_xticks([0, 50, 100, 150, 200])
    ax.set_xticklabels(["0", "50", "100", "150", "$200+$"])

    ax.set_xlabel("Width of decomposition")
    ax.set_ylabel("Number of benchmarks")


def plot_graph_analysis_ft_wmc(ax):
    factor = extract_best_decompositions(ga_wmc_factor)

    def cap_data(data, column):
        data = data.copy()
        data.loc[data[column] > 50, column] = 50
        return data[column]

    DisplayInfo = collections.namedtuple("DisplayInfo", ["name", "data", "color"])
    bars_to_display = [
        DisplayInfo("Treewidth of $G$", cap_data(factor, "Tree"), "#023880"),
        DisplayInfo(
            "Carving width after \\textbf{FT}", cap_data(factor, "Carving"), "#a7e831"
        ),
    ]

    ax.hist(
        [d.data for d in bars_to_display],
        bins=range(0, 54, 2),
        histtype="bar",
        align="mid",
        color=[d.color for d in bars_to_display],
        label=[d.name for d in bars_to_display],
    )

    ax.legend(
        borderaxespad=0,
        handletextpad=0.2,
        labelspacing=0.4,
        handlelength=2,
        frameon=False,
    )
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_xticklabels(["0", "10", "20", "30", "40", "$50+$"])

    ax.set_xlabel("Width of decomposition")
    ax.set_ylabel("Number of benchmarks")


"""
Generate all high-level plots and analysis.
"""


def generate_appendix_plots():
    f, ax = output.figure(ncols=1)
    plot_graph_analysis_vertex_cover(ax)
    f.save(0.6, "3/appendix_vertex_cover_width")

    f, ax = output.figure(ncols=1)
    plot_graph_analysis_lg_wmc(ax)
    f.save(0.6, "3/appendix_wmc_lg_width")

    f, ax = output.figure(ncols=1)
    plot_graph_analysis_ft_wmc(ax)
    f.save(0.6, "3/appendix_wmc_ft_width")


def generate_width_plots():
    def plot_width_cactus_line(ax, structure_exp, time_exp, **kwargs):
        widths = extract_best_decompositions(structure_exp)["Carving"]
        if time_exp is None:
            times = [999] * len(widths)  # For computing overall benchmarks
        else:
            times = load_inference_data(time_exp)["Total Time"]

        completed_widths = [
            int(w) for w, t in zip(widths, times) if t < 1000 and not math.isnan(w)
        ]
        completed_widths = sorted(completed_widths)
        x, y = [], []
        for i, width in enumerate(completed_widths):
            if (
                i == len(completed_widths) - 1
                or completed_widths[i + 1] > completed_widths[i]
            ):
                x += [width]
                y += [i]
        ax.plot(x, y, **kwargs)

    f, ax = output.figure(ncols=1)
    plot_width_cactus_line(
        ax,
        ga_wmc_factor,
        None,
        label="All benchmarks",
        color="#000000",
        linestyle=":",
        linewidth=2,
    )
    plot_width_cactus_line(
        ax,
        ga_wmc_factor,
        wmc_factor_htd,
        label="FT+htd",
        color="#ffd700",
        linestyle="--",
        linewidth=2,
    )
    plot_width_cactus_line(
        ax,
        ga_wmc_factor,
        wmc_factor_flow,
        label="FT+Flow",
        color="#ffb14e",
        linestyle=":",
        linewidth=2,
    )
    plot_width_cactus_line(
        ax,
        ga_wmc_factor,
        wmc_factor_tamaki,
        label="FT+Tamaki",
        color="#fa8775",
        linestyle="-",
        linewidth=2,
    )
    plot_width_cactus_line(
        ax,
        ga_wmc_factor,
        wmc_cachet,
        label="cachet",
        color="#dd0f0f",
        linestyle="--",
        linewidth=2,
    )
    plot_width_cactus_line(
        ax,
        ga_wmc_factor,
        wmc_minic2d,
        label="miniC2D",
        color="#ea5f94",
        linestyle=":",
        linewidth=2,
    )
    plot_width_cactus_line(
        ax,
        ga_wmc_factor,
        wmc_d4,
        label="d4",
        color="#9d02d7",
        linestyle="-",
        linewidth=2,
    )
    ax.set_xlabel("Upper bound on carving width")
    ax.set_ylabel("Number of solved benchmarks")
    ax.set_xlim(left=9, right=50)
    ax.set_ylim(bottom=0, top=1100)
    ax.legend(
        borderaxespad=0,
        handletextpad=0.2,
        labelspacing=0.4,
        handlelength=2,
        frameon=False,
        loc="upper left",
    )
    f.save(0.55, "3/cachet_inference_carving_cactus")


generate_appendix_plots()
generate_width_plots()
