# /redeploy — Walk the Store Cloud Run Jobs redeploy

Rebuild the container image and update the Cloud Run Job to use it.
**This skill performs deploy/update only. It NEVER triggers a live execution or a forced rerun.**

---

## Hard guardrails (non-negotiable)

1. **NEVER** run `gcloud run jobs execute` in this skill. Not as verification, not as smoke test, not "just once."
2. **NEVER** pass `--force`, `--async` tricks, `--no-wait` tricks, or any flag whose effect is to trigger a run.
3. **NEVER** modify Cloud Scheduler to fire earlier.
4. **NEVER** bypass pre-commit hooks, skip signing, or use `--amend` on an already-pushed commit.
5. **NEVER** auto-commit uncommitted work without the user's explicit say-so.
6. If the user asks you — inside this skill — to trigger a run, **refuse** and tell them:
   > "This skill does not trigger runs. The next scheduled run will pick up the new image automatically. If you want to fire one yourself, run `gcloud run jobs execute $JOB_NAME --region=$REGION --project=$PROJECT_ID` manually — but remember live runs DM the whole team."

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

Ask the user to confirm (or provide) these env vars:
- `PROJECT_ID` (e.g. `walk-the-store-prod`)
- `REGION` (default: `us-east1`)
- `JOB_NAME` (default: `walk-the-store`)
- `REPO` (default: `walk-the-store-repo`)

Construct:
- `IMAGE = $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$JOB_NAME`

Show the constructed `IMAGE` back to the user. Do not proceed until they confirm these values are correct.

### Step 4 — Build the image

Run:
```bash
gcloud builds submit --tag $IMAGE . --project=$PROJECT_ID | tail -30
```

Keep output trimmed per CLAUDE.md §10. Wait for `SUCCESS`. If the build fails:
- Show the relevant error lines to the user.
- Stop. Do not continue to Step 5.

### Step 5 — Update the Cloud Run Job

Run:
```bash
gcloud run jobs update $JOB_NAME \
  --image=$IMAGE \
  --region=$REGION \
  --project=$PROJECT_ID
```

If this fails, report the error and stop. Do not retry silently.

### Step 6 — Verify the new image is set

Run:
```bash
gcloud run jobs describe $JOB_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(spec.template.template.spec.containers[0].image)"
```

Compare the returned image tag to `$IMAGE`. If they don't match, flag it loudly.

### Step 7 — Report results

Output a short summary to the user containing:
- Build status (✅ SUCCESS or ❌ with the error excerpt)
- The new image tag now set on the job
- Whether the working tree was clean at build time
- **A reminder, explicit every time:** "No live run was triggered. The next scheduled run (7 AM LA time) will use the new image automatically. To run it yourself now, execute `gcloud run jobs execute $JOB_NAME --region=$REGION --project=$PROJECT_ID` manually — this skill will not do that for you."

---

## Why these guardrails exist

Live runs DM the whole Emplicit team via Slack. A deploy tool that accidentally triggers a run — even "just to verify" — is a paging accident waiting to happen. The user has explicitly mandated that redeploy must be a quiet image swap only. The next scheduled run is sufficient validation; anything sooner is a deliberate human decision made outside this skill.
