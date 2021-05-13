import collections

import util
import slurmqueen


SLICE_CUTOFF = 80


class SliceData:
    def __init__(self, data_dir, num_cores):
        self.__instance = slurmqueen.Experiment("", []).instance(data_dir)
        self.__num_cores = num_cores

    def slice_round_times(self):
        """
        Return: A dict mapping rank_limit to a list of times for each slice round
        """
        num_slice_rounds = int(SLICE_CUTOFF / self.__num_cores)
        col_names = ["Slice " + str(i + 1) + " Time" for i in range(num_slice_rounds)]
        data = self.__instance.query("SELECT * FROM data")

        data_slice_times = [data[c] for c in col_names]
        return {row[0]: row[1:] for row in zip(data["rank_limit"], *data_slice_times)}

    def avg_time_per_slice_from_total(self):
        data = self.__instance.query("SELECT * FROM data")
        res = {}
        for rank, time in zip(data["rank_limit"], data["Contraction Time"]):
            res[rank] = time / SLICE_CUTOFF
        return res

    def avg_time_per_slice(self):
        slice_round_times = self.slice_round_times()
        res = {}
        for rank in slice_round_times:
            total_time = sum(slice_round_times[rank][1:])
            num_slices = self.__num_cores * (len(slice_round_times[rank]) - 1)
            res[rank] = total_time / num_slices
        return res

    def compilation_time(self):
        slice_round_times = self.slice_round_times()
        time_per_slice = self.avg_time_per_slice()
        return {
            rank: slice_round_times[rank][0] - time_per_slice[rank] * self.__num_cores for rank in slice_round_times
        }


jax_cpu = SliceData(util.data_dir("5/tpu/jax_cpu"), 1)
jax_tpu = SliceData(util.data_dir("5/tpu/jax_tpu"), 8)
numpy = SliceData(util.data_dir("5/tpu/numpy"), 1)


def gen(output):
    f, ax = output.figure(0.45, ncols=1, nrows=1)

    DisplayInfo = collections.namedtuple(
        "DisplayInfo", ["name", "data", "color", "marker"]
    )
    lines = [
        DisplayInfo("Compile (TPU8-graph)", jax_tpu.compilation_time(), "#ffb14e", "p"),
        DisplayInfo("Compile (CPU8-graph)", jax_cpu.compilation_time(), "#0000dd", "p"),
        DisplayInfo("Execute (TPU8-graph)", jax_tpu.avg_time_per_slice(), "#ffb14e", "P"),
        DisplayInfo("Execute (CPU8-graph)", jax_cpu.avg_time_per_slice(), "#0000dd", "P"),
        DisplayInfo("Execute (CPU8)", numpy.avg_time_per_slice_from_total(), "#dd0f0f", "o"),
    ]

    for exp_info in lines:
        ax.plot(
            exp_info.data.keys(),
            exp_info.data.values(),
            color=exp_info.color,
            linewidth=1,
            markersize=5,
            markerfacecolor=exp_info.color,
            markeredgewidth=0.5,
            markeredgecolor="black",
            marker=exp_info.marker,
            label=exp_info.name,
        )

    ax.set_yscale("log", nonpositive="mask")
    ax.set_ylim(bottom=0.00001, top=1000)
    ax.set_xlim(left=9, right=21)
    ax.set_ylabel("Time (s)")
    ax.set_xlabel("$k$: Sliced Max Rank")
    util.set_legend(ax, loc="lower left", ncol=3, columnspacing=1.8)

    f.save("5/tpu")


if __name__ == "__main__":
    gen(util.output_pdf())
