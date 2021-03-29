# Experiments and Figures
Code for generating all plots in the thesis. This requires the following python packages:
1. `matplotlib`
2. `slurmqueen`

## Setup
Experimental data and benchmarks must be downloaded separately. Expected file structure is:
```
experiments
|  data
|  |  3
|  |  4
|  |  5
|  |  6
|  benchmarks
|  |  cachet
|  |  cubic_vertex_cover
|  |  pseudoweighted
|  src
|  |  ...
```

## Usage
To generate all figures as .pgf in [/figures](../figures), use make:
```
make figures
```

The figure generation is individually done by chapter. For example, all figures for Chapter 3 can be generated with:
```
python 3/gen.py
```

Finally, individual figures can be rendered as .pdf for easy previewing. To do this, run python files individually:
```
python 3/gen_cachet.py
```