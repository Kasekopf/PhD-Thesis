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

    def threshold_times(self, method, width, default_val=None):
        """
        For each log, find the time at which the solver first found a contraction tree of max-rank at or below [width].

        :param width: The bound on max-rank to check.
        :param default_val: The time to use if the solver never finds a good enough contraction tree
        :return: A list of times
        """
        data = self.__instance.query(
            'SELECT [Log] FROM data WHERE [method] ="'
            + method
            + '" ORDER BY [|benchmark] DESC'
        )
        result = []
        for log in data["Log"]:
            best_width = None
            found = False
            if log is not None:
                for time, widths in eval(log):
                    if best_width is None or widths["Carving"] < best_width:
                        if widths["Carving"] <= width and (
                            best_width is None or best_width > width
                        ):
                            result.append(time)
                            found = True
                            break
            if not found:
                result.append(default_val)
        return result


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

    util.set_legend(ax, loc="upper left")
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

    util.set_legend(ax, loc="upper right")
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

    util.set_legend(ax, loc="upper right")
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_xticklabels(["0", "10", "20", "30", "40", "$50+$"])

    ax.set_xlabel("Width of decomposition")
    ax.set_ylabel("Number of benchmarks")


def plot_planning_fig(axs):
    for ax, width in zip(axs, [30, 25, 20]):
        ax.plot(
            *util.cactus(
                ga_wmc_factor.threshold_times("factor-htd", width, default_val=TIMEOUT)
            ),
            label="FT+htd",
            color="#ffd700",
            linestyle="--",
            linewidth=2,
        )

        ax.plot(
            *util.cactus(
                ga_wmc_factor.threshold_times("factor-Flow", width, default_val=TIMEOUT)
            ),
            label="FT+Flow",
            color="#ffb14e",
            linestyle=":",
            linewidth=2,
        )
        ax.plot(
            *util.cactus(
                ga_wmc_factor.threshold_times(
                    "factor-Tamaki", width, default_val=TIMEOUT
                )
            ),
            label="FT+Tamaki",
            color="#fa8775",
            linestyle="-",
            linewidth=2,
        )
        util.set_cactus_axes(
            ax, 1091, TIMEOUT, legend_args={"loc": "lower right"}, bottom=0.1
        )


def gen(output):
    f, ax = output.figure(0.6, ncols=1)
    plot_graph_analysis_vertex_cover(ax)
    f.save("3/appendix_vertex_cover_width")

    f, ax = output.figure(0.6, ncols=1)
    plot_graph_analysis_lg_wmc(ax)
    f.save("3/appendix_wmc_lg_width")

    f, ax = output.figure(0.6, ncols=1)
    plot_graph_analysis_ft_wmc(ax)
    f.save("3/appendix_wmc_ft_width")

    f, axs = output.figure(1, nrows=3)
    plot_planning_fig(axs)
    f.save("3/tree_solver_analysis")


if __name__ == "__main__":
    gen(util.output_pdf())
