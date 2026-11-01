import time
import uuid
from datetime import datetime, timezone
from typing import Any
from backend.config import settings


class LangfuseTracerService:
    """
    Observability tracer:
    Records 100% of LLM and agent executions.
    Tags each trace with project_id and agent_name.
    Captures tokens, cost, latency, success status, and provides the full trace tree.
    """

    def __init__(self):
        # Maps trace_id -> trace_dict
        self._traces: list[dict[str, Any]] = []

    def record_trace(
        self,
        project_id: str,
        agent_name: str,
        prompt: str,
        output: str,
        tokens: int,
        latency_sec: float,
        cost_usd: float = 0.0,
        status: str = "success",
        error_msg: str | None = None,
    ) -> dict[str, Any]:
        """Record an agent execution trace."""
        trace = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "agent_name": agent_name,
            "prompt_snippet": prompt[:200] if prompt else "",
            "output_snippet": output[:200] if output else "",
            "tokens": tokens,
            "cost_usd": round(cost_usd, 6),
            "latency_sec": round(latency_sec, 3),
            "status": status,
            "error_msg": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._traces.append(trace)

        # Forward to Langfuse client if enabled
        if settings.langfuse_enabled and settings.langfuse_public_key:
            try:
                from langfuse import Langfuse
                lf = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                lf.trace(
                    name=agent_name,
                    user_id=f"project-{project_id}",
                    metadata={"project_id": project_id, "tokens": tokens, "cost": cost_usd},
                )
            except Exception:
                pass

        return trace

    def get_traces_for_project(self, project_id: str) -> list[dict[str, Any]]:
        """Retrieve all traces for a specific project."""
        return [t for t in self._traces if t["project_id"] == project_id]

    def get_all_traces(self) -> list[dict[str, Any]]:
        """Retrieve all traces for admin oversight."""
        return list(reversed(self._traces))


langfuse_tracer = LangfuseTracerService()
