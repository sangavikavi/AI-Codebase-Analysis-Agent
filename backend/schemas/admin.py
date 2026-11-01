from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from backend.models.user import UserRole


class UserAdminOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    project_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class AnalyticsOut(BaseModel):
    total_users: int
    total_projects: int
    active_analyses: int
    completed_projects: int
    failed_projects: int
    completion_rate_percent: float
    total_endpoints_analyzed: int
    total_files_analyzed: int
