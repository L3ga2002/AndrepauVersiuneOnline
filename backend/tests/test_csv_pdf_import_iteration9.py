"""
Iteration 9: Test CSV Import and PDF Import features for ANDREPAU POS
Tests:
- POST /api/products/csv-template - Download CSV template
- POST /api/products/import-csv - Upload CSV file, parse and preview
- POST /api/products/import-csv/confirm - Confirm and execute CSV import
- POST /api/nir/parse-pdf - Upload PDF, parse invoice, extract items
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Get authentication token for tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in login response"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def casier_token(self):
        """Login as casier and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "casier",
            "password": "casier123"
        })
        assert response.status_code == 200, f"Casier login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in login response"
        return data["token"]


class TestCSVTemplate(TestAuth):
    """Test CSV template download endpoint"""
    
    def test_csv_template_requires_auth(self):
        """CSV template endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/products/csv-template")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: CSV template requires authentication")
    
    def test_csv_template_requires_admin(self, casier_token):
        """CSV template endpoint requires admin role"""
        response = requests.get(
            f"{BASE_URL}/api/products/csv-template",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 403, f"Expected 403 for casier, got {response.status_code}"
        print("PASS: CSV template requires admin role")
    
    def test_csv_template_download(self, admin_token):
        """Admin can download CSV template"""
        response = requests.get(
            f"{BASE_URL}/api/products/csv-template",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        assert 'text/csv' in content_type, f"Expected text/csv, got {content_type}"
        
        # Check content disposition
        content_disp = response.headers.get('content-disposition', '')
        assert 'attachment' in content_disp, f"Expected attachment, got {content_disp}"
        assert 'template_import_produse.csv' in content_disp, f"Expected filename in header"
        
        # Check CSV content has headers
        content = response.content.decode('utf-8-sig')
        assert 'Denumire' in content, "Missing 'Denumire' header"
        assert 'Categorie' in content, "Missing 'Categorie' header"
        assert 'Pret Vanzare' in content, "Missing 'Pret Vanzare' header"
        
        print(f"PASS: CSV template downloaded successfully, content length: {len(content)}")


class TestCSVImport(TestAuth):
    """Test CSV import parsing endpoint"""
    
    def test_csv_import_requires_auth(self):
        """CSV import endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/products/import-csv")
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print("PASS: CSV import requires authentication")
    
    def test_csv_import_requires_admin(self, casier_token):
        """CSV import endpoint requires admin role"""
        csv_content = "Denumire,Pret Vanzare\nTest Product,10.00"
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv",
            headers={"Authorization": f"Bearer {casier_token}"},
            files=files
        )
        assert response.status_code == 403, f"Expected 403 for casier, got {response.status_code}"
        print("PASS: CSV import requires admin role")
    
    def test_csv_import_rejects_non_csv(self, admin_token):
        """CSV import rejects non-CSV files"""
        files = {'file': ('test.txt', 'some text content', 'text/plain')}
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert response.status_code == 400, f"Expected 400 for non-CSV, got {response.status_code}"
        print("PASS: CSV import rejects non-CSV files")
    
    def test_csv_import_parse_valid_csv(self, admin_token):
        """CSV import parses valid CSV and returns preview"""
        csv_content = """Denumire,Categorie,Cod Bare,Pret Achizitie,Pret Vanzare,TVA %,Unitate,Stoc,Stoc Minim
TEST_Produs Import 1,Materiale Construcții,1234567890123,15.00,25.00,19,buc,50,5
TEST_Produs Import 2,Scule Manuale,,10.00,18.50,19,buc,100,10"""
        
        files = {'file': ('test_import.csv', csv_content, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Missing 'items' in response"
        assert "total_parsed" in data, "Missing 'total_parsed' in response"
        assert "total_create" in data, "Missing 'total_create' in response"
        assert "total_update" in data, "Missing 'total_update' in response"
        assert "columns_found" in data, "Missing 'columns_found' in response"
        
        assert data["total_parsed"] == 2, f"Expected 2 items parsed, got {data['total_parsed']}"
        assert len(data["items"]) == 2, f"Expected 2 items, got {len(data['items'])}"
        
        # Check item structure
        item = data["items"][0]
        assert "nume" in item, "Missing 'nume' in item"
        assert "categorie" in item, "Missing 'categorie' in item"
        assert "pret_vanzare" in item, "Missing 'pret_vanzare' in item"
        assert "action" in item, "Missing 'action' in item"
        assert item["action"] in ["create", "update"], f"Invalid action: {item['action']}"
        
        print(f"PASS: CSV import parsed {data['total_parsed']} items ({data['total_create']} new, {data['total_update']} updates)")
    
    def test_csv_import_semicolon_delimiter(self, admin_token):
        """CSV import handles semicolon delimiter"""
        csv_content = """Denumire;Categorie;Pret Vanzare
TEST_Semicolon Product;Feronerie;35.00"""
        
        files = {'file': ('test_semicolon.csv', csv_content, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["total_parsed"] == 1, f"Expected 1 item, got {data['total_parsed']}"
        assert data["items"][0]["nume"] == "TEST_Semicolon Product"
        
        print("PASS: CSV import handles semicolon delimiter")
    
    def test_csv_import_missing_required_columns(self, admin_token):
        """CSV import rejects CSV without required columns"""
        csv_content = """Categorie,Stoc
Materiale,100"""
        
        files = {'file': ('test_missing.csv', csv_content, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert response.status_code == 400, f"Expected 400 for missing columns, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Missing error detail"
        
        print("PASS: CSV import rejects CSV without required columns")


class TestCSVImportConfirm(TestAuth):
    """Test CSV import confirmation endpoint"""
    
    def test_csv_confirm_requires_auth(self):
        """CSV confirm endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            json={"items": []}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: CSV confirm requires authentication")
    
    def test_csv_confirm_requires_admin(self, casier_token):
        """CSV confirm endpoint requires admin role"""
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            headers={"Authorization": f"Bearer {casier_token}"},
            json={"items": []}
        )
        assert response.status_code == 403, f"Expected 403 for casier, got {response.status_code}"
        print("PASS: CSV confirm requires admin role")
    
    def test_csv_confirm_empty_items(self, admin_token):
        """CSV confirm rejects empty items list"""
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"items": []}
        )
        assert response.status_code == 400, f"Expected 400 for empty items, got {response.status_code}"
        print("PASS: CSV confirm rejects empty items")
    
    def test_csv_confirm_create_product(self, admin_token):
        """CSV confirm creates new product"""
        import uuid
        unique_name = f"TEST_CSV_Create_{uuid.uuid4().hex[:8]}"
        
        items = [{
            "nume": unique_name,
            "categorie": "Materiale Construcții",
            "cod_bare": "",
            "pret_achizitie": 10.0,
            "pret_vanzare": 15.0,
            "tva": 19.0,
            "unitate": "buc",
            "stoc": 50.0,
            "stoc_minim": 5.0,
            "action": "create",
            "existing_id": None
        }]
        
        response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"items": items}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "created" in data, "Missing 'created' in response"
        assert "updated" in data, "Missing 'updated' in response"
        assert "total" in data, "Missing 'total' in response"
        assert data["created"] == 1, f"Expected 1 created, got {data['created']}"
        
        # Verify product was created
        search_response = requests.get(
            f"{BASE_URL}/api/products?search={unique_name}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] >= 1, "Product not found after creation"
        
        print(f"PASS: CSV confirm created product '{unique_name}'")
        
        # Cleanup - delete the test product
        if search_data["products"]:
            product_id = search_data["products"][0]["id"]
            requests.delete(
                f"{BASE_URL}/api/products/{product_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )


class TestPDFImport(TestAuth):
    """Test PDF import/parsing endpoint"""
    
    def test_pdf_parse_requires_auth(self):
        """PDF parse endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/nir/parse-pdf")
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print("PASS: PDF parse requires authentication")
    
    def test_pdf_parse_requires_admin(self, casier_token):
        """PDF parse endpoint requires admin role"""
        # Create a minimal PDF-like content
        pdf_content = b'%PDF-1.4 minimal test'
        files = {'file': ('test.pdf', pdf_content, 'application/pdf')}
        response = requests.post(
            f"{BASE_URL}/api/nir/parse-pdf",
            headers={"Authorization": f"Bearer {casier_token}"},
            files=files
        )
        assert response.status_code == 403, f"Expected 403 for casier, got {response.status_code}"
        print("PASS: PDF parse requires admin role")
    
    def test_pdf_parse_rejects_non_pdf(self, admin_token):
        """PDF parse rejects non-PDF files"""
        files = {'file': ('test.txt', 'some text content', 'text/plain')}
        response = requests.post(
            f"{BASE_URL}/api/nir/parse-pdf",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert response.status_code == 400, f"Expected 400 for non-PDF, got {response.status_code}"
        print("PASS: PDF parse rejects non-PDF files")
    
    def test_pdf_parse_valid_pdf_structure(self, admin_token):
        """PDF parse returns correct response structure for valid PDF"""
        # Create a simple valid PDF with some invoice-like text
        # This is a minimal PDF that PyMuPDF can open
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Factura nr. FV-001) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
300
%%EOF"""
        
        files = {'file': ('invoice.pdf', pdf_content, 'application/pdf')}
        response = requests.post(
            f"{BASE_URL}/api/nir/parse-pdf",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        
        # The PDF might fail to parse properly but should return 200 with empty items
        # or 400 if it can't open the PDF at all
        if response.status_code == 200:
            data = response.json()
            assert "invoice_number" in data, "Missing 'invoice_number' in response"
            assert "supplier_name" in data, "Missing 'supplier_name' in response"
            assert "items" in data, "Missing 'items' in response"
            assert "total_items" in data, "Missing 'total_items' in response"
            assert isinstance(data["items"], list), "Items should be a list"
            print(f"PASS: PDF parse returns correct structure (found {data['total_items']} items)")
        else:
            # PDF might be invalid for PyMuPDF
            print(f"INFO: PDF parse returned {response.status_code} - minimal PDF may not be valid")
            assert response.status_code == 400, f"Expected 400 for invalid PDF, got {response.status_code}"
            print("PASS: PDF parse correctly rejects invalid PDF")


class TestEndToEndCSVImport(TestAuth):
    """End-to-end test for CSV import flow"""
    
    def test_full_csv_import_flow(self, admin_token):
        """Test complete CSV import flow: upload -> preview -> confirm"""
        import uuid
        unique_suffix = uuid.uuid4().hex[:8]
        
        # Step 1: Upload CSV for parsing
        csv_content = f"""Denumire,Categorie,Pret Achizitie,Pret Vanzare,TVA %,Unitate,Stoc,Stoc Minim
TEST_E2E_Product_{unique_suffix},Electrice,20.00,35.00,19,buc,25,3"""
        
        files = {'file': ('e2e_test.csv', csv_content, 'text/csv')}
        parse_response = requests.post(
            f"{BASE_URL}/api/products/import-csv",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert parse_response.status_code == 200, f"Parse failed: {parse_response.text}"
        
        parse_data = parse_response.json()
        assert parse_data["total_parsed"] == 1, "Expected 1 item parsed"
        
        # Step 2: Confirm import
        items = parse_data["items"]
        confirm_response = requests.post(
            f"{BASE_URL}/api/products/import-csv/confirm",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"items": items}
        )
        assert confirm_response.status_code == 200, f"Confirm failed: {confirm_response.text}"
        
        confirm_data = confirm_response.json()
        assert confirm_data["total"] == 1, "Expected 1 product imported"
        
        # Step 3: Verify product exists
        search_response = requests.get(
            f"{BASE_URL}/api/products?search=TEST_E2E_Product_{unique_suffix}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] >= 1, "Product not found after import"
        
        product = search_data["products"][0]
        assert product["pret_vanzare"] == 35.0, f"Wrong price: {product['pret_vanzare']}"
        assert product["stoc"] == 25.0, f"Wrong stock: {product['stoc']}"
        
        print(f"PASS: Full CSV import flow completed for product '{product['nume']}'")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/products/{product['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
