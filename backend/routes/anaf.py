from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import logging

from database import db
from auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache for searched companies
companies_cache = {}


@router.post("/anaf/search-cui")
async def search_anaf_cui(data: dict, user: dict = Depends(get_current_user)):
    import httpx

    cui = data.get("cui", "").strip()
    openapi_key = data.get("openapi_key", "").strip()

    if not cui:
        raise HTTPException(status_code=400, detail="CUI este obligatoriu")

    cui_clean = cui.upper().replace("RO", "").strip()

    try:
        cui_int = int(cui_clean)
    except ValueError:
        raise HTTPException(status_code=400, detail="CUI invalid - trebuie să fie un număr")

    if cui_clean in companies_cache:
        logger.info(f"Returning cached company data for CUI {cui_clean}")
        return companies_cache[cui_clean]

    existing = await db.companies_cache.find_one({"cui": cui_clean})
    if existing:
        cached_data = {
            "cui": existing.get("cui"),
            "denumire": existing.get("denumire"),
            "adresa": existing.get("adresa"),
            "nr_reg_com": existing.get("nr_reg_com"),
            "telefon": existing.get("telefon", ""),
            "cod_postal": existing.get("cod_postal", ""),
            "platitor_tva": existing.get("platitor_tva", False),
            "stare": existing.get("stare", ""),
            "localitate": existing.get("localitate", ""),
            "judet": existing.get("judet", ""),
            "from_cache": True
        }
        companies_cache[cui_clean] = cached_data
        return cached_data

    onrc_company = await db.romania_companies.find_one({"cui": cui_clean})
    if onrc_company:
        result_data = {
            "cui": onrc_company.get("cui"),
            "denumire": onrc_company.get("denumire"),
            "adresa": onrc_company.get("adresa"),
            "nr_reg_com": onrc_company.get("nr_reg_com"),
            "telefon": "",
            "cod_postal": onrc_company.get("cod_postal", ""),
            "platitor_tva": False,
            "stare": "ACTIV",
            "localitate": onrc_company.get("localitate", ""),
            "judet": onrc_company.get("judet", ""),
            "source": "onrc",
            "from_cache": True
        }
        companies_cache[cui_clean] = result_data
        return result_data

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    company_data = None
    anaf_error_detail = None

    if openapi_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.get(
                    f"https://api.openapi.ro/api/companies/{cui_int}",
                    headers={"x-api-key": openapi_key}
                )

                if response.status_code == 200:
                    result = response.json()
                    company_data = {
                        "cui": cui_clean,
                        "denumire": result.get("denumire", ""),
                        "adresa": result.get("adresa", ""),
                        "nr_reg_com": result.get("numar_reg_com", ""),
                        "telefon": result.get("telefon", ""),
                        "cod_postal": result.get("cod_postal", ""),
                        "platitor_tva": result.get("tva", False),
                        "stare": result.get("stare", ""),
                        "localitate": result.get("localitate", ""),
                        "judet": result.get("judet", ""),
                        "source": "openapi.ro"
                    }
        except Exception as e:
            logger.warning(f"OpenAPI.ro error: {str(e)}")

    if not company_data:
        anaf_url = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva"
        payload = [{"cui": cui_int, "data": today}]

        try:
            async with httpx.AsyncClient(
                timeout=20.0,
                follow_redirects=True,
                verify=True
            ) as http_client:
                response = await http_client.post(
                    anaf_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                )

                logger.info(f"ANAF v9 response status: {response.status_code}")

                if response.status_code in (200, 404) and response.headers.get("content-type", "").startswith("application"):
                    result = response.json()

                    if result.get("found") and len(result["found"]) > 0:
                        company = result["found"][0]
                        date_generale = company.get("date_generale", {})
                        adresa_sediu = company.get("adresa_sediu_social", {})
                        inregistrare_tva = company.get("inregistrare_scop_Tva", {})

                        address_parts = []
                        if adresa_sediu.get("sdenumire_Strada"):
                            street = adresa_sediu.get("sdenumire_Strada", "")
                            nr = adresa_sediu.get("snumar_Strada", "")
                            if nr:
                                address_parts.append(f"{street} {nr}")
                            else:
                                address_parts.append(street)
                        if adresa_sediu.get("sdenumire_Localitate"):
                            address_parts.append(adresa_sediu.get("sdenumire_Localitate"))
                        if adresa_sediu.get("sdenumire_Judet"):
                            address_parts.append(f"Jud. {adresa_sediu.get('sdenumire_Judet')}")

                        full_address = ", ".join(address_parts) if address_parts else date_generale.get("adresa", "")

                        company_data = {
                            "cui": cui_clean,
                            "denumire": date_generale.get("denumire", ""),
                            "adresa": full_address,
                            "nr_reg_com": date_generale.get("nrRegCom", ""),
                            "telefon": date_generale.get("telefon", ""),
                            "cod_postal": adresa_sediu.get("scod_Postal", "") or date_generale.get("codPostal", ""),
                            "platitor_tva": inregistrare_tva.get("scpTVA", False),
                            "stare": date_generale.get("stare_inregistrare", ""),
                            "localitate": adresa_sediu.get("sdenumire_Localitate", ""),
                            "judet": adresa_sediu.get("sdenumire_Judet", ""),
                            "source": "anaf"
                        }
                    elif result.get("notFound"):
                        anaf_error_detail = f"CUI {cui_clean} nu a fost găsit în baza de date ANAF."
                    else:
                        anaf_error_detail = f"ANAF a răspuns dar fără date pentru CUI {cui_clean}."
                elif "<!DOCTYPE" in response.text or "<html" in response.text.lower():
                    anaf_error_detail = "ANAF a returnat o pagină HTML. Serviciul poate fi indisponibil temporar."
                else:
                    anaf_error_detail = f"ANAF a răspuns cu status {response.status_code}."

        except Exception as e:
            err_msg = str(e).strip()
            logger.warning(f"ANAF v9 error: {err_msg or type(e).__name__}")
            anaf_error_detail = "ANAF nu este disponibil momentan. Încercați din nou."

    if company_data:
        cache_doc = {**company_data, "updated_at": datetime.now(timezone.utc)}
        cache_doc.pop("_id", None)
        await db.companies_cache.update_one(
            {"cui": cui_clean},
            {"$set": cache_doc},
            upsert=True
        )
        companies_cache[cui_clean] = company_data
        return company_data

    error_msg = anaf_error_detail or "Serviciul ANAF nu este disponibil momentan."
    error_msg += " Completați datele manual sau încercați din OpenAPI.ro (openapi.ro - 100 căutări gratuite/lună)."
    raise HTTPException(status_code=503, detail=error_msg)


