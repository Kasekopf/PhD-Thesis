import collections
import slurmqueen

import util

ProjectedModelCounter = collections.namedtuple(
    "ModelCounter", ["data_name", "label", "line"]
)

counters = [
    ProjectedModelCounter("dpmc/lg/flow/mcs0", "ProCount", {"linestyle": "-"},),
    ProjectedModelCounter("d4p0", "D4\\textsubscript{P}", {"linestyle": "-"},),
    ProjectedModelCounter("projmc0", "projMC", {"linestyle": "-"},),
    ProjectedModelCounter("ssat0", "reSSAT", {"linestyle": "-"},),
]


procount_configs = [
    ProjectedModelCounter(
        "dpmc/lg/flow/mcs0", "ProCount(FlowCutter, MCS)", {"linestyle": "-"},
    ),
    ProjectedModelCounter(
        "dpmc/lg/flow/lp0", "ProCount(FlowCutter, LP)", {"linestyle": "-."},
    ),
    ProjectedModelCounter(
        "dpmc/lg/htd/mcs0", "ProCount(htd, MCS)", {"linestyle": "-."},
    ),
    ProjectedModelCounter("dpmc/lg/htd/lp0", "ProCount(htd, LP)", {"linestyle": "-."}),
    ProjectedModelCounter(
        "dpmc/lg/tcs/mcs0", "ProCount(Tamaki, MCS)", {"linestyle": "-."},
    ),
    ProjectedModelCounter(
        "dpmc/lg/tcs/lp0", "ProCount(Tamaki, LP)", {"linestyle": "-."},
    ),
]
TIMEOUT = 1000


class SolverData:
    def __init__(self, data_dir):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)

    def raw_times(self):
        data = self.__instance.query(
            "select [time], [count], [benchmarkFile], [benchmark] from data"
        )

        data.loc[data["count"].isnull(), "time"] = TIMEOUT
        data.loc[data["count"] == 0, "time"] = TIMEOUT
        data.loc[data["time"].isnull(), "time"] = TIMEOUT
        data.loc[data["time"] > TIMEOUT, "time"] = TIMEOUT
        return data

    def times(self, expected=891):
        data = self.raw_times()
        data = data.sort_values("benchmarkFile")

        if expected is not None and len(data) != expected:
            print(
                "Only {0}/{1} datapoints observed for {2}".format(
                    len(data), expected, self.__instance._local_directory
                )
            )

        return list(data["time"])

    def par2_by_width(self, widths, width_count):
        """
        Return a plot of x-y pairs where, at x-value x, the y-value is the average par2 score
        of all benchmarks of width between x-width_count and x+width_count

        :param widths: A mapping from width -> list of benchmark names. Must return [] on invalid widths
        :param width_count: The number of widths to average over
        :return: (list of x values, list of y values)
        """
        raw_data = self.raw_times()
        par2_by_benchmark = {
            b: t if t < TIMEOUT else 2 * TIMEOUT
            for b, t in zip(raw_data["benchmark"], raw_data["time"])
        }

        x, y = [], []
        for i in range(10 + width_count - 1, 99 - width_count):
            num_benchmarks = 0
            par2 = 0
            for j in range(i - width_count, i + width_count + 1):
                for b in widths[j]:
                    num_benchmarks += 1
                    par2 += par2_by_benchmark[b]
            if num_benchmarks == 0:
                continue
            x.append(i)
            y.append(par2 / num_benchmarks)
        return x, y


counter_exps = {
    counter.data_name: SolverData(util.data_dir("6/solving/" + counter.data_name))
    for counter in counters
}

procount_exps = {
    config.data_name: SolverData(util.data_dir("6/solving/" + config.data_name))
    for config in procount_configs
}


def plot_comparison_exp(ax):
    for counter in counters:
        ax.plot(
            *util.cactus(counter_exps[counter.data_name].times(), endpoint=TIMEOUT),
            label=counter.label,
            linewidth=1,
            **counter.line,
        )

    vbs0 = util.vbs(
        *[counter_exps[counter.data_name].times() for counter in counters[1:]]
    )
    ax.plot(
        *util.cactus(vbs0, endpoint=TIMEOUT), label="VBS0", linewidth=1, linestyle="--",
    )
    vbs1 = util.vbs(*[counter_exps[counter.data_name].times() for counter in counters])
    ax.plot(
        *util.cactus(vbs1, endpoint=TIMEOUT), label="VBS1", linewidth=1, linestyle=":",
    )
    util.set_cactus_axes(ax, 400, TIMEOUT, bottom=0.0005)


def plot_procount_comparison_exp(ax):
    for counter in procount_configs:
        ax.plot(
            *util.cactus(procount_exps[counter.data_name].times(), endpoint=TIMEOUT),
            label=counter.label,
            linewidth=1,
            **counter.line,
        )
    util.set_cactus_axes(ax, 400, TIMEOUT, bottom=0.0005)


def plot_comparison_by_width(ax):
    import gen_planning_figures as planning

    widths = planning.planning_data["flow"].benchmarks_by_width()

    for counter in counters:
        ax.plot(
            *counter_exps[counter.data_name].par2_by_width(widths, 5),
            label=counter.label,
            linewidth=1,
            **counter.line,
        )
    util.set_legend(ax, loc="upper left")
    ax.set_xlabel("Mean of 10 project-join tree widths")
    ax.set_ylabel("Mean PAR-2 score of 10 widths")


def gen(output):
    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_comparison_exp(ax)
    f.save("6/figSolving")

    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_procount_comparison_exp(ax)
    f.save("6/figSolvingA")

    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_comparison_by_width(ax)
    f.save("6/figWidths")


if __name__ == "__main__":
    gen(util.output_pdf())
