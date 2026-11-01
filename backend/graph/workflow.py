from typing import Any
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graph.state import AnalysisState
from backend.agents.coordinator import coordinator_node
from backend.agents.extractor import extractor_node
from backend.agents.web_researcher import web_research_node
from backend.agents.sde_writer import sde_writer_node
from backend.agents.pm_writer import pm_writer_node
from backend.agents.diagram_agent import diagram_node
from backend.agents.evaluator import evaluator_node


def build_analysis_graph(checkpointer: Any = None):
    """
    Construct the LangGraph multi-agent orchestration graph.
    Integrates 7 specialized nodes with checkpointer support.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = StateGraph(AnalysisState)

    # Register all 7 agents
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("web_researcher", web_research_node)
    graph.add_node("sde_writer", sde_writer_node)
    graph.add_node("pm_writer", pm_writer_node)
    graph.add_node("diagram_agent", diagram_node)
    graph.add_node("evaluator", evaluator_node)

    # Define linear and coordinated edges
    graph.add_edge(START, "coordinator")
    graph.add_edge("coordinator", "extractor")
    graph.add_edge("extractor", "web_researcher")
    graph.add_edge("web_researcher", "sde_writer")
    graph.add_edge("sde_writer", "pm_writer")
    graph.add_edge("pm_writer", "diagram_agent")
    graph.add_edge("diagram_agent", "evaluator")
    graph.add_edge("evaluator", END)

    # Compile with checkpointing
    compiled = graph.compile(checkpointer=checkpointer)
    return compiled


checkpointer = MemorySaver()
analysis_graph = build_analysis_graph(checkpointer)
