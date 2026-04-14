#!/bin/bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
  TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  # Attempt to pull the first user message from the session JSONL as a summary
  SUMMARY=""
  TRANSCRIPT="$HOME/.claude/projects/C--Users-stpol-OneDrive-Desktop-Walk-The-Store-AI-Agent/${SESSION_ID}.jsonl"
  if [ -f "$TRANSCRIPT" ]; then
    SUMMARY=$(python -c "
import sys, json
try:
    lines = open('$TRANSCRIPT').readlines()
    for line in lines:
        try:
            obj = json.loads(line)
            if obj.get('role') == 'user':
                c = obj.get('content', '')
                t = c[0]['text'] if isinstance(c, list) else c
                print(str(t)[:120])
                break
        except: pass
except: pass
" 2>/dev/null | tr -d '\n')
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
