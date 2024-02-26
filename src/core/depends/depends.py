from typing import List, Any, Literal
from types import UnionType
from http import HTTPStatus

from fastapi.security import APIKeyCookie, APIKeyHeader
from fastapi import Query, Depends, HTTPException, status, WebSocketException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.tokens import models as models_t, schemas as schemas_t
from app.tokens import services as TokensService
from app.tokens.schemas.tokens import JwtPayload
from app.users import models as models_u, schemas as schemas_u
from app.users import services as UserService
from core.security import tokens as TokenSecurity
from core.database import get_session

from core import settings as conf


if conf.DEBUG:
    access_token_scheme = APIKeyCookie(
        name="access",
        scheme_name="Cookie access token",
        description="Поле и кнопка ниже просто для автоматической подстановки в запросах, они сделаны для отображения запросов, требующих авторизации",
        auto_error=False,
    )
else:
    access_token_scheme = APIKeyHeader(
        name="Authorization",
        scheme_name="Header Authorization token",
        description="Поле и кнопка ниже просто для автоматической подстановки в запросах, они сделаны для отображения запросов, требующих авторизации",
        auto_error=False,
    )

refresh_token_scheme = APIKeyCookie(
    name="refresh",
    scheme_name="Cookie refresh token",
    description="Поле и кнопка ниже ни на что не влияют, они сделаны для отображения запросов, требующих авторизации",
    auto_error=False,
)


async def get_refresh(
    refresh_t=Depends(refresh_token_scheme),
    db_session: AsyncSession = Depends(get_session),
) -> schemas_t.JwtPayload:
    if not refresh_t:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated"
        )

    token_data: schemas_t.JwtPayload = await TokenSecurity.verify_jwt_token(
        token=refresh_t, secret=conf.REFRESH_SECRET_KEY, db_session=db_session
    )

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    banned_token = await TokensService.ban_token(
        db_session=db_session, token=refresh_t, payload=token_data
    )

    return token_data


async def get_access(
    access_t: str = Depends(access_token_scheme),
    db_session: AsyncSession = Depends(get_session),
) -> schemas_t.JwtPayload:
    if not access_t:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated"
        )

    if isinstance(access_token_scheme, APIKeyHeader):
        if not access_t.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate header credentials",
            )
        access_t = access_t.replace("Bearer ", "")

    token_data = await TokenSecurity.verify_jwt_token(
        token=access_t, secret=conf.ACCESS_SECRET_KEY, db_session=db_session
    )

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return token_data


async def ws_get_access(token: str = Query(None), db_session: AsyncSession = Depends(get_session)):  
    if not token:
        return None
    
    token_data = await TokenSecurity.verify_jwt_token(
        token=token, secret=conf.ACCESS_SECRET_KEY, db_session=db_session
    )
    
    if not token_data:
        return None
        
    return token_data


async def auto_token_ban(
    refresh_t=Depends(refresh_token_scheme),
    access_t=Depends(access_token_scheme),
    db_session: AsyncSession = Depends(get_session),
) -> None:
    refresh_data = await TokenSecurity.verify_jwt_token(
        refresh_t, secret=conf.REFRESH_SECRET_KEY, db_session=db_session
    )
    if refresh_data:
        await TokensService.ban_token(
            db_session=db_session,
            token=refresh_t,
            payload=schemas_t.JwtPayload(**refresh_data),
        )
    access_data = await TokenSecurity.verify_jwt_token(
        access_t, secret=conf.ACCESS_SECRET_KEY, db_session=db_session
    )
    if access_data:
        await TokensService.ban_token(
            db_session=db_session,
            token=access_data,
            payload=schemas_t.JwtPayload(**access_data),
        )


