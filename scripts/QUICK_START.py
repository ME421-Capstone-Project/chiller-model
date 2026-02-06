"""
QUICK START GUIDE: Chiller Array Visualizations
================================================

This package contains professional, publication-quality visualizations for
the chiller array thermal interference simulation.

GENERATED FILES
---------------
✓ figure_1_thermal_plume.png (287 KB)
  - Shows thermal wake from a single chiller source
  - Demonstrates Gaussian plume dispersion
  - Includes wind direction arrow and statistics

✓ figure_2_cop_degradation.png (424 KB)
  - Compares isolated vs. dense array performance
  - Shows 30% COP reduction in crowded configurations
  - Three-panel layout with comparison bar chart

✓ figure_3_optimization_comparison.png (474 KB)
  - Standard activation vs. wind-aware optimization
  - Demonstrates 12% energy savings
  - Includes COP heatmaps and performance metrics

✓ figure_4_wind_sensitivity.png (535 KB)
  - Wind direction impact analysis (0-360°)
  - Polar and Cartesian views
  - Shows optimal wind angles

✓ figure_5_optimal_array_size.png (403 KB)
  - "Less is more" principle demonstration
  - Optimal number of active chillers analysis
  - Shows 15-18% maximum savings

USAGE
-----
1. Review figures in any image viewer
2. Include in reports (all at 300 DPI for publication)
3. Reference VISUALIZATION_REPORT.md for detailed descriptions

REGENERATING FIGURES
--------------------
To regenerate with different parameters:

    python examples_visualization.py

Modify parameters in the script:
- Array size (GRID_SIDE)
- Spacing between chillers (spacing_m)
- Wind conditions (velocity_m_per_s)
- Cooling load (TOTAL_LOAD_KW)
- Dispersion coefficient (dispersion_coeff)

CUSTOMIZATION EXAMPLES
----------------------
Change wind speed:
    wind = WindVector(velocity_m_per_s=(3.0, 1.5), ambient_temp_k=298.15)

Change array size:
    array = ChillerArray.create_grid(rows=7, cols=7, spacing_m=4.0)

Change dispersion:
    model = GaussianPlumeModel(dispersion_coeff=2.0)

FIGURE SPECIFICATIONS
---------------------
Format: PNG
Resolution: 300 DPI
Color space: RGB
Font family: DejaVu Sans (matplotlib default)
Grid style: Dashed, alpha=0.3
Legend: Framed boxes with black borders

Figure 1: 10×8 inches (3000×2400 px)
Figure 2: 16×5 inches (4800×1500 px)
Figure 3: 16×10 inches (4800×3000 px)
Figure 4: 16×6 inches (4800×1800 px)
Figure 5: 12×10 inches (3600×3000 px)

KEY FINDINGS
------------
1. Thermal interference reduces COP by up to 30% in dense arrays
2. Wind-aware optimization saves 10-15% energy
3. Running 40-50% of chillers can be optimal (not 100%)
4. Wind direction matters (5% variation for symmetric arrays)
5. Upwind positions always perform better

REPORT INTEGRATION
------------------
For LaTeX:
    \includegraphics[width=\textwidth]{figure_1_thermal_plume.png}

For Word/PowerPoint:
    Insert → Picture → Select file
    (300 DPI ensures crisp printing)

For HTML:
    <img src="figure_1_thermal_plume.png" alt="Thermal Plume" width="800">

TROUBLESHOOTING
---------------
Q: Script fails with import errors?
A: Install dependencies:
   pip install matplotlib seaborn numpy pydantic

Q: Figures look blurry on screen?
A: Normal for 300 DPI. They'll print perfectly. 
   For screen-only, change to dpi=150 in setup_publication_style()

Q: Want different colors?
A: Edit the colormap in each function:
   - Thermal: colors_list = ['#ffffff', '#fff4cc', ...]
   - COP: cmap='RdYlGn' → try 'viridis', 'plasma', 'coolwarm'

Q: Need vector graphics (SVG/PDF)?
A: Change save_path extension:
   save_path="figure_1_thermal_plume.pdf"
   (Will be larger files but infinitely scalable)

CITATION
--------
If using these figures in publications:

    Author et al. (2026). Wind-Aware Optimization of Chiller Arrays 
    for Data Center Cooling. Chiller-Sim Package v0.1.0. 
    https://github.com/example/chiller-model

FURTHER READING
---------------
- VISUALIZATION_REPORT.md: Detailed figure descriptions
- README.md: Package overview
- docs/examples.rst: Code examples
- demo.ipynb: Interactive demonstrations

CONTACT
-------
Questions? Open an issue on GitHub or consult the documentation.

Last Updated: 2026-02-06
Package Version: 0.1.0
"""

if __name__ == "__main__":
    print(__doc__)
