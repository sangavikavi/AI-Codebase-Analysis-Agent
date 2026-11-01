import asyncio
import re
from pathlib import Path
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models.checkpoint import AnalysisChat, AnalysisCheckpoint
from backend.models.project import Project
from backend.models.report import ProjectReport
from backend.services.event_bus import event_bus
from backend.services.preprocessor import process_and_index_codebase
from backend.agents.coordinator import coordinator_node
from backend.agents.extractor import extractor_node
from backend.agents.web_researcher import web_research_node
from backend.agents.sde_writer import sde_writer_node
from backend.agents.pm_writer import pm_writer_node
from backend.agents.diagram_agent import diagram_node
from backend.agents.evaluator import evaluator_node
from backend.graph.state import AnalysisState


class OrchestrationManager:
    """
    Manages live background execution of multi-agent graph,
    checkpoint persistence, pause/resume lifecycle, and guarded interactive chat.
    """

    def __init__(self):
        # Maps project_id -> asyncio.Task
        self._running_tasks: dict[str, asyncio.Task] = {}
        # Maps project_id -> in-memory active state
        self._active_states: dict[str, AnalysisState] = {}
        # Flags for pause signal
        self._pause_signals: dict[str, bool] = {}

    async def get_or_restore_state(self, project_id: str, db: AsyncSession) -> AnalysisState:
        """Retrieve state from memory or restore from database checkpoint."""
        if project_id in self._active_states:
            return self._active_states[project_id]

        # Check DB checkpoint
        stmt = select(AnalysisCheckpoint).where(AnalysisCheckpoint.project_id == project_id)
        result = await db.execute(stmt)
        cp = result.scalar_one_or_none()

        if cp and cp.state_json:
            state = AnalysisState(**cp.state_json)
            self._active_states[project_id] = state
            return state

        # If fresh, fetch Project
        proj_stmt = select(Project).where(Project.id == project_id)
        proj_res = await db.execute(proj_stmt)
        proj = proj_res.scalar_one_or_none()

        context_injections = proj.config.get("context_injections", []) if proj and proj.config else []

        initial_state: AnalysisState = {
            "project_id": project_id,
            "repo_path": proj.repo_path if proj else "",
            "personas": proj.personas if proj else ["sde", "pm"],
            "config": proj.config if proj else {},
            "user_context_injections": context_injections,
            "detected_stack": proj.detected_stack or "Python Web Project",
            "entry_points": proj.entry_points or ["main.py"],
            "total_files": proj.total_files or 0,
            "endpoint_count": proj.endpoint_count or 0,
            "api_endpoints": [],
            "data_models": [],
            "code_structure": {},
            "web_research": [],
            "sde_report": "",
            "pm_report": "",
            "diagrams": [],
            "evaluation": {},
            "current_step": "initialized",
            "is_paused": False,
            "progress_percentage": 5.0,
        }
        self._active_states[project_id] = initial_state
        return initial_state

    async def save_checkpoint(
        self, project_id: str, node_name: str, state: AnalysisState, db: AsyncSession
    ) -> None:
        """Persist state checkpoint to database to survive server restart and page refresh."""
        self._active_states[project_id] = state
        stmt = select(AnalysisCheckpoint).where(AnalysisCheckpoint.project_id == project_id)
        result = await db.execute(stmt)
        cp = result.scalar_one_or_none()

        if not cp:
            cp = AnalysisCheckpoint(
                id=project_id,
                project_id=project_id,
                node_name=node_name,
                state_json=dict(state),
            )
            db.add(cp)
        else:
            cp.node_name = node_name
            cp.state_json = dict(state)

        await db.commit()

    async def run_pipeline(self, project_id: str) -> None:
        """Run the sequential agent pipeline with checkpointer and pause checks."""
        async with AsyncSessionLocal() as db:
            state = await self.get_or_restore_state(project_id, db)
            self._pause_signals[project_id] = False

            # Update project status
            proj_stmt = select(Project).where(Project.id == project_id)
            proj_res = await db.execute(proj_stmt)
            proj = proj_res.scalar_one_or_none()
            if proj:
                proj.status = "analyzing"
                await db.commit()

            pipeline_nodes = [
                ("coordinator", coordinator_node),
                ("extractor", extractor_node),
                ("web_researcher", web_research_node),
                ("sde_writer", sde_writer_node),
                ("pm_writer", pm_writer_node),
                ("diagram_agent", diagram_node),
                ("evaluator", evaluator_node),
            ]

            # Determine where to start if resuming
            start_index = 0
            current_step = state.get("current_step", "")
            node_names = [n[0] for n in pipeline_nodes]
            if current_step in node_names:
                start_index = node_names.index(current_step) + 1

            for name, node_fn in pipeline_nodes[start_index:]:
                # Check for pause signal
                if self._pause_signals.get(project_id, False):
                    state["is_paused"] = True
                    await self.save_checkpoint(project_id, name, state, db)
                    if proj:
                        proj.status = "paused"
                        proj.current_stage = f"Paused before {name}"
                        await db.commit()
                    await event_bus.emit_event(
                        project_id=project_id,
                        event_type="warning",
                        stage="Paused",
                        message=f"Analysis paused by user. State saved at checkpoint '{name}'.",
                        percentage=state.get("progress_percentage", 50.0),
                        db=db,
                    )
                    return

                # Execute Agent Node
                update = await node_fn(state)
                state.update(update)
                await self.save_checkpoint(project_id, name, state, db)

                # Sync progress to Project table
                if proj:
                    proj.progress_percentage = state.get("progress_percentage", 0.0)
                    proj.current_stage = name.replace("_", " ").title()
                    await db.commit()

            # Finalize analysis
            if proj:
                proj.status = "completed"
                proj.progress_percentage = 100.0
                proj.current_stage = "Analysis Completed"

                # Upsert SDE Report
                if state.get("sde_report"):
                    s_stmt = select(ProjectReport).where(
                        ProjectReport.project_id == project_id,
                        ProjectReport.persona == "sde"
                    )
                    s_res = await db.execute(s_stmt)
                    s_rep = s_res.scalar_one_or_none()
                    if s_rep:
                        s_rep.content_markdown = state["sde_report"]
                        s_rep.metadata_json = state.get("evaluation", {})
                    else:
                        db.add(ProjectReport(
                            project_id=project_id,
                            persona="sde",
                            title="SDE Technical Specification & Architecture",
                            content_markdown=state["sde_report"],
                            metadata_json=state.get("evaluation", {})
                        ))

                # Upsert PM Report
                if state.get("pm_report"):
                    p_stmt = select(ProjectReport).where(
                        ProjectReport.project_id == project_id,
                        ProjectReport.persona == "pm"
                    )
                    p_res = await db.execute(p_stmt)
                    p_rep = p_res.scalar_one_or_none()
                    if p_rep:
                        p_rep.content_markdown = state["pm_report"]
                        p_rep.metadata_json = state.get("evaluation", {})
                    else:
                        db.add(ProjectReport(
                            project_id=project_id,
                            persona="pm",
                            title="PM Business Architecture & Feature Inventory",
                            content_markdown=state["pm_report"],
                            metadata_json=state.get("evaluation", {})
                        ))

                # Upsert Diagrams
                if state.get("diagrams"):
                    d_stmt = select(ProjectReport).where(
                        ProjectReport.project_id == project_id,
                        ProjectReport.persona == "diagrams"
                    )
                    d_res = await db.execute(d_stmt)
                    d_rep = d_res.scalar_one_or_none()
                    if d_rep:
                        d_rep.diagrams_json = state["diagrams"]
                    else:
                        db.add(ProjectReport(
                            project_id=project_id,
                            persona="diagrams",
                            title="Mermaid System Architecture & Flow Diagrams",
                            content_markdown="Rendered Diagrams",
                            diagrams_json=state["diagrams"]
                        ))

                await db.commit()

            await event_bus.emit_event(
                project_id=project_id,
                event_type="milestone",
                stage="Completed",
                message="Multi-Agent Analysis successfully completed. SDE & PM reports and diagrams are ready for review.",
                percentage=100.0,
                db=db,
            )

    def start_analysis_task(self, project_id: str) -> None:
        """Launch analysis pipeline in background async task."""
        task = asyncio.create_task(self.run_pipeline(project_id))
        self._running_tasks[project_id] = task

    async def pause_analysis(self, project_id: str, db: AsyncSession) -> dict:
        """Pause running analysis without data loss."""
        self._pause_signals[project_id] = True
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        proj = result.scalar_one_or_none()
        if proj:
            proj.status = "paused"
            await db.commit()
        return {"status": "paused", "message": "Analysis pause requested."}

    async def resume_analysis(self, project_id: str, db: AsyncSession) -> dict:
        """Resume paused analysis from exact checkpoint."""
        self._pause_signals[project_id] = False
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        proj = result.scalar_one_or_none()
        if proj:
            proj.status = "analyzing"
            await db.commit()

        await event_bus.emit_event(
            project_id=project_id,
            event_type="info",
            stage="Resumed",
            message="Analysis resumed from saved checkpoint.",
            percentage=proj.progress_percentage if proj else 50.0,
            db=db,
        )

        self.start_analysis_task(project_id)
        return {"status": "resumed", "message": "Analysis resumed from checkpoint."}

    async def handle_chat_message(
        self, project_id: str, message: str, db: AsyncSession
    ) -> dict[str, str]:
        """
        Classifies user message with M5 guardrails:
        1. Question about current analysis -> Answer from state
        2. Context injection -> Store in instructions and reflect in docs
        3. Anything else -> Refuse or redirect
        Persists all interaction history in AnalysisChat.
        """
        clean_msg = message.strip()
        msg_lower = clean_msg.lower()

        # Retrieve current project & state
        proj_stmt = select(Project).where(Project.id == project_id)
        proj_res = await db.execute(proj_stmt)
        proj = proj_res.scalar_one_or_none()

        state = await self.get_or_restore_state(project_id, db)

        # Log user message
        db.add(AnalysisChat(
            project_id=project_id,
            role="user",
            message_type="inquiry",
            content=clean_msg,
        ))

        # Guardrail 1: Questions about ongoing analysis
        question_keywords = [
            "what", "how", "where", "why", "who", "which", "status",
            "progress", "analyzing", "found so far", "files", "endpoints", "?"
        ]
        is_question = any(q in msg_lower for q in question_keywords) and not msg_lower.startswith(("focus", "note", "remember", "deprecate", "use ", "assume", "ignore"))

        if is_question:
            # Generate accurate answer from live state
            endpoints_count = len(state.get("api_endpoints", [])) or (proj.endpoint_count if proj else 0)
            files_count = state.get("total_files", 0) or (proj.total_files if proj else 0)
            stage = proj.current_stage if proj else state.get("current_step", "preprocessing")
            pct = proj.progress_percentage if proj else state.get("progress_percentage", 0.0)
            stack = state.get("detected_stack") or (proj.detected_stack if proj else "Unknown")

            answer = (
                f"Currently analyzing a {stack} codebase. "
                f"We have scanned {files_count} files and detected {endpoints_count} API routes. "
                f"The active stage is '{stage}' with {pct:.0f}% completion."
            )
            msg_type = "question"

        # Guardrail 2: Context injection directives
        elif any(kw in msg_lower for kw in [
            "focus", "deprecat", "important", "remember", "priority", "assume",
            "ignore", "rule", "context", "constraint", "architecture", "payment",
            "security", "database", "we use", "our"
        ]):
            # Append context injection
            if "user_context_injections" not in state:
                state["user_context_injections"] = []
            state["user_context_injections"].append(clean_msg)

            # Persist to project config
            if proj:
                cfg = dict(proj.config or {})
                injs = cfg.get("context_injections", [])
                injs.append(clean_msg)
                cfg["context_injections"] = injs
                proj.config = cfg

            await self.save_checkpoint(project_id, state.get("current_step", "extractor"), state, db)

            await event_bus.emit_event(
                project_id=project_id,
                event_type="info",
                stage="Context Injection",
                message=f"Direct user directive received and saved: '{clean_msg}'. Will be reflected in generated SDE and PM reports.",
                percentage=proj.progress_percentage if proj else 50.0,
                db=db,
            )

            answer = f"Context received and saved: '{clean_msg}'. The SDE and PM writer agents will incorporate this directive into the final documentation."
            msg_type = "context"

        # Guardrail 3: Refuse and redirect off-topic messages
        else:
            answer = (
                "Notice: This interactive assistant only supports questions regarding the active codebase analysis "
                "or directives to steer the analysis (e.g. 'focus on payments', '/admin is deprecated'). "
                "Please submit an inquiry about the analysis or provide technical context directives."
            )
            msg_type = "refusal"

        # Persist agent response
        db.add(AnalysisChat(
            project_id=project_id,
            role="agent",
            message_type=msg_type,
            content=answer,
        ))
        await db.commit()

        return {
            "message_type": msg_type,
            "response": answer,
        }


# Global orchestration manager singleton
orchestrator = OrchestrationManager()
