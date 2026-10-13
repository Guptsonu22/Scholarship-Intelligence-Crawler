"""Crawl Scheduler API Routes.

Exposes controlled scheduler start, stop, and status inspection endpoints.
"""
from fastapi import APIRouter
from app.models.schemas import SchedulerStatusResponse, SchedulerControlResponse
from app.services.crawling.scheduler import scheduler

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.post("/start", response_model=SchedulerControlResponse)
def start_scheduler():
    """Starts the background recurring crawl scheduler daemon."""
    res = scheduler.start()
    return SchedulerControlResponse(**res)


@router.post("/stop", response_model=SchedulerControlResponse)
def stop_scheduler():
    """Gracefully stops the background recurring crawl scheduler daemon."""
    res = scheduler.stop()
    return SchedulerControlResponse(**res)


@router.get("/status", response_model=SchedulerStatusResponse)
def get_scheduler_status():
    """Retrieves current scheduler active state, interval, and next scheduled run."""
    return scheduler.get_status()
