"""
Iteration 16 Backend Tests
Covers:
- POST /api/sales -> product updated_at set on stock decrement
- GET /api/sync/sales-since (no auth, ?since filter)
- POST /api/sync/apply-remote-sales (sync_secret, dedupe, stock decrement)
- POST /api/sync/receive (still works, updated_at on decrement)
- POST /api/sync/products/push (no stoc overwrite on update, stoc on new insert)
- POST /api/nir/parse-pdf (TOP_2026001074.pdf -> 12 items with pret_vanzare)
- POST /api/nir/from-pdf (pret_vanzare accepted; existing name kept)
- POST /api/products/bulk-barcode (merge logic)
- Auth still works (admin/admin123)
"""
import os
import time
import uuid
import asyncio
import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


def _get_product_raw(product_id):
    """Fetch product directly from Mongo to access fields not exposed via API (e.g. updated_at)."""
    async def _run():
        client = AsyncIOMotorClient(MONGO_URL)
        try:
            return await client[DB_NAME].products.find_one({"id": product_id}, {"_id": 0})
        finally:
            client.close()
    return asyncio.run(_run())

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://offline-retail-hub-4.preview.emergentagent.com").rstrip("/")
SYNC_SECRET = "andrepau-sync-2026"
API = f"{BASE_URL}/api"

PDF_URL = "https://customer-assets.emergentagent.com/job_ad0f20f7-cab4-4afd-b37e-39b6879f80b6/artifacts/ukck0e9d_TOP_2026001074.pdf"
PDF_LOCAL = "/tmp/TOP_2026001074.pdf"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=15)
    assert r.status_code == 200, f"Auth failed: {r.status_code} {r.text}"
    token = r.json().get("access_token") or r.json().get("token")
    assert token, f"No token in response: {r.json()}"
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def test_product(admin_headers):
    """Create a product we can use to test sales/stock updates."""
    payload = {
        "nume": f"TEST_SYNC_PROD_{uuid.uuid4().hex[:6]}",
        "categorie": "TEST",
        "cod_bare": f"TEST{uuid.uuid4().hex[:10]}",
        "pret_achizitie": 10.0,
        "pret_vanzare": 20.0,
        "tva": 19,
        "unitate": "buc",
        "stoc": 100,
        "stoc_minim": 5,
        "descriere": "test product",
        "furnizor_id": None,
    }
    r = requests.post(f"{API}/products", json=payload, headers=admin_headers, timeout=10)
    assert r.status_code == 200, f"Create product failed: {r.status_code} {r.text}"
    prod = r.json()
    yield prod
    # cleanup
    requests.delete(f"{API}/products/{prod['id']}", headers=admin_headers, timeout=10)


@pytest.fixture(scope="module")
def test_pdf_bytes():
    """Download test PDF once for the module."""
    if not os.path.exists(PDF_LOCAL):
        r = requests.get(PDF_URL, timeout=30)
        assert r.status_code == 200
        with open(PDF_LOCAL, "wb") as f:
            f.write(r.content)
    with open(PDF_LOCAL, "rb") as f:
        return f.read()


