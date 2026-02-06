Visual Architecture Guide
=========================

Quick Reference for Module Visualization
-----------------------------------------

This page provides quick visual references for understanding the chiller-model package architecture.

For complete details, see :doc:`architecture`.

System Layers (High-Level View)
--------------------------------

The package is organized into five distinct layers:

.. code-block:: text

    ┌───────────────────────────────────────────────────┐
    │  1. USER INTERFACE LAYER                          │
    │     • Scripts, notebooks, examples                │
    │     • Direct user interaction                     │
    └─────────────────────┬─────────────────────────────┘
                          │ uses
    ┌─────────────────────▼─────────────────────────────┐
    │  2. SIMULATION LAYER                              │
    │     • SimulationEnvironment (orchestrator)        │
    │     • Optimizer (energy optimization)             │
    └─────────────────────┬─────────────────────────────┘
                          │ composes
    ┌─────────────────────▼─────────────────────────────┐
    │  3. COMPONENT LAYER                               │
    │     • ChillerArray (spatial layout)               │
    │     • WindVector (atmospheric conditions)         │
    │     • InteractionModel (pluggable physics)        │
    └─────────────────────┬─────────────────────────────┘
                          │ implements/uses
    ┌─────────────────────▼─────────────────────────────┐
    │  4. MODEL LAYER                                   │
    │     • BaseInteractionModel (abstract interface)   │
    │     • GaussianPlumeModel (default physics)        │
    └─────────────────────┬─────────────────────────────┘
                          │ validated by
    ┌─────────────────────▼─────────────────────────────┐
    │  5. CORE LAYER                                    │
    │     • configs (Pydantic validation)               │
    │     • constants (physical constants)              │
    │     • data structures (specs, states)             │
    └───────────────────────────────────────────────────┘

Module Interaction Map
----------------------

This shows which modules interact with each other:

.. code-block:: text

    simulation/environment.py
         │
         ├──► components/chiller_array.py
         │         └──► core/constants.py
         │         └──► core/configs.py
         │
         ├──► components/wind.py
         │         └──► core/configs.py
         │
         └──► models/base_interaction.py
                   │
                   └──► models/gaussian_plume.py
                            └──► core/constants.py

    simulation/optimizer.py
         └──► simulation/environment.py
                   (see above)

Key Data Structures
-------------------

Immutable data structures used throughout:

.. code-block:: python

    # Configuration (input validation)
    ChillerConfig:
        - base_cop: float
        - rated_capacity_kw: float
        - alpha: float

    WindConfig:
        - velocity_x_m_per_s: float
        - velocity_y_m_per_s: float
        - ambient_temp_k: float

    # Physical representations (frozen/immutable)
    ChillerArray:
        - positions_m: NDArray (Nx2)
        - base_cop: float
        - alpha: float

    WindVector:
        - velocity_m_per_s: tuple
        - ambient_temp_k: float
        -> direction: NDArray (computed)
        -> speed_m_per_s: float (computed)

    # Computation results (NamedTuples)
    PerformanceResult:
        - total_work_kw: float
        - cop_array: NDArray (N,)
        - temp_rise_array: NDArray (N,)
        - load_per_unit_kw: float

    OptimizationResult:
        - optimal_mask: NDArray (N,)
        - optimal_work_kw: float
        - baseline_work_kw: float
        - savings_fraction: float
        - performance: PerformanceResult
        - iterations: int

Typical Workflow
----------------

1. **Setup Phase**

   .. code-block:: python

       # Create components
       array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
       wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
       model = GaussianPlumeModel(dispersion_coeff=1.2)

2. **Environment Initialization**

   .. code-block:: python

       # Compose into environment
       env = SimulationEnvironment(array, wind, model)
       # → Precomputes interaction matrix A (25×25)

3. **Performance Evaluation**

   .. code-block:: python

       # Evaluate a configuration
       active_mask = np.ones(25, dtype=bool)  # All active
       result = env.compute_performance(active_mask, total_load_kw=100.0)
       print(f"Total work: {result.total_work_kw:.2f} kW")

4. **Optimization (Optional)**

   .. code-block:: python

       # Find optimal configuration
       optimizer = Optimizer(env, total_load_kw=100.0)
       opt_result = optimizer.optimize_greedy(min_active=15)
       print(f"Savings: {opt_result.savings_fraction:.1%}")

Quick Module Lookup
-------------------

Need to find a specific functionality? Use this reference:

**I want to...**

* **Validate input parameters** → ``src/core/configs.py`` (Pydantic models)
* **Create a chiller layout** → ``src/components/chiller_array.py`` (``create_grid``, ``create_random``)
* **Define wind conditions** → ``src/components/wind.py`` (``WindVector``)
* **Use different physics** → ``src/models/base_interaction.py`` (subclass ``BaseInteractionModel``)
* **Calculate performance** → ``src/simulation/environment.py`` (``compute_performance``)
* **Optimize chiller selection** → ``src/simulation/optimizer.py`` (``optimize_greedy``)
* **Access physical constants** → ``src/core/constants.py``

Interactive Diagrams
--------------------

For interactive Mermaid diagrams with zoom/pan capabilities, see ``docs/diagrams.md``.

These diagrams can be:

* Viewed in GitHub (automatic Mermaid rendering)
* Edited in `Mermaid Live Editor <https://mermaid.live/>`_
* Exported as SVG/PNG for presentations

See Also
--------

* :doc:`architecture` - Complete architecture documentation
* :doc:`getting-started` - Quick start guide
* :doc:`api/index` - Full API reference
