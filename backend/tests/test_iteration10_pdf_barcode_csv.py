"""
Iteration 10 Tests: PDF Import, Post-NIR Barcode Dialog, CSV Import
Tests for ANDREPAU POS - Construction materials shop

Features tested:
1. POST /api/nir/parse-pdf - Parse Romanian invoice PDF (e-Factura format)
2. POST /api/products/bulk-barcode - Bulk update barcodes for products
3. GET /api/products/csv-template - Download CSV template
4. POST /api/products/import-csv - Parse CSV, return preview
5. POST /api/products/import-csv/confirm - Execute CSV import
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://store-checkout-32.preview.emergentagent.com')

# Test credentials
ADMIN_CREDS = {"username": "admin", "password": "admin123"}
CASIER_CREDS = {"username": "casier", "password": "casier123"}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def casier_token():
    """Get casier authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=CASIER_CREDS)
    assert response.status_code == 200, f"Casier login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin auth headers"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def casier_headers(casier_token):
    """Casier auth headers"""
    return {"Authorization": f"Bearer {casier_token}"}


# ==================== PDF PARSING TESTS ====================

class TestPdfParsing:
    """Tests for POST /api/nir/parse-pdf endpoint"""

    def test_parse_pdf_requires_auth(self):
        """PDF parsing requires authentication"""
        with open("/tmp/test_factura.pdf", "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", files=files)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_parse_pdf_requires_admin(self, casier_headers):
        """PDF parsing requires admin role"""
        with open("/tmp/test_factura.pdf", "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", headers=casier_headers, files=files)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_parse_pdf_rejects_non_pdf(self, admin_headers):
        """PDF parsing rejects non-PDF files"""
        fake_file = io.BytesIO(b"This is not a PDF")
        files = {"file": ("test.txt", fake_file, "text/plain")}
        response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", headers=admin_headers, files=files)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    def test_parse_pdf_extracts_4_products(self, admin_headers):
        """PDF parsing extracts exactly 4 products from test invoice"""
        with open("/tmp/test_factura.pdf", "rb") as f:
            files = {"file": ("test_factura.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", headers=admin_headers, files=files)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify total items
        assert data["total_items"] == 4, f"Expected 4 items, got {data['total_items']}"
        assert len(data["items"]) == 4, f"Expected 4 items in list, got {len(data['items'])}"

    def test_parse_pdf_extracts_invoice_number(self, admin_headers):
        """PDF parsing extracts invoice number TOP 26000633"""
        with open("/tmp/test_factura.pdf", "rb") as f:
            files = {"file": ("test_factura.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", headers=admin_headers, files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "TOP 26000633" in data["invoice_number"], f"Expected 'TOP 26000633' in invoice_number, got '{data['invoice_number']}'"

    def test_parse_pdf_extracts_supplier_name(self, admin_headers):
        """PDF parsing extracts supplier name TOP MASTER L.T.D. SRL"""
        with open("/tmp/test_factura.pdf", "rb") as f:
            files = {"file": ("test_factura.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", headers=admin_headers, files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "TOP MASTER" in data["supplier_name"], f"Expected 'TOP MASTER' in supplier_name, got '{data['supplier_name']}'"

    def test_parse_pdf_extracts_correct_product_names(self, admin_headers):
        """PDF parsing extracts correct product names"""
        with open("/tmp/test_factura.pdf", "rb") as f:
            files = {"file": ("test_factura.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", headers=admin_headers, files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        product_names = [item["denumire_pdf"] for item in data["items"]]
        
        # Check for expected products
        assert any("GRUND METAL DK GRI" in name for name in product_names), f"Missing GRUND METAL DK GRI in {product_names}"
        assert any("GRUND METAL DK ROSU OXID" in name for name in product_names), f"Missing GRUND METAL DK ROSU OXID in {product_names}"
        assert any("DILUANT UNIVERSAL 500ML" in name for name in product_names), f"Missing DILUANT UNIVERSAL 500ML in {product_names}"
        assert any("DILUANT UNIVERSAL 900ML" in name for name in product_names), f"Missing DILUANT UNIVERSAL 900ML in {product_names}"

    def test_parse_pdf_extracts_correct_quantities(self, admin_headers):
        """PDF parsing extracts correct quantities"""
        with open("/tmp/test_factura.pdf", "rb") as f:
            files = {"file": ("test_factura.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", headers=admin_headers, files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Expected: GRUND GRI qty=6, GRUND ROSU qty=6, DILUANT 500ML qty=16, DILUANT 900ML qty=12
        quantities = {item["denumire_pdf"]: item["cantitate"] for item in data["items"]}
        
        for name, qty in quantities.items():
            if "GRI" in name or "ROSU" in name:
                assert qty == 6.0, f"Expected qty 6 for {name}, got {qty}"
            elif "500ML" in name:
                assert qty == 16.0, f"Expected qty 16 for {name}, got {qty}"
            elif "900ML" in name:
                assert qty == 12.0, f"Expected qty 12 for {name}, got {qty}"

    def test_parse_pdf_extracts_correct_prices(self, admin_headers):
        """PDF parsing extracts correct unit prices"""
        with open("/tmp/test_factura.pdf", "rb") as f:
            files = {"file": ("test_factura.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/nir/parse-pdf", headers=admin_headers, files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Expected: GRUND price=16.72, DILUANT 500ML price=3.95, DILUANT 900ML price=6.14
        prices = {item["denumire_pdf"]: item["pret_unitar"] for item in data["items"]}
        
        for name, price in prices.items():
            if "GRUND" in name:
                assert abs(price - 16.72) < 0.01, f"Expected price 16.72 for {name}, got {price}"
            elif "500ML" in name:
                assert abs(price - 3.95) < 0.01, f"Expected price 3.95 for {name}, got {price}"
            elif "900ML" in name:
                assert abs(price - 6.14) < 0.01, f"Expected price 6.14 for {name}, got {price}"


# ==================== BULK BARCODE UPDATE TESTS ====================

class TestBulkBarcodeUpdate:
    """Tests for POST /api/products/bulk-barcode endpoint"""

    def test_bulk_barcode_requires_auth(self):
        """Bulk barcode update requires authentication"""
        response = requests.post(f"{BASE_URL}/api/products/bulk-barcode", json={"updates": []})
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_bulk_barcode_requires_admin(self, casier_headers):
        """Bulk barcode update requires admin role"""
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-barcode",
            headers=casier_headers,
            json={"updates": []}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_bulk_barcode_rejects_empty_updates(self, admin_headers):
        """Bulk barcode update rejects empty updates list"""
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-barcode",
            headers=admin_headers,
            json={"updates": []}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    def test_bulk_barcode_updates_products(self, admin_headers):
        """Bulk barcode update successfully updates product barcodes"""
        # First, create a test product
        product_data = {
            "nume": "TEST_BARCODE_PRODUCT",
            "categorie": "Materiale Construcții",
            "pret_vanzare": 10.0,
            "stoc": 100,
            "stoc_minim": 5
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/products",
            headers={**admin_headers, "Content-Type": "application/json"},
            json=product_data
        )
        assert create_resp.status_code == 200, f"Failed to create test product: {create_resp.text}"
        product_id = create_resp.json()["id"]
        
        try:
            # Update barcode
            test_barcode = "1234567890123"
            response = requests.post(
                f"{BASE_URL}/api/products/bulk-barcode",
                headers={**admin_headers, "Content-Type": "application/json"},
                json={"updates": [{"product_id": product_id, "cod_bare": test_barcode}]}
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert data["updated"] >= 1, f"Expected at least 1 update, got {data['updated']}"
            
            # Verify barcode was updated
            get_resp = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=admin_headers)
            assert get_resp.status_code == 200
            assert get_resp.json()["cod_bare"] == test_barcode
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/products/{product_id}", headers=admin_headers)


# ==================== CSV TEMPLATE TESTS ====================

class TestCsvTemplate:
    """Tests for GET /api/products/csv-template endpoint"""

    def test_csv_template_requires_auth(self):
        """CSV template download requires authentication"""
        response = requests.get(f"{BASE_URL}/api/products/csv-template")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_csv_template_requires_admin(self, casier_headers):
        """CSV template download requires admin role"""
        response = requests.get(f"{BASE_URL}/api/products/csv-template", headers=casier_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_csv_template_returns_csv(self, admin_headers):
        """CSV template returns valid CSV file"""
        response = requests.get(f"{BASE_URL}/api/products/csv-template", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/csv" in response.headers.get("content-type", ""), "Expected CSV content type"
        
        # Check content has expected headers
        content = response.text
        assert "Denumire" in content, "Missing 'Denumire' header"
        assert "Categorie" in content, "Missing 'Categorie' header"
        assert "Pret Vanzare" in content, "Missing 'Pret Vanzare' header"


# ==================== CSV IMPORT TESTS ====================

class TestCsvImport:
    """Tests for POST /api/products/import-csv endpoint"""

    def test_csv_import_requires_auth(self):
        """CSV import requires authentication"""
        csv_content = "Denumire,Categorie,Pret Vanzare\nTest,Test,10"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = requests.post(f"{BASE_URL}/api/products/import-csv", files=files)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_csv_import_requires_admin(self, casier_headers):
        """CSV import requires admin role"""
        csv_content = "Denumire,Categorie,Pret Vanzare\nTest,Test,10"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = requests.post(f"{BASE_URL}/api/products/import-csv", headers=casier_headers, files=files)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_csv_import_rejects_non_csv(self, admin_headers):
        """CSV import rejects non-CSV files"""
        files = {"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")}
        response = requests.post(f"{BASE_URL}/api/products/import-csv", headers=admin_headers, files=files)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    def test_csv_import_parses_valid_csv(self, admin_headers):
        """CSV import parses valid CSV and returns preview"""
        csv_content = """Denumire,Categorie,Cod Bare,Pret Achizitie,Pret Vanzare,TVA %,Unitate,Stoc,Stoc Minim
TEST_CSV_PRODUCT_1,Materiale Construcții,1111111111111,10.00,15.00,19,buc,50,5
TEST_CSV_PRODUCT_2,Vopsele,2222222222222,20.00,30.00,19,litru,100,10"""
        
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8-sig')), "text/csv")}
        response = requests.post(f"{BASE_URL}/api/products/import-csv", headers=admin_headers, files=files)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["total_parsed"] == 2, f"Expected 2 parsed items, got {data['total_parsed']}"
        assert len(data["items"]) == 2, f"Expected 2 items, got {len(data['items'])}"
        
        # Check first item
        item1 = data["items"][0]
        assert item1["nume"] == "TEST_CSV_PRODUCT_1"
        assert item1["categorie"] == "Materiale Construcții"
        assert item1["pret_vanzare"] == 15.0
        assert item1["action"] == "create"  # New product

    def test_csv_import_handles_semicolon_delimiter(self, admin_headers):
        """CSV import handles semicolon delimiter (European format)"""
        csv_content = """Denumire;Categorie;Pret Vanzare
TEST_SEMICOLON_PRODUCT;Feronerie;25.50"""
        
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8-sig')), "text/csv")}
        response = requests.post(f"{BASE_URL}/api/products/import-csv", headers=admin_headers, files=files)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["total_parsed"] == 1, f"Expected 1 parsed item, got {data['total_parsed']}"


# ==================== CSV IMPORT CONFIRM TESTS ====================

class TestCsvImportConfirm:
    """Tests for POST /api/products/import-csv/confirm endpoint"""

    def test_csv_confirm_requires_auth(self):
        """CSV import confirm requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            json={"items": []}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_csv_confirm_requires_admin(self, casier_headers):
        """CSV import confirm requires admin role"""
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            headers=casier_headers,
            json={"items": []}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_csv_confirm_rejects_empty_items(self, admin_headers):
        """CSV import confirm rejects empty items list"""
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            headers={**admin_headers, "Content-Type": "application/json"},
            json={"items": []}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    def test_csv_confirm_creates_products(self, admin_headers):
        """CSV import confirm creates new products"""
        items = [{
            "nume": "TEST_CSV_CONFIRM_PRODUCT",
            "categorie": "Consumabile",
            "cod_bare": "9999999999999",
            "pret_achizitie": 5.0,
            "pret_vanzare": 10.0,
            "tva": 19,
            "unitate": "buc",
            "stoc": 50,
            "stoc_minim": 5,
            "action": "create"
        }]
        
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            headers={**admin_headers, "Content-Type": "application/json"},
            json={"items": items}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["created"] >= 1, f"Expected at least 1 created, got {data['created']}"
        
        # Cleanup - find and delete the test product
        search_resp = requests.get(
            f"{BASE_URL}/api/products?search=TEST_CSV_CONFIRM_PRODUCT",
            headers=admin_headers
        )
        if search_resp.status_code == 200:
            products = search_resp.json().get("products", [])
            for p in products:
                if p["nume"] == "TEST_CSV_CONFIRM_PRODUCT":
                    requests.delete(f"{BASE_URL}/api/products/{p['id']}", headers=admin_headers)


# ==================== NIR CREATION AND BARCODE FLOW TESTS ====================

class TestNirAndBarcodeFlow:
    """Tests for NIR creation and post-NIR barcode update flow"""

    def test_nir_creation_flow(self, admin_headers):
        """Test complete NIR creation flow"""
        # First, get suppliers
        suppliers_resp = requests.get(f"{BASE_URL}/api/suppliers", headers=admin_headers)
        assert suppliers_resp.status_code == 200
        suppliers = suppliers_resp.json()
        
        if not suppliers:
            # Create a test supplier
            supplier_resp = requests.post(
                f"{BASE_URL}/api/suppliers",
                headers={**admin_headers, "Content-Type": "application/json"},
                json={"nume": "TEST_SUPPLIER_NIR"}
            )
            assert supplier_resp.status_code == 200
            supplier_id = supplier_resp.json()["id"]
        else:
            supplier_id = suppliers[0]["id"]
        
        # Get products
        products_resp = requests.get(f"{BASE_URL}/api/products", headers=admin_headers)
        assert products_resp.status_code == 200
        products = products_resp.json().get("products", [])
        
        if not products:
            pytest.skip("No products available for NIR test")
        
        product = products[0]
        initial_stock = product["stoc"]
        
        # Create NIR
        nir_data = {
            "furnizor_id": supplier_id,
            "numar_factura": "TEST-NIR-001",
            "items": [{
                "product_id": product["id"],
                "nume": product["nume"],
                "cantitate": 10,
                "pret_achizitie": 5.0
            }],
            "total": 50.0
        }
        
        nir_resp = requests.post(
            f"{BASE_URL}/api/nir",
            headers={**admin_headers, "Content-Type": "application/json"},
            json=nir_data
        )
        
        assert nir_resp.status_code == 200, f"NIR creation failed: {nir_resp.text}"
        nir = nir_resp.json()
        assert "numar_nir" in nir
        
        # Verify stock was updated
        updated_product_resp = requests.get(f"{BASE_URL}/api/products/{product['id']}", headers=admin_headers)
        assert updated_product_resp.status_code == 200
        updated_stock = updated_product_resp.json()["stoc"]
        assert updated_stock == initial_stock + 10, f"Stock not updated correctly: expected {initial_stock + 10}, got {updated_stock}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