class UserSession:
    request_method: Literal[
        "http",
        "ws"
    ] = "http"
    
    def __init__(self, query_options: Any = None, query_args: Any = None) -> None:
        self.__options = None
        if query_options and query_args:
            self.__options = (query_options, query_args)

    async def __call__(
        self,
        token_data: schemas_t.JwtPayload = Depends(get_access),
    ) -> Any:

        return token_data, self

    def __raise(self, code, comment):
        match self.request_method:
            case "http":
                raise HTTPException(
                    status_code=code,
                    detail=comment,
                )
            case "ws":
                raise WebSocketException(
                    code=status.WS_1000_NORMAL_CLOSURE,
                    reason=comment,
                )
        
    async def get_current_user(self, db_session: AsyncSession, token_data: schemas_t.JwtPayload) -> models_u.User:
        user = await UserService.get_by_email(
            db_session, email=token_data.sub, options=self.__options
        )

        if not user:
            # Можно кидать 404 с юзер нот фоунд, но т.к. токен валиден,
            #  но я думаю лучше использовать одинаковый ответ
            self.__raise(
                code=status.HTTP_401_UNAUTHORIZED,
                comment="Could not validate credentials",
            )

        return user

    async def get_current_active_user(self, db_session: AsyncSession, token_data: schemas_t.JwtPayload) -> models_u.User:
        current_user = await self.get_current_user(db_session, token_data)
        
        is_active = UserService.is_active(current_user)

        if not is_active:
            self.__raise(
                code=status.HTTP_404_NOT_FOUND, comment="User is not active"
            )

        return current_user


class WsUserSession(UserSession):
    request_method = "ws"
    
    async def __call__(
        self,
        token_data: JwtPayload = Depends(ws_get_access),
    ) -> Any:
        if not token_data:
            return None

        return await super().__call__(token_data)


__base_responses: dict = {
    get_refresh: {
        "parrent": None,
        403: {"model": schemas_t.TokenError},
        401: {"model": schemas_u.UserError},
    },
    get_access: {
        "parrent": None,
        403: {"model": schemas_t.TokenError},
        401: {"model": schemas_u.UserError},
    },
    auto_token_ban: {
        "parrent": None,
    },
    UserSession.get_current_user: {
        "parrent": get_access,
        401: {"model": schemas_u.UserError}
    },
    UserSession.get_current_active_user: {
        "parrent": UserSession.get_current_user,
        404: {"model": schemas_u.UserError},
    },
}


def __merge_responses(response_list):
    result_dict = {}

    for response in response_list:
        for code, details in response.items():
            if code in result_dict:
                # Код ответа уже существует в результате, объединяем значения
                for key, value in details.items():
                    if key in result_dict[code]:
                        # Ключ уже существует, объединяем значения
                        if key == "model":
                            merged_models = __merge_models(
                                result_dict[code][key], value
                            )
                            result_dict[code][key] = merged_models[0]
                        elif value not in result_dict[code][key]:
                            # Для других ключей объединяем значения как строки через <br>
                            result_dict[code][
                                key
                            ] = f"{result_dict[code][key]}<br>{value}"
                    else:
                        # Ключ отсутствует, просто добавляем его в результат
                        result_dict[code][key] = value
            else:
                # Код ответа отсутствует, просто добавляем его в результат
                result_dict[code] = details

    return result_dict


def __merge_models(model1, model2):
    if type(model1) == type(model2) == dict:
        # Оба значения являются словарями, рекурсивно объединяем их
        return __merge_responses([model1, model2])

    elif type(model1) == type(model2) == str:
        # Одно из значений строковое, объединяем через <br>
        return f"{model1}<br>{model2}"
    else:
        return model1 | model2, "merged"


def __update_is_changed(response_dict: dict):
    varn_str = "<br><mark>Модель была изменена, проверь SCHEMA!</mark>"

    for code, details in response_dict.items():
        model = details.get("model")
        description = details.get("description", HTTPStatus(code).phrase)
        # Описание по умолчанию автоматически заполняется в fastapi, однако
        #  после изменения описания вручную оно перезаписыватеся

        if isinstance(model, UnionType) and varn_str not in description:
            details["description"] = description + varn_str

    return response_dict


def build_response(
    func: object, *, final_responses: list = [], base_responses: dict = __base_responses
):
    response_dict: dict = base_responses.get(func, {})

    while response_dict:
        parent_func = response_dict.get("parrent")
        
        try:
            del response_dict["parrent"]
        except KeyError:
            pass

        final_responses.append(response_dict)

        if parent_func:
            response_dict = base_responses.get(parent_func, {})
        else:
            break
        
    responses_dict = __merge_responses(final_responses)
    return __update_is_changed(responses_dict)
