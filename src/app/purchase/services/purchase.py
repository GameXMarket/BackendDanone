import json
from typing import Any, Literal
from inspect import cleandoc


from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import insert, select, delete, exists, desc, asc
from app.offers.services import get_raw_offer_by_id, update_offer
from .. import schemas as schemas_p, models as models_p
from app.offers import models as models_f
from app.users import models as models_u
from app.attachment.services import offer_attachment_manager, user_attachment_manager
from app.messages.routers.message import (
    base_connection_manager as message_connection_manager,
)
from app.messages.services import message_manager
from app.messages.schemas import SystemMessageCreate
from app.users.routers.users_notifications import user_notification_manager


#  мб нужно начать писать более сложные обработчики ошибок,
#   а не просто возвращать None в любое удобном случае
class PurchaseManager:
    def __init__(self) -> None:
        pass

    async def create_purchase(
        self,
        db_session: AsyncSession,
        buyer_id: int,
        new_purchase_data: schemas_p.PurchaseCreate,
    ):
        offer = await get_raw_offer_by_id(db_session, new_purchase_data.offer_id)

        if not offer:
            raise HTTPException(404, "Offer doesn't exist")

        if offer.user_id == buyer_id:
            raise HTTPException(403, "BuyerID cannot be equal to the SellerID")

        check_other_purchases_stmt = select(
            exists(models_p.Purchase)
            .where(models_p.Purchase.offer_id == new_purchase_data.offer_id)
            .where(models_p.Purchase.buyer_id == buyer_id)
            .where(models_p.Purchase.status.in_(("process", "review", "dispute")))
        )
        active_purchase_exists = (
            await db_session.execute(check_other_purchases_stmt)
        ).scalar()
        if active_purchase_exists:
            raise HTTPException(
                403, "Only one purchase can be created at the same time"
            )

        offer_real_count = await offer.get_real_count(db_session)

        if new_purchase_data.count > offer_real_count:
            raise HTTPException(403, "There is not enough quantity")

        if not offer.is_autogive_enabled:
            await update_offer(
                db_session,
                offer,
                {"count": offer.count - new_purchase_data.count},
                need_commit=False,
            )

        # todo добавить логику времени на сделку
        purchase = models_p.Purchase(
            buyer_id=buyer_id,
            offer_id=offer.id,
            name=offer.name,
            description=offer.description,
            price=offer.price,
            count=new_purchase_data.count,
        )

        db_session.add(purchase)
        await db_session.flush()

        if offer.is_autogive_enabled:
            subquery = (
                select(models_f.Delivery.id)
                .where(models_f.Delivery.offer_id == offer.id)
                .limit(new_purchase_data.count)
            )
            delete_delivery_subquery = (
                delete(models_f.Delivery)
                .where(models_f.Delivery.id.in_(subquery))
                .returning(models_f.Delivery.value)
            )
            q = await db_session.execute(delete_delivery_subquery)
            deleted_deliveries: list[str] = q.scalars().all()

            for delivery_value in deleted_deliveries:
                create_parcel_stmt = insert(models_p.Parcel).values(
                    purchase_id=purchase.id, value=delivery_value
                )
                await db_session.execute(create_parcel_stmt)
            
            await self.__update_purchase(
                db_session, purchase, {"status": "review"}
            )

        buyer_notifications = user_notification_manager.sse_managers.get(
            purchase.buyer_id
        )
        seller_notifications = user_notification_manager.sse_managers.get(offer.user_id)
        dialog_data = await message_manager.get_dialog_id_by_user_id(
            db_session, buyer_id, offer.user_id
        )
        if not dialog_data:
            dialog_data = await message_manager.create_dialog(
                db_session, buyer_id, offer.user_id
            )
            if not dialog_data:
                raise HTTPException(404, "User not found, How did you get here?")

        event_data = json.dumps(dialog_data).replace("\n", " ")
        if buyer_notifications:
            await buyer_notifications.create_event(
                event="new_chat",
                data=event_data,
                comment="new chat with you created",
            )

        if seller_notifications:
            await seller_notifications.create_event(
                event="new_chat",
                data=event_data,
                comment="new chat with you created",
            )

        purchase_event = (
            f"{purchase.buyer_id} купил у {offer.user_id} "
            + f"оффер '{offer.name}' в количестве {purchase.count} на сумму {purchase.price * purchase.count}"
        )
        purchase_dict_data = purchase.to_dict("parcels")
        system_message = SystemMessageCreate(
            chat_id=dialog_data["chat_id"],
            content=json.dumps(purchase_dict_data),
        )
        await message_connection_manager.send_and_create_system_message(
            db_session, system_message, [purchase.buyer_id, offer.user_id]
        )

        if buyer_notifications:
            await buyer_notifications.create_event(
                event="new_purchase", data=purchase_dict_data, comment=purchase_event
            )

        if seller_notifications:
            await seller_notifications.create_event(
                event="new_purchase", data=purchase_dict_data, comment=purchase_event
            )
        
        await db_session.commit()
        await db_session.refresh(purchase)

        return purchase

    async def create_confirmation_request(
        self,
        db_session: AsyncSession,
        purchase_id: int,
        seller_id: int,
    ):
        """
        Продавец после выполнения заказа меняет статус на проверку,
         после этого пользователь должен подтвердить выполнение
        Метод для пользователя
        """
        purchase = await self.get_sale(db_session, purchase_id, seller_id)
        if not purchase:
            raise HTTPException(404, "Sale not found")

        if purchase.status != "process":
            raise HTTPException(403, "Sale status not in process")

        purchase = await self.__update_purchase(
            db_session, purchase, {"status": "review"}
        )

        buyer_notifications = user_notification_manager.sse_managers.get(
            purchase.buyer_id
        )
        seller_notifications = user_notification_manager.sse_managers.get(seller_id)

        # Предполагается, что уже есть чатик (создаётся при создании покупки)
        dialog_data = await message_manager.get_dialog_id_by_user_id(
            db_session, seller_id, purchase.buyer_id
        )
        status_change_event = f"Продавец ({seller_id}) выполнил заказ ({purchase.id}) пользователя ({purchase.buyer_id}) и просит подтверждения.."

        system_message = SystemMessageCreate(
            chat_id=dialog_data["chat_id"],
            content=status_change_event,
        )
        await message_connection_manager.send_and_create_system_message(
            db_session, system_message, [seller_id, purchase.buyer_id]
        )

        if buyer_notifications:
            await buyer_notifications.create_event(
                event="new_purchase_status",
                data=purchase.to_dict(),
                comment=status_change_event,
            )

        if seller_notifications:
            await seller_notifications.create_event(
                event="new_purchase_status",
                data=purchase.to_dict(),
                comment=status_change_event,
            )

        return purchase

    async def change_confirmation_request_status(
        self,
        db_session: AsyncSession,
        purchase_id: int,
        buyer_id: int,
        purchase_completed: bool,
    ):
        """
        Меняется статус после подтверждения покупателем,
         можно как одобрить так и запретить
        Метод для пользователя
        """

        purchase = await self.get_purchase(
            db_session, purchase_id, buyer_id, (selectinload, models_p.Purchase.offer)
        )

        if not purchase:
            raise HTTPException(404, "Purchase not found")

        if purchase.status != "review":
            raise HTTPException(403, "Purchase status not in review")

        seller_id = purchase.offer.user_id
        status = "completed" if purchase_completed else "dispute"
        purchase = await self.__update_purchase(
            db_session, purchase, {"status": status}
        )

        buyer_notifications = user_notification_manager.sse_managers.get(
            purchase.buyer_id
        )
        seller_notifications = user_notification_manager.sse_managers.get(seller_id)

        # Предполагается, что уже есть чатик (создаётся при создании покупки)
        dialog_data = await message_manager.get_dialog_id_by_user_id(
            db_session, seller_id, purchase.buyer_id
        )
        status_change_event = f"Покупатель ({purchase.buyer_id}) подтвердил выполнение заказа ({purchase.id}) продавца ({seller_id}) ..."

        system_message = SystemMessageCreate(
            chat_id=dialog_data["chat_id"],
            content=status_change_event,
        )
        await message_connection_manager.send_and_create_system_message(
            db_session, system_message, [seller_id, purchase.buyer_id]
        )

        if buyer_notifications:
            await buyer_notifications.create_event(
                event="new_purchase_status",
                data=purchase.to_dict(),
                comment=status_change_event,
            )

        if seller_notifications:
            await seller_notifications.create_event(
                event="new_purchase_status",
                data=purchase.to_dict(),
                comment=status_change_event,
            )

        return purchase

    async def change_purchase_status(
        self,
        db_session: AsyncSession,
        purchase: models_p.Purchase,
        status: Literal[
            "process",
            "review",
            "completed",
            "dispute",
            "refund",
        ],
    ):
        str_ = cleandoc(
            """
        Метод для смены статусов, много накладных расходов на упрощение 
        Легче дублировать часть кода (мне просто лень прописывать доп условия)
        """
        )

        raise NotImplementedError(str_)

    async def get_purchase(
        self,
        db_session: AsyncSession,
        purchase_id: int,
        buyer_id: int,
        options: Any = None,
    ):
        stmt = (
            select(models_p.Purchase)
            .where(models_p.Purchase.id == purchase_id)
            .where(models_p.Purchase.buyer_id == buyer_id)
        )

        if options:
            stmt = stmt.options(options[0](options[1]))

        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sale(
        self,
        db_session: AsyncSession,
        purchase_id: int,
        seller_id: int,
    ):
        stmt = (
            select(models_p.Purchase)
            .join(models_f.Offer, models_f.Offer.id == models_p.Purchase.offer_id)
            .where(models_p.Purchase.id == purchase_id)
            .where(models_f.Offer.user_id == seller_id)
        )

        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def __update_purchase(
        self,
        db_session: AsyncSession,
        db_obj: models_p.Purchase,
        obj_in: schemas_p.PurchaseInDB | dict,
    ):
        obj_data = jsonable_encoder(db_obj)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db_session.add(db_obj)
        await db_session.commit()
        await db_session.refresh(db_obj)

        return db_obj

    async def __delete_purchase(
        self,
        db_session: AsyncSession,
        user_id: int,
    ):

        raise NotImplementedError("Просто не юзается (заглушка)")

    async def get_all_purchases(
        self,
        db_session: AsyncSession,
        buyer_id: int,
        offset: int,
        limit: int,
        by_last_udpate: bool = False,
        search_query: str = None,
        is_reviewed: bool = None,
        statuses: list[
            Literal["process", "review", "completed", "dispute", "refund"]
        ] = ["process", "review", "completed", "dispute", "refund"],
    ):
        _result = []

        stmt = (
            select(
                models_p.Purchase.name,
                models_p.Purchase.count,
                models_p.Purchase.created_at,
                models_p.Purchase.price,
                models_p.Purchase.status,
                models_p.Purchase.offer_id,
                models_u.User.id,  # Seller user_id
                models_u.User.username,
                models_p.Purchase.id,
            )
            .join(models_f.Offer, models_f.Offer.id == models_p.Purchase.offer_id)
            .join(models_u.User, models_u.User.id == models_f.Offer.user_id)
            .where(models_p.Purchase.buyer_id == buyer_id)
            .where(models_p.Purchase.status.in_(statuses))
            .order_by(
                desc(models_p.Purchase.updated_at)
                if by_last_udpate
                else desc(models_p.Purchase.created_at)
            )
            .offset(offset)
            .limit(limit)
        )

        if search_query:
            stmt = stmt.where(models_p.Purchase.name.ilike(f"%{search_query}%"))
        
        if is_reviewed is not None:
            stmt = stmt.where(models_p.Purchase.is_reviewed == is_reviewed)

        rows = await db_session.execute(stmt)

        for row in rows:
            seller_files = await user_attachment_manager.get_only_files(
                db_session, row[6]
            )
            offer_files = await offer_attachment_manager.get_only_files(
                db_session, row[5]
            )
            purchase_dict = {
                "id": row[8],
                "seller_id": row[6],
                "name": row[0],
                "count": row[1],
                "created_at": row[2],
                "price": row[3],
                "status": row[4],
                "seller_username": row[7],
                "seller_files": seller_files,
                "purchase_files": offer_files,
            }

            _result.append(purchase_dict)

        return _result

    async def get_all_sells(
        self,
        db_session: AsyncSession,
        offset: int,
        limit: int,
        seller_id: int,
        by_last_udpate: bool = False,
        search_query: str = None,
        is_reviewed: bool = None,
        statuses: list[
            Literal["process", "review", "completed", "dispute", "refund"]
        ] = ["process", "review", "completed", "dispute", "refund"],
    ):
        stmt = (
            select(models_p.Purchase)
            .join(models_f.Offer, models_f.Offer.id == models_p.Purchase.offer_id)
            .join(models_u.User, models_u.User.id == models_f.Offer.user_id)
            .where(models_u.User.id == seller_id)
            .where(models_p.Purchase.status.in_(statuses))
            .order_by(
                desc(models_p.Purchase.updated_at)
                if by_last_udpate
                else desc(models_p.Purchase.created_at)
            )
            .offset(offset)
            .limit(limit)
        )

        if search_query:
            stmt = stmt.where(models_p.Purchase.name.ilike(f"%{search_query}%"))
        
        if is_reviewed is not None:
            stmt = stmt.where(models_p.Purchase.is_reviewed == is_reviewed)
        
        query = await db_session.execute(stmt)
        return query.scalars().all()

    async def get_all_sells_by_offer(
        self,
        offset: int,
        limit: int,
        offer_id: int,
        seller_id: int,
        db_session: AsyncSession,
    ):
        stmt = (
            select(models_p.Purchase)
            .join(models_f.Offer, models_f.Offer.id == models_p.Purchase.offer_id)
            .join(models_u.User, models_u.User.id == models_f.Offer.user_id)
            .where(models_f.Offer.id == offer_id)
            .where(models_u.User.id == seller_id)
            .offset(offset)
            .limit(limit)
        )
        query = await db_session.execute(stmt)
        return query.scalars().all()
    
    async def create_review(
        self,
        buyer_id: int,
        review_data: schemas_p.ReviewCreate,
        db_session: AsyncSession,
    ):
        purchase = await self.get_purchase(db_session, review_data.purchase_id, buyer_id)
        if not purchase:
            raise HTTPException(404, "Purchase not found")
        
        # Тоже не знаю нужны ли ревьюшки в refund статусе
        if purchase.status not in ("completed", "refund"):
            raise HTTPException(403, "Purchase status must be equal to completed or refund")
        
        create_review_stmt = (
            insert(models_p.Review)
            .values(
                purchase_id=review_data.purchase_id,
                offer_id=purchase.offer_id,
                rating=review_data.rating,
                value=review_data.value,
            )
            .returning(models_p.Review)
        )
        q = await db_session.execute(create_review_stmt)

        return q.scalar_one_or_none()


purchase_manager = PurchaseManager()
