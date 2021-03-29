import slurmqueen

import util

MAX_WIDTH = 30
TIMEOUT = 100


MCS_FLOW0 = slurmqueen.Experiment([]).instance(
    util.data_dir("6/execution/dmc/lg/flow/mcs0")
)
LP_FLOW0 = slurmqueen.Experiment([]).instance(
    util.data_dir("6/execution/dmc/lg/flow/lp0")
)
LM_FLOW0 = slurmqueen.Experiment([]).instance(
    util.data_dir("6/execution/dmc/lg/flow/lm0")
)
MF_FLOW0 = slurmqueen.Experiment([]).instance(
    util.data_dir("6/execution/dmc/lg/flow/mf0")
)

MCS_FLOW0_LAST = slurmqueen.Experiment([]).instance(
    util.data_dir("6/execution/dmc/lg/flow/t_mcs0")
)
LP_FLOW0_LAST = slurmqueen.Experiment([]).instance(
    util.data_dir("6/execution/dmc/lg/flow/t_lp0")
)
LM_FLOW0_LAST = slurmqueen.Experiment([]).instance(
    util.data_dir("6/execution/dmc/lg/flow/t_lm0")
)
MF_FLOW0_LAST = slurmqueen.Experiment([]).instance(
    util.data_dir("6/execution/dmc/lg/flow/t_mf0")
)


def getExecutionTimes(exp):
    return exp.query(
        """
        select * from data where time <= 100 and count > 0
    """
    )["time"].tolist()


def plot_execution_exp(ax):
    ax.plot(
        *util.cactus(getExecutionTimes(MCS_FLOW0), endpoint=TIMEOUT),
        label="MCS",
        linestyle="-",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(LP_FLOW0), endpoint=TIMEOUT),
        label="LP",
        linestyle="-",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(LM_FLOW0), endpoint=TIMEOUT),
        label="LM",
        linestyle="--",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(MF_FLOW0), endpoint=TIMEOUT),
        label="MF",
        linestyle="--",
        linewidth=1,
    )

    util.set_cactus_axes(ax, 400, TIMEOUT)


def plot_execution_a_exp(ax):
    ax.plot(
        *util.cactus(getExecutionTimes(MCS_FLOW0), endpoint=TIMEOUT),
        label="MCS, first",
        linestyle="-",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(LP_FLOW0), endpoint=TIMEOUT),
        label="LP, first",
        linestyle="-",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(LM_FLOW0), endpoint=TIMEOUT),
        label="LM, first",
        linestyle="--",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(MF_FLOW0), endpoint=TIMEOUT),
        label="MF, first",
        linestyle="--",
        linewidth=1,
    )

    ax.plot(
        *util.cactus(getExecutionTimes(MCS_FLOW0_LAST), endpoint=TIMEOUT),
        label="MCS, last",
        linestyle=":",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(LP_FLOW0_LAST), endpoint=TIMEOUT),
        label="LP, last",
        linestyle=":",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(LM_FLOW0_LAST), endpoint=TIMEOUT),
        label="LM, last",
        linestyle="-.",
        linewidth=1,
    )
    ax.plot(
        *util.cactus(getExecutionTimes(MF_FLOW0_LAST), endpoint=TIMEOUT),
        label="MF, last",
        linestyle="-.",
        linewidth=1,
    )

    util.set_cactus_axes(ax, 400, TIMEOUT)


def gen(output):
    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_execution_exp(ax)
    f.save("6/figExecution")

    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_execution_a_exp(ax)
    f.save("6/figExecutionA")


if __name__ == "__main__":
    gen(util.output_pdf())
