Getting Started
===============

A short guide to install and run your first simulation.


Installation
------------

Install from source:

.. code-block:: bash

   git clone https://github.com/example/chiller-model.git
   cd chiller-model
   pip install -e .


Basic Concepts
--------------

When chillers are packed close together, hot exhaust from one can blow into
another's intake. That heats the air and makes the second chiller work harder.

Key Concepts
^^^^^^^^^^^^

**COP (Coefficient of Performance)**
   Cooling output ÷ electrical input. A COP of 4.0 means 4 kW cooling per 1 kW electricity.

**Thermal Interference**
   One chiller's exhaust heats another's intake, so the second chiller loses efficiency.

**Gaussian Plume Model**
   A physics-based model for how hot exhaust spreads downwind.


Package Structure
^^^^^^^^^^^^^^^^^

- ``src.core``: Constants and configuration
- ``src.components``: Wind, chillers, data center load
- ``src.models``: Thermal interaction models (e.g. Gaussian plume)
- ``src.simulation``: Simulation and optimization


Your First Simulation
---------------------

Here's a minimal example:

.. code-block:: python

   import numpy as np
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment

   # 1. Wind (5 m/s east, 25°C)
   wind = WindVector(
       velocity_m_per_s=(5.0, 2.0),
       ambient_temp_k=298.15
   )

   # 2. Chiller array (4×4 grid, 3 m spacing)
   array = ChillerArray.create_grid(
       rows=4, cols=4, spacing_m=3.0,
       base_cop=4.0, alpha=0.7
   )

   # 3. Interaction model
   model = GaussianPlumeModel(dispersion_coeff=1.2)

   # 4. Run simulation
   env = SimulationEnvironment(array, wind, model)
   active_mask = np.ones(array.num_chillers, dtype=bool)
   result = env.compute_performance(active_mask, total_load_kw=100.0)

   print(f"Total work: {result.total_work_kw:.2f} kW")
   print(f"Mean COP: {np.mean(result.cop_array):.2f}")


Understanding the Results
^^^^^^^^^^^^^^^^^^^^^^^^^

``compute_performance`` returns:

- ``total_work_kw``: Total electrical power (kW)
- ``cop_array``: COP per chiller (degraded by thermal interference)
- ``load_array``: Load per chiller (kW)


Optimization
------------

The package includes an optimizer that finds the best subset of chillers to run:

.. code-block:: python

   from src.simulation import Optimizer

   # Create optimizer for a given load
   optimizer = Optimizer(env, total_load_kw=100.0)

   # Run greedy optimization (keep at least 10 units active)
   opt_result = optimizer.optimize_greedy(min_active=10)

   # Get the optimized configuration
   optimal_mask = opt_result.optimal_mask
   print(f"Active chillers: {opt_result.num_active}")
   print(f"Final work: {opt_result.final_work_kw:.2f} kW")

The optimizer uses a greedy removal strategy, iteratively turning off
the chiller whose removal provides the greatest efficiency improvement.


Next Steps
----------

- See :doc:`user-guide` for detailed usage examples
- See :doc:`examples` for real-world scenarios
- See :doc:`api/index` for the complete API reference
