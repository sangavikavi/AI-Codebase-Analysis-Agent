from typing import Any
from backend.services.vector_store import vector_store


class MCPKnowledgeBaseServer:
    """
    Model Context Protocol (MCP) Knowledge Base Server:
    Exposes code chunk querying, entity schema resolution, and semantic search
    tools for single-purpose agents during analysis.
    """

    @staticmethod
    def query_codebase_knowledge(project_id: str, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Query knowledge base for code chunks relevant to an architectural concern."""
        return vector_store.semantic_search(project_id, query, top_k=top_k)

    @staticmethod
    def get_component_definition(project_id: str, component_name: str) -> dict[str, Any] | None:
        """Retrieve definition snippet and metadata for a specific named class or function."""
        chunks = vector_store.get_chunks(project_id)
        for c in chunks:
            if c.name.lower() == component_name.lower():
                return {
                    "name": c.name,
                    "type": c.chunk_type,
                    "file_path": c.file_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "summary": c.summary,
                    "content": c.content,
                }
        return None


mcp_kb_server = MCPKnowledgeBaseServer()
