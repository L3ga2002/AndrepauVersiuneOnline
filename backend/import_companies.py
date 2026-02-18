#!/usr/bin/env python3
"""
Import Romanian companies from data.gov.ro CSV into MongoDB
Uses simple insert_many for faster processing
"""

import csv
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "andrepau_pos")

async def import_companies():
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Drop existing collection and create fresh
    await db.romania_companies.drop()
    
    # Create indexes
    await db.romania_companies.create_index("cui", unique=True)
    await db.romania_companies.create_index("denumire")
    
    print("Starting import from od_firme.csv...")
    
    batch = []
    batch_size = 5000
    total_imported = 0
    skipped = 0
    seen_cui = set()
    
    with open('od_firme.csv', 'r', encoding='utf-8-sig') as f:
        # CSV uses ^ as delimiter
        reader = csv.DictReader(f, delimiter='^')
        
        for row in reader:
            try:
                cui = row.get('CUI', '')
                if cui is None:
                    continue
                cui = str(cui).strip()
                
                # Skip companies without valid CUI
                if not cui or cui == '0' or not cui.isdigit() or len(cui) > 10:
                    skipped += 1
                    continue
                
                # Skip duplicates
                if cui in seen_cui:
                    skipped += 1
                    continue
                seen_cui.add(cui)
                
                # Build address
                address_parts = []
                street = row.get('ADR_DEN_STRADA', '') or ''
                nr = row.get('ADR_NR_STRADA', '') or ''
                if street.strip():
                    if nr.strip() and nr.strip() != '0':
                        address_parts.append(f"{street.strip()} {nr.strip()}")
                    else:
                        address_parts.append(street.strip())
                        
                bloc = row.get('ADR_BLOC', '') or ''
                if bloc.strip():
                    address_parts.append(f"Bl. {bloc.strip()}")
                    
                localitate = row.get('ADR_LOCALITATE', '') or ''
                if localitate.strip():
                    address_parts.append(localitate.strip())
                    
                judet = row.get('ADR_JUDET', '') or ''
                if judet.strip():
                    address_parts.append(f"Jud. {judet.strip()}")
                
                company = {
                    "cui": cui,
                    "denumire": (row.get('DENUMIRE', '') or '').strip(),
                    "nr_reg_com": (row.get('COD_INMATRICULARE', '') or '').strip(),
                    "adresa": ", ".join(address_parts),
                    "localitate": localitate.strip() if localitate else '',
                    "judet": judet.strip() if judet else '',
                    "cod_postal": (row.get('ADR_COD_POSTAL', '') or '').strip(),
                    "source": "onrc"
                }
                
                batch.append(company)
                
                if len(batch) >= batch_size:
                    try:
                        await db.romania_companies.insert_many(batch, ordered=False)
                        total_imported += len(batch)
                    except Exception as e:
                        # Count successful inserts
                        total_imported += len(batch)
                    
                    batch = []
                    print(f"Importat {total_imported:,} firme... (sărit {skipped:,})", end='\r')
                    
            except Exception as e:
                skipped += 1
                continue
    
    # Import remaining batch
    if batch:
        try:
            await db.romania_companies.insert_many(batch, ordered=False)
            total_imported += len(batch)
        except Exception:
            total_imported += len(batch)
    
    # Get final count
    final_count = await db.romania_companies.count_documents({})
    
    print(f"\n\n✅ Import complet!")
    print(f"   Total firme în bază: {final_count:,}")
    print(f"   Sărite (fără CUI valid/duplicate): {skipped:,}")
    
    # Test search
    test = await db.romania_companies.find_one({"cui": "18189442"})
    if test:
        print(f"\n   Test căutare CUI 18189442: {test.get('denumire', 'N/A')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(import_companies())
