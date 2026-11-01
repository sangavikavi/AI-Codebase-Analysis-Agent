from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.models.project import Project
from backend.models.report import ProjectReport
from backend.models.user import User, UserRole
from backend.schemas.report import ReportOut
from backend.services.auth_service import get_current_user
from backend.services.export_service import generate_markdown_export, generate_pdf_export

router = APIRouter(prefix="/api/projects", tags=["Reports & Exports"])


@router.get("/{project_id}/reports", response_model=List[ReportOut])
async def list_project_reports(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all persona reports and diagrams generated for a project."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    rep_stmt = select(ProjectReport).where(ProjectReport.project_id == project_id)
    rep_result = await db.execute(rep_stmt)
    return rep_result.scalars().all()


@router.get("/{project_id}/reports/{persona}", response_model=ReportOut)
async def get_persona_report(
    project_id: str,
    persona: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a specific persona report (e.g., 'sde', 'pm', 'diagrams')."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    rep_stmt = (
        select(ProjectReport)
        .where(
            ProjectReport.project_id == project_id,
            ProjectReport.persona == persona.lower()
        )
        .order_by(ProjectReport.created_at.desc())
    )
    rep_result = await db.execute(rep_stmt)
    report = rep_result.scalars().first()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No report found for persona '{persona}'.")

    return report


@router.get("/{project_id}/export/markdown")
async def export_markdown(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """M6: Export unified Markdown document containing all persona reports and diagrams."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    rep_stmt = select(ProjectReport).where(ProjectReport.project_id == project_id)
    rep_result = await db.execute(rep_stmt)
    reports = [
        {
            "persona": r.persona,
            "title": r.title,
            "content_markdown": r.content_markdown,
            "diagrams_json": r.diagrams_json,
        }
        for r in rep_result.scalars().all()
    ]

    md_content = generate_markdown_export(reports, project.name)

    return PlainTextResponse(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{project.name.replace(" ", "_")}_documentation.md"'
        },
    )


@router.get("/{project_id}/export/pdf")
async def export_pdf(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """M6: Export polished PDF containing all persona reports and diagrams."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    rep_stmt = select(ProjectReport).where(ProjectReport.project_id == project_id)
    rep_result = await db.execute(rep_stmt)
    reports = [
        {
            "persona": r.persona,
            "title": r.title,
            "content_markdown": r.content_markdown,
            "diagrams_json": r.diagrams_json,
        }
        for r in rep_result.scalars().all()
    ]

    settings.ensure_directories()
    pdf_path = Path(settings.exports_dir) / f"{project_id}.pdf"
    generate_pdf_export(reports, project.name, pdf_path)

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{project.name.replace(' ', '_')}_documentation.pdf",
    )
