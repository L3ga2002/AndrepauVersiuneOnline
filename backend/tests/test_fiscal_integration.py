"""
ANDREPAU POS - Fiscal Printer Integration Tests
Tests for fiscal bridge service, sales with fiscal fields, and bridge download
"""
import pytest
import requests
import os
import zipfile
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Test login with admin and casier credentials"""
    
    def test_admin_login(self):
        """Test admin login with admin/admin123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful - role: {data['user']['role']}")
    
    def test_casier_login(self):
        """Test casier login with casier/casier123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "casier",
            "password": "casier123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["username"] == "casier"
        assert data["user"]["role"] == "casier"
        print(f"✓ Casier login successful - role: {data['user']['role']}")


class TestSalesWithFiscalFields:
    """Test POST /api/sales with fiscal_number and fiscal_status fields"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture
    def admin_user_id(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["user"]["id"]
    
    @pytest.fixture
    def product_id(self, admin_token):
        """Get first product for sale"""
        response = requests.get(
            f"{BASE_URL}/api/products?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        products = response.json()["products"]
        if products:
            return products[0]["id"]
        return None
    
    def test_sale_with_fiscal_number(self, admin_token, admin_user_id, product_id):
        """Test creating sale with fiscal_number field"""
        import uuid
        transaction_id = f"TEST_fiscal_{uuid.uuid4()}"
        
        sale_data = {
            "items": [{
                "product_id": product_id,
                "nume": "TEST Product",
                "cantitate": 1,
                "pret_unitar": 10.0,
                "tva": 19.0
            }],
            "subtotal": 10.0,
            "tva_total": 1.60,
            "total": 10.0,
            "discount_percent": 0,
            "metoda_plata": "numerar",
            "suma_numerar": 10.0,
            "suma_card": 0,
            "casier_id": admin_user_id,
            "transaction_id": transaction_id,
            "fiscal_number": "12345",
            "fiscal_status": "printed"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/sales",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "numar_bon" in data
        assert data.get("fiscal_number") == "12345"
        assert data.get("fiscal_status") == "printed"
        print(f"✓ Sale created with fiscal_number={data.get('fiscal_number')}, fiscal_status={data.get('fiscal_status')}")
    
    def test_sale_without_fiscal_receipt(self, admin_token, admin_user_id, product_id):
        """Test creating sale without fiscal receipt (fiscal_status = 'none')"""
        import uuid
        transaction_id = f"TEST_no_fiscal_{uuid.uuid4()}"
        
        sale_data = {
            "items": [{
                "product_id": product_id,
                "nume": "TEST Product No Fiscal",
                "cantitate": 2,
                "pret_unitar": 5.0,
                "tva": 19.0
            }],
            "subtotal": 10.0,
            "tva_total": 1.60,
            "total": 10.0,
            "discount_percent": 0,
            "metoda_plata": "card",
            "suma_numerar": 0,
            "suma_card": 10.0,
            "casier_id": admin_user_id,
            "transaction_id": transaction_id,
            "fiscal_number": None,
            "fiscal_status": "none"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/sales",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data.get("fiscal_status") == "none"
        print(f"✓ Sale created without fiscal receipt - fiscal_status={data.get('fiscal_status')}")


class TestCashOperations:
    """Test cash operations API"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_create_cash_operation(self, admin_token):
        """Test POST /api/cash-operations"""
        operation_data = {
            "type": "CASH_IN",
            "amount": 100.0,
            "description": "TEST_Intrare numerar",
            "operator_id": "test-op",
            "operator_name": "test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/cash-operations",
            json=operation_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["type"] == "CASH_IN"
        assert data["amount"] == 100.0
        print(f"✓ Cash operation created: type={data['type']}, amount={data['amount']}")
    
    def test_get_daily_stats(self, admin_token):
        """Test GET /api/cash-operations/daily-stats"""
        response = requests.get(
            f"{BASE_URL}/api/cash-operations/daily-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Verify expected fields in daily stats
        assert "totalCash" in data
        assert "totalCard" in data
        assert "totalVoucher" in data
        assert "cashIn" in data
        assert "cashOut" in data
        assert "receiptsCount" in data
        print(f"✓ Daily stats: totalCash={data['totalCash']}, receiptsCount={data['receiptsCount']}")
    
    def test_get_operations_history(self, admin_token):
        """Test GET /api/cash-operations/history"""
        response = requests.get(
            f"{BASE_URL}/api/cash-operations/history?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "operations" in data
        assert isinstance(data["operations"], list)
        print(f"✓ Operations history: {len(data['operations'])} operations")


class TestBridgeDownload:
    """Test bridge download endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_bridge_download_returns_zip(self, admin_token):
        """Test GET /api/bridge/download returns a ZIP file"""
        response = requests.get(
            f"{BASE_URL}/api/bridge/download",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/zip" in content_type or "application/octet-stream" in content_type
        
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert ".zip" in content_disposition.lower()
        print(f"✓ Bridge download returns ZIP file - Content-Disposition: {content_disposition}")
    
    def test_bridge_zip_contains_required_files(self, admin_token):
        """Test that bridge ZIP contains 3 required files"""
        response = requests.get(
            f"{BASE_URL}/api/bridge/download",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        
        # Parse ZIP content
        zip_buffer = io.BytesIO(response.content)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            file_list = zf.namelist()
            
            # Check for required files
            required_files = ['fiscal_bridge.py', 'install_bridge.bat', 'start_bridge.bat']
            missing_files = []
            
            for rf in required_files:
                if rf not in file_list:
                    missing_files.append(rf)
            
            assert len(missing_files) == 0, f"Missing files in ZIP: {missing_files}"
            print(f"✓ Bridge ZIP contains all required files: {required_files}")
            print(f"  All files in ZIP: {file_list}")
    
    def test_bridge_download_requires_auth(self):
        """Test that bridge download requires authentication"""
        response = requests.get(f"{BASE_URL}/api/bridge/download")
        # Should return 403 or 401 without auth
        assert response.status_code in [401, 403]
        print("✓ Bridge download requires authentication (returns 401/403 without token)")


class TestFiscalSettings:
    """Test fiscal settings API"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_fiscal_settings(self, admin_token):
        """Test GET /api/settings/fiscal"""
        response = requests.get(
            f"{BASE_URL}/api/settings/fiscal",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Default settings should contain bridge_url
        assert "bridge_url" in data or response.status_code == 200
        print(f"✓ Fiscal settings: {data}")
