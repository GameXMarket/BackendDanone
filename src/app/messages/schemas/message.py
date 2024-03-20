from pydantic import field_validator, Field, BaseModel


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
    content: str = Field(min_length=1, max_length=4096)

    @field_validator("content", mode="before")
    def process_text(cls, v: str) -> str:
        return v.strip().replace("  ", " ")
