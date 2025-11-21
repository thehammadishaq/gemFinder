"""
FastAPI Application Entry Point
Main application file that initializes and runs the FastAPI server
"""
import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from config.settings import settings
from routes import api_router
from database.database import init_db, close_db
import os

# Fix for Windows: Set event loop policy for Playwright compatibility
if sys.platform == 'win32':
    # Set policy before any async operations
    if sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        # For Python < 3.8, use SelectorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Initialize FastAPI app
app = FastAPI(
    title="Company Profile API",
    description="REST API for Company Profile Data Management (MongoDB)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware - Allow frontend to access API
# CORS_ORIGINS is converted to list by model_validator
cors_origins = settings.cors_origins_list
# Handle wildcard for development
if "*" in cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if "*" not in cors_origins else False,  # Can't use credentials with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static files for supply chain graphs
supply_chain_graphs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "supply-chain-graphs")
if os.path.exists(supply_chain_graphs_dir):
    app.mount("/supply-chain-graphs", StaticFiles(directory=supply_chain_graphs_dir), name="supply-chain-graphs")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Company Profile API",
        "version": "1.0.0",
        "database": "MongoDB",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "MongoDB"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=settings.DEBUG
    )
