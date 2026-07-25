from pydantic import BaseModel


class RestoreResult(BaseModel):
    restored: bool
    safety_backup_filename: str
