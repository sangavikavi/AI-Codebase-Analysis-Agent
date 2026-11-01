from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.event import ActivityEvent
from backend.models.project import Project
from backend.models.user import User, UserRole
from backend.schemas.admin import AnalyticsOut, UserAdminOut, UserAdminUpdate
from backend.schemas.project import ProjectOut
from backend.services.auth_service import require_admin
from backend.services.langfuse_tracer import langfuse_tracer

router = APIRouter(prefix="/api/admin", tags=["Admin & Observability"])


@router.get("/users", response_model=List[UserAdminOut])
async def list_all_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: List all registered users with their project counts."""
    stmt = (
        select(User, func.count(Project.id).label("proj_count"))
        .outerjoin(Project, Project.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id.asc())
    )
    result = await db.execute(stmt)
    user_list = []
    for user, proj_count in result.all():
        user_list.append(
            UserAdminOut(
                id=user.id,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                project_count=proj_count,
            )
        )
    return user_list


@router.put("/users/{user_id}", response_model=UserAdminOut)
async def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: Update user role or active status."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)

    proj_count_stmt = select(func.count(Project.id)).where(Project.user_id == user.id)
    p_res = await db.execute(proj_count_stmt)
    count = p_res.scalar() or 0

    return UserAdminOut(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        project_count=count,
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: Delete a user and cascade delete their projects."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    await db.delete(user)
    await db.commit()
    return None


@router.get("/projects", response_model=List[ProjectOut])
async def list_all_projects(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: List all projects across all users."""
    stmt = select(Project).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_project(
    project_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: Delete any project by ID."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    proj = result.scalar_one_or_none()

    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    await db.delete(proj)
    await db.commit()
    return None


@router.get("/analytics", response_model=AnalyticsOut)
async def get_system_analytics(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin: Retrieve platform analytics:
    Total users, total projects, active analyses, completed projects,
    failed projects, completion rate %, total endpoints analyzed, and files analyzed.
    """
    users_stmt = select(func.count(User.id))
    u_res = await db.execute(users_stmt)
    total_users = u_res.scalar() or 0

    projects_stmt = select(func.count(Project.id))
    p_res = await db.execute(projects_stmt)
    total_projects = p_res.scalar() or 0

    active_stmt = select(func.count(Project.id)).where(Project.status.in_(["analyzing", "preprocessing"]))
    a_res = await db.execute(active_stmt)
    active_analyses = a_res.scalar() or 0

    completed_stmt = select(func.count(Project.id)).where(Project.status == "completed")
    c_res = await db.execute(completed_stmt)
    completed_projects = c_res.scalar() or 0

    failed_stmt = select(func.count(Project.id)).where(Project.status == "failed")
    f_res = await db.execute(failed_stmt)
    failed_projects = f_res.scalar() or 0

    completion_rate = (
        round((completed_projects / total_projects) * 100, 1)
        if total_projects > 0 else 0.0
    )

    endpoints_stmt = select(func.sum(Project.endpoint_count))
    ep_res = await db.execute(endpoints_stmt)
    total_endpoints = ep_res.scalar() or 0

    files_stmt = select(func.sum(Project.total_files))
    fl_res = await db.execute(files_stmt)
    total_files = fl_res.scalar() or 0

    return AnalyticsOut(
        total_users=total_users,
        total_projects=total_projects,
        active_analyses=active_analyses,
        completed_projects=completed_projects,
        failed_projects=failed_projects,
        completion_rate_percent=completion_rate,
        total_endpoints_analyzed=total_endpoints,
        total_files_analyzed=total_files,
    )


@router.get("/traces")
async def get_observability_traces(
    admin: User = Depends(require_admin),
):
    """
    Admin: Langfuse observability traces showing execution tree,
    tokens, latency, and cost per agent and project.
    """
    return {
        "total_traces": len(langfuse_tracer.get_all_traces()),
        "traces": langfuse_tracer.get_all_traces(),
    }


@router.get("/error-logs")
async def get_error_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: Retrieve activity feed error events."""
    stmt = (
        select(ActivityEvent)
        .where(ActivityEvent.event_type == "error")
        .order_by(ActivityEvent.timestamp.desc())
        .limit(50)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
