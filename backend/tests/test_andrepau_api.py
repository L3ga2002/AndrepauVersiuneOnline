"""
ANDREPAU POS API Tests
Tests for authentication, products, stock, and export functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
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
    
    def test_casier_login_success(self):
        """Test casier login with valid credentials"""
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
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "invalid",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestProducts:
    """Product endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture
    def casier_token(self):
        """Get casier authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "casier",
            "password": "casier123"
        })
        return response.json()["token"]
    
    def test_get_products_list(self, admin_token):
        """Test fetching products list"""
        response = requests.get(
            f"{BASE_URL}/api/products?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "pages" in data
        assert isinstance(data["products"], list)
    
    def test_get_products_with_search(self, admin_token):
        """Test product search functionality"""
        response = requests.get(
            f"{BASE_URL}/api/products?search=DIBLU&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
    
    def test_get_categories(self, admin_token):
        """Test fetching product categories"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_casier_can_view_products(self, casier_token):
        """Test that casier can view products"""
        response = requests.get(
            f"{BASE_URL}/api/products?limit=5",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 200


class TestExcelExport:
    """Excel export endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture
    def casier_token(self):
        """Get casier authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "casier",
            "password": "casier123"
        })
        return response.json()["token"]
    
    def test_excel_export_admin(self, admin_token):
        """Test Excel export endpoint for admin"""
        response = requests.get(
            f"{BASE_URL}/api/products/export/xls",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")
        assert ".xlsx" in response.headers.get("content-disposition", "")
    
    def test_excel_export_casier_forbidden(self, casier_token):
        """Test that casier cannot export Excel (admin only)"""
        response = requests.get(
            f"{BASE_URL}/api/products/export/xls",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 403


class TestStock:
    """Stock management endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_stock_dashboard(self, admin_token):
        """Test stock dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/stock/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert "low_stock" in data
        assert "out_of_stock" in data
        assert "total_value" in data
    
    def test_stock_alerts(self, admin_token):
        """Test stock alerts endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/stock/alerts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestSuppliers:
    """Supplier endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_suppliers(self, admin_token):
        """Test fetching suppliers list"""
        response = requests.get(
            f"{BASE_URL}/api/suppliers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestNIR:
    """NIR (goods reception) endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_get_nirs(self, admin_token):
        """Test fetching NIR list"""
        response = requests.get(
            f"{BASE_URL}/api/nir",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestBackup:
    """Backup endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_backup_endpoint(self, admin_token):
        """Test backup endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/backup",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "suppliers" in data
        assert "created_at" in data


class TestReports:
    """Reports endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_sales_report(self, admin_token):
        """Test sales report endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/reports/sales?period=today",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data
        assert "count" in data
    
    def test_top_products_report(self, admin_token):
        """Test top products report endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/reports/top-products?limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
