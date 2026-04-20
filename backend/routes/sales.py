from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import os
import logging

from database import db
from auth import get_current_user, require_admin
from models import SaleCreate, SaleResponse

router = APIRouter()
logger = logging.getLogger(__name__)

IS_LOCAL = os.environ.get("LOCAL_MODE", "").lower() == "true"


async def generate_bon_number():
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = await db.sales.count_documents({"numar_bon": {"$regex": f"^BON-{today}"}})
    return f"BON-{today}-{str(count + 1).zfill(4)}"


@router.post("/sales", response_model=SaleResponse)
async def create_sale(sale: SaleCreate, user: dict = Depends(get_current_user)):
    if sale.transaction_id:
        existing = await db.sales.find_one({"transaction_id": sale.transaction_id}, {"_id": 0})
        if existing:
            logger.warning(f"[SALE] Duplicate blocked: txn={sale.transaction_id}, user={user['username']}")
            return SaleResponse(**existing)

    numar_bon = await generate_bon_number()

    casier = await db.users.find_one({"id": sale.casier_id}, {"_id": 0})
    casier_nume = casier["full_name"] if casier else "Necunoscut"

    sale_doc = {
        "id": str(uuid.uuid4()),
        "numar_bon": numar_bon,
        **sale.model_dump(),
        "transaction_id": sale.transaction_id or str(uuid.uuid4()),
        "casier_nume": casier_nume,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "synced": not IS_LOCAL
    }

    stock_changes = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in sale.items:
        result = await db.products.update_one(
            {"id": item.product_id},
            {
                "$inc": {"stoc": -item.cantitate},
                "$set": {"updated_at": now_iso}
            }
        )
        stock_changes.append({
            "product_id": item.product_id,
            "nume": item.nume,
            "cantitate": -item.cantitate,
            "matched": result.matched_count
        })

    await db.sales.insert_one(sale_doc)

    logger.info(
        f"[SALE] #{numar_bon} | Total: {sale.total} RON | "
        f"Plata: {sale.metoda_plata} | Fiscal: {sale.fiscal_status} | "
        f"Items: {len(sale.items)} | Casier: {casier_nume} | "
        f"TXN: {sale_doc['transaction_id']}"
    )
    for sc in stock_changes:
        if sc["matched"] == 0:
            logger.error(f"[STOCK] Product not found for deduction: {sc['product_id']} ({sc['nume']})")

    return SaleResponse(**{k: v for k, v in sale_doc.items() if k != "_id"})


@router.get("/sales", response_model=List[SaleResponse])
async def get_sales(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}

    sales = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    return [SaleResponse(**s) for s in sales]


@router.get("/sales/{sale_id}", response_model=SaleResponse)
async def get_sale(sale_id: str, user: dict = Depends(get_current_user)):
    sale = await db.sales.find_one({"id": sale_id}, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Vânzare negăsită")
    return SaleResponse(**sale)


@router.post("/sales/{sale_id}/cancel")
async def cancel_sale(sale_id: str, user: dict = Depends(get_current_user)):
    sale = await db.sales.find_one({"id": sale_id}, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Vânzare negăsită")

    if sale.get("fiscal_status") == "cancelled":
        return {"message": "Vânzarea este deja anulată"}

    for item in sale.get("items", []):
        await db.products.update_one(
            {"id": item["product_id"]},
            {"$inc": {"stoc": item["cantitate"]}}
        )

    await db.sales.update_one(
        {"id": sale_id},
        {"$set": {"fiscal_status": "cancelled"}}
    )

    logger.info(f"Sale {sale_id} cancelled, stock restored")
    return {"message": "Vânzare anulată, stoc restaurat"}


@router.get("/settings/fiscal")
async def get_fiscal_settings(user: dict = Depends(get_current_user)):
    settings = await db.settings.find_one({"key": "fiscal"}, {"_id": 0})
    if not settings:
        return {
            "fiscal_mode": False,
            "bridge_url": "http://localhost:5555",
            "auto_print": True
        }
    return settings.get("value", {})


@router.post("/settings/fiscal")
async def update_fiscal_settings(data: dict, user: dict = Depends(require_admin)):
    await db.settings.update_one(
        {"key": "fiscal"},
        {"$set": {"key": "fiscal", "value": data, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"message": "Setări fiscale salvate", "settings": data}
