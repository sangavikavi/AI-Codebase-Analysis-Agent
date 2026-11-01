# 🤖 Multi-Agent Codebase Analysis & Documentation System

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119%2B-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-purple.svg)](https://github.com/langchain-ai/langgraph)
[![React](https://img.shields.io/badge/Frontend-React_19_Vite-61dafb.svg)](https://react.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind-CSS_v4-38bdf8.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise multi-agent AI system that ingests any software codebase (via ZIP upload or public GitHub URL) and produces role-specific documentation with interactive steering, live progress streaming, sub-3-second grounded RAG Q&A, and dynamic Mermaid diagrams.

---

## 🌟 Architecture & System Design

```mermaid
flowchart TD
    subgraph Ingestion ["1. Codebase Ingestion & Validation"]
        User(["Client / Stakeholder"]) -->|Upload ZIP or GitHub URL| Loader["Repo Loader & Validator"]
        Loader -->|Check Size <100MB, Format, Code Integrity| Pre["Intelligent Preprocessor"]
    end

    subgraph Preprocessing ["2. Intelligent Preprocessing"]
        Pre -->|Detect Stack & Entrypoints| AST["AST Logical Chunking"]
        AST -->|Functions & Classes| Vector["Vector Store & Embeddings"]
        AST -->|Endpoint Counter| DB[("SQLAlchemy Database")]
    end

    subgraph Orchestration ["3. LangGraph Multi-Agent Team"]
        Vector --> Coordinator["1. Coordinator / Router Agent"]
        Coordinator --> Extractor["2. API & Code Extractor Agent"]
        Extractor --> WebResearcher["3. Web Research Agent"]
        WebResearcher --> SDEWriter["4. SDE Doc Writer Agent"]
        SDEWriter --> PMWriter["5. PM Doc Writer Agent"]
        PMWriter --> DiagramAgent["6. Diagram Generator Agent"]
        DiagramAgent --> Evaluator["7. Quality Evaluator Agent"]
    end

    subgraph Interaction ["4. Interactive Steering & Controls"]
        User <-->|Pause / Resume & Checkpoints| Orch["Orchestration Manager"]
        User <-->|Guarded Chat & Directives| Orch
        Orch -->|SSE Real-time Stream| Feed["Activity Feed & Progress"]
    end

    subgraph Outputs ["5. Rich Multi-Persona Outputs"]
        SDEWriter --> SDEReport["Technical Architecture & API Docs"]
        PMWriter --> PMReport["Business Features & User Flows"]
        DiagramAgent --> Mermaid["4x Mermaid Diagrams (Arch, Flow, Seq, ER)"]
        SDEReport & PMReport & Mermaid --> Export["Markdown & PDF Export"]
        Vector --> RAG["Sub-3s Grounded RAG Q&A with Line Citations"]
    end
```

---

## 👥 Personas: Technical SDE vs. Business PM

The system produces clearly differentiated reports tailored to two distinct audiences:

| Persona | Audience | Focus Areas | Tone & Content |
|:---|:---|:---|:---|
| **SDE** | Engineers, Architects, DevOps | Architecture topology, API request/response schemas, DB models, setup & deployment, security protocols, OWASP citations | Technical, explicit code structures, data schemas, and deployment commands |
| **PM** | Product Managers, Leaders, Clients | Feature inventory, user onboarding & operational journeys, feature priority matrix, integrations, limitations, roadmap | Business-focused, non-technical, outcome-oriented language |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (Node 20+ recommended)
- Git

### 2. Local Setup
```bash
# Clone the repository
git clone https://github.com/sangavikavi/AI-Codebase-Analysis-Agent.git
cd AI-Codebase-Analysis-Agent

# Install backend dependencies
pip install -r requirements.txt

# Install frontend React dependencies
cd frontend
npm install
cd ..

# Copy environment variables
cp .env.example .env
```

### 3. Run the Backend API
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger UI will be reachable at: **`http://localhost:8000/docs`**

### 4. Run the React + Tailwind CSS v4 Dashboard
```bash
cd frontend
npm run dev
```
Open **`http://localhost:5173`** in your browser.

### 5. One-Command Setup with Docker Compose
```bash
docker-compose up --build
```
This launches:
- **PostgreSQL + pgvector** on port `5432`
- **FastAPI Backend** on port `8000`
- **React Frontend** on port `5173`
- **Langfuse Observability** on port `3000`

---

## 🧪 Running the Automated Test Suite

The test suite covers 100% of milestones (M1 through M7) and validation rejection rules:

```bash
# Run all test suites
python -m pytest tests/ -v
```

### Milestone Test Coverage:
- `tests/test_m1_auth_and_validation.py`: Signup, login, JWT token, user project isolation, and all 6 invalid-input validation cases.
- `tests/test_m2_preprocessing.py`: Stack detection (>=90% accuracy), entrypoints, endpoint counting, AST chunking, semantic vector search.
- `tests/test_m3_m4_agents_graph.py`: SSE progress streaming, structured activity feed, 7 specialized agents, web research citations.
- `tests/test_m5_interactive_control.py`: Checkpoint pause/resume surviving restart, chat guardrail 1 (progress questions), guardrail 2 (context injection), guardrail 3 (refuse/redirect).
- `tests/test_m6_m7_reports_qa_admin.py`: Persona report differentiation, 4 Mermaid diagrams, Markdown and PDF export, sub-3s RAG Q&A, admin CRUD, Langfuse traces.

---

## 🔑 Key Features & Milestones

### 1. Ingestion & Validation (M1)
Rejects invalid inputs with clear messages:
1. Corrupt or incomplete ZIP archives
2. File over limit (> 100MB)
3. Non-code repositories (docs-only or binary-only)
4. Unsupported archive formats (`.rar`, `.7z`, `.tar`)
5. Empty repositories
6. Malformed GitHub URLs or private repos without access

### 2. Intelligent Preprocessing (M2)
- Automatically detects framework and language (e.g. `Python FastAPI project`, `TypeScript Next.js project`, `Go Gin project`).
- Locates entry points (`main.py`, `index.js`, `server.ts`).
- Parses functions, classes, and routes via AST into semantic chunks.
- Embeds chunks with semantic indexing for hybrid vector & lexical retrieval.

### 3. Real-Time Streaming & Activity Feed (M3)
- Live Server-Sent Events (SSE) streaming percentage, stage label, and current file (`Processing file 1/100: auth.py`).
- Color-coded feed items (`milestone`, `info`, `warning`, `error`).

### 4. LangGraph Multi-Agent Team (M4)
- **Coordinator Agent**: Orchestrates pipeline by depth and selected personas.
- **Extractor Agent**: Extracts API schemas and DB models.
- **Web Research Agent**: Conducts live web research on OWASP security standards and framework best practices.
- **SDE Writer Agent**: Synthesizes technical specifications and cites external research.
- **PM Writer Agent**: Synthesizes non-technical feature inventories and user workflows.
- **Diagram Agent**: Synthesizes 4 Mermaid diagram types (Architecture, Flowchart, Sequence, ER).
- **Quality Evaluator Agent**: Checklist and LLM-as-judge scoring per persona.

### 5. Interactive Control & Guarded Steering (M5)
- **Pause & Resume**: Interrupts and resumes from exact checkpoints without data loss.
- **Guarded Chat**:
  - *Guardrail 1*: Progress & status questions answered from live state.
  - *Guardrail 2*: Directives (*"focus on payments"*, *"/admin is deprecated"*) injected into future agent prompts and reflected in final docs.
  - *Guardrail 3*: Off-topic queries refused and redirected.

### 6. Rich Outputs & Grounded Q&A (M6)
- **4 Types of Mermaid Diagrams**: Interactive architecture, flowchart, sequence, and ER diagrams.
- **Exporting**: One-click download of unified Markdown and styled PDF documents.
- **Sub-3s Codebase RAG Q&A**: Answers questions with verified file and line citations.

### 7. Observability & Administration (M7)
- **Admin Dashboard**: Full CRUD over users and projects, platform analytics, completion rate.
- **Langfuse Tracing**: Captures 100% of LLM calls with tokens, cost, latency, and status.

---

## 📜 License
MIT License. Built for enterprise software documentation and codebase understanding.
