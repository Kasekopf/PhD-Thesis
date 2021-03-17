import collections
import slurmqueen
import util

""""
Definition and analysis of experiments computing graph decomposition quality.
"""

TIMEOUT = 1000


class DecompositionData:
    def __init__(self, data_dir):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)

    def extract_best_decompositions_vertex_cover(self):
        data = self.__instance.query(
            "SELECT [Carving], [Tree], [|num_vars], [|i] FROM data"
        )

        # Take the best decomposition found across all solvers on each benchmark
        data = data.groupby(["|num_vars", "|i"], as_index=False).min()

        # Take the median runtime for each number of variables, across all 100 benchmarks
        data = data.groupby(["|num_vars"], as_index=False).median()

        if len(data) != 21:
            print(
                "Only {0}/21 options for the numbers of variables observed for {1}".format(
                    len(data), self.__instance
                )
            )

        return data.sort_values("|num_vars")

    def extract_best_decompositions_wmc(self):
        data = self.__instance.query(
            "SELECT [Carving], [Tree], [|benchmark], [output] FROM data"
        )

        # Take the best decomposition found across all solvers on each benchmark
        data = data.groupby(["|benchmark"], as_index=False).min()

        if len(data) != 1091:
            print(
                "Only {0}/1091 options for the numbers of variables observed for {1}".format(
                    len(data), self.__instance
                )
            )
        return data.sort_values("|benchmark")


ga_vertex_cover_line = DecompositionData(
    util.data_dir("3/appendix_graph_analysis/cubic_vertex_cover/line")
)
ga_vertex_cover_factor = DecompositionData(
    util.data_dir("3/appendix_graph_analysis/cubic_vertex_cover/factor")
)


def plot_graph_analysis_vertex_cover(ax):
    line = ga_vertex_cover_line.extract_best_decompositions_vertex_cover()
    factor = ga_vertex_cover_factor.extract_best_decompositions_vertex_cover()

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


ga_wmc_line = DecompositionData(util.data_dir("3/appendix_graph_analysis/wmc/line"))
ga_wmc_factor = DecompositionData(util.data_dir("3/appendix_graph_analysis/wmc/factor"))


def plot_graph_analysis_lg_wmc(ax):
    line = ga_wmc_line.extract_best_decompositions_wmc()

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
    factor = ga_wmc_factor.extract_best_decompositions_wmc()

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


def generate_decomposition_plots(output):
    f, ax = output.figure(ncols=1)
    plot_graph_analysis_vertex_cover(ax)
    f.save(0.6, "3/appendix_vertex_cover_width")

    f, ax = output.figure(ncols=1)
    plot_graph_analysis_lg_wmc(ax)
    f.save(0.6, "3/appendix_wmc_lg_width")

    f, ax = output.figure(ncols=1)
    plot_graph_analysis_ft_wmc(ax)
    f.save(0.6, "3/appendix_wmc_ft_width")


if __name__ == "__main__":
    generate_decomposition_plots(util.output_pdf())
