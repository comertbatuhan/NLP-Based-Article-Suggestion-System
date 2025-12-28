#backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router
from .cache import cleanup_cache_dir, get_cache_dir

app = FastAPI(title="Research Finder API", version="0.1.0")

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

# Ensure cache directory exists on startup
@app.on_event("startup")
def _init_cache_dir():
    get_cache_dir()


# Clean up Hugging Face cache when the server stops
@app.on_event("shutdown")
def _cleanup_cache():
    cleanup_cache_dir()

@app.get("/health")
def health():
    return {"status": "ok"}
