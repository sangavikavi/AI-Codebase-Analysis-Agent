from typing import Any, List, Optional
from typing_extensions import TypedDict


class AnalysisState(TypedDict):
    """
    Typed graph state passed between all agents in the LangGraph orchestration.
    """
    project_id: str
    repo_path: str
    personas: list[str]
    config: dict
    user_context_injections: list[str]

    # Preprocessed & Extracted Metadata
    detected_stack: str
    entry_points: list[str]
    total_files: int
    endpoint_count: int
    api_endpoints: list[dict]
    data_models: list[dict]
    code_structure: dict

    # Web Research
    web_research: list[dict]

    # Generated Persona Reports
    sde_report: str
    pm_report: str
    diagrams: list[dict]
    evaluation: dict

    # Workflow controls
    current_step: str
    is_paused: bool
    progress_percentage: float
