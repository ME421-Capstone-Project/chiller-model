Architecture & Module Flow
===========================

This document provides a comprehensive overview of the chiller-model package architecture, showing how different modules interact to simulate thermal interference in chiller arrays.

System Overview
---------------

The package uses a **modular, composition-based architecture** where components are composed together rather than using deep inheritance hierarchies. This design follows scientific computing best practices for maintainability and testability.

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────────┐
    │                    User Interface / Scripts                     │
    │                   (demo.ipynb, examples)                        │
    └────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                   Simulation Layer                              │
    │  ┌──────────────────────┐    ┌───────────────────────┐         │
    │  │  SimulationEnvironment│◄───│    Optimizer         │         │
    │  │  - compute_performance│    │  - optimize_greedy   │         │
    │  │  - with_new_wind      │    │  - sensitivity_analysis│       │
    │  └──────────┬───────────┘    └───────────────────────┘         │
    └─────────────┼───────────────────────────────────────────────────┘
                  │
                  │ Composes ▼
    ┌─────────────┴───────────────────────────────────────────────────┐
    │                   Component Layer                               │
    │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐         │
    │  │ChillerArray│  │ WindVector  │  │ InteractionModel │         │
    │  │- positions │  │- velocity   │  │ (pluggable)      │         │
    │  │- base_cop  │  │- direction  │  │                  │         │
    │  │- alpha     │  │- speed      │  │                  │         │
    │  └────────────┘  └─────────────┘  └──────────────────┘         │
    └─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ Uses ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                   Model Layer                                   │
    │  ┌──────────────────────┐    ┌───────────────────────┐         │
    │  │BaseInteractionModel  │◄───┤ GaussianPlumeModel   │         │
    │  │  (Abstract Base)     │    │  - dispersion_coeff  │         │
    │  │                      │    │  - compute_interaction│         │
    │  └──────────────────────┘    └───────────────────────┘         │
    └─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ Validated by ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                   Core Layer                                    │
    │  ┌────────────┐  ┌─────────────┐  ┌────────────────┐           │
    │  │  configs   │  │  constants  │  │  ChillerSpec   │           │
    │  │ (Pydantic) │  │  (SI units) │  │  ChillerState  │           │
    │  └────────────┘  └─────────────┘  └────────────────┘           │
    └─────────────────────────────────────────────────────────────────┘


Module Hierarchy
----------------