# ============= AUTH =============
class TestAuth:
    def test_login_admin(self):
        r = requests.post(f"{API}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("access_token") or data.get("token")


# ============= SALES: updated_at on stock decrement =============
class TestSalesStockUpdatedAt:
    def test_create_sale_sets_product_updated_at(self, admin_headers, test_product):
        # get current updated_at
        r0 = requests.get(f"{API}/products/{test_product['id']}", headers=admin_headers, timeout=10)
        assert r0.status_code == 200
        before_updated_at = r0.json().get("updated_at")
        stoc_before = r0.json().get("stoc", 0)

        time.sleep(1)  # ensure timestamp diff

        txn_id = f"TEST_TXN_{uuid.uuid4().hex[:10]}"
        sale = {
            "items": [{
                "product_id": test_product["id"],
                "nume": test_product["nume"],
                "cantitate": 2,
                "pret_unitar": test_product["pret_vanzare"],
                "tva": 19,
                "total": 40.0,
            }],
            "subtotal": 40.0,
            "tva_total": 0.0,
            "total": 40.0,
            "metoda_plata": "numerar",
            "suma_numerar": 40.0,
            "suma_card": 0.0,
            "discount_percent": 0,
            "casier_id": "admin",
            "fiscal_status": "none",
            "transaction_id": txn_id,
        }
        rs = requests.post(f"{API}/sales", json=sale, headers=admin_headers, timeout=10)
        assert rs.status_code == 200, rs.text

        r1 = requests.get(f"{API}/products/{test_product['id']}", headers=admin_headers, timeout=10)
        assert r1.status_code == 200
        after = r1.json()
        assert after.get("stoc") == stoc_before - 2, f"Stock not decremented: {after.get('stoc')}"
        raw = _get_product_raw(test_product["id"])
        assert raw and raw.get("updated_at"), "updated_at not set after sale (raw DB check)"


# ============= SYNC: sales-since & apply-remote-sales =============
class TestSyncSalesSince:
    def test_sales_since_no_auth(self):
        r = requests.get(f"{API}/sync/sales-since", timeout=10)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "sales" in data and "count" in data
        assert isinstance(data["sales"], list)

    def test_sales_since_with_future_filter(self):
        future = "2099-01-01T00:00:00+00:00"
        r = requests.get(f"{API}/sync/sales-since", params={"since": future}, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 0

    def test_sales_since_with_past_filter(self):
        past = "2000-01-01T00:00:00+00:00"
        r = requests.get(f"{API}/sync/sales-since", params={"since": past}, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["sales"], list)


class TestApplyRemoteSales:
    def test_invalid_secret(self):
        r = requests.post(f"{API}/sync/apply-remote-sales", json={"sync_secret": "wrong", "sales": []}, timeout=10)
        assert r.status_code == 401

    def test_empty_sales(self):
        r = requests.post(f"{API}/sync/apply-remote-sales", json={"sync_secret": SYNC_SECRET, "sales": []}, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data == {"applied": 0, "skipped": 0}

    def test_apply_decrements_stock_and_skips_duplicate(self, admin_headers, test_product):
        # Get current stock
        r0 = requests.get(f"{API}/products/{test_product['id']}", headers=admin_headers, timeout=10)
        stoc_before = r0.json().get("stoc", 0)

        sale_id = f"TEST_RS_{uuid.uuid4().hex[:8]}"
        txn_id = f"TEST_RS_TXN_{uuid.uuid4().hex[:10]}"
        remote_sale = {
            "id": sale_id,
            "transaction_id": txn_id,
            "numar_bon": "BON-TEST-REMOTE-001",
            "items": [{
                "product_id": test_product["id"],
                "nume": test_product["nume"],
                "cantitate": 3,
                "pret_unitar": 20.0,
                "tva": 19,
                "total": 60.0,
            }],
            "subtotal": 60.0, "tva_total": 0, "total": 60.0,
            "metoda_plata": "numerar", "suma_numerar": 60.0, "suma_card": 0,
            "discount_percent": 0, "casier_id": "admin", "fiscal_status": "none",
            "created_at": "2026-04-20T10:00:00+00:00",
        }
        r1 = requests.post(f"{API}/sync/apply-remote-sales",
                           json={"sync_secret": SYNC_SECRET, "sales": [remote_sale]}, timeout=15)
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert d1["applied"] == 1, d1
        assert d1["skipped"] == 0

        # Verify stock decremented + updated_at set
        r2 = requests.get(f"{API}/products/{test_product['id']}", headers=admin_headers, timeout=10)
        after = r2.json()
        assert after.get("stoc") == stoc_before - 3, f"{after.get('stoc')} vs {stoc_before - 3}"
        raw = _get_product_raw(test_product["id"])
        assert raw and raw.get("updated_at"), "updated_at missing after remote sale apply (raw DB)"

        # Duplicate detection by transaction_id
        r3 = requests.post(f"{API}/sync/apply-remote-sales",
                           json={"sync_secret": SYNC_SECRET, "sales": [remote_sale]}, timeout=10)
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3["skipped"] == 1 and d3["applied"] == 0

        # Duplicate by id (no txn_id on duplicate payload)
        dup_by_id = dict(remote_sale)
        dup_by_id.pop("transaction_id", None)
        r4 = requests.post(f"{API}/sync/apply-remote-sales",
                           json={"sync_secret": SYNC_SECRET, "sales": [dup_by_id]}, timeout=10)
        assert r4.status_code == 200
        d4 = r4.json()
        assert d4["skipped"] == 1 and d4["applied"] == 0


# ============= SYNC: receive still works with stock decrement =============
class TestSyncReceive:
    def test_receive_invalid_secret(self):
        r = requests.post(f"{API}/sync/receive", json={"sync_secret": "nope", "sales": []}, timeout=10)
        assert r.status_code == 401

    def test_receive_decrements_stock_and_sets_updated_at(self, admin_headers, test_product):
        r0 = requests.get(f"{API}/products/{test_product['id']}", headers=admin_headers, timeout=10)
        stoc_before = r0.json().get("stoc", 0)

        txn_id = f"TEST_RCV_TXN_{uuid.uuid4().hex[:10]}"
        sale = {
            "id": f"TEST_RCV_{uuid.uuid4().hex[:8]}",
            "transaction_id": txn_id,
            "numar_bon": "BON-TEST-RCV-001",
            "items": [{
                "product_id": test_product["id"],
                "nume": test_product["nume"],
                "cantitate": 1,
                "pret_unitar": 20.0,
                "tva": 19, "total": 20.0,
            }],
            "total": 20.0, "metoda_plata": "numerar",
            "casier_id": "admin", "fiscal_status": "none",
            "created_at": "2026-04-20T10:30:00+00:00",
        }
        r = requests.post(f"{API}/sync/receive",
                          json={"sync_secret": SYNC_SECRET, "sales": [sale]}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["received"] == 1

        r2 = requests.get(f"{API}/products/{test_product['id']}", headers=admin_headers, timeout=10)
        after = r2.json()
        assert after.get("stoc") == stoc_before - 1
        raw = _get_product_raw(test_product["id"])
        assert raw and raw.get("updated_at"), "updated_at missing after sync/receive (raw DB)"


# ============= SYNC: products/push -> no stoc overwrite on update =============
class TestProductsPushNoStocOverwrite:
    def test_existing_product_stoc_not_overwritten(self, admin_headers, test_product):
        """When pushing an existing product, 'stoc' must NOT be copied."""
        # Confirm current stock
        r0 = requests.get(f"{API}/products/{test_product['id']}", headers=admin_headers, timeout=10)
        current_stoc = r0.json().get("stoc", 0)

        # Push with a different stoc and newer updated_at -> stoc should NOT change
        future_ts = "2099-12-31T23:59:59+00:00"
        pushed = dict(r0.json())
        pushed.pop("_id", None)
        pushed["stoc"] = 99999  # must be ignored
        pushed["pret_vanzare"] = 77.77  # should update
        pushed["updated_at"] = future_ts

        r = requests.post(f"{API}/sync/products/push",
                          json={"sync_secret": SYNC_SECRET, "products": [pushed]}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["updated"] >= 1

        r2 = requests.get(f"{API}/products/{test_product['id']}", headers=admin_headers, timeout=10)
        after = r2.json()
        assert after["stoc"] == current_stoc, f"stoc was overwritten! {after['stoc']} != {current_stoc}"
        assert abs(after["pret_vanzare"] - 77.77) < 0.01

    def test_new_product_gets_stoc_on_insert(self, admin_headers):
        new_id = str(uuid.uuid4())
        prod = {
            "id": new_id,
            "nume": f"TEST_SYNC_NEW_{uuid.uuid4().hex[:6]}",
            "categorie": "TEST",
            "cod_bare": f"TESTN{uuid.uuid4().hex[:10]}",
            "pret_achizitie": 5.0,
            "pret_vanzare": 15.0,
            "tva": 19,
            "unitate": "buc",
            "stoc": 42,
            "stoc_minim": 5,
            "descriere": "", "furnizor_id": None,
            "created_at": "2026-04-20T10:00:00+00:00",
            "updated_at": "2026-04-20T10:00:00+00:00",
        }
        r = requests.post(f"{API}/sync/products/push",
                          json={"sync_secret": SYNC_SECRET, "products": [prod]}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["added"] == 1

        r2 = requests.get(f"{API}/products/{new_id}", headers=admin_headers, timeout=10)
        assert r2.status_code == 200
        assert r2.json()["stoc"] == 42

        # cleanup
        requests.delete(f"{API}/products/{new_id}", headers=admin_headers, timeout=10)


# ============= NIR: parse-pdf (TOP_2026001074) =============
class TestNirParsePdf:
    def test_parse_returns_12_items_with_pret_vanzare(self, admin_headers, test_pdf_bytes):
        files = {"file": ("TOP_2026001074.pdf", test_pdf_bytes, "application/pdf")}
        r = requests.post(f"{API}/nir/parse-pdf", files=files, headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        items = data.get("items", [])
        assert len(items) == 12, f"Expected 12 items, got {len(items)}: {items}"

        # Check pret_unitar values exist and include expected vanzare prices
        prices = [float(it.get("pret_unitar", 0)) for it in items]
        # Must contain pret_vanzare values (not lower achizitie values)
        for expected in [25.00, 60.00, 41.00]:
            assert any(abs(p - expected) < 0.5 for p in prices), \
                f"Expected price ~{expected} missing. Got: {prices}"

        # Sanity: every item has a name (denumire_pdf from matcher) + cantitate + pret_unitar
        for it in items:
            assert it.get("denumire") or it.get("denumire_pdf"), f"Missing name in item: {it}"
            assert float(it.get("cantitate", 0)) > 0
            assert float(it.get("pret_unitar", 0)) > 0


# ============= NIR: from-pdf =============
class TestNirFromPdf:
    def test_new_product_uses_pret_vanzare_directly(self, admin_headers):
        # Create supplier first
        supplier = {"nume": f"TEST_SUP_{uuid.uuid4().hex[:6]}", "cui": "RO123", "adresa": "x"}
        rs = requests.post(f"{API}/suppliers", json=supplier, headers=admin_headers, timeout=10)
        assert rs.status_code == 200, rs.text
        supp_id = rs.json()["id"]

        try:
            uniq_name = f"TEST_NIR_PROD_{uuid.uuid4().hex[:6]}"
            payload = {
                "furnizor_id": supp_id,
                "numar_factura": f"TEST-{uuid.uuid4().hex[:6]}",
                "items": [{
                    "denumire": uniq_name,
                    "cantitate": 5,
                    "pret_vanzare": 50.0,
                    "um": "buc"
                }],
            }
            r = requests.post(f"{API}/nir/from-pdf", json=payload, headers=admin_headers, timeout=15)
            assert r.status_code == 200, r.text
            out = r.json()
            assert out["products_created_count"] == 1

            # Search product by name
            rp = requests.get(f"{API}/products", params={"search": uniq_name},
                              headers=admin_headers, timeout=10)
            products = rp.json().get("products", [])
            match = next((p for p in products if p["nume"] == uniq_name), None)
            assert match, f"Product not found: {uniq_name}"
            # pret_vanzare from PDF directly (no markup)
            assert abs(match["pret_vanzare"] - 50.0) < 0.01, \
                f"Expected pret_vanzare=50.0, got {match['pret_vanzare']}"
            assert match["stoc"] == 5

            prod_id = match["id"]
        finally:
            # cleanup supplier (suppresses errors)
            requests.delete(f"{API}/suppliers/{supp_id}", headers=admin_headers, timeout=10)

        # Now add another NIR targeting this existing product with different name -> name should be preserved
        try:
            supplier2 = {"nume": f"TEST_SUP2_{uuid.uuid4().hex[:6]}", "cui": "RO124", "adresa": "y"}
            rs2 = requests.post(f"{API}/suppliers", json=supplier2, headers=admin_headers, timeout=10)
            supp_id2 = rs2.json()["id"]
            payload2 = {
                "furnizor_id": supp_id2,
                "numar_factura": f"TEST-{uuid.uuid4().hex[:6]}",
                "items": [{
                    "product_id": prod_id,
                    "denumire": "DIFFERENT NAME SHOULD NOT OVERWRITE",
                    "cantitate": 3,
                    "pret_vanzare": 77.0,
                    "um": "buc"
                }],
            }
            r2 = requests.post(f"{API}/nir/from-pdf", json=payload2, headers=admin_headers, timeout=15)
            assert r2.status_code == 200, r2.text
            assert r2.json()["products_updated_count"] == 1

            rp2 = requests.get(f"{API}/products/{prod_id}", headers=admin_headers, timeout=10)
            prod2 = rp2.json()
            assert prod2["nume"] == uniq_name, f"Name overwritten! {prod2['nume']}"
            assert prod2["stoc"] == 8, f"Stock not incremented: {prod2['stoc']}"
            assert abs(prod2["pret_vanzare"] - 77.0) < 0.01, \
                f"pret_vanzare not updated: {prod2['pret_vanzare']}"
        finally:
            requests.delete(f"{API}/products/{prod_id}", headers=admin_headers, timeout=10)
            requests.delete(f"{API}/suppliers/{supp_id2}", headers=admin_headers, timeout=10)


# ============= Products: bulk-barcode MERGE =============
class TestBulkBarcodeMerge:
    def test_merge_when_barcode_exists_on_another_product(self, admin_headers):
        # Create two products: A has barcode 'XYZ', B has no barcode
        barcode = f"MERGETEST{uuid.uuid4().hex[:10]}"
        prodA = {
            "nume": f"TEST_MERGE_A_{uuid.uuid4().hex[:6]}",
            "categorie": "TEST", "cod_bare": barcode,
            "pret_achizitie": 5, "pret_vanzare": 10,
            "tva": 19, "unitate": "buc",
            "stoc": 50, "stoc_minim": 5,
            "descriere": "", "furnizor_id": None,
        }
        prodB = dict(prodA)
        prodB["nume"] = f"TEST_MERGE_B_{uuid.uuid4().hex[:6]}"
        prodB["cod_bare"] = ""
        prodB["stoc"] = 20

        ra = requests.post(f"{API}/products", json=prodA, headers=admin_headers, timeout=10)
        rb = requests.post(f"{API}/products", json=prodB, headers=admin_headers, timeout=10)
        assert ra.status_code == 200 and rb.status_code == 200
        idA = ra.json()["id"]
        idB = rb.json()["id"]

        try:
            # Apply barcode from A on product B -> B should merge INTO A
            r = requests.post(f"{API}/products/bulk-barcode",
                              json={"updates": [{"product_id": idB, "cod_bare": barcode}]},
                              headers=admin_headers, timeout=15)
            assert r.status_code == 200, r.text
            out = r.json()
            assert out.get("merged") == 1, out
            assert "merge_details" in out
            assert len(out["merge_details"]) == 1
            detail = out["merge_details"][0]
            assert detail.get("stoc_transferat") == 20

            # B should be deleted
            rb2 = requests.get(f"{API}/products/{idB}", headers=admin_headers, timeout=10)
            assert rb2.status_code == 404

            # A should have stock 70
            ra2 = requests.get(f"{API}/products/{idA}", headers=admin_headers, timeout=10)
            assert ra2.status_code == 200
            assert ra2.json()["stoc"] == 70
        finally:
            requests.delete(f"{API}/products/{idA}", headers=admin_headers, timeout=10)
            requests.delete(f"{API}/products/{idB}", headers=admin_headers, timeout=10)

    def test_normal_update_when_barcode_unique(self, admin_headers):
        barcode = f"UNIQ{uuid.uuid4().hex[:10]}"
        prod = {
            "nume": f"TEST_BC_UNIQ_{uuid.uuid4().hex[:6]}",
            "categorie": "TEST", "cod_bare": "",
            "pret_achizitie": 5, "pret_vanzare": 10,
            "tva": 19, "unitate": "buc",
            "stoc": 10, "stoc_minim": 5,
            "descriere": "", "furnizor_id": None,
        }
        rp = requests.post(f"{API}/products", json=prod, headers=admin_headers, timeout=10)
        assert rp.status_code == 200
        pid = rp.json()["id"]
        try:
            r = requests.post(f"{API}/products/bulk-barcode",
                              json={"updates": [{"product_id": pid, "cod_bare": barcode}]},
                              headers=admin_headers, timeout=10)
            assert r.status_code == 200
            out = r.json()
            assert out.get("updated") == 1
            assert out.get("merged") == 0

            r2 = requests.get(f"{API}/products/{pid}", headers=admin_headers, timeout=10)
            assert r2.json()["cod_bare"] == barcode
        finally:
            requests.delete(f"{API}/products/{pid}", headers=admin_headers, timeout=10)
