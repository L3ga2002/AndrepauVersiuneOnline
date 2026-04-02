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


# =============================================
#  SINCRONIZARE PRODUSE (VPS <-> Local)
# =============================================

@router.get("/sync/products")
async def get_all_products_for_sync(data: dict = None):
    """Returneaza toate produsele pentru sincronizare (folosit de cealalta instanta)"""
    # Accept both GET with query param and direct call
    products = await db.products.find({}, {"_id": 0}).to_list(None)
    return {"products": products, "count": len(products)}


@router.post("/sync/products/push")
async def receive_products(data: dict):
    """Primeste produse de la cealalta instanta si le sincronizeaza"""
    secret = data.get("sync_secret", "")
    if secret != SYNC_SECRET:
        raise HTTPException(status_code=401, detail="Cheie sincronizare invalida")

    products = data.get("products", [])
    if not products:
        return {"added": 0, "updated": 0}

    added = 0
    updated = 0

    for prod in products:
        prod.pop("_id", None)
        prod_id = prod.get("id")
        cod_bare = prod.get("cod_bare", "")
        nume = prod.get("nume", "")
        if not prod_id and not cod_bare and not nume:
            continue

        # Cauta produsul existent: dupa id, cod_bare, sau nume exact
        existing = None
        if prod_id:
            existing = await db.products.find_one({"id": prod_id})
        if not existing and cod_bare:
            existing = await db.products.find_one({"cod_bare": cod_bare})
        if not existing and nume:
            existing = await db.products.find_one({"nume": nume})

        if existing:
            # Actualizeaza DOAR daca produsul sursă e mai nou
            src_updated = prod.get("updated_at", prod.get("created_at", ""))
            dst_updated = existing.get("updated_at", existing.get("created_at", ""))
            if src_updated and dst_updated and src_updated <= dst_updated:
                continue

            update_fields = {}
            for key in ["pret_achizitie", "pret_vanzare", "tva", "stoc", "stoc_minim",
                        "categorie", "unitate", "furnizor", "cod_bare"]:
                if key in prod and prod[key] != existing.get(key):
                    update_fields[key] = prod[key]
            if update_fields:
                update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
                await db.products.update_one(
                    {"_id": existing["_id"]},
                    {"$set": update_fields}
                )
                updated += 1
        else:
            # Produs nou - adauga
            prod["updated_at"] = datetime.now(timezone.utc).isoformat()
            await db.products.insert_one(prod)
            added += 1

    logger.info(f"[SYNC] Produse: {added} adaugate, {updated} actualizate")
    return {"added": added, "updated": updated}


@router.get("/sync/products/changes")
async def get_changed_products(since: str = ""):
    """Returneaza doar produsele modificate dupa un anumit timestamp"""
    query = {}
    if since:
        query["$or"] = [
            {"updated_at": {"$gt": since}},
            {"created_at": {"$gt": since}}
        ]
    products = await db.products.find(query, {"_id": 0}).to_list(None)
    return {"products": products, "count": len(products)}