Core Layer (``src/core/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Foundation modules providing validation, constants, and data structures.

**configs.py** - Pydantic Validation Models
  * ``ChillerConfig``: Validates chiller specifications (COP, capacity, alpha)
  * ``WindConfig``: Validates wind velocity and ambient temperature
  * ``SimulationConfig``: Validates simulation parameters
  
  **Purpose**: Ensures all inputs are physically plausible before entering calculations.
  
  **Key Features**:
    - SI unit enforcement (K, Pa, kg/s, J)
    - Physical constraint validation (e.g., COP ≤ 10)
    - Type-safe configuration objects

**constants.py** - Physical Constants
  * ``DEFAULT_BASE_COP``: 4.0
  * ``DEFAULT_ALPHA``: 0.7
  * ``DEFAULT_DISPERSION_COEFF``: 1.2
  * ``MAX_REALISTIC_COP``: 10.0
  * Temperature bounds (``MIN_REALISTIC_TEMP_K``, ``MAX_REALISTIC_TEMP_K``)
  
  **Purpose**: Centralized physical constants to avoid magic numbers.

Component Layer (``src/components/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Physical components that represent real hardware and environmental conditions.

**wind.py** - WindVector Class
  * Immutable representation of atmospheric conditions
  * Properties: ``velocity_m_per_s``, ``ambient_temp_k``, ``direction``, ``speed_m_per_s``
  * Factory methods: ``from_config()``, ``from_speed_and_angle()``
  
  **Purpose**: Encapsulates wind conditions affecting thermal plume dispersion.
  
  **Key Physics**:
    - Wind direction determines upwind/downwind relationships
    - Unit vector normalization for geometric calculations
    - Ambient temperature baseline for thermal interference

**chiller.py** - Chiller Data Structures
  * ``ChillerSpec``: Immutable manufacturer specifications (frozen dataclass)
  * ``ChillerState``: Immutable thermodynamic state (NamedTuple)
  
  **Purpose**: Represent individual chiller units and their operational states.
  
  **Design Pattern**: Uses immutability - new state objects returned after each process.

**chiller_array.py** - ChillerArray Class
  * Spatial arrangement of multiple chillers
  * Properties: ``positions_m``, ``base_cop``, ``alpha``, ``num_chillers``
  * Factory methods: ``create_grid()``, ``create_random()``
  * Utilities: ``get_bounding_box()``, ``centroid_m``
  
  **Purpose**: Manages geometric layout determining interference patterns.
  
  **Key Features**:
    - 2D position tracking (N×2 array)
    - Vectorized spatial operations
    - Grid and random placement utilities

Model Layer (``src/models/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pluggable physics models for thermal interaction calculations.

**base_interaction.py** - BaseInteractionModel (Abstract)
  * Abstract interface for interaction models
  * Key method: ``compute_interaction_matrix()``
  * Validation: ``validate_matrix()``
  
  **Purpose**: Defines the contract for thermal interaction physics.
  
  **Design Pattern**: Uses composition - models are held by SimulationEnvironment, not inherited.

**gaussian_plume.py** - GaussianPlumeModel
  * Implements Gaussian plume dispersion theory
  * Parameter: ``dispersion_coeff`` (σ, default 1.2)
  * Methods: ``compute_interaction_matrix()``, distance utilities
  
  **Purpose**: Default model for thermal wake effects between chillers.
  
  **Physics Equation**:
  
  .. math::
  
      A_{km} = \frac{\exp(-d_{lat}^2 / (\sigma (d_{long} + 1)))}{d_{long} + 1}
  
  Where:
    - :math:`d_{long}`: Longitudinal distance along wind (m)
    - :math:`d_{lat}`: Lateral distance perpendicular to wind (m)
    - :math:`\sigma`: Dispersion coefficient
  
  **Key Implementation**:
    - Fully vectorized NumPy operations (O(N²) but no loops)
    - Broadcasting for pairwise computations
    - Einsum for projection calculations

Simulation Layer (``src/simulation/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

High-level orchestration of components for performance calculation and optimization.

**environment.py** - SimulationEnvironment
  * Central orchestrator using COMPOSITION design
  * Attributes: ``chiller_array``, ``wind``, ``interaction_model``
  * Key methods:
    - ``compute_performance(active_mask, total_load_kw)``
    - ``compute_cop_at_position(position_idx, active_mask)``
    - ``get_thermal_impact_on(target_idx)``
    - ``with_new_wind(wind)``, ``with_new_model(model)``
  
  **Purpose**: Composes all components to calculate system performance.
  
  **Returns**: ``PerformanceResult`` (immutable NamedTuple)
    - ``total_work_kw``
    - ``cop_array`` (N×1)
    - ``temp_rise_array`` (N×1)
    - ``load_per_unit_kw``
  
  **COP Degradation Model**:
  
  .. math::
  
      COP_m = \frac{COP_{base}}{1 + \alpha \sum_k A_{km} \cdot active_k}

**optimizer.py** - Optimizer
  * Strategies for minimizing energy consumption
  * Key methods:
    - ``optimize_greedy(min_active, max_iterations)``
    - ``evaluate_configuration(active_mask)``
    - ``compare_configurations(masks)``
    - ``sensitivity_analysis(active_mask)``
  
  **Purpose**: Find optimal chiller activation patterns.
  
  **Returns**: ``OptimizationResult`` (immutable NamedTuple)
    - ``optimal_mask``
    - ``optimal_work_kw``
    - ``baseline_work_kw``
    - ``savings_fraction``
    - ``performance``
    - ``iterations``
  
  **Algorithm**: Greedy removal strategy
    1. Start with all chillers active
    2. Iteratively deactivate the chiller whose removal most reduces work
    3. Stop when no improvement possible
    
  **Complexity**: O(N²) where N = number of chillers


Data Flow Diagram
-----------------

Typical simulation workflow showing how data flows through the system:

.. code-block:: text

    1. Configuration Input
    ═══════════════════════
    User provides:
    - Chiller specs (base_cop, alpha, capacity)
    - Array layout (positions or grid params)
    - Wind conditions (velocity, temperature)
    - Interaction model parameters (sigma)
    
                     ▼
    
    2. Component Creation
    ═══════════════════════
    ┌─────────────────────────────────────────────┐
    │ ChillerArray.create_grid(rows=5, cols=5,    │
    │                          spacing_m=3.0)     │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │ WindVector(velocity_m_per_s=(5.0, 0.0),    │
    │            ambient_temp_k=298.15)           │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │ GaussianPlumeModel(dispersion_coeff=1.2)    │
    └──────────────────┬──────────────────────────┘
    
                     ▼
    
    3. Environment Setup
    ═══════════════════════
    ┌─────────────────────────────────────────────┐
    │ env = SimulationEnvironment(                │
    │     chiller_array=array,                    │
    │     wind=wind,                              │
    │     interaction_model=model                 │
    │ )                                           │
    │ # Precomputes interaction matrix A (N×N)   │
    └──────────────────┬──────────────────────────┘
    
                     ▼
    
    4. Performance Calculation
    ═══════════════════════════
    ┌─────────────────────────────────────────────┐
    │ active_mask = np.ones(25, dtype=bool)       │
    │ result = env.compute_performance(           │
    │     active_mask=active_mask,                │
    │     total_load_kw=100.0                     │
    │ )                                           │
    └──────────────────┬──────────────────────────┘
                       │
                       │ Internal Steps:
                       │ ───────────────
                       │ a) Distribute load: load_per_unit = 100.0 / 25 = 4.0 kW
                       │ b) Compute temp rise: temp_rise = active_mask @ A
                       │ c) Degrade COP: cop = base_cop / (1 + alpha * temp_rise)
                       │ d) Sum work: total_work = sum(load / cop)
                       ▼
    ┌─────────────────────────────────────────────┐
    │ PerformanceResult(                          │
    │     total_work_kw=27.8,                     │
    │     cop_array=[3.5, 3.8, 2.9, ...],         │
    │     temp_rise_array=[0.5, 0.3, 1.2, ...],   │
    │     load_per_unit_kw=4.0                    │
    │ )                                           │
    └──────────────────┬──────────────────────────┘
    
                     ▼
    
    5. Optimization (Optional)
    ═══════════════════════════
    ┌─────────────────────────────────────────────┐
    │ optimizer = Optimizer(env, total_load_kw=100)│
    │ opt_result = optimizer.optimize_greedy(     │
    │     min_active=15                           │
    │ )                                           │
    └──────────────────┬──────────────────────────┘
                       │
                       │ Internal Loop:
                       │ ──────────────
                       │ For each iteration:
                       │   - Try removing each active chiller
                       │   - Compute resulting total_work_kw
                       │   - Keep removal that reduces work most
                       │   - Repeat until no improvement
                       ▼
    ┌─────────────────────────────────────────────┐
    │ OptimizationResult(                         │
    │     optimal_mask=[T,T,F,T,F,...],           │
    │     optimal_work_kw=24.5,                   │
    │     baseline_work_kw=27.8,                  │
    │     savings_fraction=0.118,  # 11.8%        │
    │     performance=PerformanceResult(...),     │
    │     iterations=10                           │
    │ )                                           │
    └─────────────────────────────────────────────┘


