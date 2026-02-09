"""Professional visualization examples for chiller array simulation.

This script demonstrates key features of the chiller simulation package
with publication-quality figures suitable for technical reports.

Author: Chiller Model Team
Date: 2026-02-06
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as fx

from components import WindVector, ChillerArray
from models import GaussianPlumeModel
from simulation import SimulationEnvironment, Optimizer


# ============================================================================
# Publication-Quality Matplotlib Settings
# ============================================================================
def setup_publication_style() -> None:
    """Configure matplotlib for publication-quality figures."""
    plt.rcParams.update({
        'figure.figsize': (10, 8),
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.2,
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'legend.frameon': False,  # No legend frame
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        'axes.axisbelow': True,
        'lines.linewidth': 2.0,
        'lines.markersize': 8,
    })


# ============================================================================
# Example 1: Thermal Plume Visualization
# ============================================================================
def create_thermal_plume_visualization(
    save_path: str = "figure_1_thermal_plume.png"
) -> None:
    """Visualize thermal wake from a single chiller source.
    
    This figure shows how one chiller's exhaust affects neighboring units
    in a 5x5 grid, with wind direction indicated by an arrow.
    
    Parameters
    ----------
    save_path : str
        Output file path for the figure.
    """
    print("Generating Figure 1: Thermal Plume Visualization...")
    
    # Setup environment
    wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    env = SimulationEnvironment(array, wind, model)
    
    # Get thermal impact from center chiller
    source_idx = 12  # Center of 5x5 grid
    thermal_impact = env.interaction_matrix[source_idx, :]
    positions = array.positions_m
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Custom colormap: white -> yellow -> orange -> red
    colors_list = ['#ffffff', '#fff4cc', '#ffe699', '#ffc266', '#ff9933', '#ff6600']
    n_bins = 100
    cmap = LinearSegmentedColormap.from_list('thermal', colors_list, N=n_bins)
    
    # Plot thermal impact as scatter with size and color
    scatter = ax.scatter(
        positions[:, 0], 
        positions[:, 1],
        c=thermal_impact, 
        cmap=cmap,
        s=600,
        edgecolors='black',
        linewidths=2.5,
        vmin=0,
        vmax=np.max(thermal_impact) * 1.1,
        zorder=3
    )
    
    # Highlight source chiller
    ax.scatter(
        positions[source_idx, 0], 
        positions[source_idx, 1],
        c='#0066cc',
        s=800,
        marker='*',
        edgecolors='black',
        linewidths=2.5,
        label='Source Chiller',
        zorder=4
    )
    
    # Draw wind direction arrow - positioned in top-left corner
    x_range = positions[:, 0].max() - positions[:, 0].min()
    y_range = positions[:, 1].max() - positions[:, 1].min()
    wind_arrow_start = (positions[:, 0].min() + 0.1 * x_range, 
                        positions[:, 1].max() - 0.15 * y_range)
    wind_scale = 2.0
    arrow = FancyArrowPatch(
        wind_arrow_start,
        (wind_arrow_start[0] + wind.direction[0] * wind_scale,
         wind_arrow_start[1] + wind.direction[1] * wind_scale),
        arrowstyle='->,head_width=0.8,head_length=0.8',
        color='#0066cc',
        linewidth=3.5,
        zorder=5
    )
    ax.add_patch(arrow)
    
    # Wind label with background - positioned to avoid overlap
    wind_text = ax.text(
        wind_arrow_start[0] + wind.direction[0] * wind_scale + 0.5,
        wind_arrow_start[1] + wind.direction[1] * wind_scale,
        f'Wind\n{wind.speed_m_per_s:.1f} m/s',
        ha='left',
        va='center',
        fontsize=10,
        fontweight='bold',
        color='#0066cc',
        zorder=6
    )
    wind_text.set_path_effects([
        fx.Stroke(linewidth=3, foreground='white'),
        fx.Normal()
    ])
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02, fraction=0.046)
    cbar.set_label('Thermal Impact Factor', fontsize=12, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)
    
    # Formatting
    ax.set_xlabel('X Position (m)', fontweight='bold')
    ax.set_ylabel('Y Position (m)', fontweight='bold')
    ax.set_title(
        'Thermal Wake Effect from Single Chiller\n5×5 Array with 3m Spacing',
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    ax.legend(loc='upper right', frameon=False)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Adjust limits to prevent clipping
    x_margin = (positions[:, 0].max() - positions[:, 0].min()) * 0.15
    y_margin = (positions[:, 1].max() - positions[:, 1].min()) * 0.15
    ax.set_xlim(positions[:, 0].min() - x_margin, positions[:, 0].max() + x_margin)
    ax.set_ylim(positions[:, 1].min() - y_margin, positions[:, 1].max() + y_margin)
    
    # Add statistics box
    max_impact = np.max(thermal_impact[thermal_impact > 0])
    mean_impact = np.mean(thermal_impact[thermal_impact > 0])
    num_affected = np.sum(thermal_impact > 0.01) - 1  # Exclude source
    
    stats_text = (
        f'Statistics:\n'
        f'• Max Impact: {max_impact:.3f}\n'
        f'• Mean Impact: {mean_impact:.3f}\n'
        f'• Affected Units: {num_affected}/24'
    )
    ax.text(
        0.02, 0.98, stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black')
    )
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"✓ Saved: {save_path}")


# ============================================================================
# Example 2: COP Degradation Comparison
# ============================================================================
def create_cop_degradation_comparison(
    save_path: str = "figure_2_cop_degradation.png"
) -> None:
    """Compare COP of isolated vs. crowded chiller configurations.
    
    This figure demonstrates the "density penalty" - how a chiller's
    performance degrades when surrounded by active neighbors.
    
    Parameters
    ----------
    save_path : str
        Output file path for the figure.
    """
    print("Generating Figure 2: COP Degradation Comparison...")
    
    # Setup
    wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0, base_cop=4.0)
    env = SimulationEnvironment(array, wind, GaussianPlumeModel(1.2))
    
    center_idx = 12
    
    # Case A: Isolated chiller
    state_solo = np.zeros(array.num_chillers, dtype=bool)
    state_solo[center_idx] = True
    result_solo = env.compute_performance(state_solo, 10.0)
    cop_solo = result_solo.cop_array[center_idx]
    
    # Case B: All chillers active
    state_full = np.ones(array.num_chillers, dtype=bool)
    result_full = env.compute_performance(state_full, 250.0)
    cop_full = result_full.cop_array[center_idx]
    
    # Calculate metrics
    efficiency_loss = (cop_solo - cop_full) / cop_solo * 100
    
    # Create visualization
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))
    
    positions = array.positions_m
    
    # ---- Panel 1: Isolated Configuration ----
    colors_solo = np.full(array.num_chillers, 0.3)
    colors_solo[center_idx] = 1.0
    
    sc1 = ax1.scatter(
        positions[:, 0], positions[:, 1],
        c=colors_solo,
        cmap='RdYlGn',
        s=600,
        edgecolors='black',
        linewidths=2.0,
        vmin=0, vmax=1,
        zorder=3
    )
    ax1.scatter(
        positions[center_idx, 0], positions[center_idx, 1],
        s=800, marker='*', c='gold', edgecolors='black',
        linewidths=2.5, zorder=4
    )
    ax1.set_title('Isolated Operation\n(1 Active Chiller)', fontweight='bold')
    ax1.set_xlabel('X Position (m)', fontweight='bold')
    ax1.set_ylabel('Y Position (m)', fontweight='bold')
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    
    # COP annotation
    ax1.text(
        0.5, 0.05,
        f'COP = {cop_solo:.2f}\n(No Interference)',
        transform=ax1.transAxes,
        ha='center',
        fontsize=11,
        fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.9, edgecolor='black')
    )
    
    # ---- Panel 2: Full Array Configuration ----
    colors_full = np.ones(array.num_chillers)
    
    sc2 = ax2.scatter(
        positions[:, 0], positions[:, 1],
        c=colors_full,
        cmap='RdYlGn',
        s=600,
        edgecolors='black',
        linewidths=2.0,
        vmin=0, vmax=1,
        zorder=3
    )
    ax2.scatter(
        positions[center_idx, 0], positions[center_idx, 1],
        s=800, marker='*', c='gold', edgecolors='black',
        linewidths=2.5, zorder=4, label='Target Chiller'
    )
    ax2.set_title('Dense Operation\n(25 Active Chillers)', fontweight='bold')
    ax2.set_xlabel('X Position (m)', fontweight='bold')
    ax2.set_ylabel('Y Position (m)', fontweight='bold')
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right', frameon=False)
    
    # COP annotation
    ax2.text(
        0.5, 0.05,
        f'COP = {cop_full:.2f}\n(High Interference)',
        transform=ax2.transAxes,
        ha='center',
        fontsize=11,
        fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='salmon', alpha=0.9, edgecolor='black')
    )
    
    # ---- Panel 3: Comparison Bar Chart ----
    configurations = ['Isolated', 'Dense Array']
    cop_values = [cop_solo, cop_full]
    colors_bar = ['#90EE90', '#FF6B6B']
    
    bars = ax3.bar(configurations, cop_values, color=colors_bar, 
                   edgecolor='black', linewidth=2.0, width=0.6)
    
    # Add value labels on bars
    for bar, val in zip(bars, cop_values):
        height = bar.get_height()
        ax3.text(
            bar.get_x() + bar.get_width() / 2., height + 0.1,
            f'{val:.2f}',
            ha='center', va='bottom',
            fontsize=12, fontweight='bold'
        )
    
    ax3.set_ylabel('Coefficient of Performance (COP)', fontweight='bold')
    ax3.set_title('Performance Comparison', fontweight='bold')
    ax3.set_ylim(0, cop_solo * 1.2)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add efficiency loss annotation
    ax3.text(
        0.5, 0.95,
        f'Efficiency Loss: {efficiency_loss:.1f}%',
        transform=ax3.transAxes,
        ha='center', va='top',
        fontsize=12, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='black')
    )
    
    plt.suptitle(
        'Density Penalty: COP Degradation in Chiller Arrays',
        fontsize=16, fontweight='bold', y=1.02
    )
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"✓ Saved: {save_path}")


# ============================================================================
# Example 3: Optimization Comparison
# ============================================================================
def create_optimization_comparison(
    save_path: str = "figure_3_optimization_comparison.png"
) -> None:
    """Compare standard vs. wind-aware optimized chiller activation.
    
    This figure demonstrates energy savings from intelligent
    chiller selection based on wind direction.
    
    Parameters
    ----------
    save_path : str
        Output file path for the figure.
    """
    print("Generating Figure 3: Optimization Comparison...")
    
    # Setup
    wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
    model = GaussianPlumeModel(dispersion_coeff=1.2)
    env = SimulationEnvironment(array, wind, model)
    
    total_load = 100.0
    target_units = 15
    
    # Standard: First 15 chillers
    state_std = np.zeros(array.num_chillers, dtype=bool)
    state_std[:target_units] = True
    result_std = env.compute_performance(state_std, total_load)
    
    # Optimized: Greedy selection
    optimizer = Optimizer(env, total_load)
    opt_result = optimizer.optimize_greedy(min_active=target_units)
    result_opt = env.compute_performance(opt_result.optimal_mask, total_load)
    
    # Calculate savings
    savings_pct = (1 - result_opt.total_work_kw / result_std.total_work_kw) * 100
    
    # Create figure
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])
    
    positions = array.positions_m
    
    # ---- Panel 1: Standard Activation ----
    cop_normalized_std = result_std.cop_array / array.base_cop
    
    # Plot inactive chillers in grey
    inactive_std = ~state_std
    if np.any(inactive_std):
        ax1.scatter(
            positions[inactive_std, 0], 
            positions[inactive_std, 1],
            c='#D3D3D3',  # Light grey
            s=200,
            edgecolors='#808080',  # Dark grey edge
            linewidths=1.5,
            zorder=2,
            label='Inactive'
        )
    
    # Plot active chillers with colormap
    sc1 = ax1.scatter(
        positions[state_std, 0], 
        positions[state_std, 1],
        c=cop_normalized_std[state_std],
        cmap='RdYlGn',
        s=600,
        edgecolors='black',
        linewidths=2.5,
        vmin=0.5, vmax=1.0,
        zorder=3,
        label='Active'
    )
    
    # Wind arrow
    add_wind_arrow(ax1, wind, positions)
    
    ax1.set_title(
        f'Standard Activation\n(First {target_units} Units)',
        fontweight='bold', fontsize=12
    )
    ax1.set_xlabel('X Position (m)', fontweight='bold')
    ax1.set_ylabel('Y Position (m)', fontweight='bold')
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    
    # Stats box - positioned lower to avoid wind arrow
    ax1.text(
        0.98, 0.02,
        f'Total Work: {result_std.total_work_kw:.2f} kW\n'
        f'Mean COP: {np.mean(result_std.cop_array[state_std]):.2f}',
        transform=ax1.transAxes,
        fontsize=9,
        ha='right',
        va='bottom',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.95, edgecolor='black', linewidth=1.5)
    )
    
    # ---- Panel 2: Optimized Activation ----
    cop_normalized_opt = result_opt.cop_array / array.base_cop
    
    # Plot inactive chillers in grey
    inactive_opt = ~opt_result.optimal_mask
    if np.any(inactive_opt):
        ax2.scatter(
            positions[inactive_opt, 0], 
            positions[inactive_opt, 1],
            c='#D3D3D3',  # Light grey
            s=200,
            edgecolors='#808080',  # Dark grey edge
            linewidths=1.5,
            zorder=2,
            label='Inactive'
        )
    
    # Plot active chillers with colormap
    sc2 = ax2.scatter(
        positions[opt_result.optimal_mask, 0], 
        positions[opt_result.optimal_mask, 1],
        c=cop_normalized_opt[opt_result.optimal_mask],
        cmap='RdYlGn',
        s=600,
        edgecolors='black',
        linewidths=2.5,
        vmin=0.5, vmax=1.0,
        zorder=3,
        label='Active'
    )
    
    # Wind arrow
    add_wind_arrow(ax2, wind, positions)
    
    ax2.set_title(
        f'Wind-Aware Optimization\n({np.sum(opt_result.optimal_mask)} Units)',
        fontweight='bold', fontsize=12
    )
    ax2.set_xlabel('X Position (m)', fontweight='bold')
    ax2.set_ylabel('Y Position (m)', fontweight='bold')
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    
    # Stats box - positioned lower to avoid wind arrow
    ax2.text(
        0.98, 0.02,
        f'Total Work: {result_opt.total_work_kw:.2f} kW\n'
        f'Mean COP: {np.mean(result_opt.cop_array[opt_result.optimal_mask]):.2f}',
        transform=ax2.transAxes,
        fontsize=9,
        ha='right',
        va='bottom',
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.95, edgecolor='black', linewidth=1.5)
    )
    
    # Shared colorbar - vertical and centered between panels
    # Create a new axis for the colorbar between ax1 and ax2
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    
    # Position colorbar in the space between the two panels
    cbar_ax = fig.add_axes([0.48, 0.55, 0.02, 0.35])  # [left, bottom, width, height]
    cbar = plt.colorbar(sc2, cax=cbar_ax, orientation='vertical')
    cbar.set_label('Normalized COP\n(COP/COP_base)', fontsize=10, fontweight='bold')
    
    # ---- Panel 3: Performance Metrics Comparison ----
    metrics = ['Total Power\n(kW)', 'Mean COP', 'Energy\nSavings (%)']
    std_values = [result_std.total_work_kw, 
                  np.mean(result_std.cop_array[state_std]), 
                  0]
    opt_values = [result_opt.total_work_kw, 
                  np.mean(result_opt.cop_array[opt_result.optimal_mask]), 
                  savings_pct]
    
    x_pos = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax3.bar(x_pos - width/2, std_values, width, 
                    label='Standard', color='#FF9999', 
                    edgecolor='black', linewidth=1.5)
    bars2 = ax3.bar(x_pos + width/2, opt_values, width, 
                    label='Optimized', color='#90EE90', 
                    edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax3.text(
                    bar.get_x() + bar.get_width() / 2., height + 0.5,
                    f'{height:.1f}',
                    ha='center', va='bottom',
                    fontsize=10, fontweight='bold'
                )
    
    ax3.set_ylabel('Value', fontweight='bold', fontsize=12)
    ax3.set_ylim(0, 1.2 * max(np.max(std_values), np.max(opt_values)))
    ax3.set_title('Performance Metrics Comparison', fontweight='bold', fontsize=13)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(metrics, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=11, frameon=False)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add savings highlight - positioned right side to avoid legend
    ax3.text(
        0.75, 0.50,
        f'Optimization achieves\n{savings_pct:.1f}% energy savings',
        transform=ax3.transAxes,
        ha='center', va='center',
        fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.95, 
                 edgecolor='black', linewidth=2)
    )
    
    plt.suptitle(
        'Wind-Aware Optimization: Standard vs. Intelligent Chiller Selection',
        fontsize=16, fontweight='bold', y=0.98
    )
    plt.savefig(save_path)
    plt.close()
    print(f"✓ Saved: {save_path}")


# ============================================================================
# Example 4: Wind Direction Sensitivity Analysis
# ============================================================================
def create_wind_sensitivity_analysis(
    save_path: str = "figure_4_wind_sensitivity.png"
) -> None:
    """Analyze system efficiency across different wind directions.
    
    This figure shows how wind direction affects total energy consumption
    for a fully-active chiller array.
    
    Parameters
    ----------
    save_path : str
        Output file path for the figure.
    """
    print("Generating Figure 4: Wind Direction Sensitivity Analysis...")
    
    # Setup
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
    model = GaussianPlumeModel(1.2)
    active_mask = np.ones(array.num_chillers, dtype=bool)
    total_load = 100.0
    
    # Test different wind angles
    angles = np.linspace(0, 360, 73)  # Every 5 degrees
    work_values = []
    mean_cop_values = []
    
    for angle in angles:
        wind = WindVector.from_speed_and_angle(
            speed_m_per_s=2.0,
            angle_deg=angle,
            ambient_temp_k=298.15
        )
        env = SimulationEnvironment(array, wind, model)
        result = env.compute_performance(active_mask, total_load)
        work_values.append(result.total_work_kw)
        mean_cop_values.append(np.mean(result.cop_array))
    
    work_values = np.array(work_values)
    mean_cop_values = np.array(mean_cop_values)
    
    # Find best and worst
    best_idx = np.argmin(work_values)
    worst_idx = np.argmax(work_values)
    
    # Create figure with polar and Cartesian plots
    fig = plt.figure(figsize=(16, 6))
    
    # Polar plot for work
    ax1 = plt.subplot(1, 3, 1, projection='polar')
    theta = np.deg2rad(angles)
    ax1.plot(theta, work_values, 'b-', linewidth=2.5, label='Total Work')
    ax1.scatter(theta[best_idx], work_values[best_idx], 
               c='green', s=200, marker='*', zorder=5, 
               edgecolors='black', linewidths=2,
               label=f'Best: {angles[best_idx]:.0f}°')
    ax1.scatter(theta[worst_idx], work_values[worst_idx], 
               c='red', s=200, marker='X', zorder=5,
               edgecolors='black', linewidths=2,
               label=f'Worst: {angles[worst_idx]:.0f}°')
    ax1.set_theta_zero_location('E')
    ax1.set_theta_direction(1)
    ax1.set_title('Total Work vs. Wind Direction\n(Polar View)', 
                 fontweight='bold', pad=20, fontsize=12)
    ax1.legend(loc='upper left', bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=9)
    ax1.grid(True, alpha=0.5)
    
    # Cartesian plot for work
    ax2 = plt.subplot(1, 3, 2)
    ax2.plot(angles, work_values, 'b-', linewidth=2.5)
    ax2.scatter(angles[best_idx], work_values[best_idx],
               c='green', s=200, marker='*', zorder=5,
               edgecolors='black', linewidths=2,
               label=f'Best: {angles[best_idx]:.0f}° ({work_values[best_idx]:.2f} kW)')
    ax2.scatter(angles[worst_idx], work_values[worst_idx],
               c='red', s=200, marker='X', zorder=5,
               edgecolors='black', linewidths=2,
               label=f'Worst: {angles[worst_idx]:.0f}° ({work_values[worst_idx]:.2f} kW)')
    ax2.axhline(y=np.mean(work_values), color='gray', linestyle='--', 
               linewidth=2, alpha=0.7, label=f'Mean: {np.mean(work_values):.2f} kW')
    ax2.fill_between(angles, work_values, alpha=0.3, color='blue')
    ax2.set_xlabel('Wind Direction (degrees)', fontweight='bold')
    ax2.set_ylabel('Total Work (kW)', fontweight='bold')
    ax2.set_title('Total Work vs. Wind Direction\n(Cartesian View)', fontweight='bold', fontsize=12)
    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 360)
    
    # COP plot
    ax3 = plt.subplot(1, 3, 3)
    ax3.plot(angles, mean_cop_values, 'g-', linewidth=2.5)
    ax3.scatter(angles[best_idx], mean_cop_values[best_idx],
               c='green', s=200, marker='*', zorder=5,
               edgecolors='black', linewidths=2)
    ax3.scatter(angles[worst_idx], mean_cop_values[worst_idx],
               c='red', s=200, marker='X', zorder=5,
               edgecolors='black', linewidths=2)
    ax3.axhline(y=np.mean(mean_cop_values), color='gray', linestyle='--',
               linewidth=2, alpha=0.7, label=f'Mean COP: {np.mean(mean_cop_values):.2f}')
    ax3.fill_between(angles, mean_cop_values, alpha=0.3, color='green')
    ax3.set_xlabel('Wind Direction (degrees)', fontweight='bold')
    ax3.set_ylabel('Mean COP', fontweight='bold')
    ax3.set_title('Mean COP vs. Wind Direction', fontweight='bold', fontsize=12)
    ax3.legend(loc='upper right', frameon=False)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, 360)
    
    # Add statistics box
    delta_work = work_values[worst_idx] - work_values[best_idx]
    delta_pct = (delta_work / work_values[best_idx]) * 100
    
    stats_text = (
        f'Wind Direction Impact:\n'
        f'• Best Angle: {angles[best_idx]:.0f}°\n'
        f'• Worst Angle: {angles[worst_idx]:.0f}°\n'
        f'• ΔWork: {delta_work:.2f} kW ({delta_pct:.1f}%)\n'
        f'• Range: {work_values.min():.2f} - {work_values.max():.2f} kW'
    )
    
    fig.text(
        0.5, -0.02, stats_text,
        ha='center', va='top', fontsize=10, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', 
                 alpha=0.95, edgecolor='black', linewidth=2)
    )
    
    plt.suptitle(
        'Wind Direction Sensitivity: Impact on System Performance',
        fontsize=16, fontweight='bold', y=0.98
    )
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    plt.savefig(save_path)
    plt.close()
    print(f"✓ Saved: {save_path}")


# ============================================================================
# Example 5: Optimal Array Size Analysis
# ============================================================================
def create_optimal_size_analysis(
    save_path: str = "figure_5_optimal_array_size.png"
) -> None:
    """Demonstrate 'less is more' principle with varying active chillers.
    
    This figure shows that running fewer, optimally-selected chillers
    can be more efficient than running all units.
    
    Parameters
    ----------
    save_path : str
        Output file path for the figure.
    """
    print("Generating Figure 5: Optimal Array Size Analysis...")
    
    # Setup larger array
    array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
    wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
    model = GaussianPlumeModel(1.2)
    env = SimulationEnvironment(array, wind, model)
    
    total_load = 100.0
    
    # Test different numbers of active chillers
    n_active_range = range(10, 26)
    work_results = []
    cop_results = []
    
    for n_active in n_active_range:
        optimizer = Optimizer(env, total_load)
        opt_result = optimizer.optimize_greedy(min_active=n_active)
        perf = env.compute_performance(opt_result.optimal_mask, total_load)
        work_results.append(perf.total_work_kw)
        cop_results.append(np.mean(perf.cop_array[opt_result.optimal_mask]))
    
    work_results = np.array(work_results)
    cop_results = np.array(cop_results)
    
    # Find optimal
    optimal_idx = np.argmin(work_results)
    optimal_n = list(n_active_range)[optimal_idx]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # ---- Panel 1: Work vs. Active Chillers ----
    ax1.plot(list(n_active_range), work_results, 'b-o', 
            linewidth=3, markersize=8, markerfacecolor='lightblue',
            markeredgecolor='black', markeredgewidth=2)
    ax1.scatter(optimal_n, work_results[optimal_idx],
               c='red', s=400, marker='*', zorder=5,
               edgecolors='black', linewidths=2.5,
               label=f'Optimal: {optimal_n} units')
    
    # Highlight optimal region
    ax1.axvline(x=optimal_n, color='red', linestyle='--', 
               linewidth=2, alpha=0.7)
    ax1.axhline(y=work_results[optimal_idx], color='red', 
               linestyle='--', linewidth=2, alpha=0.7)
    
    # Fill area under curve
    ax1.fill_between(list(n_active_range), work_results, 
                     alpha=0.2, color='blue')
    
    ax1.set_xlabel('Number of Active Chillers', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Total Work (kW)', fontweight='bold', fontsize=12)
    ax1.set_title(
        'Total Energy Consumption vs. Array Size\n"Less is More" Principle',
        fontweight='bold', fontsize=14
    )
    ax1.legend(loc='upper right', frameon=False, fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(9, 26)
    
    # Add annotations
    max_savings_idx = len(work_results) - 1
    max_savings = (work_results[max_savings_idx] - work_results[optimal_idx]) / \
                  work_results[max_savings_idx] * 100
    
    ax1.text(
        0.98, 0.95,
        f'Maximum Savings: {max_savings:.1f}%\n'
        f'(using {optimal_n} vs. 25 chillers)',
        transform=ax1.transAxes,
        ha='right', va='top',
        fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='yellow', 
                 alpha=0.95, edgecolor='black', linewidth=2)
    )
    
    # ---- Panel 2: Mean COP vs. Active Chillers ----
    ax2.plot(list(n_active_range), cop_results, 'g-o',
            linewidth=3, markersize=8, markerfacecolor='lightgreen',
            markeredgecolor='black', markeredgewidth=2)
    ax2.scatter(optimal_n, cop_results[optimal_idx],
               c='red', s=400, marker='*', zorder=5,
               edgecolors='black', linewidths=2.5,
               label=f'Optimal COP: {cop_results[optimal_idx]:.2f}')
    
    # Highlight optimal region
    ax2.axvline(x=optimal_n, color='red', linestyle='--',
               linewidth=2, alpha=0.7)
    
    # Fill area under curve
    ax2.fill_between(list(n_active_range), cop_results,
                     alpha=0.2, color='green')
    
    ax2.set_xlabel('Number of Active Chillers', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Mean COP of Active Units', fontweight='bold', fontsize=12)
    ax2.set_title(
        'Mean COP vs. Array Size',
        fontweight='bold', fontsize=14
    )
    ax2.legend(loc='upper right', frameon=False, fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(9, 26)
    
    # Add explanation
    ax2.text(
        0.02, 0.05,
        'Key Insight: COP increases with fewer active chillers\n'
        'due to reduced thermal interference',
        transform=ax2.transAxes,
        ha='left', va='bottom',
        fontsize=10, style='italic',
        bbox=dict(boxstyle='round', facecolor='lightblue',
                 alpha=0.9, edgecolor='black')
    )
    
    plt.suptitle(
        'Optimal Array Size: Balancing Load Distribution and Thermal Interference',
        fontsize=16, fontweight='bold', y=0.995
    )
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"✓ Saved: {save_path}")


# ============================================================================
# Helper Functions
# ============================================================================
def add_wind_arrow(
    ax: plt.Axes,
    wind: WindVector,
    positions: np.ndarray
) -> None:
    """Add a wind direction arrow to a plot.
    
    Parameters
    ----------
    ax : plt.Axes
        Matplotlib axes to add arrow to.
    wind : WindVector
        Wind vector for direction.
    positions : np.ndarray
        Array positions for placement.
    """
    # Position arrow in top-left area of plot
    x_range = positions[:, 0].max() - positions[:, 0].min()
    y_range = positions[:, 1].max() - positions[:, 1].min()
    arrow_start = (positions[:, 0].min() + 0.12 * x_range, 
                   positions[:, 1].max() - 0.15 * y_range)
    wind_scale = 1.8
    
    arrow = FancyArrowPatch(
        arrow_start,
        (arrow_start[0] + wind.direction[0] * wind_scale,
         arrow_start[1] + wind.direction[1] * wind_scale),
        arrowstyle='->,head_width=0.5,head_length=0.5',
        color='#0066cc',
        linewidth=2.5,
        zorder=5
    )
    ax.add_patch(arrow)
    
    # Wind label positioned to avoid overlap
    wind_text = ax.text(
        arrow_start[0] + wind.direction[0] * wind_scale * 0.5,
        arrow_start[1] + wind.direction[1] * wind_scale * 0.5 - 0.4,
        'Wind',
        ha='center', va='top',
        fontsize=9, fontweight='bold',
        color='#0066cc',
        zorder=6
    )
    wind_text.set_path_effects([
        fx.Stroke(linewidth=2.5, foreground='white'),
        fx.Normal()
    ])


# ============================================================================
# Main Execution
# ============================================================================
def main() -> None:
    """Generate all publication-quality figures."""
    print("\n" + "="*70)
    print("CHILLER ARRAY SIMULATION - PUBLICATION FIGURES")
    print("="*70 + "\n")
    
    setup_publication_style()
    
    # Generate all figures
    create_thermal_plume_visualization()
    create_cop_degradation_comparison()
    create_optimization_comparison()
    create_wind_sensitivity_analysis()
    create_optimal_size_analysis()
    
    print("\n" + "="*70)
    print("✓ All figures generated successfully!")
    print("="*70 + "\n")
    
    print("Generated files:")
    print("  • figure_1_thermal_plume.png")
    print("  • figure_2_cop_degradation.png")
    print("  • figure_3_optimization_comparison.png")
    print("  • figure_4_wind_sensitivity.png")
    print("  • figure_5_optimal_array_size.png")
    print("\nThese figures are publication-quality (300 DPI) and ready")
    print("for inclusion in technical reports and presentations.\n")


if __name__ == "__main__":
    main()
