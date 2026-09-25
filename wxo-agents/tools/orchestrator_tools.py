"""
Shared BAMOE tools used by the Orchestrator agent.
Handles process lifecycle: starting hiring processes and listing them.
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


@tool(name="start_hiring_process",
      description="Start a new hiring process for a candidate. Creates a new application with the candidate's details.")
def start_hiring_process(first_name: str,
                         last_name: str,
                         position: str,
                         email: Optional[str] = None,
                         phone: Optional[str] = None,
                         skills: Optional[str] = None,
                         experience: Optional[str] = None,
                         education: Optional[str] = None) -> str:
    """Start a new hiring process for a candidate.

    Args:
        first_name: The candidate's first name.
        last_name: The candidate's last name.
        position: The job position the candidate is applying for.
        email: The candidate's email address.
        phone: The candidate's phone number.
        skills: Comma-separated list of relevant skills.
        experience: Brief summary of work experience.
        education: Highest level of education / degree.

    Returns:
        A JSON string with the process instance id, hr_approval and it_approval status.
    """
    candidate = {
        "firstName": first_name,
        "lastName": last_name,
        "position": position,
    }
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
        f"{BAMOE_BASE_URL}/hiring",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})


@tool(name="list_hiring_processes",
      description="List all currently active hiring processes. Returns a JSON array of active process instances with their IDs and approval statuses.")
def list_hiring_processes() -> str:
    """List all currently active hiring processes.

    Returns:
        A JSON array of active hiring process instances.
    """
    req = urllib.request.Request(f"{BAMOE_BASE_URL}/hiring", method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return json.dumps({"error": e.reason, "status": e.code})
