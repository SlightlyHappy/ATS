from __future__ import annotations
import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

# Configure logging for worker process
configure_logging(settings.LOG_LEVEL, service="worker", env=settings.ENV)
log = get_logger("celery")

celery_app = Celery(
    "resume_analyzer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_routes={
        "app.workers.tasks.*_io": {"queue": "io"},
        "app.workers.tasks.*_llm": {"queue": "llm"},
        "app.workers.tasks.monitor_resume_status": {"queue": "io"},
        "app.workers.tasks.resume_health_check": {"queue": "io"},
    },
    worker_concurrency=int(os.getenv("WORKER_CONCURRENCY", "24")),  # Increased from 8 to 24 for 32-core system
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,       # 10 minutes hard limit
    worker_prefetch_multiplier=4,  # More aggressive task prefetching
    beat_schedule={
        "monitor-resume-status": {
            "task": "monitor_resume_status",
            "schedule": 60.0,  # Run every 1 minute (was 5 minutes) - much more aggressive monitoring
        },
        "resume-health-check": {
            "task": "resume_health_check", 
            "schedule": 300.0,  # Run every 5 minutes (was 30 minutes) - more frequent health checks
        },
    },
    timezone='UTC',
)


@task_prerun.connect
def _on_task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):  # type: ignore[no-redef]
    try:
        task_name = getattr(sender, "name", None)
        # Reduce logging verbosity - skip health check tasks
        if task_name and not task_name.endswith('_health_check'):
            log.info("celery_task_start", task=task_name, task_id=task_id)
    except Exception:
        pass


@task_postrun.connect
def _on_task_postrun(sender=None, task_id=None, retval=None, state=None, **extra):  # type: ignore[no-redef]
    try:
        task_name = getattr(sender, "name", None)
        # Only log failures and important task completions to reduce log volume
        if task_name and not task_name.endswith('_health_check'):
            if state in ['FAILURE', 'RETRY'] or (state == 'SUCCESS' and '_io' in task_name):
                log.info("celery_task_done", task=task_name, task_id=task_id, state=state)
    except Exception:
        pass


@task_failure.connect
def _on_task_failure(task_id=None, exception=None, traceback=None, sender=None, **kwargs):  # type: ignore[no-redef]
    try:
        task_name = getattr(sender, "name", None)
        # Always log failures but without full traceback to reduce volume
        error_msg = str(exception) if exception else 'Unknown error'
        log.error("celery_task_fail", task=task_name, task_id=task_id, error=error_msg)
    except Exception:
        pass
