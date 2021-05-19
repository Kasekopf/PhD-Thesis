import collections
import math
import slurmqueen

import gen_planning_figures as planning
import util

Executor = collections.namedtuple("Executor", ["name", "label", "linestyle", "args"])


executors = [
    Executor("CPU1", "CPU1", "-", {"tensor_library": "numpy", "thread_limit": 1}),
    Executor("CPU8", "CPU8", ":", {"tensor_library": "numpy"}),
    Executor(
        "GPU",
        "GPU",
        "--",
        {"tensor_library": "tensorflow-gpu20", "mem_limit": 15676243968.0},
    ),
]

tensor_configs = [
    (planning.planners[0], executors[0]),
    (planning.planners[5], executors[0]),
    (planning.planners[5], executors[1]),
    (planning.planners[5], executors[2]),
]

TIMEOUT = 1000


class ExecutorData:
    def __init__(self, data_dir, planner, executor):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)
        self.__planner = planner
        self.__executor = executor

    def contraction_times(self):
        result = {}
        data = self.__instance.query(
            "SELECT [<], [Contraction Time], [Estimated FLOPs] FROM data"
        )
        for record, time in zip(data["<"], data["Contraction Time"]):
            result[record] = time
        return result

    def prepare_simulation(self, planning_exp):
        contraction_times = self.contraction_times()

        class ContractionTreeInfo:
            def __init__(self, log_entry, record):
                self.rank = log_entry[1]["Carving"]
                self.FLOPs = log_entry[2]
                self.time_generate = log_entry[0]
                if (
                    record in contraction_times
                    and str(contraction_times[record]) != "nan"
                ):
                    self.time_contract = contraction_times[record]
                else:
                    self.time_contract = TIMEOUT

            def __repr__(self):
                return str(
                    (self.rank, self.FLOPs, self.time_generate, self.time_contract)
                )

        data = planning_exp.generation_times()
        result = []
        for log, _, store in zip(data["Log"], data["<"], data["store"]):
            result.append([])
            if log is None:
                continue
            for i, entries in enumerate(eval(log)):
                result[-1].append(
                    ContractionTreeInfo(entries, store + "/" + str(i + 1) + ".con")
                )
        return result


executor_data = {
    (executor.name + "/" + planner.name): ExecutorData(
        util.data_dir(
            "5/performance_factor/" + executor.name + "/" + planner.name + "/raw"
        ),
        planner,
        executor,
    )
    for planner in planning.planners
    for executor in executors
}


def estimate(max_rank, performance_factor):
    def do(trees):
        stop_time = TIMEOUT
        finish_time = TIMEOUT
        for tree in trees:
            if tree.rank > max_rank:
                continue
            if stop_time < tree.time_generate:
                # Stop at the previous tree
                return finish_time
            else:
                stop_time = performance_factor * tree.FLOPs
                finish_time = max(stop_time, tree.time_generate) + tree.time_contract
        return finish_time

    return do


def do_simulation(data, strategy):
    return [strategy(d) for d in data]


def PAR2_score(analysis, contract, min_x, max_x, num_datapoints):
    data = contract.prepare_simulation(analysis)
    stride = (math.log2(max_x) - math.log2(min_x)) / (num_datapoints - 1)

    x_vals = []
    y_vals = []
    for i in range(num_datapoints):
        performance_factor = pow(2, math.log2(min_x) + i * stride)
        number_complete = 0
        for t in do_simulation(data, estimate(31, performance_factor)):
            if t < TIMEOUT:
                number_complete += t
            else:
                number_complete += 2 * TIMEOUT
        x_vals.append(performance_factor)
        y_vals.append(number_complete)
    return x_vals, y_vals


def completed_score(analysis, contract, min_x, max_x, num_datapoints):
    data = contract.prepare_simulation(analysis)
    stride = (math.log2(max_x) - math.log2(min_x)) / (num_datapoints - 1)

    x_vals = []
    y_vals = []
    for i in range(num_datapoints):
        performance_factor = pow(2, math.log2(min_x) + i * stride)
        number_complete = 0
        for t in do_simulation(data, estimate(31, performance_factor)):
            if t < TIMEOUT:
                number_complete += 1
        x_vals.append(performance_factor)
        y_vals.append(number_complete)
    return x_vals, y_vals


def compute_optimal_performance_factors(min_x, max_x, num_datapoints):
    result = {}
    for planner in planning.planners:
        for executor in executors:
            factors, pars = PAR2_score(
                planning.planning_data[planner.name],
                executor_data[executor.name + "/" + planner.name],
                min_x,
                max_x,
                num_datapoints,
            )
            result[planner.name + "/" + executor.name] = factors[pars.index(min(pars))]
    return result


def plot_performance_graph(ax, min_x, max_x, num_datapoints):
    for planner, executor in tensor_configs:
        ax.plot(
            *PAR2_score(
                planning.planning_data[planner.name],
                executor_data[executor.name + "/" + planner.name],
                min_x,
                max_x,
                num_datapoints,
            ),
            color=planner.color,
            linestyle=executor.linestyle,
            linewidth=2,
            label=planner.label + "+" + executor.label,
        )
    ax.set_xscale("log", nonpositive="mask")
    ax.set_xlim(left=min_x, right=max_x)
    ax.set_xlabel("Performance factor")
    ax.set_ylabel("Par-2 Score")
    util.set_legend(ax, loc="lower right")


def gen_performance_table():
    factors = compute_optimal_performance_factors(10 ** (-21), 1, 400)
    table = ""
    for planner in planning.planners:
        table += " & \\pkg{" + planner.label + "}"
    table += "\\\\ \\hline \n"
    for executor in executors:
        table += "\\pkg{" + executor.label + "}"

        for planner in planning.planners:
            factor = factors[planner.name + "/" + executor.name]
            table += " & $" + f"{factor:.2}".replace("e-", "\\cdot 10^{-") + "}$"
        table += "\\\\ \\hline \n"
    return table


def gen(output):
    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_performance_graph(ax, 10 ** (-21), 1, 400)
    ax.set_ylim(bottom=1000000, top=4000000)
    f.save("5/performance_factor")
    print(gen_performance_table())


if __name__ == "__main__":
    gen(util.output_pdf())
