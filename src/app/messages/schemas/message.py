from pydantic import field_validator, Field, BaseModel
from fastapi import UploadFile


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


class MessageCreateTemp(BaseModel):
    # Временная схема (вопрос насколько ахах)
    message_image: UploadFile | None = Field(default=None, examples=[None])
    content: str = Field(min_length=0, max_length=4096)

    @field_validator("content", mode="before")
    def process_text(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError
        
        return v.strip().replace("  ", " ")
    
    def get_message_create(self, chat_id: int):
        return MessageCreate(
            content=self.content,
            chat_id=chat_id,
        )


class MessageCreate(BaseModel):
    need_wait: int = 0
    chat_id: int
    content: str = Field(min_length=0, max_length=4096)

    @field_validator("content", mode="before")
    def process_text(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError
        
        return v.strip().replace("  ", " ")


class SystemMessageCreate(BaseModel):
    chat_id: int
    content: str | dict
    
    def get_message_broadcast(self):
        return SystemMessageBroadcast(
            chat_id=self.chat_id,
            content=self.content
        )


class SystemMessageBroadcast(SystemMessageCreate):
    user_id: int = -1


class MessageBroadcast(BaseModel):
    id: int
    chat_id: int
    user_id: int
    content: str
    files: list[str] | None = None
    created_at: int
