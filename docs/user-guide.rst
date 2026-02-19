User Guide
==========

Main features and how to use them.


Wind: Atmospheric Conditions
----------------------------

``WindVector`` holds wind speed, direction, and ambient temperature (all SI units).

**Create from velocity (vx, vy) in m/s:**

.. code-block:: python

   from src.components import WindVector

   wind = WindVector(
       velocity_m_per_s=(5.0, 2.0),
       ambient_temp_k=298.15
   )

**Or from speed and angle (degrees from x-axis):**

.. code-block:: python

   wind = WindVector.from_speed_and_angle(
       speed_m_per_s=5.0,
       angle_deg=45.0,
       ambient_temp_k=298.15
   )

**Useful attributes:**

.. code-block:: python

   wind.speed_m_per_s     # Scalar speed
   wind.direction         # Unit vector (vx, vy)
   wind.ambient_temp_k    # Temperature (K)


ChillerArray: Layout and Properties
-----------------------------------

``ChillerArray`` holds chiller positions and properties (base COP, alpha, age).

**Grid layout:**

.. code-block:: python

   from src.components import ChillerArray

   array = ChillerArray.create_grid(
       rows=5, cols=5, spacing_m=3.0,
       base_cop=4.0, alpha=0.7
   )

**Custom positions:**

.. code-block:: python

   import numpy as np

   positions = np.array([[0, 0], [5, 0], [2.5, 4.33]])
   array = ChillerArray(positions_m=positions, base_cop=4.0, alpha=0.7)

**Aging:** Pass ``ages_years`` (one value per chiller) to model older units.
Omit it for new chillers (age 0). See the Examples page for details.

**Alpha:** How sensitive COP is to inlet temperature rise. Higher = more
degradation. Typical: 0.5–1.0.


Interaction Models
------------------

Interaction models compute the thermal interference between chillers.

GaussianPlumeModel
^^^^^^^^^^^^^^^^^^

The default model uses Gaussian plume dispersion physics:

.. code-block:: python

   from src.models import GaussianPlumeModel

   model = GaussianPlumeModel(dispersion_coeff=1.2)

The dispersion coefficient (σ) controls plume spread:

- Lower values (~0.8): Narrow, concentrated plumes
- Higher values (~2.0): Wide, dispersed plumes

Custom Interaction Models
^^^^^^^^^^^^^^^^^^^^^^^^^

Create custom models by subclassing ``BaseInteractionModel``:

.. code-block:: python

   from src.models import BaseInteractionModel
   from src.components import WindVector
   import numpy as np

   class SimpleDistanceModel(BaseInteractionModel):
       """A simple inverse-distance interaction model."""
       
       def __init__(self, decay_factor: float = 1.0):
           self.decay_factor = decay_factor
       
       def compute_interaction_matrix(
           self,
           positions: np.ndarray,
           wind: WindVector
       ) -> np.ndarray:
           """Compute interaction based on downwind distance."""
           n = len(positions)
           wind_vec = wind.direction
           A = np.zeros((n, n), dtype=np.float64)
           
           for k in range(n):
               for m in range(n):
                   if k == m:
                       continue
                   d_km = positions[m] - positions[k]
                   long_dist = np.dot(d_km, wind_vec)
                   if long_dist > 0:  # Only affect downwind units
                       distance = np.linalg.norm(d_km)
                       A[k, m] = self.decay_factor / (distance + 1.0)
           
           return A


SimulationEnvironment
---------------------

The ``SimulationEnvironment`` orchestrates the simulation by combining
the chiller array, wind conditions, and interaction model.

Setup and Execution
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.simulation import SimulationEnvironment
   import numpy as np

   env = SimulationEnvironment(
       chiller_array=array,
       wind=wind,
       interaction_model=model
   )

   # The interaction matrix is computed automatically
   print(f"Matrix shape: {env.interaction_matrix.shape}")

   # Run simulation with a boolean mask
   active_mask = np.ones(array.num_chillers, dtype=bool)
   active_mask[0] = False  # Turn off first chiller
   
   result = env.compute_performance(active_mask, total_load_kw=100.0)


PerformanceResult
^^^^^^^^^^^^^^^^^

The result contains:

.. code-block:: python

   result.total_work_kw   # Total electrical consumption
   result.cop_array       # COP for each chiller
   result.load_array      # Load assigned to each chiller


Optimization
------------

The ``Optimizer`` class finds efficient chiller configurations.

Greedy Optimization
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.simulation import Optimizer

   optimizer = Optimizer(env, total_load_kw=100.0)

   # Keep at least 15 chillers active
   result = optimizer.optimize_greedy(min_active=15)

   print(f"Active: {result.num_active}")
   print(f"Work: {result.optimal_work_kw:.2f} kW")
   print(f"Mask: {result.optimal_mask}")

The optimizer starts with all chillers on, then removes the one whose removal
saves the most energy, until ``min_active`` remain.

Comparing Strategies
^^^^^^^^^^^^^^^^^^^^

Compare standard vs. optimized activation:

.. code-block:: python

   # Standard: First N chillers
   state_std = np.zeros(array.num_chillers, dtype=bool)
   state_std[:15] = True
   result_std = env.compute_performance(state_std, 100.0)

   # Optimized: Greedy selection
   result_opt = optimizer.optimize_greedy(min_active=15)
   state_opt = result_opt.optimal_mask
   result_opt_perf = env.compute_performance(state_opt, 100.0)

   # Calculate improvement
   improvement = (result_std.total_work_kw - result_opt_perf.total_work_kw) / \
                  result_std.total_work_kw * 100
   print(f"Efficiency improvement: {improvement:.2f}%")


Pydantic Configuration
----------------------

The package uses Pydantic for validated configuration:

.. code-block:: python

   from src.core.configs import ChillerConfig, WindConfig, SimulationConfig

   # Validated chiller configuration
   chiller_config = ChillerConfig(
       base_cop=4.5,         # Must be > 0 and <= 10
       rated_capacity_kw=50.0,
       alpha=0.8
   )

   # Validated wind configuration
   wind_config = WindConfig(
       velocity_x_m_per_s=5.0,
       velocity_y_m_per_s=2.0,
       ambient_temp_k=300.0  # Must be in realistic range
   )

   # Simulation configuration
   sim_config = SimulationConfig(
       dispersion_coeff=1.5,
       total_load_kw=100.0
   )

Invalid values raise ``ValidationError`` with helpful messages.


Best Practices
--------------

1. **Use SI Units**: All internal calculations use SI (K, Pa, kg/s, J).
   Convert at input/output boundaries.

2. **Immutable States**: WindVector and results are immutable.
   Create new instances rather than modifying.

3. **Boolean Masks**: Use ``dtype=bool`` for active masks, not float.

4. **Vectorization**: The package uses NumPy for efficient array operations.
   Avoid Python loops when working with results.

5. **Validation**: Use Pydantic configs for user-facing interfaces
   to catch invalid parameters early.
