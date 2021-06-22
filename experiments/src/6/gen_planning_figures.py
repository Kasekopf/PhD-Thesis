import collections
import slurmqueen

import util

MAX_WIDTH = 30
TIMEOUT = 100

SAT0 = slurmqueen.Experiment([]).instance(util.data_dir("6/solving/sat0"))

SATS = SAT0.query(
    """
select benchmark from data
where count != 0
"""
)


class PlanningData:
    def __init__(self, data_dir):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)

    def lg_times(self):
        return (
            self.__instance.query(
                f"select * from data where time <= 100 and width1 <= {MAX_WIDTH}"
            )
            .merge(SATS)["time1"]
            .tolist()
        )

    def lg_times_a(self):  # returned a list which may contain None
        def get_completion_time(series):
            tree = 1
            while f"width{tree}" in series:
                if series[f"width{tree}"] <= MAX_WIDTH:
                    return series[f"time{tree}"]
                else:
                    tree += 1
            return TIMEOUT

        frame = self.__instance.query("select * from data where time <= 100").merge(
            SATS
        )
        return [get_completion_time(series) for (_, series) in frame.iterrows()]

    def htb_times(self, cv, rank, choice):
        return (
            self.__instance.query(
                f"""
                select * from data where time <= 100 and width <= {MAX_WIDTH}
                and cv = '{cv}' and rank = '{rank}' and choice = '{choice}'
            """
            )
            .merge(SATS)["time"]
            .tolist()
        )

    def benchmarks_by_width(self):
        data = self.__instance.query(
            "select benchmark,width1 from data where width1 is not null"
        )

        result = collections.defaultdict(lambda: [])
        for benchmark, width in zip(data["benchmark"], data["width1"]):
            result[width].append(benchmark)
        return result


planning_data = {
    "flow": PlanningData(util.data_dir("6/planning/lg/flow0")),
    "htd": PlanningData(util.data_dir("6/planning/lg/htd0")),
    "tamaki": PlanningData(util.data_dir("6/planning/lg/tcs0")),
    "htb": PlanningData(util.data_dir("6/planning/htb0")),
}


def plot_planning_exp(ax):
    ax.plot(
        *util.cactus(planning_data["flow"].lg_times(), endpoint=TIMEOUT),
        label="LG(FlowCutter)",
        linestyle="-",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(planning_data["htd"].lg_times(), endpoint=TIMEOUT),
        label="LG(htd)",
        linestyle="-",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(planning_data["tamaki"].lg_times(), endpoint=TIMEOUT),
        label="LG(Tamaki)",
        linestyle="-",
        linewidth=1,
    )

    for cv in ["MCS"]:
        for rank in ["BE", "BM"]:
            for choice in ["Tree"]:
                ax.plot(
                    *util.cactus(
                        planning_data["htb"].htb_times(cv, rank, choice),
                        endpoint=TIMEOUT,
                    ),
                    label=f"HTB({cv}, {rank})",
                    linestyle="--",
                    linewidth=1,
                )

    util.set_cactus_axes(ax, 200, 100)


def plot_planning_a_exp(ax):
    ax.plot(
        *util.cactus(planning_data["flow"].lg_times_a(), endpoint=TIMEOUT),
        label="LG(FlowCutter)",
        linestyle="-",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(planning_data["htd"].lg_times_a(), endpoint=TIMEOUT),
        label="LG(htd)",
        linestyle="-",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(planning_data["tamaki"].lg_times_a(), endpoint=TIMEOUT),
        label="LG(Tamaki)",
        linestyle="-",
        linewidth=1,
    )

    for cv, style in [("MCS", "--"), ("LP", ":"), ("LM", "-."), ("MF", "-")]:
        for rank in ["BE", "BM"]:
            for choice in ["Tree"]:
                ax.plot(
                    *util.cactus(
                        planning_data["htb"].htb_times(cv, rank, choice),
                        endpoint=TIMEOUT,
                    ),
                    label=f"HTB({cv}, {rank})",
                    linestyle=style,
                    linewidth=1,
                )

    util.set_cactus_axes(ax, 200, TIMEOUT)


def gen(output):
    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_planning_exp(ax)
    f.save("6/figPlanning")

    f, ax = output.figure(0.45, ncols=1, nrows=1)
    plot_planning_a_exp(ax)
    f.save("6/figPlanningA")


if __name__ == "__main__":
    gen(util.output_pdf())
