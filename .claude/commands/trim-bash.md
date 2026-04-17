Review the last Bash command result in this conversation and identify if the output was larger than necessary. If so, suggest the trimmed version of the command using `| head -N`, `| tail -N`, `| grep "pattern"`, or `--limit=N` flags. Also check for any pending Bash commands in the plan and pre-trim them before running.

Reminder rules for this project:
- All `gcloud logging read` calls must include `--limit=N` and pipe through `grep`
- Build commands (`gcloud builds submit`) should use `--async` or `| tail -10`
- Never dump raw log output — always filter to ERROR/WARNING/key lines
- Never `cat` large files — use Read tool with offset/limit
