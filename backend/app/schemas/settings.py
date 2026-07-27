from pydantic import BaseModel, Field


class AppSettingsRead(BaseModel):
    daily_new_card_limit: int


class AppSettingsUpdate(BaseModel):
    daily_new_card_limit: int = Field(ge=1, le=500)
