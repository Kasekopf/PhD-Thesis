import importlib
import sys

sys.path.append("../")
gen_comparison_figures = importlib.import_module("6.gen_comparison_figures")
import util
import matplotlib.patheffects


ProjectedModelCounter = gen_comparison_figures.ProjectedModelCounter
counters = [
    ProjectedModelCounter(
        "dpmc/lg/flow/mcs0", "ProCount", {"linestyle": "-", "color": "#888888"},
    ),
    ProjectedModelCounter(
        "d4p0", "D4\\textsubscript{P}", {"linestyle": "-", "color": "#9090ff"},
    ),
    ProjectedModelCounter("projmc0", "projMC", {"linestyle": "-", "color": "#ffc000"},),
    ProjectedModelCounter("ssat0", "reSSAT", {"linestyle": "-", "color": "#cf2020"},),
]


def plot_comparison_exp(ax):
    for counter in counters:
        ax.plot(
            *util.cactus(
                gen_comparison_figures.counter_exps[counter.data_name].times(),
                endpoint=gen_comparison_figures.TIMEOUT,
            ),
            label=counter.label,
            linewidth=1,
            path_effects=[
                matplotlib.patheffects.Stroke(linewidth=1.5, foreground="#000000"),
                matplotlib.patheffects.Normal(),
            ],
            **counter.line,
        )

    vbs0 = util.vbs(
        *[
            gen_comparison_figures.counter_exps[counter.data_name].times()
            for counter in counters[1:]
        ]
    )
    ax.plot(
        *util.cactus(vbs0, endpoint=gen_comparison_figures.TIMEOUT),
        label="VBS0",
        linewidth=1,
        linestyle="--",
        color="#000000",
        path_effects=[
            matplotlib.patheffects.Stroke(linewidth=1.5, foreground="#000000"),
            matplotlib.patheffects.Normal(),
        ],
    )
    vbs1 = util.vbs(
        *[
            gen_comparison_figures.counter_exps[counter.data_name].times()
            for counter in counters
        ]
    )
    ax.plot(
        *util.cactus(vbs1, endpoint=gen_comparison_figures.TIMEOUT),
        label="VBS1",
        linewidth=1,
        linestyle=":",
        color="#000000",
        path_effects=[
            matplotlib.patheffects.Stroke(linewidth=1.5, foreground="#000000"),
            matplotlib.patheffects.Normal(),
        ],
    )
    util.set_cactus_axes(ax, 400, gen_comparison_figures.TIMEOUT, bottom=0.0005)


def gen(output):
    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_comparison_exp(ax)
    f.save("defense/projected")


if __name__ == "__main__":
    gen(util.output_pdf())
