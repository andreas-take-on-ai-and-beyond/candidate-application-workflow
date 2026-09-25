"""
IT Agent tools — used by the IT developer agent.
Handles fetching and completing IT interview tasks.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools.python_tool import tool

BAMOE_BASE_URL = os.environ.get("BAMOE_BASE_URL")
if not BAMOE_BASE_URL:
    raise EnvironmentError(
        "BAMOE_BASE_URL is not set. Add it to your .env file.\n"
        "  macOS (Lima): BAMOE_BASE_URL=http://host.lima.internal:18081\n"
        "  Linux:        BAMOE_BASE_URL=http://<host-ip>:18081"
    )


@tool(name="get_it_tasks",
      description="Get all pending IT interview tasks assigned to the developer. Returns task objects with their IDs, task names, candidate info, and status.")
def get_it_tasks() -> str:
    """Get all pending IT interview tasks.

    Returns:
        A JSON array of IT task objects.
    """
    req = urllib.request.Request(
        f"{BAMOE_BASE_URL}/usertasks/instance?user=developer&group=IT",
        method="GET",
        headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})


@tool(name="complete_it_interview",
      description="Complete an IT interview task with an approval decision. If approved (true), the candidate gets a job offer. If rejected (false), the candidate is denied.")
def complete_it_interview(task_id: str, approved: bool) -> str:
    """Complete an IT interview task with an approval decision.

    Args:
        task_id: The task ID from get_it_tasks (the 'id' field).
        approved: True to approve the candidate, False to reject.

    Returns:
        A JSON string with the completed task details and status.
    """
    payload = json.dumps({
        "transitionId": "complete",
        "data": {"it_approval": approved}
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BAMOE_BASE_URL}/usertasks/instance/{task_id}/transition?user=developer",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})
