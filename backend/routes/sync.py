from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import os
import logging

from database import db
from auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

IS_LOCAL = os.environ.get("LOCAL_MODE", "").lower() == "true"
SYNC_SECRET = os.environ.get("SYNC_SECRET", "andrepau-sync-2026")


@router.get("/sync/pending-count")
async def get_pending_count(user: dict = Depends(get_current_user)):
    """Returneaza numarul de vanzari nesincronizate (pentru modul local)"""
    count = await db.sales.count_documents({"synced": False})
    return {"pending": count}


@router.get("/sync/pending-sales")
async def get_pending_sales(user: dict = Depends(get_current_user)):
    """Returneaza vanzarile nesincronizate (pentru modul local)"""
    sales = await db.sales.find(
        {"synced": False},
        {"_id": 0}
    ).to_list(None)
    return {"sales": sales, "count": len(sales)}


@router.post("/sync/receive")
async def receive_synced_sales(data: dict):
    """Primeste vanzari de la instanta locala (endpoint VPS)"""
    secret = data.get("sync_secret", "")
    if secret != SYNC_SECRET:
        raise HTTPException(status_code=401, detail="Cheie sincronizare invalida")

    sales = data.get("sales", [])
    if not sales:
        return {"received": 0, "duplicates": 0}

    received = 0
    duplicates = 0

    for sale in sales:
        # Verifica duplicat dupa transaction_id
        txn_id = sale.get("transaction_id")
        if txn_id:
            existing = await db.sales.find_one({"transaction_id": txn_id})
            if existing:
                duplicates += 1
                continue

        # Curata si stocheaza vanzarea cu valori default
        sale.pop("_id", None)
        sale.setdefault("subtotal", sale.get("total", 0))
        sale.setdefault("tva_total", 0)
        sale.setdefault("discount_percent", 0)
        sale.setdefault("suma_numerar", sale.get("total", 0) if sale.get("metoda_plata") == "numerar" else 0)
        sale.setdefault("suma_card", sale.get("total", 0) if sale.get("metoda_plata") == "card" else 0)
        sale.setdefault("items", [])
        sale.setdefault("metoda_plata", "numerar")
        sale["synced"] = True
        sale["synced_from"] = "local"
        sale["synced_at"] = datetime.now(timezone.utc).isoformat()

        await db.sales.insert_one(sale)

        # Actualizeaza stocul
        for item in sale.get("items", []):
            await db.products.update_one(
                {"id": item.get("product_id")},
                {"$inc": {"stoc": -item.get("cantitate", 0)}}
            )

        received += 1

    logger.info(f"[SYNC] Primit {received} vanzari, {duplicates} duplicate ignorate")
    return {"received": received, "duplicates": duplicates}


@router.post("/sync/mark-done")
async def mark_synced(data: dict, user: dict = Depends(get_current_user)):
    """Marcheaza vanzarile ca sincronizate (pe instanta locala)"""
    sale_ids = data.get("sale_ids", [])
    if not sale_ids:
        return {"marked": 0}

    result = await db.sales.update_many(
        {"id": {"$in": sale_ids}},
        {"$set": {
            "synced": True,
            "synced_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    logger.info(f"[SYNC] Marcate {result.modified_count} vanzari ca sincronizate")
    return {"marked": result.modified_count}


@router.get("/sync/health")
async def sync_health():
    """Endpoint simplu pentru verificare conectivitate (folosit de frontend)"""
    return {"ok": True, "timestamp": datetime.now(timezone.utc).isoformat()}
