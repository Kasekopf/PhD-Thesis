import slurmqueen
import util
import config

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

    def load_all_trees(self, executor):
        data = self.__instance.query("SELECT [formula], [Log], [store] FROM data")
        for formula, store, raw_log in zip(data["formula"], data["store"], data["Log"]):
            if raw_log is None:
                continue
            log = eval(raw_log)
            for i, entry in enumerate(log):
                yield [
                    *executor.valuate_args(
                        formula, store.lstrip("/") + "/" + str(i + 1) + ".jt"
                    ),
                    slurmqueen.experiment.Arg.private("|jt_time", entry[0]),
                ]


planning_data = {
    planner.name: PlanningData(util.data_dir("4/planning/" + planner.name), planner)
    for planner in config.planners
}


def plot_planning_exp(ax):
    goal_width = 30
    for planner in config.planners:
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
