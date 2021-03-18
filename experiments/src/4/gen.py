import gen_comparison_figures
import gen_execution_figures
import gen_planning_figures
import util


gen_comparison_figures.gen(util.output_pgf())
gen_execution_figures.gen(util.output_pgf())
gen_planning_figures.gen(util.output_pgf())
