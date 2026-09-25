"""
AI-Hiring IT tools — used by the AI_IT_Agent.
Targets the AI-Prescreen BAMOE backend on port 18080.
"""

import json
import os
import urllib.request
import urllib.error

from ibm_watsonx_orchestrate.agent_builder.tools.python_tool import tool

AI_BAMOE_BASE_URL = os.environ.get("AI_BAMOE_BASE_URL") or os.environ.get("BAMOE_AI_BASE_URL")
if not AI_BAMOE_BASE_URL:
    raise EnvironmentError(
        "AI_BAMOE_BASE_URL is not set. Add it to your .env file.\n"
        "  macOS (Lima): AI_BAMOE_BASE_URL=http://host.lima.internal:18080\n"
        "  Linux:        AI_BAMOE_BASE_URL=http://<host-ip>:18080"
    )


@tool(name="get_ai_it_tasks",
      description="Get all pending IT interview tasks on the AI-Prescreen process (port 18080). "
                  "Each task exposes the candidate with AI-extracted fields and aiTag.")
def get_ai_it_tasks() -> str:
    """Get all pending AI-prescreen IT interview tasks."""
    req = urllib.request.Request(
        f"{AI_BAMOE_BASE_URL}/usertasks/instance?user=developer&group=IT",
        method="GET",
        headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})


@tool(name="complete_ai_it_interview",
      description="Complete an IT interview task on the AI-Prescreen process (port 18080).")
def complete_ai_it_interview(task_id: str, approved: bool) -> str:
    """Complete an AI-prescreen IT interview task."""
    payload = json.dumps({
        "transitionId": "complete",
        "data": {"it_approval": approved}
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{AI_BAMOE_BASE_URL}/usertasks/instance/{task_id}/transition?user=developer",
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
