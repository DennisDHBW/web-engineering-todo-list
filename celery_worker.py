from tasks import celery_app

# Worker starts with: celery -A celery_worker.celery_app worker --loglevel=info