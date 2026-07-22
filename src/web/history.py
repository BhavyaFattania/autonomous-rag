"""REST endpoints for browsing past runs, backed by experiments.sqlite via
the existing repository layer (src/storage/repositories/)."""

import dataclasses

from fastapi import APIRouter, HTTPException

from src.storage.repositories.experiment_repository import ExperimentRepository
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


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: int):
    experiment = await ExperimentRepository().find_by_id(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return dataclasses.asdict(experiment)
