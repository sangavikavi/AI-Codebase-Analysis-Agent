import os
import re
import shutil
import zipfile
from pathlib import Path
import httpx
from fastapi import HTTPException, UploadFile, status

from backend.config import settings

# Recognized source code file extensions
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".cpp",
    ".h", ".hpp", ".cs", ".php", ".rb", ".swift", ".kt", ".scala", ".html",
    ".vue", ".svelte", ".sql", ".sh", ".bash", ".rust", ".m", ".dart"
}

# Documentation-only extensions
DOCS_EXTENSIONS = {
    ".md", ".txt", ".rst", ".doc", ".docx", ".pdf", ".rtf", ".tex", ".odt"
}

# Binary and media extensions
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".bmp", ".webp",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".iso", ".dat", ".class",
    ".pyc", ".pyd", ".o", ".a", ".mp3", ".mp4", ".wav", ".avi", ".mov"
}

# Skip patterns during analysis
SKIP_DIRS = {
    "node_modules", ".git", "venv", ".venv", "env", "__pycache__",
    "dist", "build", ".next", ".nuxt", "target", "vendor", ".idea", ".vscode"
}


def sanitize_filename(name: str) -> str:
    """Strip dangerous characters from filename."""
    return re.sub(r"[^\w\-.]", "_", name)


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Validate and extract owner and repo from a GitHub URL.
    Accepted formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - http://github.com/owner/repo
    """
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed GitHub URL. URL cannot be empty.",
        )

    pattern = r"^(https?:\/\/)?(www\.)?github\.com\/([a-zA-Z0-9_\-\.]+)\/([a-zA-Z0-9_\-\.]+?)(\.git)?(\/)?$"
    match = re.match(pattern, url.strip())
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed GitHub URL. Must be in the format: https://github.com/owner/repository",
        )

    owner = match.group(3)
    repo = match.group(4)
    return owner, repo


def inspect_extracted_directory(extract_path: Path) -> dict:
    """
    Inspect files in the extracted directory to ensure it is a valid codebase.
    Enforces validation checks:
    - Empty repository
    - Docs-only repository
    - Binary-only repository
    - Non-code repository
    """
    all_files: list[Path] = []
    code_files: list[Path] = []
    doc_files: list[Path] = []
    binary_files: list[Path] = []

    for root, dirs, files in os.walk(extract_path):
        # Exclude skip directories in place
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for file in files:
            if file.startswith("."):
                continue
            file_path = Path(root) / file
            all_files.append(file_path)
            ext = file_path.suffix.lower()

            if ext in CODE_EXTENSIONS:
                code_files.append(file_path)
            elif ext in DOCS_EXTENSIONS:
                doc_files.append(file_path)
            elif ext in BINARY_EXTENSIONS:
                binary_files.append(file_path)

    if not all_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The repository is empty or contains no valid files.",
        )

    # Docs-only check
    if not code_files and doc_files and not binary_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Non-code repository: The repository contains only documentation files. A source code repository is required.",
        )

    # Binary-only check
    if not code_files and binary_files and not doc_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Non-code repository: The repository contains only binary or media assets. A source code repository is required.",
        )

    # No code files found
    if not code_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recognizable source code files found in the repository.",
        )

    return {
        "total_files": len(all_files),
        "code_files_count": len(code_files),
        "doc_files_count": len(doc_files),
        "binary_files_count": len(binary_files),
    }


async def save_and_extract_zip(upload_file: UploadFile, project_id: str) -> tuple[str, dict]:
    """
    Validate, save, and safely unpack a ZIP archive.
    Rejects:
    - Wrong format (RAR, 7z, etc.)
    - File over limit (100MB)
    - Corrupt or incomplete ZIP
    - Empty or non-code repository
    """
    filename = upload_file.filename or "upload.zip"
    lower_name = filename.lower()

    # Wrong format check
    for forbidden_ext in [".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"]:
        if lower_name.endswith(forbidden_ext):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported archive format '{forbidden_ext}'. Only ZIP (.zip) archives are supported.",
            )

    if not lower_name.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid archive format. Only ZIP (.zip) archives are supported.",
        )

    settings.ensure_directories()
    dest_zip_path = Path(settings.upload_dir) / f"{project_id}_{sanitize_filename(filename)}"
    extract_path = Path(settings.repos_dir) / project_id

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    total_bytes = 0

    try:
        with open(dest_zip_path, "wb") as f:
            while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    f.close()
                    dest_zip_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum upload limit of {settings.max_upload_size_mb}MB.",
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        dest_zip_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading upload file: {str(e)}",
        )

    # Validate ZIP integrity
    try:
        with zipfile.ZipFile(dest_zip_path, "r") as zf:
            corrupt_file = zf.testzip()
            if corrupt_file is not None:
                raise zipfile.BadZipFile(f"Corrupted file in archive: {corrupt_file}")
            
            # Safe extraction to prevent zip slip
            extract_path.mkdir(parents=True, exist_ok=True)
            for member in zf.infolist():
                member_path = os.path.abspath(os.path.join(extract_path, member.filename))
                if not member_path.startswith(os.path.abspath(extract_path)):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Dangerous ZIP path detected (path traversal attempt).",
                    )
            zf.extractall(extract_path)
    except (zipfile.BadZipFile, EOFError) as e:
        dest_zip_path.unlink(missing_ok=True)
        shutil.rmtree(extract_path, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupt or incomplete ZIP archive: {str(e)}",
        )

    # Validate contents
    stats = inspect_extracted_directory(extract_path)
    return str(extract_path), stats


async def clone_github_repo(github_url: str, project_id: str) -> tuple[str, dict]:
    """
    Validate and clone a public GitHub repository using GitHub's ZIP archive API or git.
    Rejects:
    - Malformed GitHub URL
    - Private repo or repo without access (404/403/401)
    - Empty or non-code repository
    """
    owner, repo = parse_github_url(github_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        try:
            resp = await client.get(api_url, headers={"User-Agent": "Codebase-Analysis-Agent"})
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Network error connecting to GitHub: {str(e)}",
            )

        if resp.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub repository not found or repository is private without access.",
            )
        elif resp.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access denied to GitHub repository. Verify access rights or token.",
            )
        elif resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub API error ({resp.status_code}): {resp.text}",
            )

        repo_meta = resp.json()
        default_branch = repo_meta.get("default_branch", "main")

        # Download repository zipball
        zipball_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{default_branch}.zip"
        zip_resp = await client.get(zipball_url)
        if zip_resp.status_code != 200:
            # Fallback to master if main branch isn't standard
            zipball_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
            zip_resp = await client.get(zipball_url)

        if zip_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to download repository archive from GitHub.",
            )

    settings.ensure_directories()
    dest_zip_path = Path(settings.upload_dir) / f"{project_id}_{owner}_{repo}.zip"
    extract_path = Path(settings.repos_dir) / project_id

    with open(dest_zip_path, "wb") as f:
        f.write(zip_resp.content)

    try:
        with zipfile.ZipFile(dest_zip_path, "r") as zf:
            extract_path.mkdir(parents=True, exist_ok=True)
            zf.extractall(extract_path)
    except Exception as e:
        dest_zip_path.unlink(missing_ok=True)
        shutil.rmtree(extract_path, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error extracting GitHub archive: {str(e)}",
        )

    # Flatten if GitHub archive placed everything in a single root folder
    subdirs = [d for d in extract_path.iterdir() if d.is_dir()]
    if len(subdirs) == 1 and not any(f.is_file() for f in extract_path.iterdir()):
        single_dir = subdirs[0]
        temp_dir = extract_path.parent / f"{project_id}_temp"
        shutil.move(str(single_dir), str(temp_dir))
        shutil.rmtree(extract_path)
        shutil.move(str(temp_dir), str(extract_path))

    stats = inspect_extracted_directory(extract_path)
    return str(extract_path), stats
