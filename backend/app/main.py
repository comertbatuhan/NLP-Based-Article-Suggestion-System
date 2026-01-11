# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router
from .cache import get_model_cache_dir, get_temp_dir, cleanup_temp_dir

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_model_cache_dir()
    get_temp_dir()
    yield
    cleanup_temp_dir()

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