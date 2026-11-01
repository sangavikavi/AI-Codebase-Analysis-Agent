from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class DiagramItem(BaseModel):
    title: str
    type: Literal["architecture", "flowchart", "sequence", "er"]
    code: str


class ReportOut(BaseModel):
    id: int
    project_id: str
    persona: str
    title: str
    content_markdown: str
    diagrams_json: list[dict] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QAQuery(BaseModel):
    question: str = Field(min_length=2)
    persona: Literal["sde", "pm"] = "sde"


class CodeCitation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    snippet: str


class QAResponse(BaseModel):
    answer: str
    persona: str
    citations: list[CodeCitation] = Field(default_factory=list)
    response_time_ms: float


class ExportRequest(BaseModel):
    format: Literal["markdown", "pdf"] = "markdown"
    personas: list[str] = Field(default_factory=lambda: ["sde", "pm"])
