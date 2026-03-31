from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
import uuid
import logging

from database import db
from auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


async def expire_old_held_orders():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
    expired_orders = await db.held_orders.find(
        {"status": "active", "created_at": {"$lt": cutoff}},
        {"_id": 0}
    ).to_list(100)

    for order in expired_orders:
        await db.held_orders.update_one(
            {"id": order["id"]},
            {"$set": {"status": "expired", "expired_at": datetime.now(timezone.utc).isoformat()}}
        )

    if expired_orders:
        logger.info(f"Expired {len(expired_orders)} held orders, stock remains deducted")


@router.post("/held-orders")
async def create_held_order(data: dict, user: dict = Depends(get_current_user)):
    items = data.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="Nu sunt produse in cos")

    held_order = {
        "id": str(uuid.uuid4()),
        "items": items,
        "discount": data.get("discount", 0),
        "created_by": user["id"],
        "created_by_name": user.get("full_name", user["username"]),
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    }

    for item in items:
        await db.products.update_one(
            {"id": item["product_id"]},
            {"$inc": {"stoc": -item["cantitate"]}}
        )

    await db.held_orders.insert_one(held_order)
    held_order.pop("_id", None)
    logger.info(f"Held order {held_order['id']} created by {user['username']}, {len(items)} items reserved")
    return held_order


@router.get("/held-orders")
async def get_held_orders(user: dict = Depends(get_current_user)):
    await expire_old_held_orders()

    orders = await db.held_orders.find(
        {"status": "active"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return {"orders": orders, "total": len(orders)}


@router.post("/held-orders/{order_id}/restore")
async def restore_held_order(order_id: str, user: dict = Depends(get_current_user)):
    order = await db.held_orders.find_one({"id": order_id, "status": "active"}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Comanda nu a fost gasita sau a expirat")

    for item in order["items"]:
        await db.products.update_one(
            {"id": item["product_id"]},
            {"$inc": {"stoc": item["cantitate"]}}
        )

    await db.held_orders.update_one(
        {"id": order_id},
        {"$set": {"status": "restored", "restored_at": datetime.now(timezone.utc).isoformat()}}
    )

    logger.info(f"Held order {order_id} restored by {user['username']}")
    return order


@router.post("/held-orders/{order_id}/cancel")
async def cancel_held_order(order_id: str, user: dict = Depends(get_current_user)):
    order = await db.held_orders.find_one({"id": order_id, "status": "active"}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Comanda nu a fost gasita")

    for item in order["items"]:
        await db.products.update_one(
            {"id": item["product_id"]},
            {"$inc": {"stoc": item["cantitate"]}}
        )

    await db.held_orders.update_one(
        {"id": order_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )

    logger.info(f"Held order {order_id} cancelled by {user['username']}")
    return {"message": "Comanda anulata, stoc restaurat"}
