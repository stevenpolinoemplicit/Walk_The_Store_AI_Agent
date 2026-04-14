# how_to_build_claude_SKILLS.md
> Reference guide for building Claude Code Agent Skills.
> Based on the Agent Skills open standard (agentskills.io) and Anthropic course material.
> Add this file to any project template repo so contributors know how to build, structure, and optimize skills.

---

## What Are Skills?

Skills are on-demand, task-specific instructions that load into Claude's context only when relevant. They are **not** always-on rules — those belong in `CLAUDE.md`.

| Feature | When it's active | Best for |
|---|---|---|
| `CLAUDE.md` | Every conversation, always | Project-wide standards, coding style, constraints that always apply |
| **Skills** | Only when Claude matches a request | Task-specific expertise, detailed procedures, workflows that would clutter every conversation |
| Hooks | Event-driven (file save, tool call) | Automated side effects, linting, validation on every action |
| Subagents | Isolated execution context | Delegated tasks that need separate tool access or context isolation |
| MCP Servers | External tool integrations | Third-party APIs, databases, services |

**Rule of thumb:** If you want Claude to know it every time — use `CLAUDE.md`. If you want Claude to know it only when the task is relevant — use a skill.

---

## Directory Structure

A skill is a **directory** with a required `SKILL.md` file. The directory name must match the `name` field exactly.

```
.claude/skills/
└── your-skill-name/
    ├── SKILL.md          # Required — metadata + instructions
    ├── scripts/          # Optional — executable code
    ├── references/       # Optional — detailed docs Claude reads on demand
    └── assets/           # Optional — templates, data files
```

