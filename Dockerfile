FROM python:3.11-slim

WORKDIR /code

RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Install cron and celery beat scheduler
RUN apt-get install -y cron

CMD ["bash", "-c", "python wait_for_db.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]