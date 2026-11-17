# Memory Consistency Models: SC, TSO and PSO

ELL305 Computer Architecture term paper, IIT Delhi (November 2026).
Advisor: Prof. Subrat Kar.

The paper asks three questions: (Q1) do the rules of SC, TSO and PSO form a strict ladder, (Q2) does a real x86-64 processor show the relaxed behaviour, and (Q3) what does strong ordering cost.

## Contents

| Path | What it is |
| --- | --- |
| `term_paper.pdf`, `term_paper.tex` | the final paper and its LaTeX source |
| `papers.bib` | the books and papers cited in the paper |
| `code/` | all programs used in the paper |
| `results/` | raw outputs of the programs |

## Running the code

The Python programs need only Python 3. The C program needs GCC on Linux and a machine with at least two cores.

```
cd code
python3 checker.py       # Q1: the axiomatic checker
python3 sb_machine.py    # Q1: the store-buffer simulation
./run_litmus.sh          # Q2: hardware test (x86-64 Linux)
python3 summarise.py     # Q2: summary of the hardware runs
python3 cpi_model.py     # Q3: the cost model
```

See `code/README.txt` for details.
