#Build Brief: Multi-Agent Code Analysis & Documentation System

You are an Al engineer. Build this project end to end, milestone by milestone. Finish and verify each milestone before starting the next. Start simple, then iterate.

## 1. Goal

Take any codebase (ZIP upload or GitHub URL) and produce role-specific documentation with Mermaid diagrams, live progress, and interactive user control. A team of single-purpose agents does the work.

**Personas**

**SDE**: architecture and component relationships, API docs (request/response schemas), DB schema and data flow, code structure and dependencies, setup and deploy, error handling and logging, performance, security and auth flows.

**PM**: feature inventory, user journeys and business processes, feature dependencies and priority, external integrations, business rules, data/analytics capabilities, limitations, roadmap implications.

SDE output must be technical. PM output must be business-focused and non-technical. The two reports must read as clearly different.

## 2. Tech Stack

Concern | Choice |

I

Orchestration | LangGraph with checkpointing (Postgres checkpointer) | Backend FastAPI with WebSocket or SSE; Swagger at /docs

UI Streamlit |

Vector search | PostgreSQL + pgvector | Tools MCP servers (file operations, knowledge base) |

Observability | Langfuse |

LLM Any (OpenAI, Claude, etc.), behind a provider-agnostic wrapper | Web search | Tavily, SerpAPI, or similar, called from an agent tool | Export Markdown and PDF (Mermaid rendered to images, e.g. mermaid-cli) |

Suggested layout: 'backend/" (api, agents, graph, services, models, mcp), 'frontend/ (Streamlit), 'docker-compose.yml (Postgres+pgvector, Langfuse), .env.example, README.md.

## 3. User Flow

1. **Auth**: sign up or log in as User or Admin. Dashboard shows the user's own projects.

2. **Create project**: upload ZIP or give a GitHub URL, pick personas (SDE, PM, both), configure agents, start analysis.

3. **Analysis**: live progress, pause, ask questions, add context, resume.

4. **Review**: per-persona reports, Q&A, diagrams, follow-ups.

5. **Export**: Markdown and PDF. Admin only: manage users and projects.

## 4. Milestones

### M1. Foundation: user can start

Signup, login, JWT auth, roles (User/Admin). Users see only their own projects.

Create a project from a ZIP or GitHub URL, with personas selected. Return a unique project ID and an "Analysis Started" confirmation.

File storage, project tracking, per-environment config, global error handling with friendly messages, Swagger docs.

***Validation. Reject with a clear error for: corrupt or incomplete ZIP, file over limit (100MB), non-code repo (docs-only or binary-only), wrong format (RAR, 7z), empty repo or no recognizable code, malformed GitHub URL, private repo without access.

### M2. Intelligent preprocessing

Detect repo type and stack (e.g. "Python FastAPI project"), with at least 90% accuracy.

Detect entry points (main.py, index.js,...), parse config and dependency files (requirements.txt, package.json, pyproject.toml, ...), detect frameworks. files. Store file metadata.

Apply skip patterns (node_modules, git, venv, dist, binaries,...). Prioritize important Chunk code logically (functions and classes, e.g. via tree-sitter or AST). Attach metadata to each chunk: file, line range, type.

Embed chunks into pgvector. Provide a semantic search endpoint (query "authentication" returns relevant chunks).

Count API endpoints.

### M3. Real-time progress

Stream stage label, current file ("Processing file 1/100: auth.py"), and percentage via SSE or WebSocket.

Structured activity feed with event types: info, milestone, warning (e.g. skipped binary), error. Persist events.

Feed text must be readable by PMs, not stack traces.

Percentage must reflect real work done.

### MA. Multi-agent orchestra

**Pre-run config**: depth (Quick/Standard/Deep), verbosity, feature toggles, diagram preferences, and saved reusable templates. Config must actually

change agent behavior.

**LangGraph graph with at least 5 distinct single-responsibility agents**, for example:

2. API/Code Extractor (endpoints, signatures, schemas)

3. Web Research Agent (best practices, OWASP, version migration notes, library patterns)

4. SDE Doc Writer

5. PM Doc Writer

6. Diagram Generator

7. Coordinator/Router (routes work by persona, runs agents in parallel where it makes sense)

+

Agents hand state to each other through graph state. Each agent emits "what I'm doing" events to the feed.

Web search must change the output (cited in docs), not be decoration.

### M5. Interactive control

**Pause/Resume** at any point using LangGraph checkpoints and interrupts. No data loss. Resume from the exact node. Survives page refresh and server

restart.

**Chat during analysis**:

*Guardrail 1, questions about the analysis: answer from the current state ("What are you analyzing?", "What have you found so far?").

*Guardrail 2, context injection: store the user's instructions ("focus on payments", "/admin is deprecated") and feed them into later agent prompts so the final docs reflect them.

Classify each user message as question or context, and refuse or redirect anything else.

Persist the interaction history.

### M6. Rich outputs

Structured reports. SDE: Architecture, API Docs, DB Schema, Code Structure, Setup Guide, plus the rest of the persona list. PM: Feature Inventory, User

Flows, Business Logic, Integrations, Limitations. Collapsible sections, a clean summary view, a prominent export button.

RAG Q&A over the codebase: answers include file and line citations and snippets, adapt to persona, respond in under 3 seconds.

**Mermaid diagrams, at least 4 types**: architecture/component, flowchart, sequence, ER. Render them in the UI.

**Export**: Markdown and PDF, containing all personas and rendered diagrams.

### M7. Observability and admin

**Admin dashboard: list all users and projects with status, full CRUD on users and projects, basic analytics (total users, active projects, completion rate), running analyses, success/failure rate, error logs.

-Langfuse: trace 100% of LLM calls. Tag each trace with project ID and agent name. Capture tokens, cost, latency, and success per agent and per

project. Show the full trace tree. Enforce admin-only routes server-side.

### Bonus: role-based agent

Persona-aware agent behavior and evaluation (e.g. LLM-as-judge or checklist scoring of report quality per persona). The spec leaves this open, so pick a reasonable design and document it.

## 5. Cross-Cutting Requirements

Secrets live only in env. Provide.env.example.

Dockerize Postgres (with pgvector) and Langfuse. Provide a one-command local setup.

Typed Pydantic models, clear API errors, structured logging. Handle large repos by chunking, batching, and respecting token limits.

Basic tests per milestone (auth, validation cases, chunking, pause/resume).

README with setup, architecture diagram, and a demo walkthrough.

## 6. Acceptance Checklist

- [x] Signup and login with role separation, and Swagger docs reachable
- [x] All 6 invalid-input cases are rejected with clear messages
- [x] Project type detected, chunks embedded, semantic search works
- [x] Live progress, activity feed, and accurate percentage
- [x] At least 5 agents, config affects output, web search is used and cited
- [x] Pause/resume works anywhere and survives refresh; user context shows up in the final docs
- [x] SDE and PM reports clearly differ; at least 4 Mermaid diagram types; Markdown and PDF export work
- [x] Q&A answers cite code and respond in under 3s
- [x] Admin CRUD works; Langfuse shows every LLM call with tokens and cost

##7. Working Instructions

1. Confirm the architecture and folder layout briefly, then start with M1.

2. After each milestone, run it, test it, and summarize what works before moving on. 3. Prefer simple, working solutions over elaborate ones. Don't add features outside this brief.

4. If something is ambiguous (for example the LLM provider or the web search API), choose a sensible default, note it in the README, and continue
