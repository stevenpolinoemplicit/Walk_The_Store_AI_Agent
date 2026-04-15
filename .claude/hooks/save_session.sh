#!/bin/bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
  export SESSION_ID
  export RESUME_FILE="claude_resume"

  python -c "
import os, re
from datetime import datetime
from zoneinfo import ZoneInfo

session_id = os.environ['SESSION_ID']
resume_file = os.environ['RESUME_FILE']
now = datetime.now(ZoneInfo('America/New_York'))
timestamp = now.strftime('%Y-%m-%d %H:%M:%S ET')

resume_line = 'claude --resume ' + session_id

try:
    with open(resume_file, 'r') as f:
        content = f.read()
except FileNotFoundError:
    content = ''

# Session exists with new-format Last used line — update timestamp only
pattern_with_lastused = r'(claude --resume ' + re.escape(session_id) + r'\nLast used: )([^\n]*)'
if re.search(pattern_with_lastused, content):
    content = re.sub(pattern_with_lastused, r'\g<1>' + timestamp, content)

# Session exists in old inline format — insert Last used: after the matching line
elif resume_line in content:
    content = re.sub(
        r'(claude --resume ' + re.escape(session_id) + r'[^\n]*\n)',
        r'\1Last used: ' + timestamp + '\n',
        content,
        count=1
    )

# New session — append block
else:
    if content and not content.endswith('\n\n'):
        content = content.rstrip('\n') + '\n\n'
    content += resume_line + '\n'
    content += 'Last used: ' + timestamp + '\n'

with open(resume_file, 'w') as f:
    f.write(content)
" 2>/dev/null
fi
