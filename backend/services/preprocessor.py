import ast
import json
import os
import re
from pathlib import Path
from typing import Any
import uuid

from backend.services.repo_loader import CODE_EXTENSIONS, SKIP_DIRS
from backend.services.vector_store import CodeChunk, vector_store


def parse_dependencies(repo_path: Path) -> dict[str, list[str]]:
    """Parse dependency files found in the repository."""
    dependencies: dict[str, list[str]] = {}

    # Python requirements.txt
    req_file = repo_path / "requirements.txt"
    if req_file.exists():
        try:
            lines = req_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            pkgs = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    pkg = re.split(r"[><=~;]", line)[0].strip().lower()
                    if pkg:
                        pkgs.append(pkg)
            dependencies["python_requirements"] = pkgs
        except Exception:
            pass

    # Node package.json
    pkg_json = repo_path / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
            deps = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
            dependencies["node_packages"] = [d.lower() for d in deps]
        except Exception:
            pass

    # Python pyproject.toml
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
            dependencies["pyproject"] = [
                fw for fw in ["fastapi", "flask", "django", "pydantic", "sqlalchemy", "celery", "pytest"]
                if fw in content
            ]
        except Exception:
            pass

    # Go go.mod
    go_mod = repo_path / "go.mod"
    if go_mod.exists():
        try:
            content = go_mod.read_text(encoding="utf-8", errors="ignore").lower()
            dependencies["go_modules"] = [
                m for m in ["gin", "echo", "fiber", "chi", "gorm", "grpc"] if m in content
            ]
        except Exception:
            pass

    # Rust Cargo.toml
    cargo = repo_path / "Cargo.toml"
    if cargo.exists():
        try:
            content = cargo.read_text(encoding="utf-8", errors="ignore").lower()
            dependencies["cargo_crates"] = [
                c for c in ["actix-web", "axum", "rocket", "tokio", "serde"] if c in content
            ]
        except Exception:
            pass

    return dependencies


def detect_stack(repo_path: Path) -> dict[str, Any]:
    """
    Detect repo type and stack with at least 90% accuracy.
    Identifies primary language, secondary languages, and active frameworks.
    """
    lang_file_counts: dict[str, int] = {}
    dep_dict = parse_dependencies(repo_path)

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for file in files:
            ext = Path(file).suffix.lower()
            if ext == ".py":
                lang_file_counts["Python"] = lang_file_counts.get("Python", 0) + 1
            elif ext in [".ts", ".tsx"]:
                lang_file_counts["TypeScript"] = lang_file_counts.get("TypeScript", 0) + 1
            elif ext in [".js", ".jsx", ".mjs"]:
                lang_file_counts["JavaScript"] = lang_file_counts.get("JavaScript", 0) + 1
            elif ext == ".go":
                lang_file_counts["Go"] = lang_file_counts.get("Go", 0) + 1
            elif ext in [".java", ".kt"]:
                lang_file_counts["Java"] = lang_file_counts.get("Java", 0) + 1
            elif ext == ".rs":
                lang_file_counts["Rust"] = lang_file_counts.get("Rust", 0) + 1
            elif ext in [".c", ".cpp", ".h", ".hpp"]:
                lang_file_counts["C/C++"] = lang_file_counts.get("C/C++", 0) + 1
            elif ext in [".cs"]:
                lang_file_counts["C#"] = lang_file_counts.get("C#", 0) + 1
            elif ext in [".php"]:
                lang_file_counts["PHP"] = lang_file_counts.get("PHP", 0) + 1
            elif ext in [".rb"]:
                lang_file_counts["Ruby"] = lang_file_counts.get("Ruby", 0) + 1

    if not lang_file_counts:
        return {"language": "Unknown", "framework": "Generic", "stack_label": "Generic Codebase"}

    primary_lang = max(lang_file_counts.items(), key=lambda x: x[1])[0]

    # Detect Framework
    frameworks: list[str] = []
    py_deps = dep_dict.get("python_requirements", []) + dep_dict.get("pyproject", [])
    node_deps = dep_dict.get("node_packages", [])
    go_deps = dep_dict.get("go_modules", [])
    rust_deps = dep_dict.get("cargo_crates", [])

    if primary_lang == "Python":
        if any("fastapi" in d for d in py_deps):
            frameworks.append("FastAPI")
        elif any("flask" in d for d in py_deps):
            frameworks.append("Flask")
        elif any("django" in d for d in py_deps):
            frameworks.append("Django")
        elif any("tornado" in d for d in py_deps):
            frameworks.append("Tornado")
        else:
            frameworks.append("Standard Python")

    elif primary_lang in ["TypeScript", "JavaScript"]:
        if any("next" in d for d in node_deps):
            frameworks.append("Next.js")
        if any("react" in d for d in node_deps) and "Next.js" not in frameworks:
            frameworks.append("React")
        if any("express" in d for d in node_deps):
            frameworks.append("Express")
        if any("nest" in d for d in node_deps):
            frameworks.append("NestJS")
        if any("vue" in d for d in node_deps):
            frameworks.append("Vue")
        if not frameworks:
            frameworks.append("Node.js")

    elif primary_lang == "Go":
        if any("gin" in d for d in go_deps):
            frameworks.append("Gin")
        elif any("echo" in d for d in go_deps):
            frameworks.append("Echo")
        else:
            frameworks.append("Standard Go")

    elif primary_lang == "Rust":
        if any("actix" in d for d in rust_deps):
            frameworks.append("Actix-web")
        elif any("axum" in d for d in rust_deps):
            frameworks.append("Axum")
        else:
            frameworks.append("Standard Rust")

    framework_label = " / ".join(frameworks) if frameworks else "Standard"
    stack_label = f"{primary_lang} {framework_label} project"

    return {
        "primary_language": primary_lang,
        "languages": lang_file_counts,
        "frameworks": frameworks,
        "stack_label": stack_label,
        "dependencies": dep_dict,
    }


