"""
AI-Hiring HR tools — used by the AI_HR_Agent.
Targets the AI-Prescreen BAMOE backend on port 18080. Each HR task exposes the
CV data extracted by AI plus any `missingFields` that HR should follow up on.
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


@tool(name="get_ai_hr_tasks",
      description="Get all pending HR interview tasks on the AI-Prescreen process (port 18080). "
                  "Each task includes the candidate object with AI-extracted fields "
                  "(email, phone, skills, experience, education), the aiTag the Prescreen_Agent "
                  "assigned, and the missingFields list HR should ask the applicant about.")
def get_ai_hr_tasks() -> str:
    """Get all pending AI-prescreen HR interview tasks."""
    req = urllib.request.Request(
        f"{AI_BAMOE_BASE_URL}/usertasks/instance?user=recruiter&group=HR",
        method="GET",
        headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})


@tool(name="complete_ai_hr_interview",
      description="Complete an HR interview task on the AI-Prescreen process (port 18080) with "
                  "an approval decision. If approved (true) the candidate moves to IT; if "
                  "rejected (false) the application is denied.")
def complete_ai_hr_interview(task_id: str, approved: bool) -> str:
    """Complete an AI-prescreen HR interview task."""
    payload = json.dumps({
        "transitionId": "complete",
        "data": {"hr_approval": approved}
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{AI_BAMOE_BASE_URL}/usertasks/instance/{task_id}/transition?user=recruiter",
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
