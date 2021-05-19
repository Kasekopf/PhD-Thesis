import collections
import importlib
import sys

sys.path.append("../")
gen_comparison_figures = importlib.import_module('5.gen_comparison_figures')
import util


# noinspection PyUnresolvedReferences
def plot_comparison_exp(ax, pmc_eq, which):
    configs = gen_comparison_figures.tensor_configs
    if pmc_eq:
        tensor_exps = gen_comparison_figures.tensor_pmc_experiments
        counter_exps = gen_comparison_figures.counter_pmc_experiments
        expected_number_dp = len(gen_comparison_figures.pmc_eq_benchmarks)
    else:
        tensor_exps = gen_comparison_figures.tensor_experiments
        counter_exps = gen_comparison_figures.counter_experiments
        expected_number_dp = len(gen_comparison_figures.raw_benchmarks)
    timeout = gen_comparison_figures.TIMEOUT

    Line = collections.namedtuple(
        "Line", ["display", "exp"]
    )

    lines = [
        Line({"color": "#ffffff", "linestyle": "-", "linewidth": 1, "label": "ADDMC"}, counter_exps["ADDMC"]),
        Line({"color": "#cf2020", "linestyle": "-", "linewidth": 1, "label": "gpusat2"}, counter_exps["gpusat2"]),
        Line({"color": "#ffc000", "linestyle": "-", "linewidth": 1, "label": "d4"}, counter_exps["d4"]),
        Line({"color": "#9090ff", "linestyle": "-", "linewidth": 1, "label": "miniC2D"}, counter_exps["miniC2D"]),
        Line({"color": "#000000", "linestyle": "--", "linewidth": 1.5, "label": "TensorOrder1 (CPU)"}, tensor_exps["CPU1/factor-Tamaki"]),
        Line({"color": "#000000", "linestyle": "-", "linewidth": 1, "label": "TensorOrder2 (GPU)"}, tensor_exps["GPU/factor-portfolio4"]),
        Line({"color": "#888888", "linestyle": "-", "linewidth": 1, "label": "DPMC"}, counter_exps["DPMC"]),
    ]

    if which == 0:
        # 0 presents only TensorOrder (CPU); removes DPMC and GPU
        lines.pop()
        lines.pop()
    if which == 1:
        # 1 presents up to DPMC; removes GPU
        lines.pop(-2)

    for line in lines:
        data = line.exp.load_count_data(expected_number_dp)
        if line.display["linestyle"] == "-":
            ax.plot(
                *util.cactus(data, endpoint=timeout), color="black", linewidth=1.5,
            )
        ax.plot(
            *util.cactus(data, endpoint=timeout),
            **line.display
        )

    # Plot dummy lines if needed to align legend entries
    if which == 0:
        ax.plot([0], [0], color='w', alpha=0, label=' ')
        ax.plot([0], [0], color='w', alpha=0, label=' ')
    if which == 1:
        ax.plot([0], [0], color='w', alpha=0, label=' ')

    util.set_cactus_axes(ax, 2000, timeout, legend_args={"ncol": 2, "loc": "upper left"})


def gen(output):
    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_comparison_exp(ax, pmc_eq=True, which=0)
    f.save("defense/ch1")

    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_comparison_exp(ax, pmc_eq=True, which=1)
    f.save("defense/ch2")

    f, ax = output.figure(0.4, ncols=1, nrows=1)
    plot_comparison_exp(ax, pmc_eq=True, which=2)
    f.save("defense/ch3")


if __name__ == "__main__":
    gen(util.output_pdf())
