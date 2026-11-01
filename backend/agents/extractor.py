import os
import re
from pathlib import Path
from backend.graph.state import AnalysisState
from backend.services.event_bus import event_bus
from backend.services.repo_loader import CODE_EXTENSIONS, SKIP_DIRS


async def extractor_node(state: AnalysisState) -> dict:
    """
    API & Code Extractor Agent:
    Scans files, extracts endpoint schemas, class structures, and database models.
    Streams real-time per-file progress events matching M3 requirements.
    """
    project_id = state["project_id"]
    repo_path = Path(state["repo_path"])

    code_files: list[tuple[str, Path]] = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in CODE_EXTENSIONS:
                fp = Path(root) / f
                rel = os.path.relpath(fp, repo_path).replace("\\", "/")
                code_files.append((rel, fp))

    total_files = len(code_files)
    endpoints: list[dict] = []
    data_models: list[dict] = []
    component_names: list[str] = []

    route_regex = re.compile(
        r"@(?:app|router|api)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )
    class_regex = re.compile(r"class\s+([a-zA-Z0-9_]+)(?:\(([^)]+)\))?:")

    for idx, (rel_path, fp) in enumerate(code_files, start=1):
        # Calculate real-time percentage progress (25% to 45%)
        pct = 25.0 + (20.0 * (idx / max(total_files, 1)))

        # M3 requirement: "Processing file 1/100: auth.py"
        file_msg = f"Processing file {idx}/{total_files}: {Path(rel_path).name}"
        await event_bus.emit_event(
            project_id=project_id,
            event_type="info",
            stage="Code Extraction",
            message=file_msg,
            percentage=pct,
            file_name=rel_path,
        )

        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
            # Extract endpoints
            for method, path in route_regex.findall(content):
                endpoints.append({
                    "method": method.upper(),
                    "path": path,
                    "file": rel_path,
                })

            # Extract models / classes
            for cls_name, base_cls in class_regex.findall(content):
                data_models.append({
                    "name": cls_name,
                    "base": base_cls or "object",
                    "file": rel_path,
                })
                component_names.append(cls_name)

        except Exception:
            pass

    summary_msg = f"Extractor Agent: Discovered {len(endpoints)} API endpoints and {len(data_models)} data/entity classes across {total_files} files."
    await event_bus.emit_event(
        project_id=project_id,
        event_type="milestone",
        stage="Code Extraction",
        message=summary_msg,
        percentage=45.0,
    )

    return {
        "api_endpoints": endpoints,
        "data_models": data_models,
        "code_structure": {"components": component_names[:25]},
        "endpoint_count": len(endpoints),
        "total_files": total_files,
        "current_step": "extractor",
        "progress_percentage": 45.0,
    }
