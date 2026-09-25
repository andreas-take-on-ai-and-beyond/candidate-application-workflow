"""
Prescreen Agent tools — helpers for candidate pre-screening and CV handling.

The Prescreen_Agent is driven by the BPMN service task `AiPrescreenService` which
sends the CV text directly in the user message, so the agent typically does not
need any tool call to evaluate. These helpers exist so the agent can also be
invoked directly from the WXO chat (e.g. to test a candidate) and to give the
AI_Hiring_Orchestrator a simple way to ask for structured extraction.
"""

import json

from ibm_watsonx_orchestrate.agent_builder.tools.python_tool import tool


@tool(name="prescreen_candidate",
      description="Retrieve candidate information for AI pre-screening evaluation. "
                  "Returns the candidate's basic details so the agent can evaluate suitability.")
def prescreen_candidate(first_name: str, last_name: str, position: str) -> str:
    """Get candidate details for pre-screening evaluation.

    Args:
        first_name: The candidate's first name.
        last_name: The candidate's last name.
        position: The job position the candidate is applying for.

    Returns:
        JSON string with candidate details for the agent to evaluate.
    """
    result = {
        "candidate": f"{first_name} {last_name}",
        "position": position,
    }
    return json.dumps(result)


@tool(name="required_candidate_fields",
      description="Return the list of candidate fields that HR expects for a complete "
                  "application (email, phone, skills, experience, education). Use this "
                  "together with the fields extracted from a CV to compute the missingFields list.")
def required_candidate_fields() -> str:
    """Return the canonical list of required candidate fields."""
    return json.dumps(["email", "phone", "skills", "experience", "education"])
