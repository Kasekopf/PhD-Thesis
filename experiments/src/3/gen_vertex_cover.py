import collections
import slurmqueen
import util

""""
Definition and analysis of benchmarks counting the number of vertex covers of
randomly generated cubic graphs.
"""

TIMEOUT = 1000


class VertexCoverData:
    def __init__(self, data_dir):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)

    def extract_vertex_medians(self):
        is_tensor_based = "Max Rank" in list(
            self.__instance.query("PRAGMA table_info(data)")["name"]
        )
        if is_tensor_based:
            data = self.__instance.query(
                "SELECT [Count], [Max Rank], [Total Time], [|num_vars], [|i] FROM data"
            )
        else:
            data = self.__instance.query(
                "SELECT [Count], [Total Time], [|num_vars], [|i] FROM data"
            )

        if len(data) != 2100:
            print(
                "Only {0}/2100 datapoints observed for {1}".format(
                    len(data), self.__instance
                )
            )

        # Set the total time to TIMEOUT for all experiments that did not return a count (includes timeout, memout, etc.)
        data.loc[data["Count"].isnull(), "Total Time"] = TIMEOUT

        # Take the median runtime for each solvers and each number of variables, across all 100 benchmarks
        data = data.groupby(["|num_vars"], as_index=False).median()
        return data


vertex_cover_data = {
    "sharpsat": VertexCoverData(util.data_dir("3/cubic_vertex_cover/sharpsat")),
    "d4": VertexCoverData(util.data_dir("3/cubic_vertex_cover/d4")),
    "minic2d": VertexCoverData(util.data_dir("3/cubic_vertex_cover/minic2d")),
    "cachet": VertexCoverData(util.data_dir("3/cubic_vertex_cover/cachet")),
    "dynasp": VertexCoverData(util.data_dir("3/cubic_vertex_cover/dynasp")),
    "dynqbf": VertexCoverData(util.data_dir("3/cubic_vertex_cover/dynqbf")),
    "kcmr_greedy": VertexCoverData(util.data_dir("3/cubic_vertex_cover/kcmr_greedy")),
    "kcmr_metis": VertexCoverData(util.data_dir("3/cubic_vertex_cover/kcmr_metis")),
    "kcmr_gn": VertexCoverData(util.data_dir("3/cubic_vertex_cover/kcmr_gn")),
    "line_flow": VertexCoverData(util.data_dir("3/cubic_vertex_cover/line_flow")),
    "line_htd": VertexCoverData(util.data_dir("3/cubic_vertex_cover/line_htd")),
    "line_tamaki": VertexCoverData(util.data_dir("3/cubic_vertex_cover/line_tamaki")),
    "factor_flow": VertexCoverData(util.data_dir("3/cubic_vertex_cover/factor_flow")),
    "factor_htd": VertexCoverData(util.data_dir("3/cubic_vertex_cover/factor_htd")),
    "factor_tamaki": VertexCoverData(
        util.data_dir("3/cubic_vertex_cover/factor_tamaki")
    ),
}


def plot_vertex_runtime(experiment_infos, ax):
    for exp_info in experiment_infos:
        data = exp_info.data.extract_vertex_medians()
        data = data[
            data["Total Time"] < TIMEOUT
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

    util.set_legend(ax, loc="upper left")
    ax.set_xlabel("$n$: Number of vertices")
    ax.set_ylabel("Median solving time (s)")
    ax.set_yscale("log", nonpositive="mask")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0.1, top=TIMEOUT)


def plot_vertex_rank(experiment_infos, ax):
    for exp_info in experiment_infos:
        data = exp_info.data.extract_vertex_medians()
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

    util.set_legend(ax, loc="upper left")
    ax.set_xticks([50, 100, 150, 200, 250])
    ax.set_xlabel("$n$: Number of vertices")
    ax.set_ylabel("Median max rank")


def gen(output):
    DisplayInfo = collections.namedtuple(
        "DisplayInfo", ["name", "data", "color", "marker"]
    )
    vertex_experiments = [
        DisplayInfo("cachet", vertex_cover_data["cachet"], "#dd0f0f", "p"),
        DisplayInfo("dynQBF", vertex_cover_data["dynqbf"], "#000033", "P"),
        DisplayInfo("dynasp", vertex_cover_data["dynasp"], "#0000dd", "d"),
        DisplayInfo("sharpSAT", vertex_cover_data["sharpsat"], "#403bcb", "s"),
        DisplayInfo("d4", vertex_cover_data["d4"], "#9d02d7", "o"),
        DisplayInfo("miniC2D", vertex_cover_data["minic2d"], "#ea5f94", "D"),
        DisplayInfo("greedy", vertex_cover_data["kcmr_greedy"], "#877662", "v"),
        DisplayInfo("metis", vertex_cover_data["kcmr_metis"], "#9c9146", "<"),
        DisplayInfo("GN", vertex_cover_data["kcmr_gn"], "#c7a441", ">"),
        DisplayInfo("LG+Flow", vertex_cover_data["line_flow"], "#ffb14e", "*"),
    ]
    f, ax = output.figure(0.55, ncols=1)
    plot_vertex_runtime(vertex_experiments, ax)
    f.save("3/vertex_cover_time")

    f, ax = output.figure(0.45, ncols=1)
    plot_vertex_rank(vertex_experiments[-4:], ax)
    f.save("3/vertex_cover_rank")


if __name__ == "__main__":
    gen(util.output_pdf())
