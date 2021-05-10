import collections
import slurmqueen
import sys

sys.path.append("../../")
# noinspection PyUnresolvedReferences
import benchmarks  # See ../../benchmarks
import gen_planning_figures as planning
import gen_execution_figures as executing
import util

TIMEOUT = 1000


# Benchmark info
raw_benchmarks = benchmarks.cachet_raw + benchmarks.pseudoweighted_raw
pmc_eq_benchmarks = [
    b
    for b in benchmarks.cachet_pmc_eq + benchmarks.pseudoweighted_pmc_eq
    if not b.is_trivial()
]
pmc_eq_benchmarks_trivial = [
    b
    for b in benchmarks.cachet_pmc_eq + benchmarks.pseudoweighted_pmc_eq
    if b.is_trivial()
]

preprocessing_time = {b.name: b.creation_time(TIMEOUT) for b in pmc_eq_benchmarks}


# Configuration info
tensor_configs = [
    # Planner, hardware, optimal performance factor
    (planning.planners[0], executing.executors[0], 3.7926901907322575e-11),
    (planning.planners[5], executing.executors[0], 1.623776739188719e-11),
    (planning.planners[5], executing.executors[1], 6.1584821106602706e-12),
    (planning.planners[5], executing.executors[2], 3.792690190732259e-12),
]

ModelCounter = collections.namedtuple(
    "ModelCounter", ["name", "other_args", "command", "line"]
)

weighted_counters = [
    ModelCounter(
        "miniC2D",
        {"weighted": True},
        "python /wrappers/miniC2D_wrapper.py",
        {"color": "#cf2020", "linestyle": "-"},
    ),
    ModelCounter(
        "d4",
        {"weighted": True},
        "python /wrappers/d4_wrapper.py",
        {"color": "#cf2020", "linestyle": "--"},
    ),
    ModelCounter(
        "cachet",
        {"weighted": True, "fix_normalize": False},
        "python /wrappers/cachet_wrapper.py",
        {"color": "#cf2020", "linestyle": ":"},
    ),
    ModelCounter(
        "ADDMC",
        {"weighted": True},
        "python /wrappers/ADDMC_wrapper.py",
        {"color": "#100010", "linestyle": "-"},
    ),
    ModelCounter(
        "gpusat2",
        {"weighted": True, "flags": "--NVIDIA --seed 1234567"},
        "python /wrappers/gpusat2_wrapper.py",
        {"color": "#000000", "linestyle": "--"},
    ),
    ModelCounter(
        "DPMC",
        {},
        "python /wrappers/dpmc_wrapper.py.py",
        {"color": "#000000", "linestyle": ":"},
    ),
]


# Data
class ComparisonData:
    def __init__(self, data_dir):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)

    def load_count_data(self, expected=None):
        data = self.__instance.query("SELECT [Count], [Total Time], [<] FROM data")
        # Set the total time to TIMEOUT for all experiments that did not return a count (includes timeout, memout, etc.)
        data.loc[data["Count"].isnull(), "Total Time"] = TIMEOUT
        data.loc[data["Total Time"].isnull(), "Total Time"] = TIMEOUT
        data.loc[data["Total Time"] > TIMEOUT, "Total Time"] = TIMEOUT

        # ADDMC and DPMC easily underflow, which we could as failures
        if "ADDMC" in self.__instance._local_directory or 'DPMC' in self.__instance._local_directory:
            data.loc[data["Count"] == '0', "Total Time"] = TIMEOUT
            data.loc[data["Count"] == '0.0', "Total Time"] = TIMEOUT

        if expected is not None and len(data) != expected:
            print(
                "Only {0}/{1} datapoints observed for {2}".format(
                    len(data), expected, self.__instance._local_directory
                )
            )

        data = data.sort_values("<")
        times = []
        if self.__instance._local_directory.endswith("/pmc_eq"):
            times = []
            for benchmark, time in zip(data["<"], data["Total Time"]):
                # For pmc_eq benchmarks, take into account preprocessing time
                times.append(time + preprocessing_time[benchmark])
            times.extend(b.creation_time(TIMEOUT) for b in pmc_eq_benchmarks_trivial)
            return times
        else:
            return list(data["Total Time"])

    def query(self, query):
        return self.__instance.query(query)

    def num_solved(self):
        times = self.load_count_data()
        return sum(1 if t < TIMEOUT else 0 for t in times)

    def num_fastest(self, vbs):
        times = self.load_count_data()
        return sum(1 if d == v and d < TIMEOUT else 0 for d, v in zip(times, vbs))

    def par2(self):
        times = self.load_count_data()
        total = 0
        for t in times:
            if t < TIMEOUT:
                total += t
            else:
                total += 2 * TIMEOUT
        return total


