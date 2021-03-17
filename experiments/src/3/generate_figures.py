import collections
import math
import os
import slurmqueen

import util

output = util.output_pdf()

BASE_EXPERIMENT_DIR = "../../data/3"
TIMEOUT = 1000

""""
Definition and analysis of benchmarks counting the number of vertex covers of
randomly generated cubic graphs.
"""


def vertex_cover_counter(name, location, **other_args):
    """
    Generate an experiment using an existing counter
    """
    return slurmqueen.Experiment(
        "python src/benchmark_counter.py",
        [
            {
                "": [
                    name,
                    "benchmarks/cubic_vertex_cover/cubic_vc_%d_%d.cnf" % (num_vars, i),
                ],
                "timeout": 1000,
                "counter": location,
                **other_args,
                "|num_vars": num_vars,
                "|i": i,
            }
            for num_vars in range(50, 260, 10)
            for i in range(100)
        ],
        output_argument="output",
        log_argument="&>",
    )


def vertex_cover_tensor(method):
    """
    Generate an experiment using an tensor-based method
    """
    return slurmqueen.Experiment(
        "python src/tensororder.py",
        [
            {
                "": [
                    "benchmarks/cubic_vertex_cover/cubic_vc_%d_%d.cnf" % (num_vars, i)
                ],
                "timeout": 1000,
                "method": method,
                "max_rank": 30,
                "seed": 1234567,
                "|num_vars": num_vars,
                "|i": i,
            }
            for num_vars in range(50, 260, 10)
            for i in range(100)
        ],
        output_argument="output",
        log_argument="&>",
    )


vertex_cover_sharpsat = vertex_cover_counter(
    "sharpsat", "counters/sharpSAT/sharpSAT"
).instance(BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/sharpsat")
vertex_cover_d4 = vertex_cover_counter("d4", "counters/d4/d4").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/d4"
)
vertex_cover_minic2d = vertex_cover_counter(
    "minic2d", "counters/miniC2D/miniC2D"
).instance(BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/minic2d")
vertex_cover_cachet = vertex_cover_counter(
    "cachet", "counters/cachet/cachet", weighted=False
).instance(BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/cachet")
vertex_cover_dynasp = vertex_cover_counter(
    "dynasp", "counters/dynasp/dynasp", gringo="formatters/clingo/gringo"
).instance(BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/dynasp")
vertex_cover_dynqbf = vertex_cover_counter("dynqbf", "counters/dynqbf/dynqbf").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/dynqbf"
)

vertex_cover_kcmr_greedy = vertex_cover_tensor("KCMR-greedy").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/kcmr_greedy"
)
vertex_cover_kcmr_metis = vertex_cover_tensor("KCMR-metis").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/kcmr_metis"
)
vertex_cover_kcmr_gn = vertex_cover_tensor("KCMR-gn").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/kcmr_gn"
)
vertex_cover_line_flow = vertex_cover_tensor("line-Flow").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/line_flow"
)
vertex_cover_line_htd = vertex_cover_tensor("line-htd").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/line_htd"
)
vertex_cover_line_tamaki = vertex_cover_tensor("line-Tamaki").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/line_tamaki"
)
vertex_cover_factor_flow = vertex_cover_tensor("factor-Flow").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/factor_flow"
)
vertex_cover_factor_htd = vertex_cover_tensor("factor-htd").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/factor_htd"
)
vertex_cover_factor_tamaki = vertex_cover_tensor("factor-Tamaki").instance(
    BASE_EXPERIMENT_DIR + "/cubic_vertex_cover/factor_tamaki"
)


def extract_vertex_medians(instance):
    is_tensor_based = "Max Rank" in list(
        instance.query("PRAGMA table_info(data)")["name"]
    )
    if is_tensor_based:
        data = instance.query(
            "SELECT [Count], [Max Rank], [Total Time], [|num_vars], [|i] FROM data"
        )
    else:
        data = instance.query(
            "SELECT [Count], [Total Time], [|num_vars], [|i] FROM data"
        )

    if len(data) != 2100:
        print("Only {0}/2100 datapoints observed for {1}".format(len(data), instance))

    # Set the total time to TIMEOUT for all experiments that did not return a count (includes timeout, memout, etc.)
    data.loc[data["Count"].isnull(), "Total Time"] = TIMEOUT

    # Take the median runtime for each solvers and each number of variables, across all 100 benchmarks
    data = data.groupby(["|num_vars"], as_index=False).median()
    return data


