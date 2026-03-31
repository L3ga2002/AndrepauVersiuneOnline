from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import re
import os
import uuid
import fitz
from datetime import datetime, timezone
import logging

from database import db
from auth import get_current_user, require_admin
from models import NIRCreate, NIRResponse, NIRItem
from utils import parse_number

router = APIRouter()
logger = logging.getLogger(__name__)


async def generate_nir_number():
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = await db.nirs.count_documents({"numar_nir": {"$regex": f"^NIR-{today}"}})
    return f"NIR-{today}-{str(count + 1).zfill(4)}"


@router.post("/nir", response_model=NIRResponse)
async def create_nir(nir: NIRCreate, user: dict = Depends(require_admin)):
    numar_nir = await generate_nir_number()

    supplier = await db.suppliers.find_one({"id": nir.furnizor_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Furnizor negăsit")

    nir_doc = {
        "id": str(uuid.uuid4()),
        "numar_nir": numar_nir,
        **nir.model_dump(),
        "furnizor_nume": supplier["nume"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    for item in nir.items:
        await db.products.update_one(
            {"id": item.product_id},
            {"$inc": {"stoc": item.cantitate}}
        )

    await db.nirs.insert_one(nir_doc)
    return NIRResponse(**{k: v for k, v in nir_doc.items() if k != "_id"})


@router.post("/nir/from-pdf")
async def create_nir_from_pdf(data: dict, user: dict = Depends(require_admin)):
    furnizor_id = data.get("furnizor_id")
    numar_factura = data.get("numar_factura")
    items = data.get("items", [])

    if not furnizor_id or not numar_factura or not items:
        raise HTTPException(status_code=400, detail="Date incomplete")

    supplier = await db.suppliers.find_one({"id": furnizor_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Furnizor negăsit")

    numar_nir = await generate_nir_number()
    nir_items = []
    created_products = []

    for item in items:
        product_id = item.get("product_id")
        denumire = item.get("denumire", item.get("nume", ""))
        cantitate = float(item.get("cantitate", 0))
        pret_achizitie = float(item.get("pret_achizitie", 0))
        um = item.get("um", "buc")

        if not product_id:
            new_product = {
                "id": str(uuid.uuid4()),
                "nume": denumire,
                "categorie": "Necategorisit",
                "cod_bare": "",
                "pret_achizitie": pret_achizitie,
                "pret_vanzare": round(pret_achizitie * 1.3, 2),
                "tva": 19,
                "unitate": um if um in ["buc", "sac", "kg", "metru", "litru", "rola"] else "buc",
                "stoc": cantitate,
                "stoc_minim": 5,
                "descriere": "",
                "furnizor_id": furnizor_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.products.insert_one(new_product)
            product_id = new_product["id"]
            created_products.append({"product_id": product_id, "nume": denumire, "cod_bare": ""})
        else:
            await db.products.update_one(
                {"id": product_id},
                {"$inc": {"stoc": cantitate}}
            )
            prod = await db.products.find_one({"id": product_id}, {"_id": 0, "nume": 1, "cod_bare": 1})
            created_products.append({"product_id": product_id, "nume": prod["nume"] if prod else denumire, "cod_bare": prod.get("cod_bare", "") if prod else ""})

        nir_items.append({
            "product_id": product_id,
            "nume": denumire,
            "cantitate": cantitate,
            "pret_achizitie": pret_achizitie
        })

    total = sum(i["cantitate"] * i["pret_achizitie"] for i in nir_items)
    nir_doc = {
        "id": str(uuid.uuid4()),
        "numar_nir": numar_nir,
        "furnizor_id": furnizor_id,
        "numar_factura": numar_factura,
        "items": nir_items,
        "total": total,
        "furnizor_nume": supplier["nume"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.nirs.insert_one(nir_doc)
    nir_response = {k: v for k, v in nir_doc.items() if k != "_id"}
    return {
        "nir": nir_response,
        "created_products": created_products,
        "products_created_count": len([p for p in items if not p.get("product_id")]),
        "products_updated_count": len([p for p in items if p.get("product_id")])
    }


@router.get("/nir", response_model=List[NIRResponse])
async def get_nirs(user: dict = Depends(get_current_user)):
    nirs = await db.nirs.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [NIRResponse(**n) for n in nirs]


@router.get("/nir/test-invoices")
async def list_test_invoices(user: dict = Depends(require_admin)):
    invoice_dir = os.path.join(os.path.dirname(__file__), "..", "static", "test_invoices")
    if not os.path.exists(invoice_dir):
        return {"invoices": []}
    files = [f for f in os.listdir(invoice_dir) if f.endswith('.pdf')]
    return {"invoices": files}


@router.get("/nir/test-invoices/{filename}")
async def download_test_invoice(filename: str, user: dict = Depends(require_admin)):
    invoice_dir = os.path.join(os.path.dirname(__file__), "..", "static", "test_invoices")
    filepath = os.path.join(invoice_dir, filename)
    if not os.path.exists(filepath) or not filename.endswith('.pdf'):
        raise HTTPException(status_code=404, detail="Fișier negăsit")
    return FileResponse(filepath, media_type="application/pdf", filename=filename)


@router.post("/nir/parse-pdf")
async def parse_nir_pdf(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Fișierul trebuie să fie PDF")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fișierul este prea mare (max 10MB)")

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception:
        raise HTTPException(status_code=400, detail="Fișierul PDF nu a putut fi deschis")

    all_text = ""
    all_blocks = []
    for page in doc:
        all_text += page.get_text("text") + "\n"
        for block in page.get_text("blocks"):
            if block[6] == 0:
                all_blocks.append(block[4])
    doc.close()

    invoice_number = ""
    inv_patterns = [
        r'(?:factura|fact\.?|fv|invoice)\s*(?:nr\.?|no\.?|numar|#)?\s*[:.]?\s*\n?\s*([A-Z0-9\-\/\s]+)',
        r'(?:TOP|SER|FV|FC)\s+(\d{5,})',
        r'(?:seria?\s+[A-Z]+\s+nr\.?\s*)(\d+)',
    ]
    for pattern in inv_patterns:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            invoice_number = match.group(1).strip().split('\n')[0].strip()
            break

    supplier_name = ""
    company_matches = re.findall(r'([\w\s\.\-]+\bS\.?R\.?L\.?\b|[\w\s\.\-]+\bS\.?A\.?\b|[\w\s\.\-]+\bL\.?T\.?D\.?\b)', all_text)
    for name in company_matches:
        clean = name.strip()
        if clean and 'ANDREPAU' not in clean.upper() and len(clean) > 5:
            clean = re.sub(r'^\d+[\s.]*', '', clean).strip()
            if clean and len(clean) > 5:
                supplier_name = clean
                break
    if not supplier_name:
        lines = all_text.split('\n')
        in_supplier_section = False
        for line in lines:
            stripped = line.strip()
            if re.match(r'(?i)furnizor', stripped):
                in_supplier_section = True
                continue
            if in_supplier_section and stripped:
                if 'cumparator' in stripped.lower() or 'andrepau' in stripped.lower():
                    continue
                if len(stripped) > 3 and not stripped.startswith('CUI') and not stripped.startswith('Reg'):
                    supplier_name = stripped
                    break

    extracted_items = _extract_items_from_blocks(all_blocks)

    if not extracted_items:
        extracted_items = _extract_items_from_lines(all_text)

    products = await db.products.find({}, {"_id": 0, "id": 1, "nume": 1, "cod_bare": 1, "pret_achizitie": 1}).to_list(100000)
    matched_items = []

    for item in extracted_items:
        best_match = _find_best_product_match(item["denumire"], products)
        matched_items.append({
            "denumire_pdf": item["denumire"],
            "cantitate": item["cantitate"],
            "pret_unitar": item["pret_unitar"],
            "um": item.get("um", "buc"),
            "valoare": item.get("valoare", round(item["cantitate"] * item["pret_unitar"], 2)),
            "product_id": best_match["id"] if best_match else None,
            "product_nume": best_match["nume"] if best_match else None,
            "match_confidence": best_match["confidence"] if best_match else 0,
        })

    return {
        "invoice_number": invoice_number,
        "supplier_name": supplier_name,
        "items": matched_items,
        "raw_text_preview": all_text[:2000],
        "total_items": len(matched_items)
    }


def _extract_items_from_blocks(blocks: list) -> list:
    items = []
    um_set = {"buc", "sac", "kg", "m", "ml", "m2", "mp", "mc", "litru", "l", "rola", "set", "to", "pach", "pac", "fl", "cutie", "cmp"}

    for block_text in blocks:
        parts = [p.strip() for p in block_text.strip().split('\n') if p.strip()]
        if len(parts) < 4:
            continue

        first = parts[0]
        if not re.match(r'^\d{1,4}$', first):
            continue

        row_num = int(first)
        if row_num < 1 or row_num > 999:
            continue

        um_idx = None
        for i, part in enumerate(parts[1:], 1):
            if part.lower() in um_set:
                um_idx = i
                break

        if um_idx is not None and um_idx + 2 < len(parts):
            name = ' '.join(parts[1:um_idx])
            um = parts[um_idx].lower()
            qty = parse_number(parts[um_idx + 1])
            price = parse_number(parts[um_idx + 2])
            valoare = parse_number(parts[um_idx + 3]) if um_idx + 3 < len(parts) else round(qty * price, 2)

            if qty > 0 and price > 0 and len(name) > 2:
                items.append({
                    "denumire": name,
                    "um": um if um in um_set else "buc",
                    "cantitate": qty,
                    "pret_unitar": price,
                    "valoare": valoare
                })
        else:
            num_start = None
            for i in range(1, len(parts)):
                cleaned = parts[i].replace(',', '.').replace(' ', '')
                try:
                    float(cleaned)
                    num_start = i
                    break
                except ValueError:
                    continue

            if num_start is not None and num_start > 1:
                name = ' '.join(parts[1:num_start])
                numbers = []
                for p in parts[num_start:]:
                    val = parse_number(p)
                    if val > 0:
                        numbers.append(val)

                if len(numbers) >= 2:
                    qty = numbers[0]
                    price = numbers[1]
                    valoare = numbers[2] if len(numbers) > 2 else round(qty * price, 2)
                    if len(name) > 2:
                        items.append({
                            "denumire": name,
                            "um": "buc",
                            "cantitate": qty,
                            "pret_unitar": price,
                            "valoare": valoare
                        })

    return items


def _extract_items_from_lines(text: str) -> list:
    items = []
    lines = text.split('\n')
    lines = [ln.strip() for ln in lines if ln.strip()]

    skip_words = {'denumire', 'produs', 'nr.crt', 'nr. crt', 'cantitate', 'total general',
                  'subtotal', 'tva', 'baza impozabila', 'de plata', 'cont', 'banca',
                  'factura', 'seria', 'furnizor', 'cumparator', 'adresa', 'delegat',
                  'cota tva', 'valoare tva', 'index', 'livrare', 'intocmit', 'semnatura'}

    seen_names = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        lower = line.lower()
        if any(h in lower for h in skip_words):
            i += 1
            continue

        m = re.match(r'^(\d{1,3})\s*$', line)
        if m:
            row_num = int(m.group(1))
            if 1 <= row_num <= 999 and i + 3 < len(lines):
                name = lines[i + 1].strip()
                if name.lower() in skip_words or re.match(r'^\d+[.,]?\d*$', name):
                    i += 1
                    continue

                remaining = lines[i + 2:i + 8]
                um = "buc"
                numbers = []
                for r_line in remaining:
                    r_clean = r_line.strip().lower()
                    if r_clean in {"buc", "sac", "kg", "m", "ml", "m2", "mp", "mc", "litru", "l", "rola", "set"}:
                        um = r_clean
                        continue
                    val = parse_number(r_line)
                    if val > 0:
                        numbers.append(val)
                    elif r_line.strip() and not re.match(r'^[\d.,\s]+$', r_line.strip()):
                        break

                if len(numbers) >= 2 and name not in seen_names:
                    seen_names.add(name)
                    items.append({
                        "denumire": name,
                        "um": um,
                        "cantitate": numbers[0],
                        "pret_unitar": numbers[1],
                        "valoare": numbers[2] if len(numbers) > 2 else round(numbers[0] * numbers[1], 2)
                    })

        i += 1

    return items


def _find_best_product_match(pdf_name: str, products: list) -> dict | None:
    if not pdf_name or not products:
        return None

    pdf_lower = pdf_name.lower().strip()

    for p in products:
        prod_lower = p["nume"].lower().strip()
        if pdf_lower == prod_lower:
            return {"id": p["id"], "nume": p["nume"], "confidence": 100}

    return None
