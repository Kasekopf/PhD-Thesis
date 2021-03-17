import pathlib
import util


def data_dir(path):
    """
    Get the directory to locate data (default ../../data/[path]).
    """
    return pathlib.Path(__file__).parent.parent.absolute() / "data" / path


def benchmark_dir(path):
    """
    Get the directory to locate benchmarks (default ../../benchmark/[path]).
    """
    return pathlib.Path(__file__).parent.parent.absolute() / "benchmark" / path


def output_pdf():
    """
    Get a way to output figures as PDF (default ../../figures_pdf).
    """
    return util.FigureOutput(
        "pdf", pathlib.Path(__file__).parent.parent.absolute() / "figures_pdf"
    )


def output_pgf():
    """
    Get a way to output figures as .pgf (default ../../../figures).
    """
    return pathlib.Path(__file__).parent.parent.parent.absolute() / "figures_pgf"
