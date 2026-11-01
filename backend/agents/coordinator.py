from backend.graph.state import AnalysisState
from backend.services.event_bus import event_bus


async def coordinator_node(state: AnalysisState) -> dict:
    """
    Coordinator / Router Agent:
    Inspects project configuration, personas, and depth.
    Initializes analysis stages and emits coordinated plan.
    """
    project_id = state["project_id"]
    personas = state.get("personas", ["sde", "pm"])
    config = state.get("config", {})
    depth = config.get("depth", "Standard")

    msg = f"Coordinator: Initializing {depth} analysis for personas: {', '.join(p.upper() for p in personas)}."
    await event_bus.emit_event(
        project_id=project_id,
        event_type="milestone",
        stage="Coordinator",
        message=msg,
        percentage=25.0,
    )

    return {
        "current_step": "coordinator",
        "progress_percentage": 25.0,
    }
