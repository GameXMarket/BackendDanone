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
    chat_id: int
    content: str = Field(min_length=1, max_length=4096)
    need_wait: int = 0

    @field_validator("content", mode="before")
    def process_text(cls, v: str) -> str:
        return v.strip().replace("  ", " ")


class MessageBroadcast(BaseModel):
    id: int
    chat_id: int
    user_id: int
    content: str
    files: list[str] | None = None
    created_at: int
