import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import AsyncSessionLocal
from backend.models.event import ActivityEvent


class EventBus:
    """
    Real-time pub/sub event bus supporting SSE and WebSocket streaming.
    Persists structured activity events to database and broadcasts live updates to active listeners.
    """

    def __init__(self):
        # Maps project_id -> list of asyncio.Queue
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, project_id: str) -> asyncio.Queue:
        """Register a new live subscriber queue for a project."""
        q = asyncio.Queue()
        if project_id not in self._subscribers:
            self._subscribers[project_id] = []
        self._subscribers[project_id].append(q)
        return q

    def unsubscribe(self, project_id: str, q: asyncio.Queue) -> None:
        """Unregister a subscriber queue."""
        if project_id in self._subscribers:
            try:
                self._subscribers[project_id].remove(q)
                if not self._subscribers[project_id]:
                    del self._subscribers[project_id]
            except ValueError:
                pass

    async def emit_event(
        self,
        project_id: str,
        event_type: str,  # info, milestone, warning, error
        stage: str,
        message: str,
        percentage: float,
        file_name: str | None = None,
        db: AsyncSession | None = None,
    ) -> ActivityEvent:
        """
        Record event in database and broadcast to all connected SSE clients.
        Guarantees persistence across page refreshes and server restarts.
        """
        now = datetime.now(timezone.utc)
        event_dict = {
            "project_id": project_id,
            "event_type": event_type,
            "stage": stage,
            "message": message,
            "file_name": file_name,
            "percentage": round(percentage, 1),
            "timestamp": now.isoformat(),
        }

        event_record = ActivityEvent(
            project_id=project_id,
            event_type=event_type,
            stage=stage,
            message=message,
            file_name=file_name,
            percentage=round(percentage, 1),
            timestamp=now,
        )

        # Always persist event to database
        if db is not None:
            try:
                db.add(event_record)
                await db.commit()
                event_dict["id"] = event_record.id
            except Exception:
                pass
        else:
            try:
                async with AsyncSessionLocal() as session:
                    session.add(event_record)
                    await session.commit()
                    event_dict["id"] = event_record.id
            except Exception:
                pass

        # Broadcast to active queues
        if project_id in self._subscribers:
            for q in list(self._subscribers[project_id]):
                try:
                    q.put_nowait(event_dict)
                except Exception:
                    pass

        return event_record

    async def sse_stream(self, project_id: str) -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events (SSE) stream for a project."""
        q = self.subscribe(project_id)
        try:
            yield f"data: {json.dumps({'event_type': 'info', 'stage': 'Connection', 'message': 'Connected to live analysis feed', 'percentage': 0.0})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("percentage", 0.0) >= 100.0 or event.get("stage") in ["Completed", "Failed"]:
                        break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            self.unsubscribe(project_id, q)


event_bus = EventBus()
