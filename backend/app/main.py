# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router
from .cache import cleanup_cache_dir, get_cache_dir

# Define the lifespan context manager to handle startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    get_cache_dir()
    
    yield  # The application runs here
    
    # --- Shutdown Logic ---
    cleanup_cache_dir()

# Pass the lifespan handler to the FastAPI app
app = FastAPI(
    title="Research Finder API", 
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}