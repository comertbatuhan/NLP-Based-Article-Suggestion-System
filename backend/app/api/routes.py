#backend/app/api/routes.py
from fastapi import APIRouter
from .works import router as works_router

router = APIRouter()
router.include_router(works_router, prefix="/works", tags=["works"])
