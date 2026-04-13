# Dockerfile — Walk the Store AI Agent
# Deployed as a Cloud Run Job. Runs main.py once and exits.
# Triggered by Cloud Scheduler on a daily schedule.
# No port or health check endpoint required — Cloud Run Jobs are not HTTP services.

FROM python:3.13-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer independently of source changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project source files
COPY . .

CMD ["python", "main.py"]