def plot_vertex_runtime(experiment_infos, ax):
    for exp_info in experiment_infos:
        data = exp_info.data[
            exp_info.data["Total Time"] < TIMEOUT
        ]  # Do not draw points that didn't finish (at median)
        ax.plot(
            data["|num_vars"],
            data["Total Time"],
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
    ax.set_xlabel("$n$: Number of vertices")
    ax.set_ylabel("Median solving time (s)")
    ax.set_yscale("log", nonposy="mask")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0.1, top=TIMEOUT)


def plot_vertex_rank(experiment_infos, ax):
    for exp_info in experiment_infos:
        data = exp_info.data
        ax.plot(
            data["|num_vars"],
            data["Max Rank"],
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
    ax.set_ylabel("Median max rank")


""""
Definition and analysis of 1091 probabilistic inference benchmarks.
"""


def find_benchmarks(folder, benchmark_class):
    result = []
    for obj in os.listdir(folder):
        obj_path = folder + "/" + obj
        if os.path.isdir(obj_path):
            result += find_benchmarks(obj_path, benchmark_class)
        elif os.path.isfile(obj_path) and "README" not in obj:
            result.append((obj_path, benchmark_class))
    return result


def find_benchmark_families(folder):
    benchmarks = []
    if os.path.isdir(folder):
        for family in os.listdir(folder):
            if os.path.isdir(folder + "/" + family):
                benchmarks += find_benchmarks(folder + "/" + family, family)
    return benchmarks


def cachet_benchmarks():
    return find_benchmark_families("benchmarks/cachet")


def wmc_counter(name, location, **other_args):
    return slurmqueen.Experiment(
        "python src/benchmark_counter.py",
        [
            {
                "": [name, benchmark],
                "timeout": 1000,
                "counter": location,
                **other_args,
                "|benchmark": benchmark,
                "|benchmark_class": benchmark_class,
            }
            for benchmark, benchmark_class in cachet_benchmarks()
        ],
        output_argument="output",
        log_argument="&>",
    )


def wmc_tensor(method):
    return slurmqueen.Experiment(
        "python src/tensororder.py",
        [
            {
                "": [benchmark],
                "timeout": 1000,
                "method": method,
                "max_rank": 30,
                "seed": 1234567,
                "|benchmark": benchmark,
                "|benchmark_class": benchmark_class,
            }
            for benchmark, benchmark_class in cachet_benchmarks()
        ],
        output_argument="output",
        log_argument="&>",
    )


wmc_sharpsat = wmc_counter("sharpsat", "counters/sharpSAT/sharpSAT").instance(
    BASE_EXPERIMENT_DIR + "/wmc/sharpsat"
)
wmc_d4 = wmc_counter("d4", "counters/d4/d4", weighted=True).instance(
    BASE_EXPERIMENT_DIR + "/wmc/d4"
)
wmc_minic2d = wmc_counter("minic2d", "counters/miniC2D/miniC2D").instance(
    BASE_EXPERIMENT_DIR + "/wmc/minic2d"
)
wmc_cachet = wmc_counter("cachet", "counters/cachet/cachet", weighted=True).instance(
    BASE_EXPERIMENT_DIR + "/wmc/cachet"
)
wmc_kcmr_greedy = wmc_tensor("KCMR-greedy").instance(
    BASE_EXPERIMENT_DIR + "/wmc/kcmr_greedy"
)
wmc_kcmr_metis = wmc_tensor("KCMR-metis").instance(
    BASE_EXPERIMENT_DIR + "/wmc/kcmr_metis"
)
wmc_kcmr_gn = wmc_tensor("KCMR-gn").instance(BASE_EXPERIMENT_DIR + "/wmc/kcmr_gn")
wmc_line_flow = wmc_tensor("line-Flow").instance(BASE_EXPERIMENT_DIR + "/wmc/line_flow")
wmc_line_htd = wmc_tensor("line-htd").instance(BASE_EXPERIMENT_DIR + "/wmc/line_htd")
wmc_line_tamaki = wmc_tensor("line-Tamaki").instance(
    BASE_EXPERIMENT_DIR + "/wmc/line_tamaki"
)
wmc_factor_flow = wmc_tensor("factor-Flow").instance(
    BASE_EXPERIMENT_DIR + "/wmc/factor_flow"
)
wmc_factor_htd = wmc_tensor("factor-htd").instance(
    BASE_EXPERIMENT_DIR + "/wmc/factor_htd"
)
wmc_factor_tamaki = wmc_tensor("factor-Tamaki").instance(
    BASE_EXPERIMENT_DIR + "/wmc/factor_tamaki"
)


def load_inference_data(instance):
    data = instance.query(
        "SELECT [Count], [Total Time], [|benchmark], [|benchmark_class], [output] FROM data"
    )
    # Set the total time to TIMEOUT for all experiments that did not return a count (includes timeout, memout, etc.)
    data.loc[data["Count"].isnull(), "Total Time"] = TIMEOUT
    data.loc[data["Total Time"] > TIMEOUT, "Total Time"] = TIMEOUT

    if len(data) != 1091:
        print("Only {0}/1091 datapoints observed for {1}".format(len(data), instance))

    return data.sort_values("|benchmark")


def analyze_wmc_benchmarks():
    flow = load_inference_data(wmc_factor_flow)["Total Time"]
    htd = load_inference_data(wmc_factor_htd)["Total Time"]
    tama = load_inference_data(wmc_factor_tamaki)["Total Time"]
    mini = load_inference_data(wmc_minic2d)["Total Time"]
    d4 = load_inference_data(wmc_d4)["Total Time"]
    cachet = load_inference_data(wmc_cachet)["Total Time"]

    all_tensor_best = sum(
        ((flow < mini) & (flow < d4) & (flow < cachet))
        | ((tama < mini) & (tama < d4) & (tama < cachet))
        | ((htd < mini) & (htd < d4) & (htd < cachet))
    )
    print(
        "Our contributions FT+* are faster than cachet, miniC2D, and d4 on %d benchmarks in total."
        % all_tensor_best
    )

    tensor_solve_counters_timeout = sum(
        ((flow < TIMEOUT) | (tama < TIMEOUT) | (htd < TIMEOUT))
        & (mini == TIMEOUT)
        & (d4 == TIMEOUT)
        & (cachet == TIMEOUT)
    )
    print(
        "Our contributions were able to solve %d benchmarks on which cachet, miniC2D and d4 all timed out"
        % tensor_solve_counters_timeout
    )
    comparisons = {}
    print(
        "\tFT+Flow is fastest on %d benchmarks"
        % sum(
            (flow < tama) & (flow < mini) & (flow < htd) & (flow < d4) & (flow < cachet)
        )
    )
    print(
        "\tFT+Tamaki is fastest on %d benchmarks"
        % sum(
            (tama < flow) & (tama < mini) & (tama < htd) & (tama < d4) & (tama < cachet)
        )
    )
    print(
        "\tFT+htd is fastest on %d benchmarks"
        % sum((htd < tama) & (htd < flow) & (htd < mini) & (htd < d4) & (htd < cachet))
    )
    print(
        "\td4 is fastest on %d benchmarks"
        % sum((d4 < tama) & (d4 < flow) & (d4 < htd) & (d4 < mini) & (d4 < cachet))
    )
    print(
        "\tminiC2D is fastest on %d benchmarks"
        % sum(
            (mini < tama) & (mini < flow) & (mini < htd) & (mini < d4) & (mini < cachet)
        )
    )
    print(
        "\tcachet is fastest on %d benchmarks"
        % sum(
            (cachet < tama)
            & (cachet < flow)
            & (cachet < htd)
            & (cachet < d4)
            & (cachet < mini)
        )
    )
    print(
        "\tAll timeout on %d benchmarks"
        % sum(
            (flow == TIMEOUT)
            & (tama == TIMEOUT)
            & (htd == TIMEOUT)
            & (mini == TIMEOUT)
            & (d4 == TIMEOUT)
            & (cachet == TIMEOUT)
        )
    )
    return comparisons


def plot_cactus_line(ax, times, *args, **kw_args):
    x, y = [], []
    for i, time in enumerate(sorted(times)):
        if time < TIMEOUT:
            x += [i]
            y += [time]
    ax.plot(x, y, *args, **kw_args)


def build_vbs(*times_by_instance):
    return [min(times_by_benchmark) for times_by_benchmark in zip(*times_by_instance)]


def plot_inference_cactus(ax):
    flow_times = load_inference_data(wmc_factor_flow)["Total Time"]
    htd_times = load_inference_data(wmc_factor_htd)["Total Time"]
    tamaki_times = load_inference_data(wmc_factor_tamaki)["Total Time"]
    cachet_times = load_inference_data(wmc_cachet)["Total Time"]
    minic2d_times = load_inference_data(wmc_minic2d)["Total Time"]
    d4_times = load_inference_data(wmc_d4)["Total Time"]

    # Colors from https://projects.susielu.com/viz-palette
    plot_cactus_line(
        ax, htd_times, label="FT+htd", color="#ffd700", linestyle="--", linewidth=2
    )
    plot_cactus_line(
        ax, flow_times, label="FT+Flow", color="#ffb14e", linestyle=":", linewidth=2
    )
    plot_cactus_line(
        ax, tamaki_times, label="FT+Tamaki", color="#fa8775", linestyle="-", linewidth=2
    )
    plot_cactus_line(
        ax, cachet_times, label="cachet", color="#dd0f0f", linestyle="--", linewidth=2
    )
    plot_cactus_line(
        ax, minic2d_times, label="miniC2D", color="#ea5f94", linestyle=":", linewidth=2
    )
    plot_cactus_line(
        ax, d4_times, label="d4", color="#9d02d7", linestyle="-", linewidth=2
    )
    plot_cactus_line(
        ax,
        build_vbs(
            flow_times, htd_times, tamaki_times, cachet_times, minic2d_times, d4_times
        ),
        label="VBS",
        linestyle="--",
        color="#0000ff",
        linewidth=2,
    )

    ax.set_xlabel("Solved instance")
    ax.set_ylabel("Solving time (s)")
    ax.set_xlim(left=0, right=1100)
    ax.set_ylim(bottom=0, top=1000)
    ax.legend(
        borderaxespad=0,
        handletextpad=0.2,
        labelspacing=0.4,
        handlelength=2,
        frameon=False,
    )


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


def generate_vertex_cover_plots():
    DisplayInfo = collections.namedtuple(
        "DisplayInfo", ["name", "data", "color", "marker"]
    )
    vertex_experiments = [
        DisplayInfo(
            "cachet", extract_vertex_medians(vertex_cover_cachet), "#dd0f0f", "p"
        ),
        DisplayInfo(
            "dynQBF", extract_vertex_medians(vertex_cover_dynqbf), "#000033", "P"
        ),
        DisplayInfo(
            "dynasp", extract_vertex_medians(vertex_cover_dynasp), "#0000dd", "d"
        ),
        DisplayInfo(
            "sharpSAT", extract_vertex_medians(vertex_cover_sharpsat), "#403bcb", "s"
        ),
        DisplayInfo("d4", extract_vertex_medians(vertex_cover_d4), "#9d02d7", "o"),
        DisplayInfo(
            "miniC2D", extract_vertex_medians(vertex_cover_minic2d), "#ea5f94", "D"
        ),
        DisplayInfo(
            "greedy", extract_vertex_medians(vertex_cover_kcmr_greedy), "#877662", "v"
        ),
        DisplayInfo(
            "metis", extract_vertex_medians(vertex_cover_kcmr_metis), "#9c9146", "<"
        ),
        DisplayInfo("GN", extract_vertex_medians(vertex_cover_kcmr_gn), "#c7a441", ">"),
        DisplayInfo(
            "LG+Flow", extract_vertex_medians(vertex_cover_line_flow), "#ffb14e", "*"
        ),
    ]
    f, ax = output.figure(ncols=1)
    plot_vertex_runtime(vertex_experiments, ax)
    f.save(0.55, "3/vertex_cover_time")

    f, ax = output.figure(ncols=1)
    plot_vertex_rank(vertex_experiments[-4:], ax)
    f.save(0.45, "3/vertex_cover_rank")


def generate_wmc_plots():
    analyze_wmc_benchmarks()

    f, ax = output.figure(ncols=1)
    plot_inference_cactus(ax)
    f.save(0.45, "3/cachet_inference_cactus")


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


generate_vertex_cover_plots()
generate_wmc_plots()
generate_appendix_plots()
generate_width_plots()
