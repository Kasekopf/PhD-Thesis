import igraph
import os
import random

"""
This file generates benchmark CNF files that count the number of vertex covers of randomly-generated cubic graphs.

The connected cubic graphs are randomly sampled using a Monte Carlo procedure, as implemented in igraph and described in
  Viger, F., and Latapy, M. 2005. Efficient and simple generation of random simple connected graphs with prescribed
  degree sequence. In Proc. of COCOON, 440–449
"""


FOLDER = "./cubic_vertex_cover"  # The folder in which to output all benchmarks


if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)


def save_cubic_cnf(num_vertices, filename):
    """
    Generate a random cubic graph, generate a CNF whose number of solutions is the number of vertex covers of the graph,
    and write the CNF to the provided file.

    Equivalently, produces monotone 2-CNF formulas in which every variable appears 3 times.

    :param num_vertices: The number of vertices in the graph
    :param filename: A file to write the generated CNF
    :return: None.
    """
    with open(filename, "w") as cnf_file:
        g = igraph.Graph.Degree_Sequence([3] * num_vertices, method="vl")
        cnf_file.write(
            "p cnf " + str(num_vertices) + " " + str(3 * int(num_vertices / 2)) + "\n"
        )
        for e in g.es:
            cnf_file.write(str(e.source + 1) + " " + str(e.target + 1) + " 0\n")


random.seed(3141592653)  # First 10 digits of pi

for num_vars in range(50, 260, 10):
    for instance in range(100):
        save_cubic_cnf(num_vars, FOLDER + "/cubic_vc_%d_%d.cnf" % (num_vars, instance))
