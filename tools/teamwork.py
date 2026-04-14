# teamwork.py — Teamwork API client (read-only).
# Fetches completed tasks for a given project ID so reports can show recent resolution activity.
# Credentials come from config/settings.py. Uses Basic auth with the API token as the username.

import logging
from typing import List

import httpx

from config import settings

logger = logging.getLogger(__name__)


# #note: Fetches all completed tasks for a Teamwork project and returns them as a list of dicts
def get_completed_tasks(project_id: str) -> List[dict]:
    url = f"https://{settings.TEAMWORK_DOMAIN}.teamwork.com/projects/{project_id}/tasks.json"
    try:
        response = httpx.get(
            url,
            auth=(settings.TEAMWORK_API_TOKEN, ""),
            params={"status": "completed", "includeCompletedTasks": "true"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        tasks = data.get("todo-items", [])
        # #note: Flatten each task to only the fields the report needs
        return [
            {
                "id": t.get("id"),
                "name": t.get("content"),
                "status": t.get("status"),
                "assignee": t.get("responsible-party-summary"),
                "completed_on": t.get("completed-on"),
            }
            for t in tasks
        ]
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Teamwork API error for project {project_id}: {e.response.status_code}"
        )
        raise
    except httpx.HTTPError as e:
        logger.error(f"Teamwork request failed for project {project_id}: {e}")
        raise


# #note: Fetches all completed tasks for a single Teamwork task list by list ID
def get_completed_tasks_by_list(task_list_id: str) -> List[dict]:
    url = f"https://{settings.TEAMWORK_DOMAIN}.teamwork.com/tasklists/{task_list_id}/tasks.json"
    try:
        response = httpx.get(
            url,
            auth=(settings.TEAMWORK_API_TOKEN, ""),
            params={"status": "completed", "includeCompletedTasks": "true"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        tasks = data.get("todo-items", [])
        return [
            {
                "id": t.get("id"),
                "name": t.get("content"),
                "status": t.get("status"),
                "assignee": t.get("responsible-party-summary"),
                "completed_on": t.get("completed-on"),
            }
            for t in tasks
        ]
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Teamwork API error for task list {task_list_id}: {e.response.status_code}"
        )
        raise
    except httpx.HTTPError as e:
        logger.error(f"Teamwork request failed for task list {task_list_id}: {e}")
        raise
