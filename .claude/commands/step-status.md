Read `PROJECT_SCOPE.md` and `memory.md`, then output a status table for every build step.

Format as a checklist:

**Walk the Store — Build Step Status**

For each step (Step 0 through Step 11), output one line:
- ✅ Complete — if memory.md confirms it was fully built
- 🔴 Blocked — if it requires credentials or external access not yet received (list what is blocking it)
- 🟡 In Progress — if partially built
- ⬜ Not Started — if not yet begun

After the checklist, output:
- **Next unblocked step:** the first step that can be worked on right now
- **Blocked steps:** list what external items are still needed and who owns them per PROJECT_SCOPE.md

Do not start building anything. This is a read-only status report.
