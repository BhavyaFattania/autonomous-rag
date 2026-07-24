"""REST endpoints for browsing past runs, backed by experiments.sqlite via
the existing repository layer (src/storage/repositories/)."""

import dataclasses

from fastapi import APIRouter, HTTPException

from src.storage.repositories.experiment_repository import ExperimentRepository
from src.storage.repositories.node_event_repository import NodeEventRepository
from src.storage.repositories.run_repository import RunRepository

router = APIRouter(prefix="/api")


@router.get("/runs")
async def list_runs():
    runs = await RunRepository().list_runs()
    return [dataclasses.asdict(run) for run in runs]


@router.get("/runs/{run_id}/experiments")
async def list_run_experiments(run_id: str):
    experiments = await ExperimentRepository().find_by_run_id(run_id)
    return [dataclasses.asdict(experiment) for experiment in experiments]


@router.get("/runs/{run_id}/events")
async def list_run_events(
    run_id: str,
    node: str | None = None,
    status: str | None = None,
    before_id: int | None = None,
    limit: int = 50,
):
    """Filterable, cursor-paginated node-tick log feed for one run -- the
    logger-style view: every pipeline node's tick, newest first."""
    events = await NodeEventRepository().find_by_run_id(
        run_id, node=node, status=status, before_id=before_id, limit=min(limit, 200)
    )
    return [dataclasses.asdict(event) for event in events]


@router.get("/experiments/by-uuid/{experiment_uuid}/events")
async def get_experiment_events(experiment_uuid: str):
    """Full ordered node timeline for one experiment attempt -- works
    identically whether it's still running, just finished, or from a run
    several restarts ago, since experiment_uuid is the durable join key."""
    return [
        dataclasses.asdict(event)
        for event in await NodeEventRepository().find_by_experiment_uuid(experiment_uuid)
    ]


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: int):
    experiment = await ExperimentRepository().find_by_id(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return dataclasses.asdict(experiment)
