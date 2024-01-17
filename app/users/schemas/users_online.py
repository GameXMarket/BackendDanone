from pydantic import BaseModel


class OnlineUser(BaseModel):
    id: int


class OnlineUsers(BaseModel):
    """
    [список клиентов в сети]
    """
    
    users: list[OnlineUser]


class BroadcastClient(BaseModel):
    unique_id: int


class BroadcastClients(BaseModel):
    """
    {
        клиент: [ 
            те, кто ждёт обновы по его онлайну (уник_id соккета),
            если таковых нет, удаляем клиента при изменении клиента 
            кидаем всем бродкастерам
        ]
    }
    {
        BroadcastClient: [BroadcastClient]
    }
    """

    providers: dict[BroadcastClient, list[BroadcastClient]]
