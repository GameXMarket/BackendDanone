from pydantic import BaseModel


class ChatInDB(BaseModel):
    id: int


class ChatMemberInDB(BaseModel):
    id: int
    user_id: int
    chat_id: int


class MessageInDB(BaseModel):
    id: int
    chat_member_id: int
    content: str
    created_at: int


class MessageCreate(BaseModel):
    """
    author_id - user_id, not chat_member
    """
    chat_id: int
    content: str
