# DUPLICATE THIS TEMPLATE IN VSCODE AND ACTIVATE CLAUDE IN A TERMINAL.
Make sure to follow the RESOURCE.md guide on how to begin a project - https://github.com/sunken-stone/claude_code_project_template/blob/main/RESOURCE.md

# Any individal who is collaborating with Steven and will be allowing Claude to touch their code, at any point, must create their project from this template and have completed the Anthropic course.

You can reference the SlackSDK_Recap_Agent project for more information on how to build a claude_code_project
https://github.com/sunken-stone/SlackSDK_Recap_Agent/blob/main/README.md

# [Project_Name_claude_code]
claude_code must be included at the end of every project that claude is involved in generating code for.

[PROJECT_DESCRIPTION]

---

## Getting Started

### 1. Follow the RESOURCE.md file on how to begin the project with Claude
File here: https://github.com/sunken-stone/claude_code_project_template/blob/main/RESOURCE.md

### 2. Clone and set up environment
```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
```  

### 3. Configure environment variables
```bash
cp .env.example .env
# Fill in .env with real values — never commit this file
```

### 4. Run the app
```bash
python app.py
```

---

## Project Structure

```
[PROJECT_NAME]/
├── models/          # Data structures, DB interactions
├── views/           # Output formatting, templates
├── controllers/     # Business logic, orchestration
├── tests/           # All test files (pytest)
├── app.py           # Entry point
├── CLAUDE.md        # AI coding standards (auto-loaded by Claude Code)
├── pyproject.toml   # Python project config + Black settings
├── .prettierrc      # JS formatting config
├── .env.example     # Environment variable template
└── requirements.txt # Python dependencies
```

---

## Standards

This project follows Emplicit engineering standards defined in `CLAUDE.md`.
All contributors must read `CLAUDE.md` before writing code.

---

## Running Tests
```bash
pytest
```
