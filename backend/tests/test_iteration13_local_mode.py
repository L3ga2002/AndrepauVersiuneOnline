"""
Iteration 13: Test local/offline mode features and existing online functionality
- Dynamic API URL detection
- Connection mode indicator
- Static file serving configuration
- Bridge download with local_setup scripts
- All existing functionality continues to work
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAPIRoot:
    """Test API root endpoint returns correct version"""
    
    def test_api_root_returns_version_2_0_0(self):
        """API root should return version 2.0.0"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0.0"
        assert "ANDREPAU" in data["message"]
        print(f"API root: {data}")


class TestAuthentication:
    """Test login flows for admin and casier"""
    
    def test_admin_login_success(self):
        """Admin login with admin/admin123 should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        print(f"Admin login successful: {data['user']['username']}")
    
    def test_casier_login_success(self):
        """Casier login with casier/casier123 should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "casier",
            "password": "casier123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "casier"
        print(f"Casier login successful: {data['user']['username']}")
    
    def test_invalid_login_rejected(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "invalid",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("Invalid login correctly rejected")


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_products_endpoint(self):
        """GET /api/products should return products list"""
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "products" in data or isinstance(data, list)
        print(f"Products endpoint working, returned data type: {type(data)}")
    
    def test_categories_endpoint(self):
        """GET /api/categories should return categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Categories: {len(data)} found")
    
    def test_suppliers_endpoint(self):
        """GET /api/suppliers should return suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Suppliers: {len(data)} found")
    
    def test_daily_opening_summary(self):
        """GET /api/daily/opening-summary should return dashboard data"""
        response = requests.get(f"{BASE_URL}/api/daily/opening-summary", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Should have key fields for Start Day page
        assert "sold_initial" in data or "vanzari_azi" in data or "total_vanzari" in data
        print(f"Opening summary: {data}")
    
    def test_stock_dashboard(self):
        """GET /api/stock/dashboard should return stock info"""
        response = requests.get(f"{BASE_URL}/api/stock/dashboard", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Stock dashboard: {data}")
    
    def test_stock_alerts(self):
        """GET /api/stock/alerts should return alerts list"""
        response = requests.get(f"{BASE_URL}/api/stock/alerts", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Stock alerts: {len(data)} found")
    
    def test_sales_report(self):
        """GET /api/reports/sales should return sales report"""
        response = requests.get(f"{BASE_URL}/api/reports/sales?period=today", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Sales report: {data}")
    
    def test_sales_history(self):
        """GET /api/sales should return sales history"""
        response = requests.get(f"{BASE_URL}/api/sales", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Sales history returned")
    
    def test_nir_list(self):
        """GET /api/nir should return NIR list"""
        response = requests.get(f"{BASE_URL}/api/nir", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"NIR list returned")
    
    def test_held_orders(self):
        """GET /api/held-orders should return held orders"""
        response = requests.get(f"{BASE_URL}/api/held-orders", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Response is {"orders": [], "total": 0}
        assert "orders" in data
        assert isinstance(data["orders"], list)
        print(f"Held orders: {data['total']} found")
    
    def test_fiscal_bridge_status(self):
        """GET /api/fiscal/bridge-status should return bridge status"""
        response = requests.get(f"{BASE_URL}/api/fiscal/bridge-status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        print(f"Bridge status: {data}")
    
    def test_tva_settings(self):
        """GET /api/settings/tva should return TVA settings"""
        response = requests.get(f"{BASE_URL}/api/settings/tva", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Response has cote_tva array with TVA rates
        assert "cote_tva" in data
        assert isinstance(data["cote_tva"], list)
        # Verify 21% standard rate exists
        standard_rate = next((r for r in data["cote_tva"] if r["procent"] == 21.0), None)
        assert standard_rate is not None, "21% standard TVA rate not found"
        print(f"TVA settings: {len(data['cote_tva'])} rates configured")


class TestBridgeDownload:
    """Test bridge download endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_bridge_download_returns_zip(self):
        """GET /api/bridge/download should return a zip file"""
        response = requests.get(f"{BASE_URL}/api/bridge/download", headers=self.headers)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/zip"
        assert "ANDREPAU_Bridge_Service.zip" in response.headers.get("content-disposition", "")
        # Verify it's a valid zip (starts with PK)
        assert response.content[:2] == b'PK'
        print(f"Bridge download: {len(response.content)} bytes")
    
    def test_bridge_download_contains_local_setup(self):
        """Bridge zip should contain local_setup scripts"""
        import zipfile
        import io
        
        response = requests.get(f"{BASE_URL}/api/bridge/download", headers=self.headers)
        assert response.status_code == 200
        
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            file_list = zf.namelist()
            print(f"Files in bridge zip: {file_list}")
            
            # Check for local_setup files
            expected_files = [
                "local_setup/install_andrepau.bat",
                "local_setup/start_andrepau.bat",
                "local_setup/stop_andrepau.bat",
                "local_setup/update_local.bat",
                "local_setup/README_INSTALARE.txt"
            ]
            
            for expected in expected_files:
                assert expected in file_list, f"Missing {expected} in bridge zip"
            
            print("All local_setup files present in bridge zip")


class TestAuthMe:
    """Test /auth/me endpoint"""
    
    def test_auth_me_returns_user_info(self):
        """GET /api/auth/me should return current user info"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Then get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        print(f"Auth me: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
