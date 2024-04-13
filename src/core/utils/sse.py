from typing import Optional
import asyncio


class SseQueue:
    def __init__(self) -> None:
        self._queue = asyncio.Queue()

    def __get_event_text(self, **sse_event) -> str:
        string_event = ""
        for key, value in sse_event.items():
            if not value:
                continue

            if key == "comment":
                string_event += f": {value}"
                continue

            string_event += f"{key}: {value}\n"

        if string_event.count(":") == 0:
            raise ValueError

        return string_event + "\n\n"

    async def create_event(
        self,
        event: Optional[str] = None,
        data: Optional[str] = None,
        id: Optional[int] = None,
        retry: Optional[int] = None,
        comment: Optional[str] = None,
    ) -> None:
        """
        event - Строка, идентифицирующая тип описанного события.
            Если event указан, то событие будет отправлено в браузер
            обработчику указанного имени события. Исходный код сайта
            должен использовать addEventListener() для обработки именованных
            событий. Обработчик onmessage вызывается, если для сообщения
            не указано имя события.

        data - Поле данных для сообщения. Когда EventSource получает несколько
            последовательных строк, начинающихся с data:, он объединяет их, вставляя
            символ новой строки между каждой из них. Последние переводы строки удаляются.

        id - Идентификатор события для установки значения последнего ID события для объекта EventSource.

        retry - Время переподключения, используемое при попытке отправить событие.
            Это должно быть целое число, указывающее время переподключения в миллисекундах.
            Если указано нецелое значение, поле игнорируется.
        """
        sse_event_text = self.__get_event_text(
            **{
                "event": event,
                "data": data,
                "id": id,
                "retry": retry,
                "comment": comment,
            }
        )
        await self._queue.put(sse_event_text)

    async def get_event(self) -> str:
        event = await self._queue.get()
        return event
    
    async def get_events(self):
        while True:
            yield await self.get_event()
