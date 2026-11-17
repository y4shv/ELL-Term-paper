#!/usr/bin/env python3
"""Readability scores for the main text of the paper (Appendix B).

Takes the LaTeX source, keeps the main chapters and removes non-prose
content before applying the readability formulas.

Usage: python3 readability.py term_paper.tex
"""
import re
import sys
import math


def prose(tex):
    start = tex.index("\\chapter{Introduction}")
    end = tex.index("\\appendix")
    t = tex[start:end]
    for env in ["lstlisting", "table", "figure", "tikzpicture", "tabular",
                "tabularx", "align*", "description"]:
        t = re.sub(r"\\begin\{%s\}.*?\\end\{%s\}" % (re.escape(env),
                                                     re.escape(env)),
                   " ", t, flags=re.S)
    t = re.sub(r"\\\[.*?\\\]", " ", t, flags=re.S)          # display math
    t = re.sub(r"\$[^$]*\$", " X ", t)                       # inline math
    t = re.sub(r"%.*", " ", t)                               # LaTeX comments
    t = re.sub(r"\\cite\{[^}]*\}", " ", t)
    t = re.sub(r"\\(cref|Cref|ref|label|index)\{[^}]*\}", " it ", t)
    t = re.sub(r"\\(chapter|section|subsection|paragraph)\*?\{[^}]*\}",
               " ", t)
    t = re.sub(r"\\begin\{[^}]*\}(\{[^}]*\})?|\\end\{[^}]*\}", " ", t)
    t = re.sub(r"\\(emph|textbf|code|texttt|textsf)\{([^}]*)\}", r"\2", t)
    t = re.sub(r"\\outc\{[^}]*\}\{[^}]*\}", " it ", t)
    t = re.sub(r"\\[A-Za-z]+\*?", " ", t)                    # other LaTeX commands
    t = re.sub(r"[{}\\~]", " ", t)
    t = re.sub(r"\s+", " ", t)

    return t


def syllables(word):
    w = word.lower()
    if len(w) <= 3:
        return 1

    
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)

    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def main(path):
    text = prose(open(path).read())
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text)
                 if len(re.findall(r"[A-Za-z]+", s)) >= 3]
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", " ".join(sentences))


    W, S = len(words), len(sentences)
    
    syl = [syllables(w) for w in words]
    Syl = sum(syl)
    poly = sum(1 for s in syl if s >= 3)
    chars = sum(len(re.sub(r"[^A-Za-z]", "", w)) for w in words)
    complex_words = sum(1 for w, s in zip(words, syl)
                        if s >= 3 and not w[0].isupper())
    fre = 206.835 - 1.015 * W / S - 84.6 * Syl / W
    fk = 0.39 * W / S + 11.8 * Syl / W - 15.59
    fog = 0.4 * (W / S + 100 * complex_words / W)
    smog = 1.0430 * math.sqrt(poly * 30 / S) + 3.1291
    L = chars / W * 100
    Ssent = S / W * 100
    cli = 0.0588 * L - 0.296 * Ssent - 15.8
    ari = 4.71 * chars / W + 0.5 * W / S - 21.43

    print("words %d, sentences %d, words per sentence %.1f, "
          "syllables per word %.2f" % (W, S, W / S, Syl / W))
    print("Flesch reading ease       %.1f" % fre)
    print("Flesch-Kincaid grade      %.1f" % fk)
    print("Gunning Fog index         %.1f" % fog)
    print("SMOG index                %.1f" % smog)
    print("Coleman-Liau index        %.1f" % cli)
    print("Automated readability     %.1f" % ari)


if __name__ == "__main__":
    main(sys.argv[1])
