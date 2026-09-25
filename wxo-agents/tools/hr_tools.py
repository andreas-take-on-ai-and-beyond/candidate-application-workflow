"""
HR Agent tools — used by the HR recruiter agent.
Handles fetching and completing HR interview tasks.
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


@tool(name="get_hr_tasks",
      description="Get all pending HR interview tasks assigned to the recruiter. Returns task objects with their IDs, task names, candidate info, and status.")
def get_hr_tasks() -> str:
    """Get all pending HR interview tasks.

    Returns:
        A JSON array of HR task objects.
    """
    req = urllib.request.Request(
        f"{BAMOE_BASE_URL}/usertasks/instance?user=recruiter&group=HR",
        method="GET",
        headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})


@tool(name="complete_hr_interview",
      description="Complete an HR interview task with an approval decision. If approved (true), the process moves to the IT interview. If rejected (false), the candidate is denied.")
def complete_hr_interview(task_id: str, approved: bool) -> str:
    """Complete an HR interview task with an approval decision.

    Args:
        task_id: The task ID from get_hr_tasks (the 'id' field).
        approved: True to approve the candidate, False to reject.

    Returns:
        A JSON string with the completed task details and status.
    """
    payload = json.dumps({
        "transitionId": "complete",
        "data": {"hr_approval": approved}
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BAMOE_BASE_URL}/usertasks/instance/{task_id}/transition?user=recruiter",
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
