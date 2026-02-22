from app.schemas.common import BaseSchema


class SummaryRequest(BaseSchema):

    title: str
    content: str


class SummaryResponse(BaseSchema):

    title: str
    summary: str
