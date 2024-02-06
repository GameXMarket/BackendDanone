from pydantic import BaseModel


class Message(BaseModel):
    attachment_id: int | None = None
    receiver_id: int
    reply_to: int | None = None
    content: str


class MessageInDB(Message):
    id: int
    sender_id: int
    created_at: int
