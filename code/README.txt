Code used in the term paper "Memory Consistency Models" (SC, TSO, PSO)

Q1 (Python, no installs needed):
  python3 checker.py      the axiomatic checker (uses graph.py, sc.py, tso.py, pso.py, tests.py)
  python3 sb_machine.py   store-buffer simulation, compared with the checker

Q2 (needs an x86 Linux machine with gcc):
  bash run_litmus.sh      compiles and runs litmus.c
  python3 summarise.py    summarises the raw results

Q3:
  python3 cpi_model.py    the cycle-by-cycle cost model

Paper:
  python3 readability.py  readability indices of the paper text
