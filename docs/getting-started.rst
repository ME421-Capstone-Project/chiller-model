Getting Started
===============

A short guide to install the package and run your first optimization.


Installation
------------

Install from source:

.. code-block:: bash

   git clone https://github.com/example/chiller-model.git
   cd chiller-model
   pip install -e .


Basic Concepts
--------------

**COP (Coefficient of Performance)**
   Cooling output divided by electrical input. A COP of 4.0 means 4 kW of
   cooling per 1 kW of electricity.

**Thermal interference**
   Exhaust from one chiller heats a neighbour's intake, forcing it to work
   harder for the same cooling output.

**Max cooling capacity**
   Each chiller has a nameplate limit (kW of cooling). Aging reduces this
   capacity over time.

**Startup ramp**
   A freshly started chiller comes online at reduced capacity and ramps to
   full output over a short period (default 15 minutes).


Package Structure
-----------------

- ``chiller_sim.layout``: Grid geometry and wind conditions
- ``chiller_sim.physics``: COP, degradation, ramp, and plume models
- ``chiller_sim.simulation``: Builder, simulator, and result types


Minimal Working Example
-----------------------

.. code-block:: python

   import numpy as np
   from chiller_sim import Simulator

   sim = (
       Simulator()
       .with_grid(rows=2, cols=2, spacing_m=10.0, base_cop=4.0, max_cooling_kw=500.0)
       .with_wind(speed_m_per_s=5.0, angle_deg=0.0)
       .with_ambient_temp(temp_k=298.15)
       .with_load_fn(lambda t: 800.0)
       .build()
   )

   result = sim.optimize(time_hours=0.0)

   print(f"Active mask:    {result.active_mask}")
   print(f"COP per chiller: {np.round(result.cop_array, 2)}")
   print(f"Total work:     {result.total_work_kw:.2f} kW")


Understanding Results
---------------------

``optimize()`` returns an ``OptimizeResult`` with these fields:

- ``time_hours`` -- Simulation time of this step
- ``load_kw`` -- Facility cooling load (kW)
- ``active_mask`` -- Boolean array: which chillers are running
- ``cop_array`` -- Effective COP for each chiller
- ``temp_rise_array`` -- Inlet temperature rise per chiller (K)
- ``total_work_kw`` -- Total electrical power consumed (kW)
- ``baseline_work_kw`` -- Power if all chillers were running
- ``savings_fraction`` -- Fraction of energy saved vs. baseline


Next Steps
----------

- See :doc:`user-guide` for the full API narrative and architecture overview
- See :doc:`examples` for worked examples with generated images
- See :doc:`api/index` for the complete API reference
