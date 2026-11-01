from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.project import Project
from backend.models.user import User, UserRole
from backend.schemas.report import QAQuery, QAResponse
from backend.services.auth_service import get_current_user
from backend.services.qa_service import answer_codebase_query

router = APIRouter(prefix="/api/projects", tags=["RAG Codebase Q&A"])


@router.post("/{project_id}/qa", response_model=QAResponse)
async def ask_question_over_codebase(
    project_id: str,
    payload: QAQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    M6: RAG Q&A over codebase with file & line citations and snippets.
    - Persona-adaptive ('sde' technical vs 'pm' business)
    - Responds in under 3 seconds
    - Cites exact file, start/end line, and snippet
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    response = answer_codebase_query(
        project_id=project_id,
        question=payload.question,
        persona=payload.persona,
        top_k=4,
    )
    return response
