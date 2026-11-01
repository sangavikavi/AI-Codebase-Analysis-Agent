from backend.graph.state import AnalysisState
from backend.services.event_bus import event_bus
from backend.services.web_search import perform_web_search


async def web_research_node(state: AnalysisState) -> dict:
    """
    Web Research Agent:
    Queries real web search for security advisories, OWASP best practices,
    and library architecture patterns tailored to the detected stack.
    """
    project_id = state["project_id"]
    stack = state.get("detected_stack", "Python Web")
    config = state.get("config", {})
    toggles = config.get("feature_toggles", {})

    research_notes: list[dict] = []

    if toggles.get("include_owasp", True):
        query = f"OWASP Top 10 API Security {stack} architecture best practices"
        await event_bus.emit_event(
            project_id=project_id,
            event_type="info",
            stage="Web Research",
            message=f"Web Research Agent: Investigating industry security benchmarks: '{query}'",
            percentage=50.0,
        )

        results = perform_web_search(query, max_results=3)
        research_notes.extend(results)

    research_summary = f"Web Research Agent: Found {len(research_notes)} technical benchmarks and security guidelines to cite."
    await event_bus.emit_event(
        project_id=project_id,
        event_type="milestone",
        stage="Web Research",
        message=research_summary,
        percentage=55.0,
    )

    return {
        "web_research": research_notes,
        "current_step": "web_researcher",
        "progress_percentage": 55.0,
    }