Key Design Patterns
-------------------

Composition Over Inheritance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The package uses composition to build complex functionality:

* ``SimulationEnvironment`` **holds** instances of ``ChillerArray``, ``WindVector``, and ``BaseInteractionModel``
* Not using inheritance hierarchies (no ``SimulationEnvironment`` subclasses)
* Allows runtime swapping: ``env.with_new_wind()`` creates new environment

**Benefits**:
  - Easier testing (mock individual components)
  - Flexible model switching
  - Clear dependency graph

Immutability
~~~~~~~~~~~~

Thermodynamic states use immutable data structures:

* ``ChillerSpec``: frozen dataclass
* ``ChillerState``: NamedTuple
* ``WindVector``: frozen dataclass
* ``PerformanceResult``: NamedTuple
* ``OptimizationResult``: NamedTuple

**Benefits**:
  - Thread-safe
  - Prevents accidental state mutation
  - Enables functional programming patterns
  - Clear data lineage

Vectorization
~~~~~~~~~~~~~

All array operations use NumPy broadcasting and vectorized functions:

* **No explicit for-loops** over chiller arrays
* Pairwise operations via broadcasting: ``positions_m[np.newaxis, :, :] - positions_m[:, np.newaxis, :]``
* Matrix operations: ``temp_rise = active_mask @ interaction_matrix``
* Einsum for projections: ``np.einsum("ijk,k->ij", displacements, wind_dir)``

