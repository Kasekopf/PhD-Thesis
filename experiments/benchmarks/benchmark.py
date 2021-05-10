import collections
import os


class Benchmark(collections.abc.Mapping):
    def __init__(self, name, family, location=None):
        self.__name = name
        self.__family = family
        self.__location = name if location is None else location

    @property
    def name(self):
        return self.__name

    @property
    def family(self):
        return self.__family

    @property
    def args(self):
        return {"<": self.name, "|family": self.family}

    def is_trivial(self):
        with open(self.__location) as benchmark:
            for line in benchmark:
                if (
                    line.startswith("c UNSATISFIABLE")
                    or line.startswith("c Solved by preprocessing")
                    or line.startswith("c TIMEOUT")
                ):
                    return True
        return False

    def creation_time(self, on_timeout):
        """
        Get the preprocessing time for pmc_eq benchmarks
        """
        with open(self.__location) as benchmark:
            for line in benchmark:
                if line.startswith("c TIMEOUT"):
                    return on_timeout
                if line.startswith("c CPU time (sec.)"):
                    return float(line.split()[-1])
        return None

    def __len__(self):
        return self.args.__len__()

    def __getitem__(self, name):
        return self.args.__getitem__(name)

    def __iter__(self):
        return self.args.__iter__()


def list_benchmarks(folder, family):
    result = []
    for obj in os.listdir(folder):
        obj_path = folder + "/" + obj
        if os.path.isdir(obj_path):
            result += list_benchmarks(obj_path, family)
        elif (
            os.path.isfile(obj_path)
            and "README" not in obj
            and os.stat(obj_path).st_size > 2
        ):
            result.append(Benchmark(obj_path, family))
    return result


def load(folder):
    benchmarks = []
    for family in os.listdir(folder):
        if os.path.isdir(folder + "/" + family):
            benchmarks += list_benchmarks(folder + "/" + family, family)
    return benchmarks


def load_local(folder, prefix="benchmarks"):
    local_dir = os.path.dirname(__file__)
    benchmarks = load(os.path.join(local_dir, folder))
    return [
        Benchmark(
            prefix + "/" + os.path.relpath(b.name, local_dir).replace("\\", "/"),
            b.family,
            b.name,
        )
        for b in benchmarks
    ]


def load_from_list(list_path, weight_format_finder):
    result = []
    for line in open(os.path.join(os.path.dirname(__file__), list_path), "r"):
        if len(line) <= 1 or line.startswith("#"):
            continue
        result.append(Benchmark(line.strip(), "", weight_format_finder(line)))
    return result
