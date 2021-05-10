    dir_name = "C:/Work/Projects/PhD-Thesis/experiments/data/5/comparison/DPMC/pmc_eq"
    def move(loc, to):
        from shutil import copyfile
        if loc == to:
            return
        loc_id = str(loc).zfill(4)
        to_id = str(to).zfill(4)

        # Read in [loc].in
        with open(dir_name + "/" + loc_id + ".in", 'r') as file:
            filedata = file.read()

        # Replace [loc] with [to] in [loc].in
        filedata = filedata.replace(loc_id + '.out', to_id + '.out')
        filedata = filedata.replace(loc_id + '.log', to_id + '.log')

        # Rewrite to [to].in
        with open(dir_name + "/" + to_id + ".in", 'w') as file:
            file.write(filedata)

        # Move [loc].out to [to].out and [loc].log to [to].log
        copyfile(dir_name + "/" + loc_id + ".out", dir_name + "/" + to_id + ".out")
        copyfile(dir_name + "/" + loc_id + ".log", dir_name + "/" + to_id + ".log")

    trivial_benchmarks = []
    for b in pmc_eq_benchmarks_trivial:
        trivial_benchmarks.append(b.name)

    j = 0
    for i in range(1914):
        with open(dir_name + "/" + str(i).zfill(4) + ".out") as f:
            params = eval(f.readline())
        if params['<'] not in trivial_benchmarks:
            move(i, j)
            print(str(i) + " -> " + str(j))
            j += 1