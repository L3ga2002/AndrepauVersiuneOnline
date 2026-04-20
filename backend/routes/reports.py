from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timezone, timedelta

from database import db
from auth import get_current_user, require_admin

router = APIRouter()


@router.get("/stock/dashboard")
async def get_stock_dashboard(user: dict = Depends(get_current_user)):
    total_products = await db.products.count_documents({})

    pipeline_low = [
        {"$match": {"$expr": {"$lte": ["$stoc", "$stoc_minim"]}, "stoc": {"$gt": 0}}},
        {"$count": "count"}
    ]
    low_stock_result = await db.products.aggregate(pipeline_low).to_list(1)
    low_stock = low_stock_result[0]["count"] if low_stock_result else 0

    out_of_stock = await db.products.count_documents({"stoc": {"$lte": 0}})

    pipeline_value = [
        {"$group": {"_id": None, "total": {"$sum": {"$multiply": ["$stoc", "$pret_achizitie"]}}}}
    ]
    value_result = await db.products.aggregate(pipeline_value).to_list(1)
    total_value = value_result[0]["total"] if value_result else 0

    return {
        "total_products": total_products,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "total_value": round(total_value, 2)
    }


@router.get("/stock/alerts")
async def get_stock_alerts(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"$expr": {"$lte": ["$stoc", "$stoc_minim"]}}},
        {"$addFields": {
            "severity": {
                "$cond": [{"$lte": ["$stoc", 0]}, "critical", "warning"]
            },
            "deficit": {"$subtract": ["$stoc_minim", "$stoc"]}
        }},
        {"$sort": {"severity": 1, "deficit": -1}},
        {"$project": {"_id": 0}}
    ]
    alerts = await db.products.aggregate(pipeline).to_list(200)
    return alerts


@router.get("/reports/sales")
async def get_sales_report(
    period: str = "today",
    user: dict = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)

    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    pipeline = [
        {"$match": {"created_at": {"$gte": start.isoformat()}}},
        {"$group": {
            "_id": None,
            "total_sales": {"$sum": "$total"},
            "total_tva": {"$sum": "$tva_total"},
            "count": {"$sum": 1},
            "cash": {"$sum": "$suma_numerar"},
            "card": {"$sum": "$suma_card"}
        }}
    ]

    result = await db.sales.aggregate(pipeline).to_list(1)

    if result:
        return {
            "total_sales": round(result[0]["total_sales"], 2),
            "total_tva": round(result[0]["total_tva"], 2),
            "count": result[0]["count"],
            "cash": round(result[0]["cash"], 2),
            "card": round(result[0]["card"], 2)
        }
    return {"total_sales": 0, "total_tva": 0, "count": 0, "cash": 0, "card": 0}


@router.get("/reports/top-products")
async def get_top_products(limit: int = 10, user: dict = Depends(get_current_user)):
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "nume": {"$first": "$items.nume"},
            "total_cantitate": {"$sum": "$items.cantitate"},
            "total_valoare": {"$sum": {"$multiply": ["$items.cantitate", "$items.pret_unitar"]}}
        }},
        {"$sort": {"total_valoare": -1}},
        {"$limit": limit}
    ]

    results = await db.sales.aggregate(pipeline).to_list(limit)
    return [
        {
            "product_id": r["_id"],
            "nume": r["nume"],
            "total_cantitate": round(r["total_cantitate"], 2),
            "total_valoare": round(r["total_valoare"], 2)
        }
        for r in results
    ]


@router.get("/reports/top-categories")
async def get_top_categories(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "localField": "items.product_id",
            "foreignField": "id",
            "as": "product"
        }},
        {"$unwind": {"path": "$product", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$product.categorie",
            "total_valoare": {"$sum": {"$multiply": ["$items.cantitate", "$items.pret_unitar"]}}
        }},
        {"$sort": {"total_valoare": -1}},
        {"$limit": 10}
    ]

    results = await db.sales.aggregate(pipeline).to_list(10)
    return [
        {
            "categorie": r["_id"] or "Necunoscut",
            "total_valoare": round(r["total_valoare"], 2)
        }
        for r in results
    ]


@router.get("/reports/profit")
async def get_profit_report(period: str = "month", user: dict = Depends(require_admin)):
    now = datetime.now(timezone.utc)

    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # FIX: Optimizat cu aggregation + $lookup (O(1) in loc de N+1 queries separate)
    pipeline = [
        {"$match": {"created_at": {"$gte": start.isoformat()}}},
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "localField": "items.product_id",
            "foreignField": "id",
            "as": "product"
        }},
        {"$unwind": {"path": "$product", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": None,
            "total_vanzari": {"$sum": {"$multiply": ["$items.cantitate", "$items.pret_unitar"]}},
            "total_cost": {"$sum": {"$multiply": [
                "$items.cantitate",
                {"$ifNull": ["$product.pret_achizitie", 0]}
            ]}}
        }}
    ]

    result = await db.sales.aggregate(pipeline).to_list(1)
    if result:
        total_vanzari = result[0]["total_vanzari"]
        total_cost = result[0]["total_cost"]
    else:
        total_vanzari = 0
        total_cost = 0

    profit = total_vanzari - total_cost
    margin = (profit / total_vanzari * 100) if total_vanzari > 0 else 0

    return {
        "total_vanzari": round(total_vanzari, 2),
        "total_cost": round(total_cost, 2),
        "profit": round(profit, 2),
        "margin_percent": round(margin, 2)
    }


@router.get("/reports/daily-sales")
async def get_daily_sales(days: int = 30, user: dict = Depends(get_current_user)):
    start = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {"$match": {"created_at": {"$gte": start.isoformat()}}},
        {"$addFields": {
            "date": {"$substr": ["$created_at", 0, 10]}
        }},
        {"$group": {
            "_id": "$date",
            "total": {"$sum": "$total"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    results = await db.sales.aggregate(pipeline).to_list(days)
    return [{"date": r["_id"], "total": round(r["total"], 2), "count": r["count"]} for r in results]
