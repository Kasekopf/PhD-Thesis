import collections
import slurmqueen

import util


Planner = collections.namedtuple("Planner", ["name", "label", "color", "linestyle"])


planners = [
    Planner("factor-Tamaki", "T.", "#e0e0d0", "-"),
    Planner("factor-Flow", "FlowC.", "#f0a030", ":"),
    Planner("factor-htd", "htd", "#100010", "--"),
    Planner("factor-hicks", "Hicks", "#cf2020", ":"),
    Planner("factor-portfolio3", "P3", "#000060", "-"),
    Planner("factor-portfolio4", "P4", "#9090ff", "-"),
]


timeout = 1000


class PlanningData:
    def __init__(self, data_dir, planner):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)
        self.__planner = planner

    def load_ranks(self, at_time):
        data = self.__instance.query("SELECT [Log] FROM data ORDER BY [<] DESC")
        ranks = []
        for log in data["Log"]:
            if log is None:
                ranks.append(1000)
            else:
                found = 1000
                for time, widths, _ in eval(log):
                    if time < at_time:
                        found = min(found, widths["Carving"])
                ranks.append(found)
        return ranks

    def threshold_times(self, width, default_val=None):
        """
        For each log, find the time at which the solver first found a contraction tree of max-rank at or below [width].

        :param width: The bound on max-rank to check.
        :param default_val: The time to use if the solver never finds a good enough contraction tree
        :return: A list of times
        """
        data = self.__instance.query("SELECT [Log] FROM data ORDER BY [<] DESC")
        result = []
        for log in data["Log"]:
            best_width = None
            found = False
            if log is not None:
                for time, widths, FLOPS in eval(log):
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

    def find_planning_results(self, max_width):
        data = self.__instance.query("SELECT [Log], [store] FROM data")
        result = []
        for log, store in zip(data["Log"], data["store"]):
            if log is None:
                continue
            for i, entries in enumerate(eval(log)):
                if entries[1]["Carving"] <= max_width:
                    result.append({"<": store + "/" + str(i + 1) + ".con"})
        return result

    def generation_times(self):
        return self.__instance.query(
            "SELECT [Log], [<], [store] FROM data ORDER BY [<]"
        )


planning_data = {
    planner.name: PlanningData(
        util.data_dir("5/planning/" + planner.name + "/raw"), planner
    )
    for planner in planners
}


def compare(exp1, exp2, at_time, rank_cap=1000):
    res = [0, 0, 0]
    for r1, r2 in zip(exp1.load_ranks(at_time), exp2.load_ranks(at_time)):
        if r1 < r2 and r1 < rank_cap:
            res[0] += 1
        elif r1 == r2:
            res[1] += 1
        elif r2 < rank_cap:
            res[2] += 1
    return res


def plot_planning_exp(ax):
    times = []
    for planner in planners:
        planner_time = planning_data[planner.name].threshold_times(
            30, default_val=timeout
        )
        times.append(planner_time)
        ax.plot(
            *util.cactus(planner_time, endpoint=timeout),
            color=planner.color,
            linestyle=planner.linestyle,
            linewidth=2,
            label=planner.label,
        )

    ax.plot(
        *util.cactus(util.vbs(*times), endpoint=timeout),
        color="#000000",
        linestyle=":",
        linewidth=1,
        label="VBS",
    )
    util.set_cactus_axes(ax, 2000, timeout)


def gen(output):
    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_planning_exp(ax)
    f.save("5/planning")

    comparison = compare(
        planning_data["factor-portfolio3"], planning_data["factor-portfolio4"], 1000
    )
    print(
        "P3 is better on %d, P4 is better on %d after 1000 seconds"
        % (comparison[0], comparison[2])
    )


if __name__ == "__main__":
    gen(util.output_pdf())