@router.post("/companies/save")
async def save_company_manually(data: dict, user: dict = Depends(get_current_user)):
    cui = data.get("cui", "").strip().upper().replace("RO", "")
    if not cui:
        raise HTTPException(status_code=400, detail="CUI este obligatoriu")

    company_data = {
        "cui": cui,
        "denumire": data.get("denumire", ""),
        "adresa": data.get("adresa", ""),
        "nr_reg_com": data.get("nr_reg_com", ""),
        "telefon": data.get("telefon", ""),
        "cod_postal": data.get("cod_postal", ""),
        "platitor_tva": data.get("platitor_tva", False),
        "stare": data.get("stare", "ACTIV"),
        "localitate": data.get("localitate", ""),
        "judet": data.get("judet", ""),
        "source": "manual",
        "updated_at": datetime.now(timezone.utc)
    }

    await db.companies_cache.update_one(
        {"cui": cui},
        {"$set": company_data},
        upsert=True
    )

    companies_cache[cui] = company_data
    return {"message": "Firmă salvată cu succes", "company": company_data}


@router.get("/companies/cached")
async def get_cached_companies(user: dict = Depends(get_current_user)):
    companies = await db.companies_cache.find({}, {"_id": 0}).to_list(1000)
    return {"companies": companies, "total": len(companies)}
