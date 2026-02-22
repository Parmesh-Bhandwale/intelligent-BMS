from pydantic import BaseModel, ConfigDict
from datetime import datetime


class BaseSchema(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,   # replaces orm_mode
        populate_by_name=True
    )


class TimestampMixin(BaseModel):

    created_at: datetime | None = None
    updated_at: datetime | None = None
