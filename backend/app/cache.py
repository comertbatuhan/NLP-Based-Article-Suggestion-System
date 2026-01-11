# backend/app/cache.py
import os, shutil, tempfile
from pathlib import Path
from typing import Optional

_model_cache_dir: Optional[str] = None
_temp_dir: Optional[str] = None

def get_model_cache_dir() -> str:
    global _model_cache_dir
    if _model_cache_dir is None:
        cache_path = Path.home() / ".cache" / "research-finder" / "hf"
        cache_path.mkdir(parents=True, exist_ok=True)
        _model_cache_dir = str(cache_path)
    return _model_cache_dir

def get_temp_dir() -> str:
    global _temp_dir
    if _temp_dir is None:
        _temp_dir = tempfile.mkdtemp(prefix="research-finder-tmp-")
    return _temp_dir

def cleanup_temp_dir() -> None:
    global _temp_dir
    if _temp_dir and os.path.isdir(_temp_dir):
        shutil.rmtree(_temp_dir, ignore_errors=True)
    _temp_dir = None
