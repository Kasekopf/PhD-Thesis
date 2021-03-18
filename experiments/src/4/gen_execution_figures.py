import util
import config
import gen_planning_figures as planning
import math
import slurmqueen


class FullConfig:
    def __init__(self, planner, executer, color):
        self.planner = planner
        self.executer = executer
        self.name = executer.name + "/" + planner.name
        self.color = color


COSTS = {"tensor": lambda t: t.flops, "dmc": lambda t: 2 ** t.add}


full_configs = [
    FullConfig(config.planners[-4], config.executers[0], "blue"),
    FullConfig(config.planners[-2], config.executers[0], "green"),
    FullConfig(config.planners[-4], config.executers[1], "black"),
    FullConfig(config.planners[-2], config.executers[1], "orange"),
]


class ExecutionData:
    def __init__(self, data_dir, full_config):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)
        self.__full_config = full_config

    def get_contraction_times(self):
        contraction_times = {}
        if self.__full_config.executer.name == "tensor":
            data = self.__instance.query(
                "SELECT [<] as [Join Tree], [Total Time] FROM data WHERE Count > 0"
            )
        else:  # dmc
            data = self.__instance.query(
                "SELECT [jf] as [Join Tree], [Total time] AS [Total Time] FROM data WHERE Count > 0"
            )

        for record, time in zip(data["Join Tree"], data["Total Time"]):
            contraction_times[record.lstrip("/")] = time
        return contraction_times

    def prepare_simulation(self):
        contraction_times = self.get_contraction_times()

        class JoinTreeInfo:
            def __init__(self, log_entry, record):
                self.time_generate = log_entry[0]
                self.add = log_entry[1]
                self.tensor = log_entry[2]
                self.flops = log_entry[3]
                if record[0] == "/":
                    record = record[1:]
                if (
                    record in contraction_times
                    and str(contraction_times[record]) != "nan"
                ):
                    self.time_contract = contraction_times[record]
                else:
                    self.time_contract = 100

            def __repr__(self):
                return str(
                    (
                        self.time_generate,
                        self.add,
                        self.tensor,
                        self.flops,
                        self.time_contract,
                    )
                )

        gen_time = planning.planning_data[
            self.__full_config.planner.name
        ].generation_times()
        result = []
        for log, _, store in zip(gen_time["Log"], gen_time["<"], gen_time["store"]):
            result.append([])
            if log is None:
                continue
            for i, entries in enumerate(eval(log)):
                result[-1].append(
                    JoinTreeInfo(entries, store + "/" + str(i + 1) + ".jt")
                )
        return result


execution_data = {
    full.name: ExecutionData(util.data_dir("4/execution/" + full.name), full)
    for full in full_configs
}

timeout = 100


def estimate(performance_factor, cost_function):
    def do(trees):
        stop_time = timeout
        finish_time = timeout
        for tree in trees:
            if stop_time < tree.time_generate:
                # Stop at the previous tree
                return finish_time
            else:
                stop_time = performance_factor * cost_function(tree)
                finish_time = max(stop_time, tree.time_generate) + tree.time_contract
        return finish_time

    return do


def first():
    def do(trees):
        finish_time = timeout
        for tree in trees[:1]:
            finish_time = tree.time_generate + tree.time_contract
        return finish_time

    return do


def best():
    def do(trees):
        finish_time = timeout
        for tree in trees:
            finish_time = min(finish_time, tree.time_generate + tree.time_contract)
        return finish_time

    return do


def do_simulation(data, strategy):
    return [strategy(d) for d in data]


def PAR2_score(full, min_x, max_x, num_datapoints):
    data = execution_data[full.name].prepare_simulation()
    stride = (math.log2(max_x) - math.log2(min_x)) / (num_datapoints - 1)

    x_vals = []
    y_vals = []
    for i in range(num_datapoints):
        performance_factor = pow(2, math.log2(min_x) + i * stride)
        number_complete = 0
        for t in do_simulation(
            data, estimate(performance_factor, COSTS[full.executer.name])
        ):
            if t < timeout:
                number_complete += t
            else:
                number_complete += 2 * timeout
        x_vals.append(performance_factor)
        y_vals.append(number_complete)
    return x_vals, y_vals