def detect_entry_points(repo_path: Path) -> list[str]:
    """Detect main entry points in the codebase."""
    candidates = [
        "main.py", "app.py", "server.py", "run.py", "manage.py", "wsgi.py", "asgi.py",
        "index.js", "index.ts", "server.js", "server.ts", "app.js", "app.ts",
        "main.go", "Application.java", "Program.cs", "main.rs"
    ]
    detected: list[str] = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for file in files:
            if file in candidates:
                rel = os.path.relpath(Path(root) / file, repo_path).replace("\\", "/")
                detected.append(rel)

    return sorted(detected)


def count_api_endpoints(repo_path: Path) -> int:
    """
    Count API endpoints across various frameworks (FastAPI, Flask, Express, Django, etc.).
    """
    endpoint_patterns = [
        # FastAPI / Flask: @app.get(...), @router.post(...), @api.route(...)
        re.compile(r"@\w+\.(get|post|put|delete|patch|options|head|route)\s*\(", re.IGNORECASE),
        # Express / Node: app.get('/', ...), router.post('/...', ...)
        re.compile(r"\b(app|router)\.(get|post|put|delete|patch)\s*\(", re.IGNORECASE),
        # Spring Boot: @GetMapping(...), @PostMapping(...)
        re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(", re.IGNORECASE),
        # Go Gin: r.GET(...), group.POST(...)
        re.compile(r"\b\w+\.(GET|POST|PUT|DELETE|PATCH)\s*\(", re.IGNORECASE),
    ]

    count = 0
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in CODE_EXTENSIONS:
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for pat in endpoint_patterns:
                        matches = pat.findall(content)
                        count += len(matches)
                except Exception:
                    pass
    return count


def chunk_python_code(rel_path: str, content: str, project_id: str) -> list[CodeChunk]:
    """Parse Python code using AST into logical function and class chunks."""
    chunks: list[CodeChunk] = []
    lines = content.splitlines()

    try:
        tree = ast.parse(content)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = getattr(node, "end_lineno", start + 10)
                snippet = "\n".join(lines[start - 1:end])
                doc = ast.get_docstring(node) or f"Function {node.name}"
                is_route = any(
                    isinstance(dec, ast.Call) and getattr(dec.func, "attr", "") in ["get", "post", "put", "delete", "patch", "route"]
                    for dec in node.decorator_list
                )
                chunk_type = "route" if is_route else "function"

                chunks.append(
                    CodeChunk(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        file_path=rel_path,
                        start_line=start,
                        end_line=end,
                        chunk_type=chunk_type,
                        name=node.name,
                        content=snippet,
                        summary=doc.splitlines()[0] if doc else node.name,
                    )
                )

            elif isinstance(node, ast.ClassDef):
                start = node.lineno
                end = getattr(node, "end_lineno", start + 20)
                snippet = "\n".join(lines[start - 1:end])
                doc = ast.get_docstring(node) or f"Class {node.name}"
                chunks.append(
                    CodeChunk(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        file_path=rel_path,
                        start_line=start,
                        end_line=end,
                        chunk_type="class",
                        name=node.name,
                        content=snippet,
                        summary=doc.splitlines()[0] if doc else node.name,
                    )
                )
    except SyntaxError:
        pass

    # If file was small or AST parsing found nothing, store whole file module chunk
    if not chunks and content.strip():
        chunks.append(
            CodeChunk(
                id=str(uuid.uuid4()),
                project_id=project_id,
                file_path=rel_path,
                start_line=1,
                end_line=len(lines),
                chunk_type="module",
                name=Path(rel_path).name,
                content=content[:1500],
                summary=f"Module {Path(rel_path).name}",
            )
        )

    return chunks


def chunk_generic_code(rel_path: str, content: str, project_id: str) -> list[CodeChunk]:
    """Parse JS/TS/Go/Java/Rust into functions, classes and methods using regex blocks."""
    chunks: list[CodeChunk] = []
    lines = content.splitlines()

    # Pattern for functions and classes in JS/TS/Go/Java
    func_pattern = re.compile(
        r"^(?:export\s+)?(?:async\s+)?(?:function\s+([a-zA-Z0-9_]+)|class\s+([a-zA-Z0-9_]+)|func\s+(?:\([^)]+\)\s+)?([a-zA-Z0-9_]+)|public\s+[\w<>]+\s+([a-zA-Z0-9_]+)\s*\()",
        re.MULTILINE
    )

    for i, line in enumerate(lines):
        match = func_pattern.search(line)
        if match:
            name = next((g for g in match.groups() if g is not None), "anonymous")
            start = i + 1
            end = min(i + 35, len(lines))
            snippet = "\n".join(lines[start - 1:end])
            chunk_type = "class" if "class " in line else "function"

            chunks.append(
                CodeChunk(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    file_path=rel_path,
                    start_line=start,
                    end_line=end,
                    chunk_type=chunk_type,
                    name=name,
                    content=snippet,
                    summary=f"{chunk_type.capitalize()} {name} in {rel_path}",
                )
            )

    if not chunks and content.strip():
        chunks.append(
            CodeChunk(
                id=str(uuid.uuid4()),
                project_id=project_id,
                file_path=rel_path,
                start_line=1,
                end_line=len(lines),
                chunk_type="module",
                name=Path(rel_path).name,
                content=content[:1500],
                summary=f"File {rel_path}",
            )
        )

    return chunks


def process_and_index_codebase(repo_path: Path, project_id: str) -> dict[str, Any]:
    """
    Intelligently preprocess codebase:
    1. Detect stack and frameworks
    2. Detect entry points
    3. Count API endpoints
    4. Chunk code logically and attach metadata
    5. Index chunks into vector store for semantic search
    """
    stack_info = detect_stack(repo_path)
    entry_points = detect_entry_points(repo_path)
    endpoint_count = count_api_endpoints(repo_path)

    all_chunks: list[CodeChunk] = []

    # Walk codebase prioritizing important files first
    files_to_process: list[tuple[str, Path]] = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in CODE_EXTENSIONS:
                fp = Path(root) / file
                rel = os.path.relpath(fp, repo_path).replace("\\", "/")
                files_to_process.append((rel, fp))

    # Sort files to prioritize entry points, api/routes, models
    def file_priority(item: tuple[str, Path]) -> int:
        rel = item[0].lower()
        if any(ep in rel for ep in ["main", "app", "server", "index"]):
            return 0
        if any(k in rel for k in ["api", "route", "endpoint", "controller"]):
            return 1
        if any(k in rel for k in ["model", "schema", "entity"]):
            return 2
        return 3

    files_to_process.sort(key=file_priority)

    for rel_path, file_path in files_to_process:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            ext = file_path.suffix.lower()
            if ext == ".py":
                chunks = chunk_python_code(rel_path, content, project_id)
            else:
                chunks = chunk_generic_code(rel_path, content, project_id)
            all_chunks.extend(chunks)
        except Exception:
            pass

    # Index into vector store
    vector_store.add_chunks(project_id, all_chunks)

    return {
        "stack_info": stack_info,
        "entry_points": entry_points,
        "endpoint_count": endpoint_count,
        "total_files": len(files_to_process),
        "total_chunks": len(all_chunks),
    }
