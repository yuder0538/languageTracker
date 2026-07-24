from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.media_log import router as media_log_router
from app.api.reviews import router as reviews_router
from app.api.vocabulary import router as vocabulary_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(media_log_router)
api_router.include_router(vocabulary_router)
api_router.include_router(reviews_router)


@api_router.get("/ping")
def ping(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
