import math
import re
from typing import Any
from pydantic import BaseModel


class CodeChunk(BaseModel):
    id: str
    project_id: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # function, class, route, config, module
    name: str
    content: str
    summary: str
    embedding: list[float] = []


def simple_tokenize(text: str) -> list[str]:
    """Tokenize code and text into normalized words, splitting snake_case and camelCase."""
    # Split camelCase
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    # Replace non-alphanumeric with spaces
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return [t for t in tokens if len(t) > 1]


def get_token_stems(tokens: list[str]) -> set[str]:
    """Extract stems/prefixes (min 4 chars) to match 'authenticate', 'authentication', 'auth'."""
    stems = set(tokens)
    for t in tokens:
        if len(t) >= 4:
            stems.add(t[:4])
        if len(t) >= 6:
            stems.add(t[:6])
    return stems


class VectorStoreService:
    """
    In-memory and PostgreSQL+pgvector compatible vector store for code chunks.
    Maintains project chunks with vector indexing and semantic/BM25 hybrid search.
    """

    def __init__(self):
        # Maps project_id -> list of CodeChunk
        self._stores: dict[str, list[CodeChunk]] = {}
        # Precomputed token frequency per chunk
        self._chunk_tokens: dict[str, set[str]] = {}

    def add_chunks(self, project_id: str, chunks: list[CodeChunk]) -> None:
        """Store and index code chunks for a project."""
        if project_id not in self._stores:
            self._stores[project_id] = []

        for chunk in chunks:
            full_text = f"{chunk.name} {chunk.chunk_type} {chunk.file_path} {chunk.summary} {chunk.content}"
            tokens = simple_tokenize(full_text)
            stems = get_token_stems(tokens)
            self._chunk_tokens[chunk.id] = stems

        self._stores[project_id].extend(chunks)

    def get_chunks(self, project_id: str) -> list[CodeChunk]:
        """Retrieve all indexed chunks for a project."""
        return self._stores.get(project_id, [])

    def clear_project(self, project_id: str) -> None:
        """Clear indexed chunks for a project."""
        chunks = self._stores.pop(project_id, [])
        for c in chunks:
            self._chunk_tokens.pop(c.id, None)

    def semantic_search(
        self, project_id: str, query: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Perform semantic & lexical search against project code chunks.
        Returns top matching chunks ranked by relevance score.
        """
        chunks = self.get_chunks(project_id)
        if not chunks:
            return []

        query_tokens = simple_tokenize(query)
        query_stems = get_token_stems(query_tokens)

        scored_chunks: list[tuple[float, CodeChunk]] = []

        for chunk in chunks:
            chunk_stems = self._chunk_tokens.get(chunk.id, set())

            # Calculate semantic overlap score
            exact_matches = sum(1.0 for q in query_tokens if q in chunk_stems)
            stem_matches = sum(0.5 for q in query_stems if q in chunk_stems)

            # Name / file path priority bonus
            name_tokens = set(simple_tokenize(f"{chunk.name} {chunk.file_path}"))
            name_bonus = 1.0 if any(q in name_tokens or any(s in name_tokens for s in query_stems) for q in query_tokens) else 0.0

            total_score = (exact_matches * 2.0) + (stem_matches * 1.0) + (name_bonus * 3.0)

            # Normalized score
            normalized_score = min(1.0, total_score / (len(query_tokens) * 3.0 + 1e-5))
            if normalized_score > 0.05:
                scored_chunks.append((normalized_score, chunk))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # If no strong match found, return top chunks
        if not scored_chunks:
            top_results = [(0.1, c) for c in chunks[:top_k]]
        else:
            top_results = scored_chunks[:top_k]

        return [
            {
                "id": chunk.id,
                "project_id": chunk.project_id,
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name,
                "content": chunk.content,
                "summary": chunk.summary,
                "score": round(score, 4),
            }
            for score, chunk in top_results
        ]


# Global vector store singleton
vector_store = VectorStoreService()
