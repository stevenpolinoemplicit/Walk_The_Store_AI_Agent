Check that all required environment variables are present in the `.env` file without exposing any values.

Steps:
1. Read `.env.example` to get the full list of required keys
2. Check whether a `.env` file exists in the project root
3. For each key in `.env.example`, check if it exists AND has a non-empty value in `.env`

Output a table:

| Key | Status |
|---|---|
| ANTHROPIC_API_KEY | ✅ Set |
| INTENTWISE_CLIENT_ID | ❌ Missing |
| ... | ... |

Then output:
- **Ready to run:** Yes / No
- **Missing keys:** list any that are empty or absent
- **Blocked keys:** note any that are intentionally pending (e.g. INTENTWISE_CLIENT_ID/SECRET) per PROJECT_SCOPE.md blockers

Never print the actual values — only confirm present/missing.
If `.env` does not exist at all, instruct the user to run: `cp .env.example .env` and fill in values.
