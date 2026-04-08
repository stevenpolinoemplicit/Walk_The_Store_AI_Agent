# Walkthough and Resources of how to begin a claude_code_project
Follow all steps in order

# 1, Start in Plan Mode
In Plan Mode, Claude Code explores your codebase and creates a detailed plan before editing any code.

Enter Plan Mode by pressing `shift+tab+tab`.

# Send these exact prompts in this order
> Read this claude_code_project_template folder I have loaded. Save to memory all information in the CLAUDE.md and SKILLS.md. These rules must be followed for the entire project. Respond "Done, give next walkthrough prompt: "Here is my approved scope document...." when finished.
> "Here is my approved scope document. Review it. Think through the entire project idea. Then, show the architecture, files we'll need, and implementation steps. Feel free to ask me any questions so that we are on the same page about the project before building anything."

# 2, Begin Building

Write tests first, then implement
Claude Code can write comprehensive tests to catch edge cases early and give you confidence that the code works correctly.

# Send this exact prompt
> "Edit the claude_code_project template Folder I have loaded to reflect the actual files needed. Make sure these files reflect our final plan after I have given you scope and answered all of your questions. When you have completed, give me a summary of every file you created. Then, instruct me to make a new .env file in the main branch by copying your completed .env.example and filling out the information. Never read or analyze my .env file, or any file listed in .gitignore under any circumstsances.

# 3, Level up to auto-accept mode

# Send this exact prompt
> I am about to activate auto-accept mode. Never delete files under any circumstances. If you need to adjust one file that affects another, make certain to adjust any other files and give me the reason why before each.

Once Claude Code is on the right track, hit `shift+tab` to let Claude Code autonomously edit files in your directory.
Pro tip: You can send messages anytime while Claude works and Claude adjusts course immediately.
