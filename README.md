# ELL Term Paper

**Why Two Threads Can See Memory in Different Orders: SC vs TSO from the Ground Up**

Final term paper for ELL305 Computer Architecture, IIT Delhi.

The paper explains memory ordering from the ground up: store buffers, shared memory and litmus tests, and the formal rules of SC, TSO and PSO. It includes two experiments and a discussion of what strong ordering costs.

## Contents

| File | Description |
|------|-------------|
| `final_paper.pdf` | The compiled paper |
| `final_latex_file.tex` | Single-file LaTeX source (bibliography embedded via `filecontents*`) |

## Chapters

1. Introduction
2. What We Read, and What We Took From It
3. Memory and the Store Buffer
4. Two Cores: Shared Memory and Litmus Tests
5. SC, TSO and PSO: the Rules as Math
6. Experiment 1: the Python Checker
7. Experiment 2: Seeing SB (0,0) on a Real Machine
8. What Strong Ordering Costs, and Why SC Is Still Not Shipped
9. Conclusion and Future Work

## Building

```sh
pdflatex final_latex_file
bibtex final_latex_file
makeglossaries final_latex_file
makeindex final_latex_file
pdflatex final_latex_file
pdflatex final_latex_file
```
