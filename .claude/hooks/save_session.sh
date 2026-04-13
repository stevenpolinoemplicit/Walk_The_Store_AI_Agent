#!/bin/bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
  TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  # Attempt to pull the first user message from the session JSONL as a summary
  SUMMARY=""
  TRANSCRIPT="$HOME/.claude/projects/C--Users-stpol-OneDrive-Desktop-Walk-The-Store-AI-Agent/${SESSION_ID}.jsonl"
  if [ -f "$TRANSCRIPT" ]; then
    SUMMARY=$(jq -r 'select(.role == "user") | .content | if type == "array" then .[0].text else . end' "$TRANSCRIPT" 2>/dev/null \
      | head -1 | tr -d '\n' | cut -c1-120)
  fi

  # Build entry line with optional summary
  if [ -n "$SUMMARY" ]; then
    LINE="claude --resume $SESSION_ID  # $TIMESTAMP | $SUMMARY"
  else
    LINE="claude --resume $SESSION_ID  # $TIMESTAMP"
  fi

  # Append to claude_resume — never overwrite, always preserve previous entries
  echo "$LINE" >> claude_resume

  # Append to full chronological session log
  echo "$LINE" >> claude_session_log
fi
