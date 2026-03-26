Chiller Simulation Documentation
=================================

Simulate how data center chillers affect each other and find the most efficient
way to run them.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   user-guide
   examples
   api/index


Overview
--------

When chillers sit close together, hot exhaust from one can blow into another's
intake. That heats the air and makes the second chiller work harder -- using more
electricity for the same cooling.

This package models that effect and helps you choose which chillers to run.

- **Thermal interference**: Physics-based Gaussian plume model of exhaust affecting neighbors
- **Optimization**: Greedy selection of the best subset of chillers to run
- **Aging**: Models capacity loss as chillers get older
- **Startup ramp**: Freshly started chillers come online at reduced capacity
- **Dynamic simulation**: Time-varying load, wind, and ambient temperature
- **Modular design**: Swap physics plugins via the fluent builder API


Quick Start
-----------

.. code-block:: python

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
   print(f"Work: {result.total_work_kw:.2f} kW")


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