**Benefits**:
  - 10-100× performance improvement
  - Readable mathematical notation
  - Leverages BLAS/LAPACK

Type Safety
~~~~~~~~~~~

Comprehensive type hints throughout:

* Function signatures: ``def compute_performance(active_mask: NDArray[np.bool_], total_load_kw: float) -> PerformanceResult``
* Pydantic validation at boundaries
* NumPy dtype specifications: ``np.float64``, ``np.bool_``

**Benefits**:
  - Catch errors at development time (mypy, pylance)
  - Self-documenting code
  - IDE autocomplete support


Physics Implementation
----------------------

The package models thermal interference using a three-step process:

Step 1: Interaction Matrix Computation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``GaussianPlumeModel`` computes an N×N matrix **A** where ``A[k,m]`` represents the thermal impact of chiller ``k``'s exhaust on chiller ``m``'s inlet.

**Vectorized Algorithm**:

.. code-block:: python

    # Step 1: All pairwise displacements (N×N×2)
    d_km = positions[None, :, :] - positions[:, None, :]
    
    # Step 2: Longitudinal distance along wind (N×N)
    long_dist = np.einsum("ijk,k->ij", d_km, wind_dir)
    
    # Step 3: Lateral distance perpendicular to wind (N×N)
    lat_vec = d_km - long_dist[:,:,None] * wind_dir
    lat_dist = np.linalg.norm(lat_vec, axis=2)
    
    # Step 4: Gaussian plume formula
    A = np.exp(-lat_dist**2 / (sigma * (long_dist + 1))) / (long_dist + 1)
    
    # Step 5: Zero out upwind and self-interactions
    A = np.where(long_dist > 0, A, 0.0)
    np.fill_diagonal(A, 0.0)

Step 2: Temperature Rise Calculation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a given activation pattern ``active_mask``, compute temperature rise at each chiller:

.. code-block:: python

    # Convert boolean mask to float (0.0 or 1.0)
    active_float = active_mask.astype(np.float64)
    
    # Matrix-vector multiply: temp_rise[m] = sum_k(A[k,m] * active[k])
    temp_rise = active_float @ A  # Shape: (N,)

Step 3: COP Degradation & Power Calculation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply the COP degradation model and sum total electrical work:

.. code-block:: python

    # Degrade COP based on temperature rise
    cop_array = base_cop / (1.0 + alpha * temp_rise)  # Shape: (N,)
    
    # Distribute load evenly among active chillers
    n_active = np.sum(active_mask)
    load_per_unit = total_load_kw / n_active
    
    # Total electrical work (sum over active units only)
    cop_active = cop_array[active_mask]
    total_work_kw = np.sum(load_per_unit / cop_active)


Extension Points
----------------

The architecture is designed for extensibility at several points:

Custom Interaction Models
~~~~~~~~~~~~~~~~~~~~~~~~~~

Implement ``BaseInteractionModel`` to use different physics:

