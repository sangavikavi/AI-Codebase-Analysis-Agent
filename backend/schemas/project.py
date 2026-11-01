from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class ConfigOptions(BaseModel):
    depth: Literal["Quick", "Standard", "Deep"] = "Standard"
    verbosity: Literal["Low", "Medium", "High"] = "Medium"
    feature_toggles: dict[str, bool] = Field(
        default_factory=lambda: {
            "include_owasp": True,
            "include_db_schema": True,
            "include_business_rules": True,
            "include_diagrams": True,
        }
    )
    diagram_preferences: list[str] = Field(
        default_factory=lambda: ["architecture", "flowchart", "sequence", "er"]
    )
    template_name: str = "default"


class ProjectCreateGitHub(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    github_url: str = Field(description="Public GitHub repository URL")
    personas: list[Literal["sde", "pm"]] = Field(
        default_factory=lambda: ["sde", "pm"], min_length=1
    )
    config: ConfigOptions = Field(default_factory=ConfigOptions)


class ProjectOut(BaseModel):
    id: str
    name: str
    user_id: int
    source_type: str
    github_url: str | None
    status: str
    personas: list[str]
    config: dict
    detected_stack: str | None
    entry_points: list[str]
    total_files: int
    total_chunks: int
    endpoint_count: int
    progress_percentage: float
    current_stage: str
    current_file: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectStartResponse(BaseModel):
    project_id: str
    status: str
    message: str
