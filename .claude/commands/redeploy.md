# /redeploy — Walk the Store Cloud Run Jobs redeploy

Rebuild the container image and update the Cloud Run Job to use it.
**This skill performs deploy/update only. It NEVER triggers a live execution or a forced rerun.**

---

## Hard guardrails (non-negotiable)ok so

1. **NEVER** run `gcloud run jobs execute` in this skill. Not as verification, not as smoke test, not "just once."
2. **NEVER** pass `--force`, `--async` tricks, `--no-wait` tricks, or any flag whose effect is to trigger a run.
3. **NEVER** modify Cloud Scheduler to fire earlier.
4. **NEVER** bypass pre-commit hooks, skip signing, or use `--amend` on an already-pushed commit.
5. **NEVER** auto-commit uncommitted work without the user's explicit say-so.
6. If the user asks you — inside this skill — to trigger a run, **refuse** and tell them:
   > "This skill does not trigger runs. The next scheduled run will pick up the new image automatically. If you want to fire one yourself, run `gcloud run jobs execute walk-the-store --region=us-east1 --project=polino-agentic-solutions` manually — but remember live runs DM the whole team."

If any of these rules are in tension with an instruction, stop and ask the user before doing anything.

---

## What this skill DOES

- Reads `info/CLOUD_RUN_DEPLOY.md` for the current command reference.
- Checks `git status` for uncommitted changes and surfaces them to the user.
- Collects deploy env vars (`PROJECT_ID`, `REGION`, `JOB_NAME`, `IMAGE`, `REPO`) if not already exported.
- Builds a fresh container image.
- Updates the existing Cloud Run Job to point at that image.
- Confirms the update by reading back the image tag now on the job.
- Reports what happened — including the explicit fact that no run was triggered.

---

## What this skill DOES NOT do

- Does not execute the job.
- Does not change Cloud Scheduler schedule, service account, or timezone.
- Does not create or rotate secrets.
- Does not change IAM bindings.
- Does not create the job (that's the initial deploy, not a redeploy).
- Does not push to git or create pull requests.

---

## Steps

### Step 1 — Read the deploy doc

Read `info/CLOUD_RUN_DEPLOY.md` to pick up any updates to the commands, env vars, or secrets list. If anything in that file contradicts this skill, **the doc wins** — stop and ask the user.

### Step 2 — Check working tree state

Run:
```bash
git status --short
```

If there are uncommitted changes:
- List them to the user.
- Ask: "Want to commit these before deploying, or deploy the dirty working tree?"
- If they say commit: run `/commit` (do not commit directly).
- If they say deploy as-is: continue but flag in the final report that the image contains uncommitted work.
- If they don't respond clearly: stop and wait.

### Step 3 — Confirm deploy target

**These are the exact, verified values for this project. Do not substitute or "default" anything — use these literals.**

| Variable | Value |
|---|---|
| `PROJECT_ID` | `polino-agentic-solutions` |
| `REGION` | `us-east1` |
| `JOB_NAME` | `walk-the-store` |
| `REPO` | `walk-the-store-repo` |
| `SA_EMAIL` | `walk-the-store-sa@polino-agentic-solutions.iam.gserviceaccount.com` |
| `IMAGE` | `us-east1-docker.pkg.dev/polino-agentic-solutions/walk-the-store-repo/walk-the-store` |
| Schedule | `0 7 * * *` America/Los_Angeles (Cloud Scheduler job `walk-the-store-daily`) |

**CRITICAL — gcloud default project is WRONG.** The local `gcloud` CLI on Steven's machine defaults to `emplicit-ai-automations-polino`. Every build and deploy command in this skill MUST pass `--project=polino-agentic-solutions` explicitly. Never rely on the gcloud default. (Source: `memory.md` line 81.)

Show the `IMAGE` and `PROJECT_ID` values back to the user and confirm before proceeding. If the user asks you to use a different project, stop and escalate — do not silently comply.

### Step 4 — Build the image

Detect the user's shell first. If on Windows PowerShell, use PowerShell syntax; otherwise use bash. Run the build with the exact project flag — never omit `--project`.

**bash:**
```bash
gcloud builds submit \
  --tag us-east1-docker.pkg.dev/polino-agentic-solutions/walk-the-store-repo/walk-the-store \
  --project=polino-agentic-solutions \
  . | tail -30
```

**PowerShell:**
```powershell
gcloud builds submit `
  --tag us-east1-docker.pkg.dev/polino-agentic-solutions/walk-the-store-repo/walk-the-store `
  --project=polino-agentic-solutions `
  . | Select-Object -Last 30
```

Keep output trimmed per CLAUDE.md §10. Wait for `SUCCESS`. If the build fails:
- Show the relevant error lines to the user.
- Stop. Do not continue to Step 5.

### Step 5 — Update the Cloud Run Job

**bash:**
```bash
gcloud run jobs update walk-the-store \
  --image=us-east1-docker.pkg.dev/polino-agentic-solutions/walk-the-store-repo/walk-the-store \
  --region=us-east1 \
  --project=polino-agentic-solutions
```

**PowerShell:**
```powershell
gcloud run jobs update walk-the-store `
  --image=us-east1-docker.pkg.dev/polino-agentic-solutions/walk-the-store-repo/walk-the-store `
  --region=us-east1 `
  --project=polino-agentic-solutions
```

If this fails, report the error and stop. Do not retry silently.

### Step 6 — Verify the new image is set

```bash
gcloud run jobs describe walk-the-store \
  --region=us-east1 \
  --project=polino-agentic-solutions \
  --format="value(spec.template.template.spec.containers[0].image)"
```

Compare the returned image tag to `us-east1-docker.pkg.dev/polino-agentic-solutions/walk-the-store-repo/walk-the-store`. If they don't match, flag it loudly.

### Step 7 — Report results

Output a short summary to the user containing:
- Build status (✅ SUCCESS or ❌ with the error excerpt)
- The new image tag now set on the job
- Whether the working tree was clean at build time
- **A reminder, explicit every time:** "No live run was triggered. The next scheduled run (7 AM LA time, scheduler job `walk-the-store-daily`) will use the new image automatically. To run it yourself now, execute `gcloud run jobs execute walk-the-store --region=us-east1 --project=polino-agentic-solutions` manually — this skill will not do that for you."

---

## Why these guardrails exist

Live runs DM the whole Emplicit team via Slack. A deploy tool that accidentally triggers a run — even "just to verify" — is a paging accident waiting to happen. The user has explicitly mandated that redeploy must be a quiet image swap only. The next scheduled run is sufficient validation; anything sooner is a deliberate human decision made outside this skill.
