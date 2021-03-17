import math
import slurmqueen
import util
import gen_decomposition  # For ga_wmc_factor

""""
Definition and analysis of 1091 probabilistic inference benchmarks.
"""

TIMEOUT = 1000


class CachetData:
    def __init__(self, data_dir):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)

    def get_times(self):
        data = self.__instance.query(
            "SELECT [Count], [Total Time], [|benchmark], [|benchmark_class], [output] FROM data"
        )
        # Set the total time to TIMEOUT for all experiments that did not return a count (includes timeout, memout, etc.)
        data.loc[data["Count"].isnull(), "Total Time"] = TIMEOUT
        data.loc[data["Total Time"] > TIMEOUT, "Total Time"] = TIMEOUT

        if len(data) != 1091:
            print(
                "Only {0}/1091 datapoints observed for {1}".format(
                    len(data), self.__instance
                )
            )

        return data.sort_values("|benchmark")["Total Time"]


wmc_data = {
    "sharpsat": CachetData(util.data_dir("3/wmc/sharpsat")),
    "d4": CachetData(util.data_dir("3/wmc/d4")),
    "minic2d": CachetData(util.data_dir("3/wmc/minic2d")),
    "cachet": CachetData(util.data_dir("3/wmc/cachet")),
    "dynasp": CachetData(util.data_dir("3/wmc/dynasp")),
    "dynqbf": CachetData(util.data_dir("3/wmc/dynqbf")),
    "kcmr_greedy": CachetData(util.data_dir("3/wmc/kcmr_greedy")),
    "kcmr_metis": CachetData(util.data_dir("3/wmc/kcmr_metis")),
    "kcmr_gn": CachetData(util.data_dir("3/wmc/kcmr_gn")),
    "line_flow": CachetData(util.data_dir("3/wmc/line_flow")),
    "line_htd": CachetData(util.data_dir("3/wmc/line_htd")),
    "line_tamaki": CachetData(util.data_dir("3/wmc/line_tamaki")),
    "factor_flow": CachetData(util.data_dir("3/wmc/factor_flow")),
    "factor_htd": CachetData(util.data_dir("3/wmc/factor_htd")),
    "factor_tamaki": CachetData(util.data_dir("3/wmc/factor_tamaki")),
}


# noinspection PyTypeChecker
def analyze_wmc_benchmarks():
    flow = wmc_data["factor_flow"].get_times()
    htd = wmc_data["factor_htd"].get_times()
    tama = wmc_data["factor_tamaki"].get_times()
    mini = wmc_data["minic2d"].get_times()
    d4 = wmc_data["d4"].get_times()
    cachet = wmc_data["cachet"].get_times()

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


def plot_inference_cactus(ax):
    flow_times = wmc_data["factor_flow"].get_times()
    htd_times = wmc_data["factor_htd"].get_times()
    tamaki_times = wmc_data["factor_tamaki"].get_times()
    cachet_times = wmc_data["cachet"].get_times()
    minic2d_times = wmc_data["minic2d"].get_times()
    d4_times = wmc_data["d4"].get_times()

    # Colors from https://projects.susielu.com/viz-palette
    ax.plot(
        *util.cactus(htd_times),
        label="FT+htd",
        color="#ffd700",
        linestyle="--",
        linewidth=2,
    )

    ax.plot(
        *util.cactus(flow_times),
        label="FT+Flow",
        color="#ffb14e",
        linestyle=":",
        linewidth=2,
    )
    ax.plot(
        *util.cactus(tamaki_times),
        label="FT+Tamaki",
        color="#fa8775",
        linestyle="-",
        linewidth=2,
    )
    ax.plot(
        *util.cactus(cachet_times),
        label="cachet",
        color="#dd0f0f",
        linestyle="--",
        linewidth=2,
    )
    ax.plot(
        *util.cactus(minic2d_times),
        label="miniC2D",
        color="#ea5f94",
        linestyle=":",
        linewidth=2,
    )
    ax.plot(
        *util.cactus(d4_times), label="d4", color="#9d02d7", linestyle="-", linewidth=2
    )
    ax.plot(
        *util.cactus(
            util.vbs(
                flow_times,
                htd_times,
                tamaki_times,
                cachet_times,
                minic2d_times,
                d4_times,
            )
        ),
        label="VBS",
        linestyle="--",
        color="#0000ff",
        linewidth=2,
    )

    util.set_cactus_axes(ax, 1091, TIMEOUT, legend_args={"loc": "upper left"})


def plot_by_widths(ax):

    wmc_widths = gen_decomposition.ga_wmc_factor.extract_best_decompositions_wmc()[
        "Carving"
    ]

    def plot_width_cactus_line(times, **kwargs):
        completed_widths = [
            int(w) for w, t in zip(wmc_widths, times) if t < 1000 and not math.isnan(w)
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

    plot_width_cactus_line(
        [999] * len(wmc_widths),
        label="All benchmarks",
        color="#000000",
        linestyle=":",
        linewidth=2,
    )
    plot_width_cactus_line(
        wmc_data["factor_htd"].get_times(),
        label="FT+htd",
        color="#ffd700",
        linestyle="--",
        linewidth=2,
    )
    plot_width_cactus_line(
        wmc_data["factor_flow"].get_times(),
        label="FT+Flow",
        color="#ffb14e",
        linestyle=":",
        linewidth=2,
    )
    plot_width_cactus_line(
        wmc_data["factor_tamaki"].get_times(),
        label="FT+Tamaki",
        color="#fa8775",
        linestyle="-",
        linewidth=2,
    )
    plot_width_cactus_line(
        wmc_data["cachet"].get_times(),
        label="cachet",
        color="#dd0f0f",
        linestyle="--",
        linewidth=2,
    )
    plot_width_cactus_line(
        wmc_data["minic2d"].get_times(),
        label="miniC2D",
        color="#ea5f94",
        linestyle=":",
        linewidth=2,
    )
    plot_width_cactus_line(
        wmc_data["d4"].get_times(),
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


def gen(output):
    analyze_wmc_benchmarks()

    f, ax = output.figure(ncols=1)
    plot_inference_cactus(ax)
    f.save(0.45, "3/cachet_inference_cactus")

    f, ax = output.figure(ncols=1)
    plot_by_widths(ax)
    f.save(0.55, "3/cachet_inference_carving_cactus")


if __name__ == "__main__":
    gen(util.output_pdf())
