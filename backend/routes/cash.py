from fastapi import APIRouter, Depends
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging

from database import db
from auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/cash-operations")
async def create_cash_operation(data: dict, user: dict = Depends(get_current_user)):
    operation = {
        "id": str(uuid.uuid4()),
        "type": data.get("type"),
        "amount": data.get("amount", 0),
        "description": data.get("description", ""),
        "operator_id": data.get("operator_id"),
        "operator_name": data.get("operator_name"),
        "timestamp": datetime.now(timezone.utc),
        "date_str": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }

    await db.cash_operations.insert_one(operation)
    operation.pop("_id", None)
    logger.info(f"[CASH] {operation['type']} | Amount: {operation['amount']} RON | By: {operation['operator_name']} | Desc: {operation['description']}")
    return operation


@router.get("/cash-operations/history")
async def get_cash_operations_history(
    limit: int = 50,
    date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if date:
        query["date_str"] = date

    operations = await db.cash_operations.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return {"operations": operations}


@router.get("/cash-operations/daily-stats")
async def get_daily_cash_stats(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    sales_pipeline = [
        {"$match": {"created_at": {"$gte": today_start}}},
        {"$group": {
            "_id": "$metoda_plata",
            "total": {"$sum": "$total"},
            "count": {"$sum": 1}
        }}
    ]
    sales_by_method = await db.sales.aggregate(sales_pipeline).to_list(10)

    total_cash = 0
    total_card = 0
    total_voucher = 0
    receipts_count = 0

    for s in sales_by_method:
        receipts_count += s.get("count", 0)
        if s["_id"] in ["numerar", "cash"]:
            total_cash = s.get("total", 0)
        elif s["_id"] in ["card"]:
            total_card = s.get("total", 0)
        elif s["_id"] in ["tichete", "voucher"]:
            total_voucher = s.get("total", 0)

    cash_ops_pipeline = [
        {"$match": {"date_str": today}},
        {"$group": {
            "_id": "$type",
            "total": {"$sum": "$amount"}
        }}
    ]
    cash_ops = await db.cash_operations.aggregate(cash_ops_pipeline).to_list(10)

    cash_in = 0
    cash_out = 0
    for op in cash_ops:
        if op["_id"] == "CASH_IN":
            cash_in = op.get("total", 0)
        elif op["_id"] == "CASH_OUT":
            cash_out = op.get("total", 0)

    return {
        "totalCash": round(total_cash, 2),
        "totalCard": round(total_card, 2),
        "totalVoucher": round(total_voucher, 2),
        "cashIn": round(cash_in, 2),
        "cashOut": round(cash_out, 2),
        "receiptsCount": receipts_count
    }


@router.get("/daily/opening-summary")
async def get_opening_summary(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    cash_ops = await db.cash_operations.aggregate([
        {"$match": {"date_str": today}},
        {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}}
    ]).to_list(10)
    cash_in = sum(op["total"] for op in cash_ops if op["_id"] == "CASH_IN")
    cash_out = sum(op["total"] for op in cash_ops if op["_id"] == "CASH_OUT")

    cash_sales = await db.sales.aggregate([
        {"$match": {"created_at": {"$gte": today_start.isoformat()}, "metoda_plata": {"$in": ["numerar", "cash"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
    ]).to_list(1)
    cash_from_sales = cash_sales[0]["total"] if cash_sales else 0

    card_sales = await db.sales.aggregate([
        {"$match": {"created_at": {"$gte": today_start.isoformat()}, "metoda_plata": "card", "fiscal_status": {"$ne": "cancelled"}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
    ]).to_list(1)
    card_from_sales = card_sales[0]["total"] if card_sales else 0
    card_sales_count = card_sales[0]["count"] if card_sales else 0

    all_sales = await db.sales.aggregate([
        {"$match": {"created_at": {"$gte": today_start.isoformat()}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "count": {"$sum": 1}}}
    ]).to_list(1)
    total_sales = all_sales[0]["total"] if all_sales else 0
    total_sales_count = all_sales[0]["count"] if all_sales else 0

    sold_casa = cash_in - cash_out + cash_from_sales

    last_poll = await db.fiscal_bridge_status.find_one({"key": "last_poll"}, {"_id": 0})
    bridge_connected = False
    if last_poll:
        last_time = datetime.fromisoformat(last_poll["timestamp"])
        bridge_connected = (datetime.now(timezone.utc) - last_time).total_seconds() < 30

    # Expire old held orders
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

    held_count = await db.held_orders.count_documents({"status": "active"})

    alert_count = await db.products.count_documents({"$expr": {"$lte": ["$stoc", "$stoc_minim"]}})
    out_of_stock = await db.products.count_documents({"stoc": {"$lte": 0}})

    return {
        "data": today,
        "sold_casa": round(sold_casa, 2),
        "cash_in": round(cash_in, 2),
        "cash_out": round(cash_out, 2),
        "vanzari_numerar": round(cash_from_sales, 2),
        "total_vanzari": round(total_sales, 2),
        "numar_vanzari": total_sales_count,
        "vanzari_card": round(card_from_sales, 2),
        "numar_vanzari_card": card_sales_count,
        "bridge_connected": bridge_connected,
        "comenzi_hold": held_count,
        "alerte_stoc": alert_count,
        "fara_stoc": out_of_stock,
        "ora": datetime.now(timezone.utc).strftime("%H:%M")
    }


@router.get("/settings/tva")
async def get_tva_settings():
    return {
        "cote_tva": [
            {"cod": "A", "procent": 21.0, "descriere": "Standard (21%)"},
            {"cod": "B", "procent": 11.0, "descriere": "Redusa (11%)"},
            {"cod": "C", "procent": 0.0, "descriere": "Scutit/Export (0%)"},
            {"cod": "D", "procent": 9.0, "descriere": "Tranzitorie locuinte (9%)"},
        ],
        "nota_legala": "Conform Legea 141/2025, valabil de la 1 august 2025"
    }
