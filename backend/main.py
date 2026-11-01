from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings
from backend.database import init_db
from backend.api import auth, projects, analysis, reports, qa, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and resources on startup."""
    settings.ensure_directories()
    await init_db()
    yield


app = FastAPI(
    title="Multi-Agent Codebase Analysis & Documentation System",
    description="Intelligent multi-agent system analyzing codebases into role-specific (SDE & PM) documentation with live streaming, interactive steering, and RAG Q&A.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handling with friendly messages
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_type": "HTTPException",
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "ValidationError",
            "status_code": 422,
            "detail": "; ".join(errors),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "InternalServerError",
            "status_code": 500,
            "detail": f"An unexpected server error occurred: {str(exc)}",
        },
    )


# Root Health Check
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "healthy",
        "service": "Multi-Agent Codebase Analysis API",
        "version": "1.0.0",
        "environment": settings.app_env,
        "docs_url": "/docs",
    }


# Include Routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(qa.router)
app.include_router(admin.router)
