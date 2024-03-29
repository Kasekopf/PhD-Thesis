import matplotlib as mpl
import os


def set_figure_size(height_ratio, width=433.62, overrides=None):
    """
    Set the figure size used to export matplotlib figures.

    :param height_ratio: The desired ratio of height to width
    :param width: The width to use for the figure (in pts). \the\textwidth is a good start
    :param overrides: Arguments passed (as overrides) to mpl.rcParams.update
    :return:
    """
    inches_per_pt = 1.0 / 72.27  # Convert pt to inch

    # INCLUDED FROM http://bkanuka.com/articles/native-latex-plots/
    pgf_with_latex = {  # setup matplotlib to use latex for output
        "pgf.texsystem": "pdflatex",  # change this if using xetex or lautex
        "text.usetex": True,  # use LaTeX to write all text
        "font.family": "serif",
        "font.serif": [],  # blank entries should cause plots to inherit fonts from the document
        "font.sans-serif": [],
        "font.monospace": [],
        "axes.labelsize": 10,  # LaTeX default is 10pt font.
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.figsize": [
            width * inches_per_pt,
            width * inches_per_pt * height_ratio + 0.1,
        ],
        "pgf.preamble": "\n".join(
            [
                r"\usepackage[utf8x]{inputenc}",  # use utf8 fonts becasue your computer can handle it :)
                r"\usepackage[T1]{fontenc}",  # plots will be generated using this preamble
            ]
        ),
    }

    if overrides is not None:
        for key in overrides:
            pgf_with_latex[key] = overrides[key]
    mpl.rcParams.update(pgf_with_latex)


def cactus(times, endpoint=None):
    """
    Given a list of times, construct a cactus plot for these times.

    :param times: A list of timestamps
    :param endpoint: If given, add an additional point at (#[times < endpoint], [endpoint])
    :return:
    """
    x, y = [], []
    i = 0
    for i, time in enumerate(sorted(times)):
        if endpoint and time >= endpoint:
            break
        x += [i]
        y += [time]
    if endpoint:
        x += [i]
        y += [endpoint]
    return x, y


def vbs(*times_by_solver):
    """
    Given a list of lists of times, each representing the performance of one solver on the benchmark set,
    construct the VBS of those times.

    Running times must be sorted by benchmark name.

    :param times_by_solver: A list of lists of times
    :return: A list of times, indicating the performance of the VBS
    """
    return [min(times_by_benchmark) for times_by_benchmark in zip(*times_by_solver)]


def set_legend(ax, **legend_args):
    """
    Create a legend in a uniform style
    :param ax: The graph to use
    :param legend_args: A dictionary of extra parameters for the legend
    :return: None
    """
    default_legend_args = {
        "borderaxespad": 0,
        "handletextpad": 0.2,
        "labelspacing": 0.4,
        "handlelength": 2,
        "frameon": False,
        "loc": "lower right",
    }
    default_legend_args.update(legend_args)
    ax.legend(**default_legend_args)


def set_cactus_axes(ax, num_benchmarks, timeout, legend_args=None, bottom=0.005):
    """
    Set up a graph as a cactus plot.

    :param ax: The graph to use
    :param num_benchmarks: The maximum number of benchmarks (right edge of graph)
    :param timeout: The maximum running time (top of graph)
    :param legend_args: A dictionary of extra parameters for the legend
    :param bottom: The bottom of the y-axis (default: 0.005)
    :return: None
    """
    if legend_args is None:
        legend_args = {}
    ax.set_yscale("log", nonpositive="mask")
    ax.set_ylim(bottom=bottom, top=timeout)
    ax.set_xlim(left=0, right=num_benchmarks)

    ax.set_ylabel("Longest solving time (s)")
    ax.set_xlabel("Number of benchmarks solved")
    set_legend(ax, **legend_args)


class Figure:
    def __init__(self, base, base_dir, suffix):
        self.__base = base
        self.__base_dir = base_dir
        self.__suffix = suffix

    def save(self, name, verbose=True):
        """
        Save this figure to a file, relative to the output directory.

        :param name: String name to save to (file type will be added)
        :param verbose: True if confirmation should be printed
        :return:
        """
        self.__base.tight_layout()
        path = self.__base_dir / (name + "." + self.__suffix)
        if not os.path.exists(path.parent):
            os.makedirs(path.parent)
        self.__base.savefig(path)
        if verbose:
            print(
                'Saved File "' + str(path) + '", line 1'
            )  # Generates clickable link in PyCharm


class FigureOutput:
    def __init__(self, fig_type, base_dir):
        mpl.use(fig_type)
        import matplotlib.pyplot as plt

        self.__plt = plt
        self.__base_dir = base_dir
        self.__suffix = fig_type

    def figure(self, height_ratio, *args, **kwargs):
        """
        Create a new Figure.

        Matplotlib is somewhat stateful, so it is best to finish and save a Figure before creating the next.

        :param height_ratio: The ratio of height/width to use
        :param args: Passed to matplotlib.pyplot.subplots (typically nco
        :param kwargs: Passed to matplotlib.pyplot.subplots (typically 'ncol' or 'nrow')
        :return: A new Figure object to use, together with the axes of the figure
        """
        set_figure_size(height_ratio)
        f, axs = self.__plt.subplots(*args, **kwargs)
        return Figure(f, self.__base_dir, self.__suffix), axs
