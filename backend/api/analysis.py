from pathlib import Path
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.models.project import Project
from backend.models.event import ActivityEvent
from backend.models.checkpoint import AnalysisChat
from backend.schemas.analysis import EventOut, ChatMessageIn, ChatMessageOut
from backend.services.auth_service import get_current_user
from backend.services.preprocessor import process_and_index_codebase
from backend.services.vector_store import vector_store
from backend.services.event_bus import event_bus
from backend.services.orchestrator import orchestrator

router = APIRouter(prefix="/api/projects", tags=["Analysis & Control"])


@router.post("/{project_id}/preprocess")
async def run_preprocessing(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute M2 intelligent preprocessing:
    Detect stack, count endpoints, chunk AST, index into vector store.
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    repo_path = Path(project.repo_path)
    if not repo_path.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository files not found.")

    summary = process_and_index_codebase(repo_path, project_id)

    project.detected_stack = summary["stack_info"]["stack_label"]
    project.entry_points = summary["entry_points"]
    project.endpoint_count = summary["endpoint_count"]
    project.total_files = summary["total_files"]
    project.total_chunks = summary["total_chunks"]
    project.status = "preprocessing"
    project.current_stage = "Codebase Preprocessed & Indexed"
    project.progress_percentage = 20.0

    await event_bus.emit_event(
        project_id=project_id,
        event_type="milestone",
        stage="Preprocessing",
        message=f"Detected {project.detected_stack} with {project.endpoint_count} endpoints across {project.total_files} files.",
        percentage=20.0,
        db=db,
    )

    await db.commit()
    await db.refresh(project)

    return {
        "project_id": project_id,
        "status": "preprocessed",
        "detected_stack": project.detected_stack,
        "entry_points": project.entry_points,
        "endpoint_count": project.endpoint_count,
        "total_files": project.total_files,
        "total_chunks": project.total_chunks,
    }


@router.post("/{project_id}/start")
async def start_analysis(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start multi-agent analysis orchestration in background."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    # Ensure preprocessed
    repo_path = Path(project.repo_path)
    if repo_path.exists() and not project.detected_stack:
        summary = process_and_index_codebase(repo_path, project_id)
        project.detected_stack = summary["stack_info"]["stack_label"]
        project.entry_points = summary["entry_points"]
        project.endpoint_count = summary["endpoint_count"]
        project.total_files = summary["total_files"]
        project.total_chunks = summary["total_chunks"]
        await db.commit()

    orchestrator.start_analysis_task(project_id)

    return {
        "project_id": project_id,
        "status": "analyzing",
        "message": "Multi-agent analysis orchestration started.",
    }


@router.post("/{project_id}/pause")
async def pause_analysis(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """M5: Pause analysis at any node with zero data loss."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    res = await orchestrator.pause_analysis(project_id, db)
    return res


@router.post("/{project_id}/resume")
async def resume_analysis(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """M5: Resume analysis from exact checkpoint node."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    res = await orchestrator.resume_analysis(project_id, db)
    return res


@router.get("/{project_id}/progress")
async def stream_progress(
    project_id: str,
):
    """
    M3: Server-Sent Events (SSE) live stream of analysis progress.
    Streams stage label, current file ("Processing file 1/100: auth.py"), and percentage.
    """
    return StreamingResponse(
        event_bus.sse_stream(project_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{project_id}/events", response_model=List[EventOut])
async def list_events(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """M3: Retrieve structured activity feed history."""
    stmt = (
        select(ActivityEvent)
        .where(ActivityEvent.project_id == project_id)
        .order_by(ActivityEvent.timestamp.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{project_id}/chat")
async def chat_during_analysis(
    project_id: str,
    payload: ChatMessageIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    M5: Guarded chat during analysis.
    - Guardrail 1 (Question): Answers progress/status from current state
    - Guardrail 2 (Context Injection): Saves user instructions into future agent prompts
    - Guardrail 3 (Refusal): Refuses and redirects off-topic messages
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    res = await orchestrator.handle_chat_message(project_id, payload.message, db)
    return res


@router.get("/{project_id}/chat", response_model=List[ChatMessageOut])
async def list_chat_history(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve chat conversation history for a project."""
    stmt = (
        select(AnalysisChat)
        .where(AnalysisChat.project_id == project_id)
        .order_by(AnalysisChat.timestamp.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{project_id}/search")
async def semantic_search(
    project_id: str,
    query: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """M2: Semantic search endpoint."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    if not vector_store.get_chunks(project_id):
        repo_path = Path(project.repo_path)
        if repo_path.exists():
            process_and_index_codebase(repo_path, project_id)

    results = vector_store.semantic_search(project_id, query, top_k=top_k)
    return {
        "project_id": project_id,
        "query": query,
        "total_matches": len(results),
        "results": results,
    }
