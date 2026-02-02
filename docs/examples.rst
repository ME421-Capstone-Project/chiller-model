Examples
========

This page provides practical examples demonstrating key features of the
chiller simulation package.


Example 1: Visualizing a Thermal Plume
--------------------------------------

Visualize how one chiller's exhaust affects the entire array:

.. code-block:: python

   import numpy as np
   import matplotlib.pyplot as plt
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment

   # Setup
   wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
   array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
   model = GaussianPlumeModel(dispersion_coeff=1.2)
   env = SimulationEnvironment(array, wind, model)

   # Get thermal impact from the center chiller (index 12)
   source_idx = 12
   thermal_impact = env.interaction_matrix[source_idx, :]
   positions = array.positions_m

   # Plot
   fig, ax = plt.subplots(figsize=(8, 6))
   sc = ax.scatter(
       positions[:, 0], positions[:, 1],
       c=thermal_impact, cmap='YlOrBr', s=200, edgecolor='k'
   )
   ax.scatter(
       positions[source_idx, 0], positions[source_idx, 1],
       c='blue', s=300, marker='*', label='Source'
   )
   plt.colorbar(sc, label='Temperature Rise Factor')
   ax.set_title("Thermal Wake of a Single Chiller")
   ax.legend()
   plt.show()


Example 2: The Density Penalty
------------------------------

Compare COP of an isolated chiller vs. one surrounded by active neighbors:

.. code-block:: python

   import numpy as np
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment

   # Setup 5x5 array
   wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
   array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0, base_cop=4.0)
   env = SimulationEnvironment(array, wind, GaussianPlumeModel(1.2))

   center_idx = 12  # Middle chiller

   # Case A: Center chiller alone
   state_solo = np.zeros(array.num_chillers, dtype=bool)
   state_solo[center_idx] = True
   result_solo = env.compute_performance(state_solo, 10.0)
   cop_solo = result_solo.cop_array[center_idx]

   # Case B: All chillers active
   state_full = np.ones(array.num_chillers, dtype=bool)
   result_full = env.compute_performance(state_full, 250.0)
   cop_full = result_full.cop_array[center_idx]

   # Calculate efficiency loss
   efficiency_loss = (cop_solo - cop_full) / cop_solo * 100

   print(f"Isolated Chiller COP: {cop_solo:.2f}")
   print(f"Crowded Chiller COP: {cop_full:.2f}")
   print(f"Efficiency Loss: {efficiency_loss:.1f}%")

Expected output::

   Isolated Chiller COP: 4.00
   Crowded Chiller COP: 2.80
   Efficiency Loss: 30.1%


Example 3: "Less is More" Optimization
--------------------------------------

Demonstrate that running fewer, optimally-selected chillers can be more
efficient than running all of them:

.. code-block:: python

   import numpy as np
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment, Optimizer

   # Setup
   wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
   array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
   env = SimulationEnvironment(array, wind, GaussianPlumeModel(1.2))

   total_load = 100.0  # kW

   # Case A: All 25 chillers
   state_all = np.ones(array.num_chillers, dtype=bool)
   result_all = env.compute_performance(state_all, total_load)

   # Case B: Optimized 15 chillers
   optimizer = Optimizer(env, total_load)
   opt_result = optimizer.optimize_greedy(min_active=15)
   result_opt = env.compute_performance(opt_result.optimal_mask, total_load)

   # Compare
   print(f"25 chillers: {result_all.total_work_kw:.2f} kW")
   print(f"15 optimized: {result_opt.total_work_kw:.2f} kW")
   
   savings = (result_all.total_work_kw - result_opt.total_work_kw) / \
             result_all.total_work_kw * 100
   print(f"Energy savings: {savings:.2f}%")


Example 4: Wind Direction Sensitivity
-------------------------------------

Analyze how different wind directions affect system efficiency:

.. code-block:: python

   import numpy as np
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment

   # Create array
   array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
   model = GaussianPlumeModel(1.2)
   active_mask = np.ones(array.num_chillers, dtype=bool)
   total_load = 100.0

   # Test different wind angles
   angles = np.linspace(0, 360, 37)  # Every 10 degrees
   results = []

   for angle in angles:
       wind = WindVector.from_speed_and_angle(
           speed_m_per_s=2.0,
           angle_deg=angle,
           ambient_temp_k=298.15
       )
       env = SimulationEnvironment(array, wind, model)
       result = env.compute_performance(active_mask, total_load)
       results.append(result.total_work_kw)

   # Find best and worst angles
   best_idx = np.argmin(results)
   worst_idx = np.argmax(results)

   print(f"Best wind angle: {angles[best_idx]:.0f}° ({results[best_idx]:.2f} kW)")
   print(f"Worst wind angle: {angles[worst_idx]:.0f}° ({results[worst_idx]:.2f} kW)")


Example 5: Comparing Interaction Models
---------------------------------------

Compare different thermal interaction models on the same array:

.. code-block:: python

   import numpy as np
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel, BaseInteractionModel
   from src.simulation import SimulationEnvironment

   # Custom simple model
   class SimpleDistanceModel(BaseInteractionModel):
       def __init__(self, decay: float = 0.5):
           self.decay = decay
       
       def compute_interaction_matrix(self, positions, wind):
           n = len(positions)
           A = np.zeros((n, n))
           wind_vec = wind.direction
           for k in range(n):
               for m in range(n):
                   if k != m:
                       d = positions[m] - positions[k]
                       if np.dot(d, wind_vec) > 0:
                           A[k, m] = self.decay / (np.linalg.norm(d) + 1)
           return A

   # Setup
   wind = WindVector(velocity_m_per_s=(1.0, 0.4), ambient_temp_k=298.15)
   array = ChillerArray.create_grid(rows=5, cols=5, spacing_m=3.0)
   active = np.ones(array.num_chillers, dtype=bool)
   load = 100.0

   # Compare models
   models = {
       "Gaussian (σ=1.2)": GaussianPlumeModel(1.2),
       "Gaussian (σ=2.0)": GaussianPlumeModel(2.0),
       "Simple Distance": SimpleDistanceModel(0.5),
   }

   for name, model in models.items():
       env = SimulationEnvironment(array, wind, model)
       result = env.compute_performance(active, load)
       print(f"{name}: {result.total_work_kw:.2f} kW (Mean COP: {np.mean(result.cop_array):.2f})")


Example 6: Large-Scale Array Analysis
-------------------------------------

Simulate a larger data center with 100 chillers:

.. code-block:: python

   import numpy as np
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment, Optimizer

   # 10x10 array
   array = ChillerArray.create_grid(rows=10, cols=10, spacing_m=5.0)
   wind = WindVector(velocity_m_per_s=(3.0, 1.0), ambient_temp_k=303.15)
   model = GaussianPlumeModel(1.5)
   env = SimulationEnvironment(array, wind, model)

   total_load = 500.0  # kW

   # Find optimal number of active chillers
   results = []
   for n_active in range(20, 101, 10):
       optimizer = Optimizer(env, total_load)
       opt_result = optimizer.optimize_greedy(min_active=n_active)
       perf = env.compute_performance(opt_result.optimal_mask, total_load)
       results.append((n_active, perf.total_work_kw))
       print(f"{n_active} chillers: {perf.total_work_kw:.2f} kW")

   # Find sweet spot
   min_work = min(results, key=lambda x: x[1])
   print(f"\nOptimal configuration: {min_work[0]} chillers at {min_work[1]:.2f} kW")


Jupyter Notebook Demo
---------------------

For an interactive experience with visualizations, see the ``demo.ipynb``
notebook included in the repository. It provides:

- Side-by-side comparisons with plots
- Interactive thermal plume visualization
- Step-by-step optimization walkthrough