Slash commands (explicit `/command-name` invocation) go in `.claude/commands/` as flat `.md` files.
Semantic skills (auto-triggered by matching the user's request) go in `.claude/skills/` as directories with `SKILL.md`.

---

## SKILL.md Format

Every `SKILL.md` must have YAML frontmatter followed by Markdown instructions.

```markdown
---
name: your-skill-name
description: A clear description of what this skill does and when Claude should use it.
allowed-tools: Read Grep Glob
model: sonnet
---

Skill instructions go here in Markdown.
```

### Frontmatter Fields

| Field | Required | Constraints |
|---|---|---|
| `name` | Yes | 1–64 chars. Lowercase letters, numbers, hyphens only. No leading/trailing hyphens. No consecutive hyphens. Must match directory name. |
| `description` | Yes | 1–1024 chars. What the skill does AND when to use it. This is the primary triggering mechanism. |
| `allowed-tools` | No | Space-delimited list of tools pre-approved when skill is active. Omit to use normal permission model. |
| `model` | No | Which Claude model to use. Example: `sonnet`, `claude-sonnet-4-6` |
| `license` | No | License name or path to bundled license file |
| `compatibility` | No | 1–500 chars. Environment requirements — Python version, required packages, network access, etc. |
| `metadata` | No | Arbitrary key-value map for additional properties |

### Valid name examples
```yaml
name: explain-file       # ✅
name: new-session        # ✅
name: deploy-checklist   # ✅
name: PDF-Processing     # ❌ uppercase not allowed
name: -pdf               # ❌ cannot start with hyphen
name: pdf--processing    # ❌ consecutive hyphens
```

### Minimal working example
```markdown
---
name: code-review
description: Reviews code for quality issues. Use when the user asks for a code review, says "review this", "check my code", or "look for issues in this file".
---

Review the file for: unused variables, missing error handling, and naming convention violations. Output as a bullet list grouped by severity.
```

---

## Writing Effective Descriptions

The description is the **only thing Claude uses to decide whether to activate your skill**. It is the highest-leverage field in the entire file.

### Two questions every description must answer
1. What does this skill do?
2. When should Claude use it?

### Rules
- Use **imperative phrasing**: "Use this skill when..." not "This skill does..."
- Focus on **user intent**, not implementation details
- Include specific **trigger phrases** that match how you actually talk
- Include an **"even if they don't explicitly say X"** clause for indirect triggers
- Add a **"does not trigger when"** clause to prevent false positives on near-misses
- Stay under **1024 characters**

### Good vs poor description

```yaml
# ❌ Poor — too vague, no trigger guidance
description: Helps with files.

# ✅ Good — imperative, specific triggers, clear scope
description: Use this skill when the user wants to understand what a file does,
  how it fits into the project, or what its functions mean. Triggers when the
  user says "explain this file", "what does this do", "walk me through this",
  "help me understand this code", or opens a file and asks about it — even if
  they don't say "explain" explicitly. Does not trigger for requests to write
  or modify code.
```

### If your skill isn't triggering
Add more keywords that match how you actually phrase requests. Test with real prompts, not invented ones.

### If your skill triggers too broadly
Add a "does not trigger when" clause that defines the boundary between your skill and adjacent capabilities.

---

## allowed-tools

Use `allowed-tools` to restrict what Claude can do when a skill is active. Useful for read-only workflows, security-sensitive operations, or any situation where you want guardrails.

```yaml
# Read-only skill — cannot write or edit files
allowed-tools: Read Grep Glob Bash

# Explanation skill — can only read
allowed-tools: Read

# Full write access (same as omitting the field)
# allowed-tools: Read Edit Write Bash Grep Glob
```

If you omit `allowed-tools` entirely, the skill does not restrict anything — Claude uses its normal permission model.

---

## Progressive Disclosure

When a skill activates, its full `SKILL.md` loads into Claude's context window. Every token competes for attention. Keep `SKILL.md` under **500 lines / 5,000 tokens**.

For content that is only needed sometimes, move it to `references/` or `scripts/` and tell Claude **exactly when to load it**.

```markdown
## Handling API errors

If the API returns a non-200 status, read `references/api-errors.md` for the
full error code reference before responding.
```

This is more useful than a generic "see references/ for details" — the agent won't know when to look unless you tell it the trigger.

### Scripts

Scripts in `scripts/` run without loading their contents into context. Only the output consumes tokens.

**Key rule:** Tell Claude to **run** the script, not read it.

```markdown
## Validate before deploying

Run `scripts/validate.py` and check the output. Do not proceed if it returns
any errors. Do not read the script file.
```

Good uses for scripts:
- Environment validation
- Data transformations that need to be consistent
- Operations more reliable as tested code than generated code

---

## Best Practices

### Start from real tasks, not generic knowledge
Build skills by extracting patterns from real completed tasks. A skill synthesized from your team's actual runbooks outperforms one from generic "best practices" articles.

Capture:
- Steps that worked — the sequence that led to success
- Corrections you made — where you steered Claude's approach
- Project-specific facts Claude wouldn't know from training

### Add what the agent lacks — omit what it knows
Don't explain what a PDF is, how HTTP works, or what a migration does. Focus on:
- Your specific API patterns and field names
- Non-obvious edge cases
- Project conventions that differ from defaults
- Gotchas that would cause mistakes

### Gotchas section
The highest-value content in many skills is a list of project-specific facts that defy reasonable assumptions.

```markdown
## Gotchas

- The `users` table uses soft deletes. Always include `WHERE deleted_at IS NULL`
  or results will include deactivated accounts.
- `user_id` in the DB = `uid` in auth service = `accountId` in billing API. Same value, three names.
- `/health` returns 200 even if the database is down. Use `/ready` for full health checks.
```

When Claude makes a mistake you have to correct — add it to the gotchas section immediately.

### Templates for output format
Provide a template when you need consistent output. Agents pattern-match against concrete structures better than prose descriptions.

```markdown
## Report format

Use this template:

\`\`\`markdown
## Summary
[One paragraph overview]

## Findings
- Finding with supporting data
- Finding with supporting data

## Recommended actions
1. Specific action
\`\`\`
```

### Checklists for multi-step workflows
Explicit checklists help Claude track progress and avoid skipping steps.

```markdown
## Deployment workflow

- [ ] Step 1: Run `scripts/validate.py`
- [ ] Step 2: Check output — fix any errors before continuing
- [ ] Step 3: Run `scripts/deploy.py --dry-run`
- [ ] Step 4: Confirm output looks correct, then run without `--dry-run`
```

### Calibrate specificity to fragility
Give the agent freedom when multiple approaches work. Be prescriptive when consistency or a specific sequence is critical.

```markdown
# Flexible — agent can use judgment
Check for SQL injection, missing auth checks, and error messages that leak internals.

# Prescriptive — must run this exact command
Run exactly: `python scripts/migrate.py --verify --backup`
Do not add additional flags.
```

### Provide defaults, not menus
Pick a default approach and mention alternatives briefly rather than presenting equal options.

```markdown
# ❌ Menu — agent has to choose
You can use pypdf, pdfplumber, PyMuPDF, or pdf2image...

# ✅ Default with escape hatch
Use pdfplumber for text extraction. For scanned PDFs requiring OCR, use pdf2image with pytesseract instead.
```

---

## Description Optimization

If a skill isn't triggering reliably, use this process:

1. **Write 20 test queries** — 10 that should trigger, 10 that shouldn't
2. **Should-trigger queries:** vary phrasing (formal/casual), explicitness (direct/indirect), and complexity
3. **Should-not-trigger queries:** use near-misses — queries that share keywords but need something different
4. **Split into train (60%) and validation (40%) sets**
5. **Test the current description** — does it trigger on should-trigger? Does it stay quiet on should-not-trigger?
6. **Fix failures** by addressing the general category, not the specific phrasing
7. **Validate** — run against the holdout set to confirm improvements generalize
8. **Repeat** — 5 iterations is usually enough

**Avoid overfitting:** Do not add the exact keywords from failed test queries. Find the concept they represent and address that.

---

## Skills vs CLAUDE.md — Deciding Where Things Go

Look at your current `CLAUDE.md`. Ask for each item: "Is this always relevant, or only sometimes?"

| If it's... | Put it in... |
|---|---|
| Always relevant (coding style, naming conventions, security rules) | `CLAUDE.md` |
| Only relevant for specific tasks (PR review, deployment, onboarding) | A skill |
| Triggered by an event (file save, tool call) | A hook |
| Needing isolated execution | A subagent |
| External tool or API integration | MCP server |

---

## Adding a New Skill (Checklist)

1. Create `.claude/skills/your-skill-name/` directory
2. Create `SKILL.md` with required frontmatter (`name`, `description`)
3. Write instructions — concise, project-specific, gotchas included
4. Add `allowed-tools` if the skill should be read-only or restricted
5. Add `model:` if a specific model is required
6. Test with real prompts — does it trigger when you expect? Stay quiet when you don't?
7. Add entry to `claude_skills_list.md` (or equivalent index file)
8. Commit the skill directory — never leave it uncommitted

---

## Quick Reference

```markdown
---
name: skill-name                  # required, matches directory name
description: Use this skill when  # required, 1024 char max, primary trigger
allowed-tools: Read Grep Glob      # optional, space-delimited
model: sonnet                      # optional
license: MIT                       # optional
compatibility: Requires Python 3.11+ # optional
metadata:                          # optional
  author: your-name
  version: "1.0"
---
```

Keep `SKILL.md` under 500 lines. Move detailed reference material to `references/`. Put executable helpers in `scripts/`. Store templates and data in `assets/`.

---
*Based on: agentskills.io specification, Anthropic Agent Skills course (2026)*
