User Guide
==========

Architecture, builder reference, simulation methods, results, and physics
plugins.


Architecture
------------

Three layers, each depending only on the one above it::

   layout (ChillerLayout, WindConditions)
       |
   physics (CopFn, DegradationFn, RampFn, GaussianPlumeModel)
       |
   simulation (SimulatorBuilder -> Simulator)

**layout** -- Defines where chillers sit (on a rectangular grid via
``with_grid()`` or in arbitrary positions via ``with_layout()``) and what the
wind looks like at a given moment.

**physics** -- Pluggable functions that model COP degradation, capacity aging,
startup ramp behaviour, and thermal plume dispersion.

**simulation** -- Assembles the pieces via a fluent builder, runs the
optimizer, and returns typed result objects.


SimulatorBuilder Reference
--------------------------

``SimulatorBuilder`` (imported as ``Simulator``) is the main entry point.
Chain configuration methods, then call ``.build()`` to get a ``Simulator``.

Grid / Layout
^^^^^^^^^^^^^

Use ``with_grid()`` for rectangular arrangements or ``with_layout()`` for
arbitrary chiller positions:

.. code-block:: python

   .with_grid(
       rows=4, cols=4, spacing_m=10.0,
       base_cop=4.0, max_cooling_kw=500.0,
       alpha=0.7,                     # thermal sensitivity coefficient
       ages_years=np.array([...]),     # optional, one value per chiller
       seed=42,                        # optional, for reproducible random ages
   )

Wind
^^^^

Static wind (constant for the entire run):

.. code-block:: python

   .with_wind(speed_m_per_s=5.0, angle_deg=0.0)

Time-varying wind (called at each time step):

.. code-block:: python

   def my_wind_fn(time_hours: float) -> tuple[float, float]:
       """Return (speed_m_per_s, angle_deg) at the given time."""
       return (5.0, 90.0 + 30.0 * math.sin(2 * math.pi * time_hours / 12))

   .with_wind_fn(my_wind_fn)

Temperature
^^^^^^^^^^^

Static ambient temperature:

.. code-block:: python

   .with_ambient_temp(temp_k=298.15)

Time-varying ambient temperature:

.. code-block:: python

   .with_ambient_temp_fn(lambda t: 298.15 + 5.0 * math.sin(2 * math.pi * t / 24))

Load
^^^^

A callable returning facility load in kW at a given time:

.. code-block:: python

   .with_load_fn(lambda t: 300.0 + 500.0 * math.sin(2 * math.pi * t / 24))

Physics Plugins
^^^^^^^^^^^^^^^

Override the default COP, degradation, or ramp functions:

.. code-block:: python

   .with_cop_fn(my_cop_fn)
   .with_degradation_fn(my_degradation_fn)
   .with_ramp_fn(my_ramp_fn)

Dispersion
^^^^^^^^^^

Set the Gaussian plume dispersion coefficient (default 1.2):

.. code-block:: python

   .with_dispersion(coeff=1.5)

The default :class:`~chiller_sim.physics.gaussian_plume.GaussianPlumeModel`
implements a simplified constant-:math:`\sigma` form of the standard
ground-level Gaussian plume. For an ordered pair of chillers where :math:`x`
is the along-wind distance from source *k* to target *m*, :math:`y` is the
cross-wind distance, :math:`u` is the wind speed, :math:`\sigma` is
``dispersion_coeff``, and :math:`u_{\min}` is ``u_min_m_per_s``, the per-pair
thermal influence is:

.. math::

    I_{k \to m} = \begin{cases}
        0 & u < u_{\min} \\
        \dfrac{1}{u\,(x + 1)}\,\exp\!\left(-\dfrac{y^{2}}{\sigma\,(x + 1)}\right)
            & x > 0,\ u \ge u_{\min} \\
        0 & \text{otherwise}
    \end{cases}

The :math:`1/u` factor is the dilution term from the full Gaussian plume
equation: stronger wind sweeps the plume away faster and reduces the heat
deposited on downwind chillers. ``u_min_m_per_s`` is a *hard cutoff*, not a
floor — below it the model returns zero interaction at any distance, reflecting
the assumption that the plume model does not apply in near-calm conditions.

Switching Threshold
^^^^^^^^^^^^^^^^^^^

Minimum energy savings (kW) required to switch a chiller on or off.
Prevents toggling when the benefit is marginal:

.. code-block:: python

   .with_switching_threshold(min_savings_kw=2.0)

Build
^^^^^

.. code-block:: python

   simulator = builder.build()

Raises ``ValueError`` if required fields are missing. Required: grid or layout,
wind or wind_fn, ambient_temp or ambient_temp_fn, load_fn.


Running Simulations
-------------------

optimize
^^^^^^^^

Single-step, state-aware optimization:

.. code-block:: python

   result = simulator.optimize(time_hours=0.0, load_kw=800.0)

