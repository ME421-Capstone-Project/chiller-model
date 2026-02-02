Getting Started
===============

This guide will help you get up and running with the chiller simulation package.


Installation
------------

Install from source:

.. code-block:: bash

   git clone https://github.com/example/chiller-model.git
   cd chiller-model
   pip install -e .


Basic Concepts
--------------

The package models thermal interference effects in chiller arrays caused by
wind-driven exhaust recirculation. When chillers are packed closely together,
the hot exhaust from one unit can be drawn into the intake of another,
reducing efficiency.

Key Concepts
^^^^^^^^^^^^

**Coefficient of Performance (COP)**
   The ratio of cooling provided to electrical power consumed.
   A COP of 4.0 means 4 kW of cooling per 1 kW of electricity.

**Thermal Interference**
   When exhaust from one chiller affects the intake temperature of another,
   degrading its COP.

**Gaussian Plume Model**
   A physics-based model for how thermal plumes disperse downwind.


Package Structure
^^^^^^^^^^^^^^^^^

The package follows a modular, component-based architecture:

- ``src.core``: Constants and Pydantic-validated configuration models
- ``src.components``: Physical component models (WindVector, ChillerArray)
- ``src.models``: Pluggable thermal interaction models (GaussianPlumeModel)
- ``src.simulation``: Simulation orchestration and optimization


Your First Simulation
---------------------

Here's a minimal example that sets up a chiller array and runs a simulation:

.. code-block:: python

   import numpy as np
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment

   # 1. Define wind conditions
   #    WindVector is an immutable dataclass representing atmospheric conditions
   wind = WindVector(
       velocity_m_per_s=(5.0, 2.0),  # (vx, vy) in m/s
       ambient_temp_k=298.15  # 25°C in Kelvin
   )

   # 2. Create a chiller array
   #    This creates a 4x4 grid with 3-meter spacing
   array = ChillerArray.create_grid(
       rows=4,
       cols=4,
       spacing_m=3.0,
       base_cop=4.0,  # Base COP at rated conditions
       alpha=0.7      # Sensitivity to temperature rise
   )

   # 3. Set up the thermal interaction model
   model = GaussianPlumeModel(dispersion_coeff=1.2)

   # 4. Create the simulation environment
   env = SimulationEnvironment(
       chiller_array=array,
       wind=wind,
       interaction_model=model
   )

   # 5. Run a simulation with all chillers active
   active_mask = np.ones(array.num_chillers, dtype=bool)
   result = env.compute_performance(active_mask, total_load_kw=100.0)

   print(f"Total electrical work: {result.total_work_kw:.2f} kW")
   print(f"Mean COP: {np.mean(result.cop_array):.2f}")


Understanding the Results
^^^^^^^^^^^^^^^^^^^^^^^^^

The ``compute_performance`` method returns a ``PerformanceResult`` namedtuple with:

- ``total_work_kw``: Total electrical power consumed (kW)
- ``cop_array``: COP for each chiller (degraded by thermal interference)
- ``load_array``: Cooling load assigned to each chiller (kW)


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
