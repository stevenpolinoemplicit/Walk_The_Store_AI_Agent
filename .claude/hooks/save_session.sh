#!/bin/bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')
if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
  echo "claude --resume $SESSION_ID" > claude_resume
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)  claude --resume $SESSION_ID" >> claude_session_log
fi
