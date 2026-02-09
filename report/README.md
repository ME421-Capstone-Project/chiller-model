# Chiller Array Simulation Package — Technical Report

This directory contains the LaTeX source files for the technical report documenting the `chiller-sim` package.

## Files

- **`report.tex`** — Main LaTeX document (7 pages)
- **`references.bib`** — BibLaTeX bibliography with 10 references
- **`report.pdf`** — Compiled PDF output (generated)

## Prerequisites

To compile the report, you need a complete LaTeX distribution with the following packages:

- **Core**: `pdflatex`, `biber`
- **Packages**: `amsmath`, `amssymb`, `amsthm`, `tikz`, `pgfplots`, `biblatex`, `algorithm2e`, `booktabs`, `listings`, `microtype`, `hyperref`, `cleveref`

### Installation

**macOS (MacTeX):**
```bash
brew install --cask mactex
```

**Linux (TeX Live):**
```bash
sudo apt-get install texlive-full
```

**Windows (MiKTeX):**
Download from [miktex.org](https://miktex.org/)

## Compilation

### Quick Compilation

Run the following command from this directory:

```bash
pdflatex -interaction=nonstopmode report.tex && \
biber report && \
pdflatex -interaction=nonstopmode report.tex && \
pdflatex -interaction=nonstopmode report.tex
```

### Step-by-Step Compilation

1. **First pass** (generate auxiliary files):
   ```bash
   pdflatex report.tex
   ```

2. **Process bibliography**:
   ```bash
   biber report
   ```

3. **Second pass** (resolve citations):
   ```bash
   pdflatex report.tex
   ```

4. **Third pass** (resolve cross-references):
   ```bash
   pdflatex report.tex
   ```

### Using latexmk (Recommended)

If you have `latexmk` installed, you can use:

```bash
latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode" report.tex
```

This automatically handles all passes and bibliography processing.

## Output

The compilation produces:

- **`report.pdf`** — Final typeset document (7 pages, ~290 KB)

## Auxiliary Files

The compilation process generates several auxiliary files that are ignored by git:

- `*.aux` — Cross-reference information
- `*.bbl` — Formatted bibliography
- `*.bcf`, `*.blg` — Biber control and log files
- `*.log` — Compilation log
- `*.out` — Hyperref outline data
- `*.run.xml` — Biber run information
- `*.synctex.gz` — SyncTeX data for editor integration

These files are automatically generated and should not be committed to version control.

## Cleaning Up

To remove all auxiliary files:

```bash
latexmk -c
```

To remove all auxiliary files AND the PDF:

```bash
latexmk -C
```

## Document Structure

The report contains:

1. **Abstract** — Overview of thermal recirculation problem and package capabilities
2. **Introduction** — Problem statement, motivation, key findings
3. **Mathematical Formulation** — Gaussian plume model, COP degradation, power consumption
4. **Software Architecture** — Modular design, composition patterns, immutability principles
5. **Optimization Algorithm** — Greedy removal heuristic with pseudocode
6. **Results and Validation** — Example simulations, AHRI 550/590 verification
7. **Conclusion** — Summary and future directions
8. **References** — 10 citations including ASHRAE handbooks, AHRI standards, scientific papers

## Key Equations

The report features two boxed main equations:

- **Equation 4**: Gaussian plume dispersion model
- **Equation 7**: COP degradation model

## Figures

The report includes two TikZ-generated figures:

- **Figure 1**: Layered architecture diagram (4 layers)
- **Figure 2**: Chiller array schematic (5×5 grid)

## Troubleshooting

### "! LaTeX Error: File `X.sty' not found"

Install the missing package. For TeX Live:
```bash
tlmgr install <package-name>
```

### "Package biblatex Warning: Please (re)run Biber"

You need to run the full compilation sequence (pdflatex → biber → pdflatex → pdflatex).

### Font warnings

These are usually harmless. The document uses Computer Modern fonts which are included in all standard TeX distributions.

## Customization

To modify the document class or layout, edit the preamble in `report.tex`:

- **Font size**: Change `11pt` to `10pt` or `12pt` on line 8
- **Margins**: Adjust `geometry` package options on line 11
- **Bibliography style**: Modify `biblatex` options on line 35

## Contact

For questions about the report content or compilation issues, please open an issue on the project repository.
