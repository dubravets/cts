from fastapi import APIRouter

from app.api.routes import (
    documents,
    export,
    generation,
    history,
    knowledge,
    parsing,
    quality,
    references,
    workflow,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(references.router, prefix="/references", tags=["references"])
api_router.include_router(parsing.router, prefix="/parsing", tags=["parsing"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(generation.router, prefix="/generation", tags=["generation"])
api_router.include_router(quality.router, prefix="/quality", tags=["quality"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