tensor_experiments = {
    (executor.name + "/" + planner.name): ComparisonData(
        util.data_dir(
            "5/comparison/TensorOrder/" + executor.name + "/" + planner.name + "/raw"
        )
    )
    for planner, executor, factor in tensor_configs
}

tensor_pmc_experiments = {
    (executor.name + "/" + planner.name): ComparisonData(
        util.data_dir(
            "5/comparison/TensorOrder/" + executor.name + "/" + planner.name + "/pmc_eq"
        )
    )
    for planner, executor, factor in tensor_configs
}

counter_experiments = {
    counter.name: ComparisonData(util.data_dir("5/comparison/" + counter.name + "/raw"))
    for counter in weighted_counters
}

counter_pmc_experiments = {
    counter.name: ComparisonData(
        util.data_dir("5/comparison/" + counter.name + "/pmc_eq")
    )
    for counter in weighted_counters
}


def plot_comparison_exp(tensor_exps, counter_exps, configs, ax, expected_number_dp):
    datas = []
    for planner, executor, factor in configs:
        data = tensor_exps[executor.name + "/" + planner.name].load_count_data(
            expected_number_dp
        )

        datas.append(data)
        ax.plot(
            *util.cactus(data, endpoint=TIMEOUT),
            color=planner.color,
            linestyle=executor.linestyle,
            linewidth=1,
            label=planner.label + "+" + executor.label,
        )

    for counter in weighted_counters:
        data = counter_exps[counter.name].load_count_data(expected_number_dp)
        datas.append(data)
        ax.plot(
            *util.cactus(data, endpoint=TIMEOUT),
            **counter.line,
            linewidth=1,
            label=counter.name,
        )

    util.set_cactus_axes(ax, 2000, TIMEOUT, legend_args={"ncol": 1})
    return util.vbs(*datas)


def gen_fastest_table(vbs_nopmc, vbs_pmc):
    table = ""
    for col in [
        "\\# Fastest",
        "\\# Solved",
        "PAR-2 Score",
        "\\# Fastest",
        "\\# Solved",
        "PAR-2 Score",
    ]:
        table += " & " + col
    table += "\\\\ \\hline \n"

    exps = []
    for planner, executor, factor in tensor_configs:
        exps.append(
            (
                "\\pkg{" + planner.label + "}+\\pkg{" + executor.label + "}",
                tensor_experiments[executor.name + "/" + planner.name],
                tensor_pmc_experiments[executor.name + "/" + planner.name],
            )
        )

    for counter in weighted_counters:
        exps.append(
            (
                "\\tool{" + counter.name + "}",
                counter_experiments[counter.name],
                counter_pmc_experiments[counter.name],
            )
        )

    def format_par2(exp):
        return str(round(exp.par2())) + "."

    for name, exp1, exp2 in exps:
        table += name + " & "
        table += str(exp1.num_fastest(vbs_nopmc)) + " & "
        table += str(exp1.num_solved()) + " & "
        table += format_par2(exp1) + " & "
        table += str(exp2.num_fastest(vbs_pmc)) + " & "
        table += str(exp2.num_solved()) + " & "
        table += format_par2(exp2)
        table += "\\\\ \\hline \n"
    return table


def gen(output):
    f, axs = output.figure(0.9, ncols=1, nrows=2)
    vbs_nopmc = plot_comparison_exp(
        tensor_experiments,
        counter_experiments,
        tensor_configs,
        axs[0],
        len(raw_benchmarks),
    )
    vbs_pmc = plot_comparison_exp(
        tensor_pmc_experiments,
        counter_pmc_experiments,
        tensor_configs,
        axs[1],
        len(pmc_eq_benchmarks),
    )[: -len(pmc_eq_benchmarks_trivial)]
    f.save("5/comparison_all")

    print(gen_fastest_table(vbs_nopmc, vbs_pmc))


if __name__ == "__main__":
    gen(util.output_pdf())
