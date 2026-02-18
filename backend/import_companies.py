#!/usr/bin/env python3
"""
Import Romanian companies from data.gov.ro CSV into MongoDB
Only imports active companies (with valid CUI) for faster search
"""

import csv
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import sys

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "andrepau_pos")

async def import_companies():
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Create index on CUI for fast lookup
    await db.romania_companies.create_index("cui", unique=True, sparse=True)
    await db.romania_companies.create_index("denumire")
    
    print("Starting import...")
    
    batch = []
    batch_size = 10000
    total_imported = 0
    skipped = 0
    
    with open('od_firme.csv', 'r', encoding='utf-8-sig') as f:
        # CSV uses ^ as delimiter
        reader = csv.DictReader(f, delimiter='^')
        
        for row in reader:
            cui = row.get('CUI', '').strip()
            
            # Skip companies without valid CUI (associations, individual enterprises with CUI=0)
            if not cui or cui == '0' or not cui.isdigit():
                skipped += 1
                continue
            
            # Build address
            address_parts = []
            if row.get('ADR_DEN_STRADA'):
                street = row.get('ADR_DEN_STRADA', '').strip()
                nr = row.get('ADR_NR_STRADA', '').strip()
                if nr and nr != '0':
                    address_parts.append(f"{street} {nr}")
                else:
                    address_parts.append(street)
            if row.get('ADR_BLOC') and row['ADR_BLOC'].strip():
                address_parts.append(f"Bl. {row['ADR_BLOC'].strip()}")
            if row.get('ADR_LOCALITATE'):
                address_parts.append(row['ADR_LOCALITATE'].strip())
            if row.get('ADR_JUDET'):
                address_parts.append(f"Jud. {row['ADR_JUDET'].strip()}")
            
            company = {
                "cui": cui,
                "denumire": row.get('DENUMIRE', '').strip(),
                "nr_reg_com": row.get('COD_INMATRICULARE', '').strip(),
                "adresa": ", ".join(address_parts),
                "localitate": row.get('ADR_LOCALITATE', '').strip(),
                "judet": row.get('ADR_JUDET', '').strip(),
                "cod_postal": row.get('ADR_COD_POSTAL', '').strip(),
                "forma_juridica": row.get('FORMA_JURIDICA', '').strip(),
                "data_inmatriculare": row.get('DATA_INMATRICULARE', '').strip(),
                "source": "onrc",
                "imported_at": datetime.now(timezone.utc)
            }
            
            batch.append(company)
            
            if len(batch) >= batch_size:
                # Bulk insert with upsert
                operations = [
                    {
                        "updateOne": {
                            "filter": {"cui": c["cui"]},
                            "update": {"$set": c},
                            "upsert": True
                        }
                    }
                    for c in batch
                ]
                
                try:
                    result = await db.romania_companies.bulk_write(operations, ordered=False)
                    total_imported += result.upserted_count + result.modified_count
                except Exception as e:
                    print(f"Batch error: {e}")
                
                batch = []
                print(f"Imported {total_imported:,} companies... (skipped {skipped:,})", end='\r')
    
    # Import remaining batch
    if batch:
        operations = [
            {
                "updateOne": {
                    "filter": {"cui": c["cui"]},
                    "update": {"$set": c},
                    "upsert": True
                }
            }
            for c in batch
        ]
        try:
            result = await db.romania_companies.bulk_write(operations, ordered=False)
            total_imported += result.upserted_count + result.modified_count
        except Exception as e:
            print(f"Final batch error: {e}")
    
    # Get final count
    final_count = await db.romania_companies.count_documents({})
    
    print(f"\n\n✅ Import complet!")
    print(f"   Total firme importate: {final_count:,}")
    print(f"   Sărite (fără CUI valid): {skipped:,}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(import_companies())
