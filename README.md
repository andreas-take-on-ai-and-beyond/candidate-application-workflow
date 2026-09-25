# Candidate Application Workflow

**IBM Business Automation Manager Open Edition (BAMOE) + watsonx Orchestrate**

A reference demo showing how deterministic BPMN workflows and AI agents complement each other in an end-to-end hiring process. Two parallel flows run side-by-side — a classic structured process and an AI-augmented one with automatic CV pre-screening — each driven by conversational agents embedded in role-specific web portals.

> 📖 **Related reading:**
> - [Fixed path or flexible minds?](https://schneiderandreas.net/2026/05/11/fixed-path-or-flexible-minds/) — full walkthrough of the three-stage HR scenario (application submission → HR review → business-unit decision) that this demo implements.
> - [From generative AI to AI agents — opportunities, challenges & broader impact](https://schneiderandreas.net/2025/12/10/from-generative-ai-to-ai-agents-opportunities-challenges-broader-impact/) — background on agentic AI, including reliability, autonomy, and the trust considerations that shape demos like this one.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Prerequisites](#prerequisites)
4. [Complete Setup Guide](#complete-setup-guide)
   - [Step 1 — Clone and copy the environment file](#step-1--clone-and-copy-the-environment-file)
   - [Step 2 — Build the BAMOE container images](#step-2--build-the-bamoe-container-images)
   - [Step 3 — Start the infrastructure](#step-3--start-the-infrastructure)
   - [Step 4 — Verify the BAMOE services](#step-4--verify-the-bamoe-services)
   - [Step 5 — Create the Python virtual environment](#step-5--create-the-python-virtual-environment)
   - [Step 6 — Start the watsonx Orchestrate ADK server](#step-6--start-the-watsonx-orchestrate-adk-server)
   - [Step 7 — Activate the local environment and import all agents](#step-7--activate-the-local-environment-and-import-all-agents)
   - [Step 8 — Find your agent IDs and configure the portals](#step-8--find-your-agent-ids-and-configure-the-portals)
   - [Step 9 — Serve and open the demo portals](#step-9--serve-and-open-the-demo-portals)
5. [Service URLs & Ports](#service-urls--ports)
6. [Demo Script](#demo-script)
   - [Demo Personas & CVs](#demo-personas--cvs)
   - [Scenario Walkthrough](#scenario-walkthrough)
     - [Phase 1 — Application Submission](#phase-1--application-submission)
     - [Phase 2 — HR Review & Approval](#phase-2--hr-review--approval)
     - [Phase 3 — Business Unit Assessment & Decision](#phase-3--business-unit-assessment--decision)
   - [Option A — Classic Hiring Process (no AI)](#option-a--classic-hiring-process-no-ai)
   - [Option B — AI-Prescreen Hiring Process](#option-b--ai-prescreen-hiring-process)
7. [Shutdown & Teardown Guide](#shutdown--teardown-guide)
8. [Configuration Reference](#configuration-reference)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Demo Portals  (static HTML, served on :9090)            │
│                                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│  │  Applicant           │  │  HR Dashboard        │  │  IT Dashboard    │  │
│  │  Career Portal       │  │  Recruiter view      │  │  BU lead view    │  │
│  │  /Applicant/         │  │  /HR/                │  │  /IT/            │  │
│  └──────────┬───────────┘  └──────────┬───────────┘  └────────┬─────────┘  │
│             │  wxoLoader.js embed (:3000)             │        │            │
└─────────────┼──────────────────────────────────────────────────────────────┘
              ▼                          ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│         watsonx Orchestrate Developer Edition  (:3000 chat / :4321 ADK)     │
│                                                                             │
│  AI_Application_Agent  (CV upload + start process)                         │
│  AI_HR_Agent           (pending tasks + HR approval)                       │
│  AI_IT_Agent           (pending tasks + IT approval + interview structure)  │
│  AI_Hiring_Orchestrator (routes + delegates)                               │
│  Prescreen_Agent        (called via ADK REST by the BPMN service task)     │
│                                                                             │
│  Application_Agent / HR_Agent / IT_Agent / Hiring_Orchestrator             │
│  (classic flow, no AI — isolated on port 18081)                            │
└───────────────┬──────────────────────────────┬──────────────────────────────┘
                │  REST tools (host.lima.internal)  │
                ▼                                   ▼
┌───────────────────────────┐   ┌───────────────────────────────────────────┐
│  process-hiring           │   │  process-ai-prescreen-hiring              │
│  Classic BPMN  :18081     │   │  AI-Prescreen BPMN  :18080                │
│                           │   │  ┌─────────────────────────────────────┐  │
│                           │   │  │  AiPrescreenService (BPMN task)     │  │
│                           │   │  │  → POST to ADK :4321 /v1/runs       │  │
│                           │   │  │  → polls until completed            │  │
│                           │   │  │  → parses DECISION/TAG/MISSING      │  │
│                           │   │  └─────────────────────────────────────┘  │
└──────────┬────────────────┘   └──────────────────────┬────────────────────┘
           │                                            │
           └───────────────────┬────────────────────────┘
                               ▼
             ┌──────────────────────────────┐
             │  PostgreSQL 16  :5433        │
             │  DB: kie  (classic)          │
             │  DB: kie_ai  (AI-prescreen)  │
             └──────────────────────────────┘
```

### Two Isolated Flows

| | Classic Flow | AI-Prescreen Flow |
|---|---|---|
| **Host port** | 18081 | 18080 |
| **Database** | `kie` | `kie_ai` |
| **CV processing** | ❌ manual data entry | ✅ Document Processing for wx.O |
| **AI prescreen** | ❌ | ✅ `Prescreen_Agent` (Strong / Partial / Weak match) |
| **Applicant agent** | `Application_Agent` | `AI_Application_Agent` |
| **HR agent** | `HR_Agent` | `AI_HR_Agent` |
| **IT agent** | `IT_Agent` | `AI_IT_Agent` |
| **Orchestrator** | `Hiring_Orchestrator` | `AI_Hiring_Orchestrator` |

---

## Repository Structure

```
bamoe-hiring-demo/
│
├── .env.example                         # Environment template — cp to .env and edit
├── .env                                 # Git-ignored — copy from .env.example and fill in
├── docker-compose.yml                   # Starts all five containers
│
├── process-hiring/                      # Classic BPMN Quarkus service (host port 18081)
│   ├── pom.xml
│   └── src/main/
│       ├── java/org/acme/candidate/     # Candidate domain model
│       └── resources/
│           ├── hiring.bpmn              # Classic hiring process definition
│           └── application.properties   # Quarkus config (internal port: 8080)
│
├── process-ai-prescreen-hiring/         # AI-Prescreen Quarkus service (host port 18080)
│   ├── pom.xml
│   └── src/main/
│       ├── java/org/acme/
│       │   ├── ai/
│       │   │   ├── AdkRestClient.java   # MicroProfile REST client → ADK :4321
│       │   │   └── AiPrescreenService.java  # BPMN service task — calls Prescreen_Agent
│       │   └── candidate/
│       │       └── Candidate.java       # Extended model (aiTag, missingFields, cvText)
│       └── resources/
│           ├── hiring.bpmn              # AI-Prescreen process definition
│           └── application.properties
│
├── wxo-agents/                          # All watsonx Orchestrate ADK artifacts
│   ├── import-all.sh                    # ← ONE COMMAND: imports all tools + agents
│   ├── agents/
│   │   ├── application-agent.yaml       # Classic: applicant entry point
│   │   ├── hiring-orchestrator.yaml     # Classic: orchestrator (collaborates with above 2)
│   │   ├── hr-agent.yaml                # Classic: HR reviewer
│   │   ├── it-agent.yaml                # Classic: IT reviewer
│   │   ├── ai-application-agent.yaml    # AI: applicant entry (CV/PDF upload enabled)
│   │   ├── ai-hiring-orchestrator.yaml  # AI: orchestrator
│   │   ├── ai-hr-agent.yaml             # AI: HR reviewer (shows AI tag + missing fields)
│   │   ├── ai-it-agent.yaml             # AI: IT reviewer (shows AI-extracted skills)
│   │   └── prescreen-agent.yaml         # AI: CV extraction + scoring (called by BPMN)
│   └── tools/
│       ├── orchestrator_tools.py        # start_hiring_process, list_hiring_processes → :18081
│       ├── hr_tools.py                  # get_hr_tasks, complete_hr_interview → :18081
│       ├── it_tools.py                  # get_it_tasks, complete_it_interview → :18081
│       ├── ai_orchestrator_tools.py     # start_ai_hiring_process, list_ai_hiring_processes → :18080
│       ├── ai_hr_tools.py               # get_ai_hr_tasks, complete_ai_hr_interview → :18080
│       ├── ai_it_tools.py               # get_ai_it_tasks, complete_ai_it_interview → :18080
│       └── prescreen_tools.py           # prescreen_candidate, required_candidate_fields (no HTTP)
│
├── demo-portals/                        # Role-specific web portals (static HTML/CSS/JS)
│   ├── config.js                        # ← EDIT THIS: hostURL, orchestrationID, agentIds
│   ├── Applicant/
│   │   ├── index.html                   # Career portal — 6 job listings + embedded chat
│   │   ├── script.js
│   │   └── styles.css
│   ├── HR/
│   │   ├── dashboard.html               # HR recruiter dashboard + embedded chat
│   │   ├── script.js
│   │   └── styles.css
│   └── IT/
│       ├── dashboard.html               # IT business unit dashboard + embedded chat
│       ├── script.js
│       └── styles.css
│
├── docker-compose/
│   ├── management-console/env.json      # BAMOE Management Console — backend URLs
│   ├── pgadmin/                         # pgAdmin pre-configured server connection
│   └── sql/init.sql                     # Creates roles, kie and kie_ai databases
│
├── demo-cvs/                            # Synthetic CVs for the two demo personas
│   ├── Charles-McTurland-CV-Software-Engineer.pdf   # Charles McTurland — Software Engineer
│   └── Anna-Sterling-CV-IT-Manager-Position.pdf     # Anna Sterling — IT Manager
│
├── bamoe-maven-repository/              # Offline Maven repository — BAMOE 9.3.1 artefacts
├── settings.xml                         # Maven settings — points to bamoe-maven-repository/
└── README.md
```

---

## Prerequisites

| Tool | Minimum version | How to check |
|------|----------------|--------------|
| **Java** | 17 (Temurin / IBM Semuru) | `java -version` |
| **Maven** | 3.9 | `mvn -version` |
| **Docker** (or Podman) | Docker Engine 24+ / Podman 4+ | `docker version` |
| **docker-compose** | v2 (standalone binary) | `docker-compose version` |
| **Python** | 3.11+ | `python3 --version` |
| **watsonx Orchestrate Developer Edition** | latest | Must already be installed and its `.env` file on disk |

> **Java version matters for Maven.** If `mvn -version` shows a JDK other than 17, set `JAVA_HOME` before building:
> ```bash
> export JAVA_HOME=$(/usr/libexec/java_home -v 17)   # macOS
> ```

> **Apple Silicon (M1–M4):** The BAMOE Management Console image is `linux/amd64`. Docker Desktop and Podman handle this automatically via Rosetta — no extra flags needed for `compose up`.

> **`docker compose` vs `docker-compose`:** This repo uses the **standalone** `docker-compose` binary (v2). If your setup only has the Docker CLI plugin (`docker compose`), both work — just substitute one for the other throughout this guide.

---

## Complete Setup Guide

### Step 1 — Clone and copy the environment file

```bash
git clone https://github.com/schneiderandreas/bamoe-hiring-demo.git
cd bamoe-hiring-demo

cp .env.example .env
```

The `.env` file controls the Docker Compose deployment. The defaults work for a local Developer Edition setup on macOS. Review the values that may need changing:

| Variable | Default value | When to change |
|----------|--------------|----------------|
| `PROJECT_VERSION` | `9.3.1-ibm-0006` | Only if you have a different BAMOE build |
| `MANAGEMENT_CONSOLE_IMAGE` | `quay.io/bamoe/management-console:9.3.1-ibm-0006` | Only if you have a different BAMOE build |
| `AI_PRESCREEN_URL` | `http://host.docker.internal:4321` | **Linux users:** use your Docker bridge IP instead, e.g. `http://172.17.0.1:4321`. Find it with: `ip route \| grep docker \| awk '{print $9}'` |
| `BAMOE_BASE_URL` | `http://host.lima.internal:18081` | Only if the Lima VM hostname differs |
| `AI_BAMOE_BASE_URL` | `http://host.lima.internal:18080` | Only if the Lima VM hostname differs |

> `host.lima.internal` is the hostname the Lima VM (which runs the ADK) uses to reach the macOS host. On Linux, replace it with your host IP.

---

### Step 2 — Build the BAMOE container images

The two Quarkus services must be built locally — they are not pulled from a registry (`pull_policy: never`). The build uses the offline Maven repository bundled in `bamoe-maven-repository/`.

```bash
# Force Maven to use Java 17 (required by BAMOE 9.3.x)
export JAVA_HOME=$(/usr/libexec/java_home -v 17)   # macOS only — Linux: set manually
export JAVA_TOOL_OPTIONS="-Dnet.bytebuddy.experimental=true"

# Build the AI-Prescreen service → image: dev.local/apache/process-ai-prescreen-hiring:9.3.1-ibm-0006
cd process-ai-prescreen-hiring
mvn -s ../settings.xml clean package -Pcontainer -DskipTests \
    -Dquarkus.container-image.build=true
cd ..

# Build the Classic service → image: dev.local/apache/process-hiring:9.3.1-ibm-0006
cd process-hiring
mvn -s ../settings.xml clean package -Pcontainer -DskipTests \
    -Dquarkus.container-image.build=true
cd ..
```

Confirm both images exist:

```bash
docker images | grep "dev.local/apache/process"
# Expected output:
# dev.local/apache/process-hiring                   9.3.1-ibm-0006   ...   ~223MB
# dev.local/apache/process-ai-prescreen-hiring      9.3.1-ibm-0006   ...   ~229MB
```

> This step only needs to be repeated when you change Java source or BPMN files. The images stay in the local Docker daemon between restarts.

---

### Step 3 — Start the infrastructure

Start all five containers (PostgreSQL, pgAdmin, both BAMOE services, Management Console):

```bash
# From the project root
docker-compose up -d
```

Wait for the stack to settle (~15–30 s for the BAMOE services to run Flyway migrations):

```bash
docker-compose ps
```

Expected output (all containers running, postgres healthy):

```
NAME                                   STATUS                   PORTS
bamoe-hiring-demo-postgres             Up (healthy)             0.0.0.0:5433->5432/tcp
bamoe-hiring-demo-pgadmin              Up                       0.0.0.0:8055->80/tcp
process-ai-prescreen-hiring            Up                       0.0.0.0:18080->8080/tcp
process-hiring                         Up                       0.0.0.0:18081->8080/tcp
bamoe-hiring-demo-management-console   Up (health: starting)    0.0.0.0:18280->8080/tcp
```

> **Note on internal vs host ports:** The Quarkus services always listen internally on port `8080`. Docker maps that to `18080` (AI-Prescreen) and `18081` (Classic) on the host. The `KOGITO_SERVICE_URL` / `KOGITO_JOBS_SERVICE_URL` env vars in `docker-compose.yml` use `localhost:8080` (the internal port) — this is intentional and must not be changed to the host port.

---

### Step 4 — Verify the BAMOE services

```bash
# AI-Prescreen service
curl -s http://localhost:18080/q/health/ready \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('AI-Prescreen:', d['status'])"

# Classic service
curl -s http://localhost:18081/q/health/ready \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Classic:', d['status'])"
```

Expected:
```
AI-Prescreen: UP
Classic: UP
```

Also confirm the process REST endpoints return an empty list (no active processes yet):

```bash
curl -s http://localhost:18080/hiring   # → []
curl -s http://localhost:18081/hiring   # → []
```

Swagger UI for manual API exploration:
- AI-Prescreen: http://localhost:18080/q/swagger-ui
- Classic: http://localhost:18081/q/swagger-ui

---

### Step 5 — Create the Python virtual environment

Do this once. The `.venv` directory is git-ignored.

```bash
cd wxo-agents
python3 -m venv .venv
source .venv/bin/activate
pip install ibm-watsonx-orchestrate
```

Verify the ADK CLI is available:

```bash
orchestrate --version
# ADK Version: 2.x.x
```

---

### Step 6 — Start the watsonx Orchestrate ADK server

The ADK server is the local runtime for the WXO Developer Edition. It must be running before you import agents and for the entire duration of the demo.

Open a **dedicated terminal** and keep it running:

```bash
cd wxo-agents
source .venv/bin/activate

# Replace the path with the location of your WXO Developer Edition .env file.
# --with-doc-processing is REQUIRED — it enables PDF/CV upload and parsing
# (used by the AI_Application_Agent when a candidate attaches their CV).
orchestrate server start --env-file "/path/to/wxo-dev-edition/.env" --with-doc-processing
```

Confirm it is up (ADK health endpoint):

```bash
curl -s http://localhost:4321/health
# The server is up when it responds (any JSON body)
```

The WXO chat UI is served at:
```
http://localhost:3000
```

> If the server hangs on start or the Lima VM is stuck, see [ADK server hangs](#adk-server-hangs-or-times-out-on-start).

---

### Step 7 — Activate the local environment and import all agents

In a **new terminal** (leave the ADK server terminal open):

```bash
cd wxo-agents
source .venv/bin/activate

# Point the CLI at your local Developer Edition instance
orchestrate env activate local

# Import all 14 tools and 9 agents in one command
bash import-all.sh
```

`import-all.sh` imports in the correct dependency order:
1. All tools (7 Python files → 14 registered tools)
2. Leaf agents first: `Application_Agent`, `HR_Agent`, `IT_Agent`, `Prescreen_Agent`, `AI_Application_Agent`, `AI_HR_Agent`, `AI_IT_Agent`
3. Orchestrators last: `Hiring_Orchestrator`, `AI_Hiring_Orchestrator` (they reference the leaf agents as collaborators)

Expected output — every line should say `imported successfully` or `updated successfully`, with **no warnings**:

```
═══════════════════════════════════════════════════════════════════
 Importing tools
═══════════════════════════════════════════════════════════════════
[INFO] - Tool 'list_hiring_processes' imported successfully
[INFO] - Tool 'start_hiring_process' imported successfully
[INFO] - Tool 'get_hr_tasks' imported successfully
[INFO] - Tool 'complete_hr_interview' imported successfully
[INFO] - Tool 'get_it_tasks' imported successfully
[INFO] - Tool 'complete_it_interview' imported successfully
[INFO] - Tool 'list_ai_hiring_processes' imported successfully
[INFO] - Tool 'start_ai_hiring_process' imported successfully
[INFO] - Tool 'get_ai_hr_tasks' imported successfully
[INFO] - Tool 'complete_ai_hr_interview' imported successfully
[INFO] - Tool 'get_ai_it_tasks' imported successfully
[INFO] - Tool 'complete_ai_it_interview' imported successfully
[INFO] - Tool 'prescreen_candidate' imported successfully
[INFO] - Tool 'required_candidate_fields' imported successfully

═══════════════════════════════════════════════════════════════════
 Importing agents (leaf agents first, orchestrators last)
═══════════════════════════════════════════════════════════════════
[INFO] - Agent 'Application_Agent' imported successfully
[INFO] - Agent 'HR_Agent' imported successfully
[INFO] - Agent 'IT_Agent' imported successfully
[INFO] - Agent 'Hiring_Orchestrator' imported successfully
[INFO] - Agent 'Prescreen_Agent' imported successfully
[INFO] - Agent 'AI_Application_Agent' imported successfully
[INFO] - Agent 'AI_HR_Agent' imported successfully
[INFO] - Agent 'AI_IT_Agent' imported successfully
[INFO] - Agent 'AI_Hiring_Orchestrator' imported successfully

═══════════════════════════════════════════════════════════════════
 Done.  Verify with:  orchestrate agents list
═══════════════════════════════════════════════════════════════════
```

Verify all 9 agents are present:

```bash
orchestrate agents list
```

You should see these names in the table:

```
Application_Agent        HR_Agent             IT_Agent
Hiring_Orchestrator      AI_Application_Agent AI_HR_Agent
AI_IT_Agent              AI_Hiring_Orchestrator Prescreen_Agent
```

> **Re-import is safe.** Running `import-all.sh` a second time updates existing tools and agents — it will say `updated successfully` instead of `imported successfully`. Always re-import after changing any YAML or Python tool file.

> **`Failed to find collaborator` on first run?** This can happen if the orchestrator agents were somehow processed before their leaf agents. Run `bash import-all.sh` a second time — all agents exist by then and the error disappears.

---

### Step 8 — Find your agent IDs and configure the portals

The demo portals embed the WXO chat widget pointing at specific deployed agents. You need three agent UUIDs and your tenant (orchestration) ID.

#### 8a — Get the orchestration ID (= tenant ID)

```bash
cd wxo-agents && source .venv/bin/activate

python3 - << 'EOF'
import urllib.request, urllib.parse, json, os

BASE = "http://localhost:4321"
username = os.environ["ADK_AUTH_USERNAME"]   # from your .env
password = os.environ["ADK_AUTH_PASSWORD"]   # from your .env
params = urllib.parse.urlencode({"username": username, "password": password})
req = urllib.request.Request(f"{BASE}/api/v1/auth/token",
      data=params.encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
with urllib.request.urlopen(req) as r:
    global_token = json.loads(r.read())["access_token"]

req2 = urllib.request.Request(f"{BASE}/api/v1/tenants",
       headers={"Authorization": f"Bearer {global_token}"})
tenants = json.loads(urllib.request.urlopen(req2).read())
for t in tenants:
    print(f"  {t['name']:30} id = {t['id']}")
EOF
```

Expected output — use the `wxo-dev` tenant ID as your `orchestrationID`:

```
  wxo-dev                        id = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Default WxO Tenant             id = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### 8b — Get the three agent UUIDs

```bash
# Still inside wxo-agents/ with .venv active
COLUMNS=400 orchestrate agents list 2>&1 > /tmp/agents_list.txt

grep -E "AI_Application|AI_HR|AI_IT|Prescreen|Application_Agent|HR_Agent|IT_Agent|Hiring_Orch" \
  /tmp/agents_list.txt \
  | sed 's/│//g' \
  | awk '{print $1, $NF}' \
  | grep -v "^$"
```

Example output (your UUIDs will differ):

```
AI_Hiring_Orchestrator   xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AI_IT_Agent              xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AI_HR_Agent              xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AI_Application_Agent     xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Prescreen_Agent          xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Hiring_Orchestrator      xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
IT_Agent                 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HR_Agent                 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Application_Agent        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

The three IDs you need for the portals are:
- `AI_Application_Agent` → Applicant portal
- `AI_HR_Agent` → HR portal
- `AI_IT_Agent` → IT portal

#### 8c — Update `demo-portals/config.js`

Open [`demo-portals/config.js`](demo-portals/config.js) and fill in your values:

```js
window.DEMO_CONFIG = {
  // WXO Developer Edition chat server
  hostURL: "http://localhost:3000",

  // The wxo-dev tenant UUID from Step 8a
  orchestrationID: "YOUR_ORCHESTRATION_ID",

  agentIds: {
    applicant: "YOUR_AI_APPLICATION_AGENT_ID",  // AI_Application_Agent
    hr:        "YOUR_AI_HR_AGENT_ID",           // AI_HR_Agent
    it:        "YOUR_AI_IT_AGENT_ID"            // AI_IT_Agent
  }
};
```

> Fill in your own UUIDs obtained from Steps 8a and 8b above.
> Every Developer Edition reset regenerates all UUIDs — repeat Steps 8a–8c after a reset.

---

### Step 9 — Serve and open the demo portals

The portals must be served over HTTP (not opened as `file://`) because the WXO loader script enforces same-origin or CORS rules.

```bash
# From the project root — serves all three portals on port 9090
python3 -m http.server 9090 --directory demo-portals &
```

Open all three in separate browser tabs:

```bash
# macOS
open "http://localhost:9090/Applicant/index.html"
open "http://localhost:9090/HR/dashboard.html"
open "http://localhost:9090/IT/dashboard.html"
```

Or on Linux / manually:

| Portal | URL |
|--------|-----|
| Applicant (Career Portal) | http://localhost:9090/Applicant/index.html |
| HR Dashboard | http://localhost:9090/HR/dashboard.html |
| IT Dashboard | http://localhost:9090/IT/dashboard.html |

Each page loads the WXO chat widget in the bottom-right corner. If the widget does not appear, see [WXO chat widget does not appear](#wxo-chat-widget-does-not-appear-in-the-portals).

---

## Service URLs & Ports

| Service | URL | Credentials | Notes |
|---------|-----|-------------|-------|
| **AI-Prescreen BAMOE** | http://localhost:18080 | — | REST API for the AI flow |
| **AI-Prescreen Swagger** | http://localhost:18080/q/swagger-ui | — | Interactive API docs |
| **AI-Prescreen Health** | http://localhost:18080/q/health | — | Readiness / liveness |
| **Classic BAMOE** | http://localhost:18081 | — | REST API for the classic flow |
| **Classic Swagger** | http://localhost:18081/q/swagger-ui | — | Interactive API docs |
| **Classic Health** | http://localhost:18081/q/health | — | Readiness / liveness |
| **BAMOE Management Console** | http://localhost:18280 | — | Visual BPMN process monitor |
| **WXO Chat UI** | http://localhost:3000 | — | Developer Edition web chat |
| **WXO ADK API** | http://localhost:4321 | `ADK_AUTH_USERNAME` / `ADK_AUTH_PASSWORD` from `.env` | Agent import / run API |
| **pgAdmin** | http://localhost:8055 | `user@kie.org` / `PGADMIN_DEFAULT_PASSWORD` from `.env` | PostgreSQL web UI |
| **PostgreSQL** | localhost:5433 | `kie-user` / `KIE_DB_PASSWORD` from `.env` | DBs: `kie`, `kie_ai` |
| **Demo Portals** | http://localhost:9090 | — | Static portal server |

---

## Demo Script

> 📖 The scenario below is based on the blog post [Fixed path or flexible minds?](https://schneiderandreas.net/2026/05/11/fixed-path-or-flexible-minds/) — recommended reading before running the demo.

---

### Demo Personas & CVs

Two synthetic candidates are used throughout the demo. Their CVs are in [`demo-cvs/`](demo-cvs/):

| Persona | Position | CV file | Portal agent |
|---------|----------|---------|--------------|
| **Charles McTurland** | Software Engineer | [`Charles-McTurland-CV-Software-Engineer.pdf`](demo-cvs/Charles-McTurland-CV-Software-Engineer.pdf) | `AI_Application_Agent` |
| **Anna Sterling** | IT Manager | [`Anna-Sterling-CV-IT-Manager-Position.pdf`](demo-cvs/Anna-Sterling-CV-IT-Manager-Position.pdf) | `AI_Application_Agent` |

> **How to use the CVs:** In the Applicant portal, after telling the agent which position you are applying for, the chat widget will prompt you to attach a PDF. Upload the matching CV from `demo-cvs/` at that point. The `AI_Application_Agent` uses watsonx Orchestrate Document Processing to extract all structured data automatically — no manual field entry needed.

---

### Scenario Walkthrough

The full demo runs the **AI-Prescreen flow** with both personas in parallel. Open all three portals side-by-side before you start:

| Tab | URL | Role |
|-----|-----|------|
| Applicant portal | http://localhost:9090/Applicant/index.html | Candidate view |
| HR dashboard | http://localhost:9090/HR/dashboard.html | Recruiter view |
| IT dashboard | http://localhost:9090/IT/dashboard.html | Business unit lead view |

---

#### Phase 1 — Application Submission

**Open the Applicant portal** → the chat widget is available as a floating button in the **bottom-right corner** of the page.

> **Two ways to open the chat:** Either click the **chat icon** (💬) floating in the bottom-right corner, or click any **"Apply Now"** button on a job card — both open the chat panel. The "Apply Now" buttons also pre-select the job title for context.

**Application 1 — Charles McTurland (Software Engineer)**

1. Click **"Apply Now"** on the *Software Engineer* card (or the 💬 chat icon) to open the chat panel.
2. Type (or copy-paste):
   ```
   I would like to apply for the Software Engineer position.
   ```
3. When the agent asks for a CV, **attach** `demo-cvs/Charles-McTurland-CV-Software-Engineer.pdf`.
4. The `AI_Application_Agent` uses **Document Processing for wx.O** to extract name, email, phone, skills, experience, education, and the raw CV text from the PDF, then calls `start_ai_hiring_process` on port 18080.
5. The agent confirms: *"Thank you, Charles! Your application has been forwarded to our HR team…"*

**Application 2 — Anna Sterling (IT Manager)**

1. Use the **reset button** (↺) in the chat header to start a fresh conversation, or open the portal in a new browser tab.
2. Click **"Apply Now"** on the *IT Manager* card (or the 💬 chat icon).
3. Type:
   ```
   I would like to apply for the IT Manager position.
   ```
4. Attach `demo-cvs/Anna-Sterling-CV-IT-Manager-Position.pdf` when prompted.
5. The agent confirms submission for Anna.

**What happens in the background (invisible to the applicant):**

After each `start_ai_hiring_process` call the BPMN engine immediately triggers the **AI Prescreen service task** ([`AiPrescreenService.java`](process-ai-prescreen-hiring/src/main/java/org/acme/ai/AiPrescreenService.java)). It authenticates with the ADK, locates the `Prescreen_Agent`, submits the already-extracted candidate fields plus the full CV text, and polls the run until completion. The `Prescreen_Agent` returns exactly three lines:

```
DECISION: APPROVED
TAG: Strong match
MISSING: NONE
```

These are written back into the BPMN process variables alongside the structured fields already extracted by `AI_Application_Agent` (email, phone, skills, experience, education). The BAMOE Management Console (http://localhost:18280) now shows **two active process instances** — one for Charles, one for Anna — both waiting at the HR review task.

---

#### Phase 2 — HR Review & Approval

**Switch to the HR dashboard** → http://localhost:9090/HR/dashboard.html

Start the `AI_HR_Agent` in the chat widget and say:

```
"Show me my pending tasks."
```

The agent calls `get_ai_hr_tasks` and lists **both candidates**. For each it surfaces:

- **Candidate name** and applied position
- **AI tag** assigned by `Prescreen_Agent` (e.g. *"Strong match"*)
- **AI-extracted fields**: email, phone, skills, experience, education
- **Missing fields**: anything the AI could not extract that HR should follow up on

The recruiter now has a complete candidate snapshot without any manual data entry. Approve both:

```
"Approve Charles McTurland."
```
```
"Approve Anna Sterling."
```

The agent calls `complete_ai_hr_interview` for each task. Both process instances advance to the IT interview stage.

> **In the Management Console** you can confirm the state transition: the process timeline moves from *HR Interview* to *IT Interview* for both instances.

---

#### Phase 3 — Business Unit Assessment & Decision

**Switch to the IT dashboard** → http://localhost:9090/IT/dashboard.html

Start the `AI_IT_Agent` and say:

```
"Show me my pending tasks."
```

The agent lists Charles and Anna at the top of the queue with their AI-extracted technical profiles. To go deeper on a candidate, ask:

```
"Generate a proposed interview structure for Charles McTurland."
```

The agent produces a tailored interview plan based on Charles's extracted skills and experience — without any additional tool call, purely from the data already in the process variables.

Make the final decisions:

```
"Approve Charles McTurland."
```
```
"Approve Anna Sterling."
```

Both candidates receive job offers. The BPMN process instances reach their end events and **disappear from the active workflow view** in the Management Console — the processes are complete.

---

### Option A — Classic Hiring Process (no AI)

This option runs the same three-phase flow on the **classic backend (port 18081)** without CV upload or AI prescreen. All candidate data is entered conversationally.

> **Portal configuration for the classic flow:** The demo portals ship pre-configured for the AI-Prescreen flow. To run the classic flow, temporarily update [`demo-portals/config.js`](demo-portals/config.js) to point at the classic agents — replace the three `agentIds` with the UUIDs of `Application_Agent`, `HR_Agent`, and `IT_Agent` from `orchestrate agents list`. Alternatively, use the direct WXO chat UI at http://localhost:3000 and select the appropriate agent there.

**Phase 1 — Applicant** (Applicant portal with `Application_Agent`, or WXO chat → `Application_Agent`):

```
"I would like to apply for the Software Engineer position."
```

The agent collects name, email, phone, skills, experience, education conversationally, then calls `start_hiring_process` on port 18081 and confirms receipt to the applicant.

**Phase 2 — HR Review** (HR portal with `HR_Agent`, or WXO chat → `HR_Agent`):

```
"Show me my pending tasks."
```

The agent lists open HR interview tasks with candidate details. Give a decision:
- `"Approve"` → process advances to IT interview
- `"Reject"` → candidate is denied, process ends

**Phase 3 — IT Review** (IT portal with `IT_Agent`, or WXO chat → `IT_Agent` — only if HR approved):

```
"Show me my pending tasks."
```

The agent lists open IT interview tasks. Give a final decision:
- `"Approve"` → candidate receives a job offer
- `"Reject"` → candidate is denied

---

### Option B — AI-Prescreen Hiring Process

> This is the flow described in full in the [Scenario Walkthrough](#scenario-walkthrough) above using Charles McTurland and Anna Sterling. The steps below are a condensed reference.

**Phase 1 — Applicant** (`Applicant/index.html` → select **AI_Application_Agent**):

```
"I want to apply as a Software Engineer."
```

Then **attach a CV as a PDF** (use `demo-cvs/Charles-McTurland-CV-Software-Engineer.pdf` for the demo). The agent:
1. Uses **Document Processing for wx.O** to extract: name, email, phone, skills, experience, education, and raw CV text
2. Calls `start_ai_hiring_process` (port 18080) with all extracted data
3. The BPMN process immediately triggers the **AI Prescreen service task**, which posts the CV text to `Prescreen_Agent` via the ADK REST API and polls for completion
4. `Prescreen_Agent` returns a structured response: `DECISION` (APPROVED/DENIED), `TAG` (Strong/Partial/Weak match), all extracted fields, and a `MISSING` list

**Phase 2 — HR Review** (`HR/dashboard.html` → select **AI_HR_Agent**):

```
"Show me my pending tasks."
```

The agent surfaces the **AI-extracted candidate profile**: the match tag, all extracted fields, and any fields HR still needs to ask the applicant for. Give an approval decision.

**Phase 3 — IT Review** (`IT/dashboard.html` → select **AI_IT_Agent** — only if HR approved):

```
"Show me my pending tasks."
```

The agent presents the candidate with AI-extracted technical skills. The IT lead can also request:

```
"Generate a proposed interview structure for this candidate."
```

Give a final decision. Both process instances complete and disappear from the active workflow view in the Management Console.

---

## Shutdown & Teardown Guide

When you are finished running the demo or need to reset the environment, stop the services in this order: portals → containers → ADK server.

### 1. Stop the Demo Portals Server

If you started the server **in the foreground** (without `&`), press `Ctrl + C` in that terminal.

If you started it **in the background** (with `&` or no longer have the terminal open):

```bash
# macOS / Linux
lsof -ti:9090 | xargs kill -9
```

Or on Linux if `lsof` is not available:

```bash
fuser -k 9090/tcp
```

### 2. Stop the BAMOE Infrastructure & Containers

From the root of the repository:

```bash
# Stop and remove all containers and networks (data volumes are preserved):
docker-compose down

# Full clean reset — also removes database volumes (all process data is lost):
docker-compose down -v
```

> Use `docker-compose down -v` when you want a fresh start: the next `docker-compose up -d` will re-run `init.sql` and create empty `kie` / `kie_ai` databases.

### 3. Stop the watsonx Orchestrate ADK Server

In the dedicated terminal running `orchestrate server start`, press `Ctrl + C`.

Or from any terminal with `wxo-agents/.venv` active:

```bash
cd wxo-agents && source .venv/bin/activate
orchestrate server stop
```

If the underlying Lima VM remains active or needs a hard stop:

```bash
wxo-agents/.venv/lib/python3.*/site-packages/ibm_watsonx_orchestrate/\
developer_edition/resources/lima/bin/limactl stop -f ibm-watsonx-orchestrate
```

---

## Configuration Reference

### Environment variables (`.env`)

| Variable | `.env.example` value | Purpose |
|----------|----------------------|---------|
| `PROJECT_VERSION` | `9.3.1-ibm-0006` | Tag for the locally-built container images |
| `MANAGEMENT_CONSOLE_IMAGE` | `quay.io/bamoe/management-console:9.3.1-ibm-0006` | Management Console image pulled from Quay |
| `AI_PRESCREEN_URL` | `http://host.docker.internal:4321` | How the BAMOE container reaches the ADK server on the host |
| `ADK_AUTH_USERNAME` | `wxo.archer@ibm.com` | Username for the wx.O Developer Edition (published default) |
| `ADK_AUTH_PASSWORD` | _(see `.env.example`)_ | Password for the wx.O Developer Edition (published default) |
| `ADK_TENANT_NAME` | `wxo-dev` | Tenant name for ADK Developer Edition authentication |
| `BAMOE_BASE_URL` | `http://host.lima.internal:18081` | How ADK Python tools reach the classic BAMOE service (macOS Lima) |
| `AI_BAMOE_BASE_URL` | `http://host.lima.internal:18080` | How ADK Python tools reach the AI-Prescreen BAMOE service (macOS Lima) |
| `POSTGRES_PASSWORD` | _(see `.env.example`)_ | PostgreSQL superuser password |
| `KIE_DB_PASSWORD` | _(see `.env.example`)_ | Password for the `kie-user` database role |
| `PGADMIN_DEFAULT_PASSWORD` | _(see `.env.example`)_ | pgAdmin web UI login password |
| `WO_INSTANCE` | _(empty)_ | WXO SaaS instance URL — only needed for cloud deployments |
| `WO_API_KEY` | _(empty)_ | WXO SaaS API key — only needed for cloud deployments |

### Demo portal configuration (`demo-portals/config.js`)

| Property | Description |
|----------|-------------|
| `hostURL` | Base URL of the WXO Developer Edition chat server (default: `http://localhost:3000`) |
| `orchestrationID` | The `wxo-dev` tenant UUID from Step 8a |
| `agentIds.applicant` | UUID of `AI_Application_Agent` from Step 8b |
| `agentIds.hr` | UUID of `AI_HR_Agent` from Step 8b |
| `agentIds.it` | UUID of `AI_IT_Agent` from Step 8b |

---

## Troubleshooting

### `pull access denied for minio/mc` when starting with Document Processing (`-d`)

Docker Hub rate limits or registry policies may block pulling `minio/mc:latest`. Because the watsonx Orchestrate Developer Edition runs inside a **Lima VM**, the image must be pulled and tagged **inside the Lima VM**:

```bash
# Pull and tag inside the Lima VM:
limactl shell ibm-watsonx-orchestrate docker pull quay.io/minio/mc:latest
limactl shell ibm-watsonx-orchestrate docker tag quay.io/minio/mc:latest minio/mc:latest

# Also on the host (if using Docker Desktop):
docker pull quay.io/minio/mc:latest
docker tag quay.io/minio/mc:latest minio/mc:latest
```

### ADK server hangs or times out on start

The Lima VM that backs the Developer Edition may be stuck:

```bash
# Force-stop the VM
wxo-agents/.venv/lib/python3.*/site-packages/ibm_watsonx_orchestrate/\
developer_edition/resources/lima/bin/limactl stop -f ibm-watsonx-orchestrate

# Then start again (with document processing enabled)
orchestrate server start --env-file "/path/to/wxo-dev-edition/.env" --with-doc-processing
```

### `Failed to find collaborator` during agent import

The orchestrator agents reference collaborators that may not have been imported yet on the first run. Fix:

```bash
bash wxo-agents/import-all.sh   # run the script a second time
```

### A port is already in use

```bash
lsof -ti:18080 | xargs kill -9   # AI-Prescreen BAMOE
lsof -ti:18081 | xargs kill -9   # Classic BAMOE
lsof -ti:18280 | xargs kill -9   # BAMOE Management Console
lsof -ti:5433  | xargs kill -9   # PostgreSQL
lsof -ti:9090  | xargs kill -9   # Demo portal server
```

### BAMOE container image not found

```
ERROR: No such image: dev.local/apache/process-hiring:9.3.1-ibm-0006
```

The images must be built locally (Step 2). `pull_policy: never` prevents Docker from trying to pull them from a registry. Re-run the Maven build.

### Maven uses the wrong Java version

```bash
# Check what Maven sees
mvn -version

# Force Java 17
export JAVA_HOME=$(/usr/libexec/java_home -v 17)   # macOS
mvn -version   # should now say "Java version: 17.x.x"
```

### `AI_PRESCREEN_URL` connection refused inside the container

On Linux, `host.docker.internal` is not automatically available. Find your Docker bridge IP and set it in `.env`:

```bash
ip route | grep docker | awk '{print $9}'
# e.g. 172.17.0.1

# Then in .env:
AI_PRESCREEN_URL=http://172.17.0.1:4321
```

### BAMOE service is UP but processes don't start

Check the AI-Prescreen container log for errors calling the ADK:

```bash
docker-compose logs process-ai-prescreen-hiring | grep -i "error\|prescreen\|adk" | tail -20
```

The most common cause is `AI_PRESCREEN_URL` pointing to an unreachable address. Verify the ADK server is running (`curl http://localhost:4321/health`) and that the URL in `.env` can be reached from inside the container.

### pgAdmin shows no databases

`init.sql` runs only on the **first** container creation. If a Docker volume already exists from a previous run, the script is skipped. To force a clean re-initialisation:

```bash
docker-compose down -v   # removes named volumes (all process data is lost)
docker-compose up -d
```

### WXO chat widget does not appear in the portals

Work through this checklist in order:

1. **ADK server running?**
   ```bash
   curl http://localhost:4321/health
   ```

2. **WXO chat server running?**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
   # Expected: 200
   ```

3. **Portal served over HTTP (not `file://`)?**
   Open the browser address bar — it must start with `http://localhost:9090/...`, not `file:///`.

4. **`config.js` filled in?**
   The file ships with `YOUR_ORCHESTRATION_ID` / `YOUR_AI_*_AGENT_ID` placeholders.
   If those placeholders are still present the loader will fail silently.
   Open browser DevTools → Console to see the exact error. Fill in the values from Steps 8a and 8b.

5. **Widget shows loading skeleton but no messages?**
   This is normal for ~2 s while the agent initialises after the loader script runs.
   If it stays blank after that: check `orchestrationID` and `agentId` in `config.js`.

6. **Re-run the agent import after an ADK restart** — agent UUIDs are preserved across restarts, but if you wiped the Developer Edition data volume and re-started, all UUIDs change and you must repeat Steps 8a–8c.

