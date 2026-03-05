from fastapi import APIRouter

from app.api.routes import documents, references

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(references.router, prefix="/references", tags=["references"])
