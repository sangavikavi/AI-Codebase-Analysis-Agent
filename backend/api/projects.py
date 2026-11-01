import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.models.project import Project
from backend.models.event import ActivityEvent
from backend.schemas.project import ProjectCreateGitHub, ProjectOut, ProjectStartResponse
from backend.services.auth_service import get_current_user
from backend.services.repo_loader import save_and_extract_zip, clone_github_repo

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("/upload", response_model=ProjectStartResponse, status_code=status.HTTP_201_CREATED)
async def create_project_from_zip(
    name: str = Form(...),
    personas: str = Form("[\"sde\", \"pm\"]"),
    config: str = Form("{}"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a project by uploading a ZIP codebase archive.
    Validates file format, size limits, file integrity, and code presence.
    """
    try:
        personas_list = json.loads(personas)
        if not isinstance(personas_list, list) or not personas_list:
            personas_list = ["sde", "pm"]
    except Exception:
        personas_list = ["sde", "pm"]

    try:
        config_dict = json.loads(config)
        if not isinstance(config_dict, dict):
            config_dict = {}
    except Exception:
        config_dict = {}

    project_id = str(uuid.uuid4())

    # Extract and validate ZIP file
    extract_path, stats = await save_and_extract_zip(file, project_id)

    # Create project record in database
    project = Project(
        id=project_id,
        name=name.strip(),
        user_id=current_user.id,
        source_type="zip",
        github_url=None,
        repo_path=extract_path,
        status="created",
        personas=personas_list,
        config=config_dict,
        total_files=stats.get("total_files", 0),
        progress_percentage=0.0,
        current_stage="Repository Uploaded and Verified",
    )
    db.add(project)

    # Add initial activity event
    event = ActivityEvent(
        project_id=project_id,
        event_type="milestone",
        stage="Upload & Verification",
        message=f"ZIP archive uploaded and verified. Discovered {stats.get('code_files_count', 0)} source code files.",
        percentage=5.0,
    )
    db.add(event)

    await db.commit()

    return ProjectStartResponse(
        project_id=project_id,
        status="created",
        message="Analysis Started: Repository verified and project initialized successfully.",
    )


@router.post("/github", response_model=ProjectStartResponse, status_code=status.HTTP_201_CREATED)
async def create_project_from_github(
    payload: ProjectCreateGitHub,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a project by providing a public GitHub repository URL.
    Validates URL structure, repo accessibility, and code presence.
    """
    project_id = str(uuid.uuid4())

    extract_path, stats = await clone_github_repo(payload.github_url, project_id)

    project = Project(
        id=project_id,
        name=payload.name.strip(),
        user_id=current_user.id,
        source_type="github",
        github_url=payload.github_url.strip(),
        repo_path=extract_path,
        status="created",
        personas=payload.personas,
        config=payload.config.model_dump(),
        total_files=stats.get("total_files", 0),
        progress_percentage=0.0,
        current_stage="GitHub Repository Cloned and Verified",
    )
    db.add(project)

    event = ActivityEvent(
        project_id=project_id,
        event_type="milestone",
        stage="GitHub Clone & Verification",
        message=f"GitHub repository cloned and verified. Discovered {stats.get('code_files_count', 0)} source code files.",
        percentage=5.0,
    )
    db.add(event)

    await db.commit()

    return ProjectStartResponse(
        project_id=project_id,
        status="created",
        message="Analysis Started: GitHub repository verified and project initialized successfully.",
    )


@router.get("", response_model=List[ProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List projects. Users see only their own projects.
    Admins can also see all projects or their own depending on context.
    """
    stmt = (
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details by ID. Only owner or admin may access."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project.",
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and its associated records."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this project.",
        )

    await db.delete(project)
    await db.commit()
    return None
