/**
 * demo-portals/config.js
 *
 * Central configuration for the watsonx Orchestrate chat embed.
 * Edit this file once to point all three portals at your local ADK server
 * and your deployed agent IDs.
 *
 * How to find your agent IDs — see README Step 8:
 *   orchestrate agents list
 * Then look up each agent's id via the ADK UI at http://localhost:4321
 * or with:
 *   curl -s http://localhost:4321/v1/orchestrate/agents \
 *     -H "Authorization: Bearer <token>" | jq '.[] | {name,id}'
 *
 * IMPORTANT: These UUIDs are generated fresh on every Developer Edition
 * installation/reset. Replace all placeholder values below with your own
 * UUIDs following README Step 8 before running the demo.
 */
window.DEMO_CONFIG = {
  // URL of the watsonx Orchestrate Developer Edition chat server
  // Default for local Developer Edition:
  hostURL: "http://localhost:3000",

  // Shared orchestration instance ID (same for all portals).
  // Run: orchestrate env list   and use the wxo-dev tenant UUID.
  // See README Step 8a for the full retrieval script.
  orchestrationID: "YOUR_ORCHESTRATION_ID",

  // Agent IDs — run `orchestrate agents list` (README Step 8b), then fill in
  // each agent's UUID below. Every Developer Edition reset regenerates these.
  agentIds: {
    // Applicant portal  → AI_Application_Agent
    applicant: "YOUR_AI_APPLICATION_AGENT_ID",

    // HR portal         → AI_HR_Agent
    hr:        "YOUR_AI_HR_AGENT_ID",

    // IT portal         → AI_IT_Agent
    it:        "YOUR_AI_IT_AGENT_ID"
  }
};