def completed_score(full, min_x, max_x, num_datapoints):
    data = execution_data[full.name].prepare_simulation()
    stride = (math.log2(max_x) - math.log2(min_x)) / (num_datapoints - 1)

    x_vals = []
    y_vals = []
    for i in range(num_datapoints):
        performance_factor = pow(2, math.log2(min_x) + i * stride)
        number_complete = 0
        for t in do_simulation(
            data, estimate(performance_factor, COSTS[full.executer.name])
        ):
            if t < timeout:
                number_complete += 1
        x_vals.append(performance_factor)
        y_vals.append(number_complete)
    return x_vals, y_vals


def compute_optimal_performance_factors(min_x, max_x, num_datapoints):
    result = {}
    for full in full_configs:
        if full.planner.name in ["htd", "flow", "tamaki"]:
            perf_factors, pars = PAR2_score(full, min_x, max_x, num_datapoints,)
            result[full.name] = perf_factors[pars.index(min(pars))]
    return result


def plot_line(ax, full, strategy, **kwargs):
    data = execution_data[full.name].prepare_simulation()
    result = do_simulation(data, strategy)
    ax.plot(*util.cactus(result), **kwargs)
    return result


def plot_exec_experiments(ax, factors):
    datas = []
    dmc_datas = []
    for full in full_configs:
        label = full.executer.label + "+" + full.planner.method
        if full.planner.name in ["htd", "flow", "tamaki"]:
            plot_line(
                ax,
                full,
                first(),
                label=label + " (first)",
                linestyle="--",
                color=full.color,
                linewidth=1,
            )
            res = plot_line(
                ax,
                full,
                estimate(factors[full.name], COSTS[full.executer.name]),
                label=label + " (cost)",
                linestyle="-",
                color=full.color,
                linewidth=1,
            )
            plot_line(
                ax,
                full,
                best(),
                label=label + " (best)",
                linestyle=":",
                color=full.color,
                linewidth=1,
            )
        else:
            res = plot_line(
                ax,
                full,
                first(),
                label=label,
                linestyle="-",
                color=full.color,
                linewidth=1,
            )
        datas.append(res)
        if full.executer.name == "dmc":
            dmc_datas.append(res)

    ax.plot(
        *util.cactus(util.vbs(*dmc_datas)),
        label="VBS*",
        linewidth=1,
        color="black",
        linestyle="--",
    )
    ax.plot(
        *util.cactus(util.vbs(*datas)),
        label="VBS",
        linewidth=1,
        color="black",
        linestyle=":",
    )
    util.set_cactus_axes(ax, 2000, timeout, bottom=0.005)  # , legend_args={"ncol": 2})


def gen_performance_table():
    factors = compute_optimal_performance_factors(10 ** (-21), 1, 400)
    table = ""
    for planner in config.planners:
        table += " & \\pkg{" + planner.label + "}"
    table += "\\\\ \\hline \n"
    for executer in config.executers:
        table += "\\pkg{" + executer.label + "}"

        for planner in config.planners:
            factor = factors[planner.name + "/" + executer.name]
            table += " & $" + f"{factor:.2}".replace("e-", "\cdot 10^{-") + "}$"
        table += "\\\\ \\hline \n"
    return table


def gen(output):
    factors = compute_optimal_performance_factors(10 ** (-29), 1, 150)
    print(factors)
    f, ax = output.figure(ncols=1, nrows=1)
    plot_exec_experiments(ax, factors=factors)
    f.save(0.4, "4/execution")


if __name__ == "__main__":
    gen(util.output_pdf())

    # x, y = PAR2_score(full_configs[-1], 10 ** (-29), 1, 150)
    # for i, j in zip(x, y):
    #    print(str(i) + " --- " + str(j))

    # print(full_configs[-1].name)
    # print(gen_performance_table())
