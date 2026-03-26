# Technical Report

LaTeX source for the `chiller-sim` technical report.

## Files

- **`report.tex`** -- Main document
- **`references.bib`** -- Bibliography (10 references)
- **`report.pdf`** -- Compiled output (generated)

## Compilation

With `latexmk` (recommended):

```bash
latexmk -pdf report.tex
```

Or manually:

```bash
pdflatex report.tex && biber report && pdflatex report.tex && pdflatex report.tex
```

## Cleanup

```bash
latexmk -c     # remove auxiliary files
latexmk -C     # remove auxiliary files and PDF
```
