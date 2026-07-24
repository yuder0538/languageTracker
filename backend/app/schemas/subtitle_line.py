from pydantic import BaseModel, ConfigDict


class SubtitleLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_log_id: int
    start_ms: int
    end_ms: int
    text: str


class SubtitleUploadResult(BaseModel):
    media_log_id: int
    line_count: int