Returns an ``OptimizeResult``. Pass ``load_kw`` to override the load
function for this step, or omit it to use the configured ``load_fn``.

stream
^^^^^^

Yields one ``OptimizeResult`` per time step. Advances clocks automatically:

.. code-block:: python

   for result in simulator.stream(duration_hours=24.0, time_step_hours=1.0):
       print(f"t={result.time_hours:.1f}h  work={result.total_work_kw:.1f} kW")

Use ``stream`` when you want to process results incrementally or react to
each step (e.g. logging, plotting).

simulate
^^^^^^^^

Returns a ``SimulationResult`` containing all steps:

.. code-block:: python

   sim_result = simulator.simulate(
       duration_hours=24.0,
       time_step_hours=1.0,
       initial_state=InitialState(active_mask=mask, time_since_start_hours=times),
   )

Use ``simulate`` when you need post-hoc analysis across all time steps.


Results Reference
-----------------

OptimizeResult
^^^^^^^^^^^^^^

Returned by ``optimize()`` and yielded by ``stream()``:

- ``time_hours`` -- Simulation time
- ``load_kw`` -- Facility load at this step (kW)
- ``active_mask`` -- Boolean array of active chillers
- ``cop_array`` -- Effective COP per chiller
- ``temp_rise_array`` -- Inlet temperature rise per chiller (K)
- ``total_work_kw`` -- Total electrical power (kW)
- ``baseline_work_kw`` -- Power if all chillers ran
- ``savings_fraction`` -- Energy saved vs. baseline

SimulationResult
^^^^^^^^^^^^^^^^

Returned by ``simulate()``. Wraps a list of ``OptimizeResult`` steps and
provides array-level properties:

- ``total_work_kw`` -- Shape ``(n_steps,)`` array of total work
- ``loads_kw`` -- Shape ``(n_steps,)`` array of facility load
- ``savings_fraction`` -- Shape ``(n_steps,)`` array of savings
- ``schedule`` -- Shape ``(n_steps, n_chillers)`` boolean active schedule
- ``cop_arrays`` -- Shape ``(n_steps, n_chillers)`` COP per step per chiller


Physics Plugins
---------------

Each plugin is a callable matching a Protocol. Supply your own via the
builder's ``with_*`` methods, or use the defaults.

CopFn
^^^^^

.. code-block:: python

   def my_cop_fn(base_cop: float, temp_rise_k: float, ambient_temp_k: float) -> float:
       return base_cop / (1.0 + 0.5 * temp_rise_k)

Default: ``default_cop_fn(alpha)`` -- ``base_cop / (1 + alpha * temp_rise_k)``

Equivalently, with :math:`\mathrm{COP}_{\text{base}}` the nameplate COP,
:math:`\alpha` the thermal sensitivity coefficient, and
:math:`\Delta T_{\text{rise}}` the inlet temperature rise above ambient:

.. math::

    \mathrm{COP}(\Delta T_{\text{rise}}) =
        \frac{\mathrm{COP}_{\text{base}}}{1 + \alpha \,\Delta T_{\text{rise}}}

Effective COP falls as the inlet air warms up: chillers downwind of other
active chillers see elevated :math:`\Delta T_{\text{rise}}` via the plume
model, which drives their COP (and therefore cooling efficiency) down.

DegradationFn
^^^^^^^^^^^^^

.. code-block:: python

   def my_degradation_fn(age_years: float) -> float:
       return max(0.5, 1.0 - 0.02 * age_years)

Default: ``default_capacity_degradation_fn(years_to_80_pct=10.0)`` --
exponential decay reaching 80% capacity at the specified age.

RampFn
^^^^^^

.. code-block:: python

   def my_ramp_fn(time_since_start_hours: float) -> float:
       return min(1.0, time_since_start_hours / 0.5)

Default: linear ramp from 0.1 at t=0 to 1.0 at t=0.25 h.

WindFn
^^^^^^

.. code-block:: python

   def my_wind_fn(time_hours: float) -> tuple[float, float]:
       """Return (speed_m_per_s, angle_deg)."""
       return (5.0, 90.0)

AmbientTempFn
^^^^^^^^^^^^^

.. code-block:: python

   def my_ambient_fn(time_hours: float) -> float:
       """Return ambient temperature in Kelvin."""
       return 298.15


Warm Start with InitialState
-----------------------------

Pass an ``InitialState`` to ``simulate()`` to warm-start from a known
configuration:

.. code-block:: python

   from chiller_sim import InitialState

   state = InitialState(
       active_mask=np.array([True, True, False, False]),
       time_since_start_hours=np.array([1.0, 0.5, 0.0, 0.0]),
   )

   result = simulator.simulate(
       duration_hours=24.0,
       time_step_hours=1.0,
       initial_state=state,
   )

Chillers marked active in the initial state skip the startup ramp
proportional to their ``time_since_start_hours``.
