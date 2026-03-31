from fastapi import APIRouter
from datetime import datetime, timezone
import uuid

from database import db
from auth import hash_password

router = APIRouter()


@router.post("/seed")
async def seed_database():
    existing_admin = await db.users.find_one({"username": "admin"})
    if existing_admin:
        return {"message": "Database deja populată"}

    admin_doc = {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "password": hash_password("admin123"),
        "full_name": "Administrator",
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_doc)

    casier_doc = {
        "id": str(uuid.uuid4()),
        "username": "casier",
        "password": hash_password("casier123"),
        "full_name": "Casier Principal",
        "role": "casier",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(casier_doc)

    suppliers = [
        {"id": str(uuid.uuid4()), "nume": "Dedeman S.R.L.", "telefon": "0721000001", "email": "contact@dedeman.ro", "adresa": "București", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Hornbach România", "telefon": "0721000002", "email": "contact@hornbach.ro", "adresa": "Cluj-Napoca", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Leroy Merlin", "telefon": "0721000003", "email": "contact@leroymerlin.ro", "adresa": "Timișoara", "created_at": datetime.now(timezone.utc).isoformat()},
    ]
    await db.suppliers.insert_many(suppliers)

    categories = ["Materiale Construcții", "Scule Electrice", "Scule Manuale", "Feronerie", "Instalații Sanitare", "Electrice", "Vopsele", "Consumabile"]
    units = ["buc", "sac", "kg", "metru", "litru", "rola"]

    products = [
        {"id": str(uuid.uuid4()), "nume": "Ciment Portland 40kg", "categorie": "Materiale Construcții", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000001", "pret_achizitie": 28.0, "pret_vanzare": 35.0, "tva": 21.0, "unitate": "sac", "stoc": 150, "stoc_minim": 20, "descriere": "Ciment de înaltă calitate", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Var hidratat 20kg", "categorie": "Materiale Construcții", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000002", "pret_achizitie": 12.0, "pret_vanzare": 18.0, "tva": 21.0, "unitate": "sac", "stoc": 80, "stoc_minim": 15, "descriere": "Var pentru construcții", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Nisip fin 40kg", "categorie": "Materiale Construcții", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000003", "pret_achizitie": 8.0, "pret_vanzare": 12.0, "tva": 21.0, "unitate": "sac", "stoc": 200, "stoc_minim": 30, "descriere": "Nisip pentru tencuială", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "BCA 60x20x25", "categorie": "Materiale Construcții", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000004", "pret_achizitie": 6.5, "pret_vanzare": 9.0, "tva": 21.0, "unitate": "buc", "stoc": 500, "stoc_minim": 50, "descriere": "Blocuri BCA", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Bormaşină Bosch 750W", "categorie": "Scule Electrice", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000010", "pret_achizitie": 180.0, "pret_vanzare": 250.0, "tva": 21.0, "unitate": "buc", "stoc": 15, "stoc_minim": 3, "descriere": "Bormaşină profesională", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Flex 125mm 1200W", "categorie": "Scule Electrice", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000011", "pret_achizitie": 120.0, "pret_vanzare": 170.0, "tva": 21.0, "unitate": "buc", "stoc": 12, "stoc_minim": 2, "descriere": "Polizor unghiular", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Șurubelniță electrică", "categorie": "Scule Electrice", "furnizor_id": suppliers[2]["id"], "cod_bare": "5941234000012", "pret_achizitie": 85.0, "pret_vanzare": 120.0, "tva": 21.0, "unitate": "buc", "stoc": 20, "stoc_minim": 5, "descriere": "Autofiletantă cu acumulator", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Ciocan 500g", "categorie": "Scule Manuale", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000020", "pret_achizitie": 25.0, "pret_vanzare": 38.0, "tva": 21.0, "unitate": "buc", "stoc": 40, "stoc_minim": 10, "descriere": "Ciocan cu mâner fibră", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Set șurubelnițe 6buc", "categorie": "Scule Manuale", "furnizor_id": suppliers[2]["id"], "cod_bare": "5941234000021", "pret_achizitie": 35.0, "pret_vanzare": 55.0, "tva": 21.0, "unitate": "buc", "stoc": 25, "stoc_minim": 5, "descriere": "Set complet șurubelnițe", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Cheie reglabilă 300mm", "categorie": "Scule Manuale", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000022", "pret_achizitie": 45.0, "pret_vanzare": 65.0, "tva": 21.0, "unitate": "buc", "stoc": 18, "stoc_minim": 4, "descriere": "Cheie franceză", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Șuruburi 4x40 100buc", "categorie": "Feronerie", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000030", "pret_achizitie": 8.0, "pret_vanzare": 14.0, "tva": 21.0, "unitate": "buc", "stoc": 100, "stoc_minim": 20, "descriere": "Șuruburi autofiletante", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Diblu plastic 8mm 100buc", "categorie": "Feronerie", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000031", "pret_achizitie": 6.0, "pret_vanzare": 10.0, "tva": 21.0, "unitate": "buc", "stoc": 150, "stoc_minim": 30, "descriere": "Dibluri pentru BCA", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Balama ușă 100mm", "categorie": "Feronerie", "furnizor_id": suppliers[2]["id"], "cod_bare": "5941234000032", "pret_achizitie": 12.0, "pret_vanzare": 18.0, "tva": 21.0, "unitate": "buc", "stoc": 60, "stoc_minim": 10, "descriere": "Balama din oțel", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Țeavă PPR 25mm", "categorie": "Instalații Sanitare", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000040", "pret_achizitie": 3.5, "pret_vanzare": 5.5, "tva": 21.0, "unitate": "metru", "stoc": 500, "stoc_minim": 100, "descriere": "Țeavă apă caldă/rece", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Robinet colț 1/2", "categorie": "Instalații Sanitare", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000041", "pret_achizitie": 18.0, "pret_vanzare": 28.0, "tva": 21.0, "unitate": "buc", "stoc": 40, "stoc_minim": 10, "descriere": "Robinet colțar", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Sifon chiuvetă", "categorie": "Instalații Sanitare", "furnizor_id": suppliers[2]["id"], "cod_bare": "5941234000042", "pret_achizitie": 15.0, "pret_vanzare": 25.0, "tva": 21.0, "unitate": "buc", "stoc": 35, "stoc_minim": 8, "descriere": "Sifon plastic", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Cablu electric 2.5mm", "categorie": "Electrice", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000050", "pret_achizitie": 4.0, "pret_vanzare": 6.5, "tva": 21.0, "unitate": "metru", "stoc": 800, "stoc_minim": 200, "descriere": "Cablu FY cupru", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Priză simplă", "categorie": "Electrice", "furnizor_id": suppliers[2]["id"], "cod_bare": "5941234000051", "pret_achizitie": 8.0, "pret_vanzare": 14.0, "tva": 21.0, "unitate": "buc", "stoc": 100, "stoc_minim": 25, "descriere": "Priză cu împământare", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Întrerupător simplu", "categorie": "Electrice", "furnizor_id": suppliers[2]["id"], "cod_bare": "5941234000052", "pret_achizitie": 7.0, "pret_vanzare": 12.0, "tva": 21.0, "unitate": "buc", "stoc": 90, "stoc_minim": 20, "descriere": "Întrerupător alb", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Vopsea lavabilă albă 15L", "categorie": "Vopsele", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000060", "pret_achizitie": 85.0, "pret_vanzare": 120.0, "tva": 21.0, "unitate": "buc", "stoc": 30, "stoc_minim": 5, "descriere": "Vopsea interior", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Grund alb 10L", "categorie": "Vopsele", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000061", "pret_achizitie": 55.0, "pret_vanzare": 80.0, "tva": 21.0, "unitate": "buc", "stoc": 25, "stoc_minim": 5, "descriere": "Grund acrilic", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Vopsea email albastru 0.75L", "categorie": "Vopsele", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000062", "pret_achizitie": 28.0, "pret_vanzare": 42.0, "tva": 21.0, "unitate": "buc", "stoc": 45, "stoc_minim": 10, "descriere": "Email pentru metal", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Bandă izolatoare", "categorie": "Consumabile", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000070", "pret_achizitie": 3.0, "pret_vanzare": 5.0, "tva": 21.0, "unitate": "buc", "stoc": 200, "stoc_minim": 50, "descriere": "Bandă PVC", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Silicon transparent 280ml", "categorie": "Consumabile", "furnizor_id": suppliers[2]["id"], "cod_bare": "5941234000071", "pret_achizitie": 12.0, "pret_vanzare": 18.0, "tva": 21.0, "unitate": "buc", "stoc": 80, "stoc_minim": 20, "descriere": "Silicon universal", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Disc flex 125mm metal", "categorie": "Consumabile", "furnizor_id": suppliers[1]["id"], "cod_bare": "5941234000072", "pret_achizitie": 4.0, "pret_vanzare": 7.0, "tva": 21.0, "unitate": "buc", "stoc": 150, "stoc_minim": 30, "descriere": "Disc abraziv", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Furtun grădină 20m", "categorie": "Consumabile", "furnizor_id": suppliers[0]["id"], "cod_bare": "5941234000080", "pret_achizitie": 45.0, "pret_vanzare": 65.0, "tva": 21.0, "unitate": "buc", "stoc": 3, "stoc_minim": 5, "descriere": "Furtun cu armătură", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "nume": "Mănuși protecție", "categorie": "Consumabile", "furnizor_id": suppliers[2]["id"], "cod_bare": "5941234000081", "pret_achizitie": 8.0, "pret_vanzare": 15.0, "tva": 21.0, "unitate": "buc", "stoc": 2, "stoc_minim": 10, "descriere": "Mănuși latex", "created_at": datetime.now(timezone.utc).isoformat()},
    ]
    await db.products.insert_many(products)

    return {"message": "Database populată cu succes", "users": 2, "suppliers": 3, "products": len(products)}
