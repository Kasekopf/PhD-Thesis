import util
import slurmqueen
import config
import pandas


timeout = 1000


class BaseModelCounter:
    def __init__(self, name):
        self.name = name
        self.__instance = slurmqueen.Experiment("", []).instance(
            util.data_dir("4/comparison/" + self.name)
        )

    def get_experiment(self):
        return self.__instance

    def times(self):
        if self.name == "c2d":
            # c2d was not run using SlurmQueen
            data = pandas.read_csv(util.data_dir("4/comparison/c2d.csv"))
            data = data.sort_values("formula")
            return data["Total Time"]

        data = self.data()

        # Set the total time to TIMEOUT for all experiments that did not return a count (includes timeout, memout, etc.)
        data.loc[data["Count"].isnull(), "Total Time"] = config.timeout
        data.loc[data["Total Time"].isnull(), "Total Time"] = config.timeout
        data.loc[data["Total Time"] > config.timeout, "Total Time"] = config.timeout

        if "DMC" in self.name:
            data.loc[data["Count"] == 0, "Total Time"] = config.timeout  # underflow

        if len(data) != 1976:
            print(
                "Only {0}/{1} datapoints observed for {2}".format(
                    len(data), 1976, self.name
                )
            )
        data["<"] = (
            data["<"].str.replace("/bayes/", "/").replace("/pseudoweighted/", "/")
        )
        data = data.sort_values("<")
        return list(data["Total Time"])


class DPMCConfig(BaseModelCounter):
    def __init__(self, planner, executer, color, performance_factor):
        super().__init__(executer.name + "/" + planner.name)

        self.planner = planner
        self.executer = executer
        self.performance_factor = performance_factor
        self.line = {
            "color": color,
            "linestyle": "-",
            "label": executer.label + "+" + planner.method,
        }

    def data(self):
        if self.planner.method == "HTB":
            return self.get_experiment().query(
                "SELECT [Count], [Total Time], [cf] AS [<] FROM data"
            )
        else:
            return self.get_experiment().query(
                "SELECT [Count], [Total Time], [<] FROM data"
            )


dpmc_configs = [
    DPMCConfig(config.planners[-4], config.executers[0], "blue", 1),
    DPMCConfig(config.planners[-2], config.executers[0], "green", 1.427e-13),
    DPMCConfig(config.planners[-4], config.executers[1], "black", 1),
    DPMCConfig(config.planners[-2], config.executers[1], "orange", 1.0314e-15),
]


class ModelCounter(BaseModelCounter):
    def __init__(self, name, other_args, command, line):
        super().__init__(name)

        self._other_args = other_args
        self._command = command
        self.line = line

    def data(self):
        return self.get_experiment().query(
            "SELECT [Count], [Total Time], [<] FROM data"
        )


weighted_counters = [
    ModelCounter(
        "d4",
        {"weighted": True},
        "python /wrappers/d4_wrapper.py",
        {"color": "blue", "linestyle": "--", "label": "d4"},
    ),
    ModelCounter(
        "miniC2D",
        {"weighted": True},
        "python /wrappers/miniC2D_wrapper.py",
        {"color": "green", "linestyle": "--", "label": "miniC2D"},
    ),
    ModelCounter(
        "cachet",
        {"weighted": True, "fix_normalize": False},
        "python /wrappers/cachet_wrapper.py",
        {"color": "black", "linestyle": "--", "label": "cachet"},
    ),
    ModelCounter(
        "c2d",
        {"weighted": True},
        "python /wrappers/DPMC_wrapper.py",
        {"color": "orange", "linestyle": "--", "label": "c2d"},
    ),
]


def plot_comparison_exp(ax):
    for counter in dpmc_configs + weighted_counters:
        ax.plot(
            *util.cactus(counter.times(), endpoint=config.timeout),
            linewidth=1,
            **counter.line,
        )

    vbs_existing = util.vbs(*[c.times() for c in weighted_counters])
    ax.plot(
        *util.cactus(vbs_existing, endpoint=config.timeout,),
        color="#ff0000",
        linestyle=":",
        linewidth=1,
        label="VBS*",
    )

    vbs_all = util.vbs(*[c.times() for c in weighted_counters + dpmc_configs])
    ax.plot(
        *util.cactus(vbs_all, endpoint=config.timeout,),
        color="#000000",
        linestyle=":",
        linewidth=1,
        label="VBS",
    )

    util.set_cactus_axes(
        ax, 2000, config.timeout, bottom=0.001, legend_args={"ncol": 2}
    )
    return vbs_existing


def gen(output):
    f, ax = output.figure(ncols=1, nrows=1)
    vbs_existing = plot_comparison_exp(ax)
    f.save(0.5, "4/comparison")

    hl = dpmc_configs[-1].times()
    hl_best = 0
    for t1, t2 in zip(hl, vbs_existing):
        if t1 < config.timeout and t1 <= t2:
            hl_best += 1
    print("DPMC is fastest on " + str(hl_best))


if __name__ == "__main__":
    gen(util.output_pdf())
