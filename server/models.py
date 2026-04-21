from pydantic import BaseModel
from typing import Optional


class MovePayload(BaseModel):
    from_square: int
    to_square: int
    flag: int
    promotion: int = 0


class ClientMessage(BaseModel):
    type: str
    nickname: Optional[str] = None
    move: Optional[MovePayload] = None
    message: Optional[str] = None


class ServerMessage(BaseModel):
    type: str
    payload: Optional[dict] = None
    message: Optional[str] = None
