from pydantic import BaseModel
from typing import Optional, Any


class StandardResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    detail: str
