import os
from celery import Celery

# Set the default Django settings module (if using Django)
# For a pure CrewAI project, we'll use a direct configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "crewai_flow",
    broker=REDIS_URL,
    backend=REDIS_URL,  # Use Redis as result backend as well
    include=["tasks.celery_tasks"]   # Import tasks module
)

# Optional: Configure Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,      # 30 minutes
    task_soft_time_limit=25 * 60, # 25 minutes
    worker_prefetch_multiplier=1, # Fair task distribution
)