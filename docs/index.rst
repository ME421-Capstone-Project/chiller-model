Chiller Simulation Documentation
=================================

A modular simulation package for chiller array thermal interactions with wind effects.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/index


Overview
--------

This package provides tools for simulating thermal interference effects in chiller
arrays caused by wind-driven exhaust recirculation. Key features:

- **Modular Design**: Components are independent and composable
- **Pluggable Models**: Easy to swap thermal interaction models
- **SI Units**: All internal calculations use SI units (K, Pa, kg/s, J)
- **Validated Inputs**: Pydantic models ensure physical plausibility


Quick Start
-----------

.. code-block:: python

   from src.components import WindVector, ChillerArray
   from src.models import GaussianPlumeModel
   from src.simulation import SimulationEnvironment

   # Create wind conditions
   wind = WindVector(velocity_m_per_s=(5.0, 0.0), ambient_temp_k=298.15)

   # Create chiller array (4x4 grid, 10m spacing)
   array = ChillerArray.create_grid(rows=4, cols=4, spacing_m=10.0)

   # Create interaction model
   model = GaussianPlumeModel(dispersion_coeff=1.2)

   # Run simulation
   env = SimulationEnvironment(array, wind, model)
   result = env.compute_performance(active_mask, total_load_kw=500.0)


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