.. code-block:: python

    from src.models.base_interaction import BaseInteractionModel
    import numpy as np
    
    class MyCustomModel(BaseInteractionModel):
        def __init__(self, custom_param: float):
            self.custom_param = custom_param
        
        def compute_interaction_matrix(self, positions_m, wind):
            n = len(positions_m)
            # Your custom physics here
            A = np.zeros((n, n), dtype=np.float64)
            # ... populate A ...
            return A
    
    # Use in simulation
    model = MyCustomModel(custom_param=2.5)
    env = SimulationEnvironment(array, wind, model)

Custom Array Layouts
~~~~~~~~~~~~~~~~~~~~

Create specialized array geometries:

.. code-block:: python

    # L-shaped configuration
    positions_l = np.concatenate([
        np.array([[i*3, 0] for i in range(10)]),      # Horizontal
        np.array([[0, j*3] for j in range(1, 10)])    # Vertical
    ])
    array = ChillerArray(positions_m=positions_l, base_cop=4.5, alpha=0.8)

Alternative Optimization Strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Optimizer`` class can be extended with new methods:

.. code-block:: python

    class AdvancedOptimizer(Optimizer):
        def optimize_genetic(self, population_size=50, generations=100):
            # Genetic algorithm implementation
            pass
        
        def optimize_simulated_annealing(self, temp_init=1000):
            # Simulated annealing implementation
            pass


Performance Considerations
--------------------------

Computational Complexity
~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------+----------------+------------------+
| Operation                 | Complexity     | Bottleneck       |
+===========================+================+==================+
| Interaction matrix        | O(N²) space    | Memory for large |
| computation               | O(N²) time     | arrays (N>1000)  |
+---------------------------+----------------+------------------+
| Performance calculation   | O(N²) time     | Matrix multiply  |
|                           | (once)         |                  |
+---------------------------+----------------+------------------+
| Greedy optimization       | O(N³) time     | N iterations ×   |
|                           |                | N evaluations    |
+---------------------------+----------------+------------------+

Memory Usage
~~~~~~~~~~~~

For a chiller array with N units:

* Positions: 2N × 8 bytes = 16N bytes
* Interaction matrix: N² × 8 bytes
* Active mask: N × 1 byte
* Results: ~5N × 8 bytes

**Example**: N=100 chillers
  - Interaction matrix: 100² × 8 = 80 KB
  - Total: ~85 KB (very manageable)

For very large arrays (N>10,000), consider:
  - Sparse matrix representations
  - Chunked computation
  - Approximation methods (cut-off distances)


Testing Architecture
--------------------

The test suite mirrors the source structure:

.. code-block:: text

    tests/
    ├── test_core/
    │   ├── test_configs.py      # Pydantic validation tests
    │   └── test_constants.py    # Constant value tests
    ├── test_components/
    │   ├── test_wind.py         # Wind vector tests
    │   ├── test_chiller.py      # Chiller spec/state tests
    │   └── test_chiller_array.py # Array layout tests
    ├── test_models/
    │   └── test_gaussian_plume.py # Physics model tests
    ├── test_simulation/
    │   ├── test_environment.py  # Integration tests
    │   └── test_optimizer.py    # Optimization tests
    └── conftest.py              # Shared fixtures

**Key Test Strategies**:

1. **Unit Tests**: Isolated component behavior
2. **Integration Tests**: Component composition
3. **Physics Validation**: Known analytical solutions
4. **Regression Tests**: AHRI 550/590 compliance (``verification/``)
5. **Property Tests**: Invariants (e.g., COP always decreases with interference)


References
----------

* ASHRAE Handbook - Fundamentals (2021), Chapter 24: Airflow Around Buildings
* ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40: Cooling Towers
* ASHRAE Handbook - HVAC Applications, Chapter 43: Data Centers
* AHRI Standard 550/590-2015: Performance Rating of Water-Chilling Packages
* EPA AP-42: Compilation of Air Pollutant Emission Factors


See Also
--------

* :doc:`getting-started` - Quick introduction to using the package
* :doc:`user-guide` - Detailed usage instructions
* :doc:`examples` - Example workflows and case studies
* :doc:`api/index` - Complete API reference
