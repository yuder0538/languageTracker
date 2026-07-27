from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.app_settings import AppSettings
from app.schemas.settings import AppSettingsRead, AppSettingsUpdate
from app.services.app_settings import get_app_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsRead)
def read_settings(db: Session = Depends(get_db)) -> AppSettings:
    return get_app_settings(db)


@router.patch("", response_model=AppSettingsRead)
def update_settings(
    payload: AppSettingsUpdate, db: Session = Depends(get_db)
) -> AppSettings:
    settings_row = get_app_settings(db)
    settings_row.daily_new_card_limit = payload.daily_new_card_limit
    db.commit()
    db.refresh(settings_row)
    return settings_row
