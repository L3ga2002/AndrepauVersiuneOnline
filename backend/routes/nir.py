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
    furnizor_nume = (data.get("furnizor_nume") or "").strip()
    numar_factura = data.get("numar_factura")
    items = data.get("items", [])

    if not numar_factura or not items:
        raise HTTPException(status_code=400, detail="Date incomplete (numar factura sau produse lipsa)")

    # Auto-select / auto-create supplier
    supplier = None
    if furnizor_id:
        supplier = await db.suppliers.find_one({"id": furnizor_id}, {"_id": 0})

    if not supplier and furnizor_nume:
        # Cautam dupa nume exact (case-insensitive)
        supplier = await db.suppliers.find_one(
            {"nume": {"$regex": f"^{re.escape(furnizor_nume)}$", "$options": "i"}},
            {"_id": 0}
        )
        # Daca nu exista, auto-creeaza
        if not supplier:
            new_supplier = {
                "id": str(uuid.uuid4()),
                "nume": furnizor_nume,
                "telefon": None,
                "email": None,
                "adresa": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.suppliers.insert_one(new_supplier)
            supplier = {k: v for k, v in new_supplier.items() if k != "_id"}
            logger.info(f"[NIR-PDF] Auto-created supplier: {furnizor_nume}")

    if not supplier:
        raise HTTPException(status_code=404, detail="Furnizor negăsit si numele nu a fost furnizat pentru creare automata")

    furnizor_id = supplier["id"]
    numar_nir = await generate_nir_number()
    nir_items = []
    created_products = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for item in items:
        product_id = item.get("product_id")
        denumire = item.get("denumire", item.get("nume", ""))
        cantitate = float(item.get("cantitate", 0))
        # Pretul din PDF e PRET VANZARE (valoare vanzare unitar, cu TVA inclus)
        pret_vanzare = float(item.get("pret_vanzare", item.get("pret_achizitie", 0)))
        um = item.get("um", "buc")

        if not product_id:
            # Produs NOU - denumirea din PDF, pret_vanzare din PDF
            new_product = {
                "id": str(uuid.uuid4()),
                "nume": denumire,
                "categorie": "Necategorisit",
                "cod_bare": "",
                "pret_achizitie": 0,
                "pret_vanzare": pret_vanzare,
                "tva": 21,
                "unitate": um if um in ["buc", "sac", "kg", "metru", "litru", "rola"] else "buc",
                "stoc": cantitate,
                "stoc_minim": 5,
                "descriere": "",
                "furnizor_id": furnizor_id,
                "created_at": now_iso,
                "updated_at": now_iso
            }
            await db.products.insert_one(new_product)
            product_id = new_product["id"]
            created_products.append({"product_id": product_id, "nume": denumire, "cod_bare": ""})
        else:
            # Produs EXISTENT - PASTREAZA denumirea existenta, updateaza stocul si pret_vanzare
            await db.products.update_one(
                {"id": product_id},
                {
                    "$inc": {"stoc": cantitate},
                    "$set": {
                        "pret_vanzare": pret_vanzare,
                        "updated_at": now_iso
                    }
                }
            )
            prod = await db.products.find_one({"id": product_id}, {"_id": 0, "nume": 1, "cod_bare": 1})
            created_products.append({
                "product_id": product_id,
                "nume": prod["nume"] if prod else denumire,
                "cod_bare": prod.get("cod_bare", "") if prod else ""
            })

        nir_items.append({
            "product_id": product_id,
            "nume": denumire,
            "cantitate": cantitate,
            "pret_achizitie": pret_vanzare  # Pastram campul pentru compatibilitate istoric NIR
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
        "created_at": now_iso
    }

    await db.nirs.insert_one(nir_doc)
    nir_response = {k: v for k, v in nir_doc.items() if k != "_id"}
    return {
        "nir": nir_response,
        "created_products": created_products,
        "products_created_count": len([p for p in items if not p.get("product_id")]),
        "products_updated_count": len([p for p in items if p.get("product_id")]),
        "supplier_auto_created": not data.get("furnizor_id") and bool(furnizor_nume)
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

    extracted_items = _extract_items_from_multiline_blocks(all_blocks)

    if not extracted_items:
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


def _extract_items_from_multiline_blocks(blocks: list) -> list:
    """Parser pentru NIR multi-block (format TOP MASTER si similar).
    Fiecare produs se intinde pe 2+ blocuri:
      Block A: "N | Denumire produs partea 1"
      Block B: "continuare denumire" (optional, multi-line)
      Block C: "Marfa" sau similar (optional)
      Block D: "buc | qty | qty_doc | pret_u | ... | pret_vz_unitar | total_vz"
    Detecteaza inceputul prin '<num> | <text>' si finalizeaza cand gaseste block cu UM la inceput.
    """
    items = []
    um_set = {"buc", "sac", "kg", "m", "ml", "m2", "mp", "mc", "litru", "l", "rola",
              "set", "to", "pach", "pac", "fl", "cutie", "cmp"}
    skip_continuation = {"marfa", "produs", "servicii", ""}

    i = 0
    n = len(blocks)
    while i < n:
        block = blocks[i]
        parts = [p.strip() for p in block.strip().split('\n') if p.strip()]
        if not parts:
            i += 1
            continue

        # Detect row start:
        # Case A: "N name..." on single first line (e.g., "10 CERESIT TS 62")
        # Case B: "N" alone on first line, name on subsequent lines (e.g., "1\nMOMENT WOOD...")
        first = parts[0]
        m_a = re.match(r'^(\d{1,3})\s+([A-Za-zĂÂÎȘȚăâîșț].*)', first)
        m_b = re.match(r'^(\d{1,3})$', first)

        if m_a:
            row_num = int(m_a.group(1))
            name_seed = m_a.group(2).strip()
        elif m_b and len(parts) > 1:
            row_num = int(m_b.group(1))
            name_seed = ""
        else:
            i += 1
            continue

        if not (1 <= row_num <= 999):
            i += 1
            continue

        # Collect name pieces from current block
        name_parts = []
        if name_seed:
            name_parts.append(name_seed)
        for p in parts[1:]:
            if p.lower() in um_set:
                break
            if p.lower() in skip_continuation:
                continue
            name_parts.append(p)

        # Scan forward through subsequent blocks to find the UM/numbers block
        j = i + 1
        numbers_block = None
        while j < n:
            nxt = blocks[j].strip()
            nxt_parts = [p.strip() for p in nxt.split('\n') if p.strip()]
            if not nxt_parts:
                j += 1
                continue

            nxt_first = nxt_parts[0].lower()
            first_token = nxt_first.split()[0] if nxt_first else ""

            # Does this block start with a UM token? Then it's the numbers row
            if first_token in um_set:
                numbers_block = nxt
                break

            # Is this a new row start (N name or just N)? Then bail out
            if re.match(r'^\d{1,3}\s+[A-Za-zĂÂÎȘȚăâîșț]', nxt_parts[0]) or re.match(r'^\d{1,3}$', nxt_parts[0]):
                break

            # Otherwise this is name continuation
            for p in nxt_parts:
                if p.lower() not in skip_continuation and p.lower() not in um_set:
                    name_parts.append(p)
            j += 1

        if not numbers_block:
            i = j if j > i else i + 1
            continue

        # Parse numbers from numbers_block
        nums_text = numbers_block.replace('|', ' ').replace('\n', ' ')
        tokens = nums_text.split()
        # First token is UM
        um = tokens[0].lower() if tokens else "buc"
        if um not in um_set:
            um = "buc"

        numbers = []
        for t in tokens[1:]:
            v = parse_number(t)
            if v > 0:
                numbers.append(v)

        if len(numbers) < 2:
            i = j + 1
            continue

        name = ' '.join(name_parts).strip()
        # Clean up name: remove trailing "Marfa" variants
        name = re.sub(r'\s+(Marfa|MARFA)\s*$', '', name).strip()

        if len(name) < 3:
            i = j + 1
            continue

        qty = numbers[0]
        # FORMAT NIR extins cu coloane: cant, cant_doc, pret_furnizor, val, tva, total_furnizor,
        # adaos%, adaos_u, adaos_t, pret_vz_fara_tva, aferent_adaos, tva_u, tva_t,
        # VALOARE_VANZARE_UNITAR, VALOARE_VANZARE_TOTAL
        # -> pret_vanzare = penultimul, valoare = ultimul
        if len(numbers) >= 10:
            pret_vanzare = numbers[-2]
            valoare = numbers[-1]
        elif len(numbers) >= 4:
            # Format moderat: [cant, cant_doc, pret, valoare]
            pret_vanzare = numbers[-2]
            valoare = numbers[-1]
        else:
            # Format simplu: [cant, pret, valoare?]
            pret_vanzare = numbers[1]
            valoare = numbers[2] if len(numbers) > 2 else round(qty * pret_vanzare, 2)

        if qty > 0 and pret_vanzare > 0:
            items.append({
                "denumire": name,
                "um": um,
                "cantitate": qty,
                "pret_unitar": pret_vanzare,  # PRET VANZARE din PDF (cu TVA)
                "valoare": valoare
            })

        i = j + 1

    return items


def _extract_items_from_blocks(blocks: list) -> list:
    """Extract items from PDF blocks.
    Detecteaza 2 formate:
    1. NIR cu pret vanzare unitar (format TOP MASTER cu coloane extinse):
       Nr | Denumire | UM | Cant | [Cant doc] | Pret furnizor | Val | TVA | Total |
       Adaos% | Adaos_u | Adaos_t | Pvz_fara_tva | Aferent | TVA_u | TVA_t |
       VALOARE_VANZARE_UNITAR | VALOARE_VANZARE_TOTAL
    2. Factura simpla: Nr | Denumire | UM | Cant | Pret | Valoare
    Returneaza pret_vanzare (unitar cu TVA inclus) pentru fiecare produs.
    """
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

        # Gaseste pozitia UM
        um_idx = None
        for i, part in enumerate(parts[1:], 1):
            if part.lower() in um_set:
                um_idx = i
                break

        if um_idx is not None and um_idx + 2 < len(parts):
            name = ' '.join(parts[1:um_idx])
            um = parts[um_idx].lower()
            # Extrage TOATE numerele dupa UM
            numbers = []
            for p in parts[um_idx + 1:]:
                val = parse_number(p)
                if val > 0:
                    numbers.append(val)

            if len(numbers) < 2 or len(name) < 3:
                continue

            qty = numbers[0]

            # FORMAT NIR extins (>= 10 numere dupa UM): ultimele 2 sunt pret_vanzare_unitar si total_vanzare
            # Ex: [5, 5, 15.53, 77.65, 16.31, 93.96, 33.04, 5.13, 25.66, 20.66, 1.08, 4.34, 21.69, 25.00, 125.00]
            #  -> cantitate=5, pret_vanzare=25.00, total=125.00
            if len(numbers) >= 10:
                pret_vanzare = numbers[-2]
                valoare = numbers[-1]
            # FORMAT simplu (3-4 numere): [cant, pret, valoare] sau [cant, pret]
            else:
                pret_vanzare = numbers[1]
                valoare = numbers[2] if len(numbers) > 2 else round(qty * pret_vanzare, 2)

            if qty > 0 and pret_vanzare > 0:
                items.append({
                    "denumire": name,
                    "um": um if um in um_set else "buc",
                    "cantitate": qty,
                    "pret_unitar": pret_vanzare,  # PRET VANZARE din PDF
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

                if len(numbers) >= 2 and len(name) > 2:
                    qty = numbers[0]
                    # FORMAT NIR extins detectat si aici
                    if len(numbers) >= 10:
                        pret_vanzare = numbers[-2]
                        valoare = numbers[-1]
                    else:
                        pret_vanzare = numbers[1]
                        valoare = numbers[2] if len(numbers) > 2 else round(qty * pret_vanzare, 2)

                    items.append({
                        "denumire": name,
                        "um": "buc",
                        "cantitate": qty,
                        "pret_unitar": pret_vanzare,
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
                    qty = numbers[0]
                    # FORMAT NIR extins: >= 10 numere -> pret_vanzare = penultimul, valoare = ultimul
                    if len(numbers) >= 10:
                        pret_vanzare = numbers[-2]
                        valoare = numbers[-1]
                    else:
                        pret_vanzare = numbers[1]
                        valoare = numbers[2] if len(numbers) > 2 else round(qty * pret_vanzare, 2)
                    items.append({
                        "denumire": name,
                        "um": um,
                        "cantitate": qty,
                        "pret_unitar": pret_vanzare,
                        "valoare": valoare
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
