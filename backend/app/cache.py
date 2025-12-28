# backend/app/cache.py
import os
import shutil
import tempfile
from typing import Optional

_cache_dir: Optional[str] = None


def get_cache_dir() -> str:
    """
    Return a temp directory for model caches. Created once per process.
    """
    global _cache_dir
    if _cache_dir is None:
        _cache_dir = tempfile.mkdtemp(prefix="hf-cache-")
    return _cache_dir


def cleanup_cache_dir() -> None:
    """
    Remove the temp cache directory if it exists. Safe to call multiple times.
    """
    global _cache_dir
    if _cache_dir and os.path.isdir(_cache_dir):
        shutil.rmtree(_cache_dir, ignore_errors=True)
    _cache_dir = None
