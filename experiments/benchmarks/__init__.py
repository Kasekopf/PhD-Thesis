from benchmarks.benchmark import *

# noinspection PyBroadException
try:
    cachet_raw = load_local("cachet/raw")
except:
    pass

# noinspection PyBroadException
try:
    cachet_pmc_eq = load_local("cachet/pmc_eq")
except:
    pass

# noinspection PyBroadException
try:
    pseudoweighted_raw = load_local("pseudoweighted/raw")
except:
    pass

# noinspection PyBroadException
try:
    pseudoweighted_pmc_eq = load_local("pseudoweighted/pmc_eq")
except:
    pass
