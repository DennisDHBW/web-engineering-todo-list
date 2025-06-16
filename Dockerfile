# This Dockerfile is optimized for development use.
# In production, consider using multi-stage builds for smaller final images.

FROM python:3.11-slim

ENV PYTHONPATH=/app
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Install cron and celery beat scheduler
RUN apt-get install -y cron

RUN adduser --disabled-password celeryuser
USER celeryuser

CMD ["bash", "-c", "cd app && python wait_for_db.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]