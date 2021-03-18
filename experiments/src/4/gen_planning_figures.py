import collections
import slurmqueen

import util


Planner = collections.namedtuple("Planner", ["name", "line", "method"])
lg_planners = [
    Planner(
        "htd",
        {"label": "LG+htd", "color": "#ffd700", "linestyle": "--", "linewidth": 1},
        "LG",
    ),
    Planner(
        "flow",
        {
            "label": "LG+FlowCutter",
            "color": "#ffb14e",
            "linestyle": ":",
            "linewidth": 1,
        },
        "LG",
    ),
    Planner(
        "tamaki",
        {"label": "LG+Tamaki", "color": "#ea5f94", "linestyle": "-", "linewidth": 1},
        "LG",
    ),
]


htb_planners = [
    Planner(
        str(ch) + str(cv),
        {"color": "#c0c0ff", "linestyle": "-", "linewidth": 1},
        "HTB",
    )
    # ch and cv are ordered so that (4, -5) is drawn last
    for ch in [3, 5, 6, 4]
    for cv in [3, 4, 5, 6, -4, -6, -5]
]
htb_planners[-1].line.update({"label": "Best HTB", "color": "#20a9b4"})  # (4, -5)
htb_planners[0].line.update({"label": "Non-best HTB"})

planners = htb_planners + lg_planners

timeout = 100


class PlanningData:
    def __init__(self, data_dir, planner):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)
        self.__planner = planner

    def threshold_times(self, width, default_val=None):
        """
        For each log, find the time at which the solver first found a contraction tree of max-rank at or below [width].

        :param width: The bound on max-rank to check.
        :param default_val: The time to use if the solver never finds a good enough contraction tree
        :return: A list of times
        """
        data = self.__instance.query("SELECT [Log] FROM data ORDER BY [formula] DESC")
        result = []
        for log in data["Log"]:
            found = False
            if log is not None:
                for time, _, add_width, FLOPS in eval(log):
                    if add_width <= width:
                        result.append(time)
                        found = True
                        break
            if not found:
                result.append(default_val)
        return result

    def generation_times(self):
        if self.__planner.name in ["flow", "htd", "tamaki"]:
            return self.__instance.query(
                "SELECT [Log], [<], [store] FROM data ORDER BY [<]"
            )
        else:
            return self.__instance.query(
                "SELECT [Log], [cf] as [<], [store] FROM data ORDER BY [<]"
            )


planning_data = {
    planner.name: PlanningData(util.data_dir("4/planning/" + planner.name), planner)
    for planner in planners
}


def plot_planning_exp(ax):
    goal_width = 30
    for planner in planners:
        times = planning_data[planner.name].threshold_times(
            goal_width, default_val=timeout
        )
        ax.plot(*util.cactus(times, endpoint=timeout), **planner.line)
    util.set_cactus_axes(ax, 2000, timeout, bottom=0.0009)


def gen(output):
    f, ax = output.figure(ncols=1, nrows=1)
    plot_planning_exp(ax)
    f.save(0.4, "4/planning")


if __name__ == "__main__":
    gen(util.output_pdf())
