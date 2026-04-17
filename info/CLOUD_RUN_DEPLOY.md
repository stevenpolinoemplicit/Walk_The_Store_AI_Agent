# CLOUD_RUN_DEPLOY.md — Manual Cloud Run Jobs Deploy Guide

Walk the Store runs as a **Cloud Run Job** triggered by **Cloud Scheduler** on a daily schedule.
The container runs `python main.py`, processes all accounts, and exits — no persistent connection,
no HTTP endpoint, no port required.

---

## Prerequisites

- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- Docker installed locally
- GCP project created with Cloud Run, Artifact Registry, and Cloud Scheduler APIs enabled
- Service account with: Cloud Run Jobs Invoker, Secret Manager Accessor, Google Docs + Drive scopes

---

## Step 1: Set project variables

```bash
export PROJECT_ID=your-gcp-project-id
export REGION=us-east1
export JOB_NAME=walk-the-store
export REPO=walk-the-store-repo
export IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$JOB_NAME
export SA_EMAIL=walk-the-store-sa@$PROJECT_ID.iam.gserviceaccount.com
```

---

## Step 2: Create Artifact Registry repository (first deploy only)

```bash
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID
```

---

## Step 3: Build and push the Docker image

```bash
gcloud builds submit --tag $IMAGE .
```

---

## Step 4: Store secrets in Secret Manager (first deploy only)

```bash
# Use printf (not echo) to avoid trailing newline on Windows/PowerShell
printf 'your-value' | gcloud secrets create ANTHROPIC_API_KEY --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create EMPLICIT_PG_HOST --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create EMPLICIT_PG_PORT --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create EMPLICIT_PG_DB --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create EMPLICIT_PG_USER --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create EMPLICIT_PG_PASSWORD --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create SLACK_BOT_TOKEN --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create SLACK_OPS_CHANNEL --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create TEAMWORK_DOMAIN --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create TEAMWORK_API_TOKEN --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create BRAND_SHEET_ID --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create PEOPLE_SHEET_ID --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create GOOGLE_IMPERSONATION_EMAIL --data-file=- --project=$PROJECT_ID
printf 'your-value' | gcloud secrets create DRIVE_OPS_FOLDER_ID --data-file=- --project=$PROJECT_ID

# For Google service account JSON — store the file contents directly
gcloud secrets create GOOGLE_SERVICE_ACCOUNT_JSON \
  --data-file=path/to/sa.json --project=$PROJECT_ID
```

---

## Step 5: Create the Cloud Run Job

```bash
gcloud run jobs create $JOB_NAME \
  --image=$IMAGE \
  --region=$REGION \
  --service-account=$SA_EMAIL \
  --task-timeout=10m \
  --set-secrets="ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,\
EMPLICIT_PG_HOST=EMPLICIT_PG_HOST:latest,\
EMPLICIT_PG_PORT=EMPLICIT_PG_PORT:latest,\
EMPLICIT_PG_DB=EMPLICIT_PG_DB:latest,\
EMPLICIT_PG_USER=EMPLICIT_PG_USER:latest,\
EMPLICIT_PG_PASSWORD=EMPLICIT_PG_PASSWORD:latest,\
SLACK_BOT_TOKEN=SLACK_BOT_TOKEN:latest,\
SLACK_OPS_CHANNEL=SLACK_OPS_CHANNEL:latest,\
TEAMWORK_DOMAIN=TEAMWORK_DOMAIN:latest,\
TEAMWORK_API_TOKEN=TEAMWORK_API_TOKEN:latest,\
BRAND_SHEET_ID=BRAND_SHEET_ID:latest,\
PEOPLE_SHEET_ID=PEOPLE_SHEET_ID:latest,\
GOOGLE_IMPERSONATION_EMAIL=GOOGLE_IMPERSONATION_EMAIL:latest,\
DRIVE_OPS_FOLDER_ID=DRIVE_OPS_FOLDER_ID:latest,\
GOOGLE_SERVICE_ACCOUNT_JSON=GOOGLE_SERVICE_ACCOUNT_JSON:latest" \
  --project=$PROJECT_ID
```

---

## Step 6: Schedule with Cloud Scheduler

```bash
# Create a service account for Cloud Scheduler to invoke the job (if not already created)
gcloud iam service-accounts create scheduler-invoker \
  --display-name="Cloud Scheduler — Walk the Store invoker" \
  --project=$PROJECT_ID

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:scheduler-invoker@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Runs at 7:00 AM Los Angeles time daily (handles DST automatically)
gcloud scheduler jobs create http walk-the-store-daily \
  --location=$REGION \
  --schedule="0 7 * * *" \
  --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
  --http-method=POST \
  --oauth-service-account-email="scheduler-invoker@$PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="America/Los_Angeles" \
  --project=$PROJECT_ID
```

---

## Step 7: Test manually

Run the job once without waiting for the schedule:

```bash
gcloud run jobs execute $JOB_NAME --region=$REGION --project=$PROJECT_ID
```

Stream the logs:

```bash
gcloud run jobs executions list --job=$JOB_NAME --region=$REGION --project=$PROJECT_ID
# Then tail logs for the most recent execution ID shown above:
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" \
  --limit=50 --project=$PROJECT_ID --format="value(textPayload)"
```

---

## Step 8: Update after a code change

```bash
gcloud builds submit --tag $IMAGE .
gcloud run jobs update $JOB_NAME --image=$IMAGE --region=$REGION --project=$PROJECT_ID
```

---

## Notes

- `--task-timeout=10m` gives the job up to 10 minutes to complete all accounts. Increase if you have many brands.
- Cloud Run Jobs retry failed executions by default — set `--max-retries=0` if you want no retries (avoids duplicate Slack alerts on transient failures).
- Cost: essentially free — you pay only for actual CPU/memory seconds during the ~60s run once per day.
- **Secrets:** Always use `printf 'value'` not `echo "value"` when storing secrets — `echo` adds a trailing newline on Windows/PowerShell which causes auth failures.
