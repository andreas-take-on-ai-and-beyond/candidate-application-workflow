#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# import-all.sh — import every tool and agent into the active wx.O environment
#
# Usage:
#   cd wxo-agents
#   source .venv/bin/activate          # activate the Python venv
#   orchestrate env activate local     # or your target env name
#   bash import-all.sh
#
# The script imports in dependency order:
#   tools → agents (collaborator agents before orchestrators)
#
# On first run the Hiring_Orchestrator / AI_Hiring_Orchestrator imports may
# fail if their collaborators do not exist yet — just run the script a second
# time once all agents are present.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════════"
echo " Importing tools"
echo "═══════════════════════════════════════════════════════════════════"

# Classic flow tools
orchestrate tools import -k python -f tools/orchestrator_tools.py
orchestrate tools import -k python -f tools/hr_tools.py
orchestrate tools import -k python -f tools/it_tools.py

# AI-Prescreen flow tools
orchestrate tools import -k python -f tools/ai_orchestrator_tools.py
orchestrate tools import -k python -f tools/ai_hr_tools.py
orchestrate tools import -k python -f tools/ai_it_tools.py

# Prescreen agent helpers
orchestrate tools import -k python -f tools/prescreen_tools.py

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo " Importing agents (leaf agents first, orchestrators last)"
echo "═══════════════════════════════════════════════════════════════════"

# ── Classic flow ──────────────────────────────────────────────────────────────
orchestrate agents import -f agents/application-agent.yaml
orchestrate agents import -f agents/hr-agent.yaml
orchestrate agents import -f agents/it-agent.yaml
orchestrate agents import -f agents/hiring-orchestrator.yaml   # needs the three above

# ── AI-Prescreen flow ─────────────────────────────────────────────────────────
orchestrate agents import -f agents/prescreen-agent.yaml
orchestrate agents import -f agents/ai-application-agent.yaml
orchestrate agents import -f agents/ai-hr-agent.yaml
orchestrate agents import -f agents/ai-it-agent.yaml
orchestrate agents import -f agents/ai-hiring-orchestrator.yaml  # needs the four above

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo " Done.  Verify with:  orchestrate agents list"
echo "═══════════════════════════════════════════════════════════════════"
