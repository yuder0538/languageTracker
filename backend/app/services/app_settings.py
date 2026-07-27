from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.app_settings import AppSettings

SETTINGS_ROW_ID = 1


def get_app_settings(db: Session) -> AppSettings:
    """Get-or-create the single settings row. A safety net for environments
    where the alembic seed migration hasn't run yet — the migration is still
    the primary way this row gets created."""
    row = db.get(AppSettings, SETTINGS_ROW_ID)
    if row is None:
        row = AppSettings(
            id=SETTINGS_ROW_ID,
            daily_new_card_limit=get_settings().daily_new_card_limit,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row
