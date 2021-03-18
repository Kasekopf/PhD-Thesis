import collections

from experiment import Arg, Command

EXPERIMENT_DIR = "data"

timeout = 1000

Planner = collections.namedtuple(
    "Planner", ["name", "command", "make_benchmark_arg", "line", "method"]
)


lg_planners = [
    Planner(
        "htd",
        Command(
            "./lg.sif",
            Arg.positional(
                "/solvers/htd-master/bin/htd_main -s 1234567 --opt width --iterations 0 --strategy challenge --print-progress --preprocessing full"
            ),
        ),
        lambda b: Arg.redirection("<", b.name),
        {"label": "LG+htd", "color": "#ffd700", "linestyle": "--", "linewidth": 1},
        "LG",
    ),
    Planner(
        "flow",
        Command(
            "./lg.sif",
            Arg.positional(
                "/solvers/flow-cutter-pace17/flow_cutter_pace17 -s 3141592 -p 100"
            ),
        ),
        lambda b: Arg.redirection("<", b.name),
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
        Command(
            "./lg.sif",
            Arg.positional(
                "java -classpath /solvers/TCS-Meiji -Xmx25g -Xms25g -Xss1g tw.heuristic.MainDecomposer -s 3141592 -p 100"
            ),
        ),
        lambda b: Arg.redirection("<", b.name),
        {"label": "LG+Tamaki", "color": "#ea5f94", "linestyle": "-", "linewidth": 1},
        "LG",
    ),
]


htb_planners = [
    Planner(
        str(ch) + str(cv),
        Command(
            "singularity run --bind benchmarks:benchmarks htb.sif",
            ch=ch,
            cv=cv,
            wf=3,
            rs=3141592,
        ),
        lambda b: Arg("cf", "/" + b.name),
        {"label": "Best HTB", "color": "#20a9b4", "linestyle": "-", "linewidth": 1}
        if ch == 4 and cv == -5
        else {
            "label": "Non-best HTB",
            "color": "#c0c0ff",
            "linestyle": "-",
            "linewidth": 1,
        }
        if ch == 3 and cv == 3
        else {"color": "#c0c0ff", "linestyle": "-", "linewidth": 1},
        "HTB",
    )
    # ch and cv are ordered so that (4, -5) is drawn last
    for ch in [3, 5, 6, 4]
    for cv in [3, 4, 5, 6, -4, -6, -5]
]

planners = htb_planners + lg_planners


class TensorExecutor:
    def __init__(self):
        self.name = "tensor"
        self.label = "tensor"

    def make_isolated_command(self, formula, join_tree, join_tree_time, timeout):
        return Command(
            "singularity run --bind benchmarks:benchmarks tensor.sif",
            Arg("timeout", timeout),
            Arg("thread_limit", 1),
            Arg("formula", formula),
            Arg.redirection("<", join_tree),
            Arg.private("|jt_time", join_tree_time),
        )

    def make_command(self, formula, performance_factor, timeout):
        return Command(
            "singularity run --bind benchmarks:benchmarks tensor.sif",
            Arg("timeout", timeout),
            Arg("thread_limit", 1),
            Arg("formula", "/" + formula),
            Arg("performance_factor", performance_factor),
        )


class DMCExecutor:
    def __init__(self):
        self.name = "dmc"
        self.label = "DMC"

    def make_isolated_command(self, formula, join_tree, join_tree_time, timeout):
        return Command(
            "timeout",
            str(timeout),
            "singularity run --bind benchmarks:benchmarks --bind store:store dmc.sif",
            Arg("wf", 2),
            Arg("dv", -4),
            Arg("cf", formula),
            Arg("jf", "/" + join_tree),
            Arg.private("|jt_time", join_tree_time),
        ) | Command("python dmc_process.py")

    def make_command(self, formula, performance_factor, timeout):
        return Command(
            "timeout",
            str(timeout),
            "singularity run --bind benchmarks:benchmarks --bind store:store dmc.sif",
            Arg("wf", 2),
            Arg("dv", -4),
            Arg("pf", performance_factor),
            Arg("jw", 1000),
            Arg("jf", "-"),
            Arg("cf", "/" + formula),
        ) | Command("python dmc_process.py")


executers = [TensorExecutor(), DMCExecutor()]
