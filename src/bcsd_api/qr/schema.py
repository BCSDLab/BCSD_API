from pydantic import BaseModel, Field


class QrParams(BaseModel):
    text: str = Field(..., max_length=2000)
    format: str = Field("png", pattern="^(png|svg)$")
    size: int = Field(300, ge=100, le=1000)
