Generate a properly formatted git commit for the current staged or unstaged changes, following the rules in CLAUDE.md Section 8.

Steps:
1. Run `git status` to see what files have changed
2. Run `git diff` to review what changed in each file
3. Group changes by logical unit — one commit per file or closely related set of files
4. For each commit needed, output the exact git command to run in this format:

```
git add [filename]
git commit -m "type: short description"
```

Valid types: `feature`, `fix`, `refactor`, `test`, `docs`, `config`, `chore`

Rules from CLAUDE.md:
- One commit per file or logical unit — do not bundle unrelated files
- Message format: `type: short description` (lowercase, no period)
- Never include `.env`, secrets, or `claude_resume` in commits
- Never use `--no-verify`

After outputting the commands, remind the user:
> "Before committing, confirm you have added a comment above each Claude-generated block in your own words explaining what it does."

Do not run the git commands automatically — output them for the user to review and run.
