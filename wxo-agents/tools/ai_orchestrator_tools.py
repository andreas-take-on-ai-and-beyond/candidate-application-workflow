"""
AI-Hiring tools used by the AI_Hiring_Orchestrator agent.
Target the AI-Prescreen BAMOE backend on port 18080, and accept the CV data
the orchestrator has already extracted via Document Processing for wx.O.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools.python_tool import tool

AI_BAMOE_BASE_URL = os.environ.get("AI_BAMOE_BASE_URL") or os.environ.get("BAMOE_AI_BASE_URL")
if not AI_BAMOE_BASE_URL:
    raise EnvironmentError(
        "AI_BAMOE_BASE_URL is not set. Add it to your .env file.\n"
        "  macOS (Lima): AI_BAMOE_BASE_URL=http://host.lima.internal:18080\n"
        "  Linux:        AI_BAMOE_BASE_URL=http://<host-ip>:18080"
    )


@tool(name="start_ai_hiring_process",
      description="Start a new AI-prescreened hiring application (port 18080). "
                  "Pass the candidate's first name, last name and position, plus the raw CV text "
                  "(already extracted by Document Processing for wx.O) and any structured fields "
                  "you could extract. The BPMN AI Prescreen service task will then run the "
                  "Prescreen_Agent on this candidate.")
def start_ai_hiring_process(first_name: str,
                            last_name: str,
                            position: str,
                            cv_text: Optional[str] = None,
                            email: Optional[str] = None,
                            phone: Optional[str] = None,
                            skills: Optional[str] = None,
                            experience: Optional[str] = None,
                            education: Optional[str] = None) -> str:
    """Start an AI-prescreened hiring process.

    Args:
        first_name: Candidate's first name.
        last_name: Candidate's last name.
        position: Position applied for.
        cv_text: Full CV text extracted from the PDF (optional but strongly recommended).
        email: Extracted email if any.
        phone: Extracted phone if any.
        skills: Comma-separated skills list if any.
        experience: Short experience summary if any.
        education: Short education summary if any.

    Returns:
        JSON string with the process instance id and candidate state.
    """
    candidate = {
        "firstName": first_name,
        "lastName": last_name,
        "position": position,
    }
    if cv_text:
        candidate["cvText"] = cv_text
    if email:
        candidate["email"] = email
    if phone:
        candidate["phone"] = phone
    if skills:
        candidate["skills"] = skills
    if experience:
        candidate["experience"] = experience
    if education:
        candidate["education"] = education

    payload = json.dumps({"candidate": candidate}).encode("utf-8")
    req = urllib.request.Request(
        f"{AI_BAMOE_BASE_URL}/hiring",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})


@tool(name="list_ai_hiring_processes",
      description="List all active AI-prescreen hiring processes (port 18080). "
                  "Returns a JSON array of process instances with their candidate info, "
                  "AI tag, missing fields and approval statuses.")
def list_ai_hiring_processes() -> str:
    """List all active AI-prescreen hiring processes."""
    req = urllib.request.Request(f"{AI_BAMOE_BASE_URL}/hiring", method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})
