Chiller Simulation Documentation
=================================

Simulate how data center chillers affect each other and find the most efficient
way to run them.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   architecture
   visual-guide
   user-guide
   examples
   api/index


Overview
--------

When chillers sit close together, hot exhaust from one can blow into another's
intake. That heats the air and makes the second chiller work harder—using more
electricity for the same cooling.

This package models that effect and helps you choose which chillers to run.

- **Thermal interference**: Physics-based model of exhaust affecting neighbors
- **Optimization**: Finds the best subset of chillers to run
- **Aging**: Models efficiency loss as chillers get older
- **Dynamic simulation**: Time-varying load, wind, and startup
- **Modular design**: Swap models and components easily


Quick Start
-----------

.. code-block:: python

   import numpy as np
   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment

   wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)
   array = ChillerArray.create_grid(rows=4, cols=4, spacing_m=10.0)
   model = GaussianPlumeModel(dispersion_coeff=1.2)
   env = SimulationEnvironment(array, wind, model)

   active_mask = np.ones(array.num_chillers, dtype=bool)
   result = env.compute_performance(active_mask, total_load_kw=500.0)
   print(f"Work: {result.total_work_kw:.2f} kW")


Physics Background
------------------

Thermal Interference Model
^^^^^^^^^^^^^^^^^^^^^^^^^^

The Gaussian plume dispersion model calculates thermal interference between chillers:

.. math::

   A_{km} = \frac{\exp(-d_{lat}^2 / (\sigma (d_{long} + 1)))}{d_{long} + 1}

where:

- :math:`A_{km}`: Thermal impact of chiller k on chiller m
- :math:`d_{long}`: Longitudinal distance along wind direction (m)
- :math:`d_{lat}`: Lateral distance perpendicular to wind (m)
- :math:`\sigma`: Dispersion coefficient (default 1.2)

The COP degradation follows:

.. math::

   COP_m = \frac{COP_{base}}{1 + \alpha \sum_k A_{km}}


References
----------

- ASHRAE Handbook - Fundamentals, 2021
- ASHRAE Handbook - HVAC Systems and Equipment, Chapter 40
- AHRI Standard 550/590-2015


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
