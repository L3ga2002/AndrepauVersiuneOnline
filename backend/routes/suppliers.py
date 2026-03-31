from fastapi import APIRouter, Depends, HTTPException
from typing import List
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user, require_admin
from models import SupplierCreate, SupplierResponse

router = APIRouter()


@router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(supplier: SupplierCreate, user: dict = Depends(require_admin)):
    supplier_doc = {
        "id": str(uuid.uuid4()),
        **supplier.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.suppliers.insert_one(supplier_doc)
    return SupplierResponse(**{k: v for k, v in supplier_doc.items() if k != "_id"})


@router.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(user: dict = Depends(get_current_user)):
    suppliers = await db.suppliers.find({}, {"_id": 0}).to_list(1000)
    return [SupplierResponse(**s) for s in suppliers]


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Furnizor negăsit")
    return SupplierResponse(**supplier)


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: str, supplier: SupplierCreate, user: dict = Depends(require_admin)):
    result = await db.suppliers.update_one({"id": supplier_id}, {"$set": supplier.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Furnizor negăsit")
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    return SupplierResponse(**updated)


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, user: dict = Depends(require_admin)):
    result = await db.suppliers.delete_one({"id": supplier_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Furnizor negăsit")
    return {"message": "Furnizor șters"}
