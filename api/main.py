"""FastAPI application for the chiller simulation demo."""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from schemas import SimulationRequest, SimulationResponse
from simulation import get_ages_years, run_simulation, stream_simulation

app = FastAPI(title="Chiller Sim API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/simulate", response_model=SimulationResponse)
async def simulate(req: SimulationRequest) -> SimulationResponse:
    """Run the full simulation synchronously and return all steps."""
    steps = run_simulation(req)
    return SimulationResponse(
        steps=steps,
        num_chillers=req.rows * req.cols,
        rows=req.rows,
        cols=req.cols,
        ages_years=get_ages_years(req),
    )


@app.post("/api/simulate/stream")
async def simulate_stream(req: SimulationRequest) -> EventSourceResponse:
    """Stream simulation results as Server-Sent Events, one per time step."""

    async def _event_generator():
        ages = get_ages_years(req)
        meta = json.dumps(
            {
                "num_chillers": req.rows * req.cols,
                "rows": req.rows,
                "cols": req.cols,
                "ages_years": ages,
            }
        )
        yield {"event": "meta", "data": meta}

        for step in stream_simulation(req):
            yield {"event": "step", "data": step.model_dump_json()}

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(_event_generator())


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Simple liveness check."""
    return {"status": "ok"}
