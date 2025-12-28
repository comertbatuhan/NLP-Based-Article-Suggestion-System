#backend/app/api/routes.py
from fastapi import APIRouter
from .works import router as works_router
from .test_rerank import router as test_rerank_router

router = APIRouter()
router.include_router(works_router, prefix="/works", tags=["works"])
router.include_router(test_rerank_router)