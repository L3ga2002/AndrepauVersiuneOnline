"""
Iteration 12: Backend Refactoring Tests
Tests all API endpoints after server.py was split into 12 route modules.
Verifies that all routes still work correctly after the refactoring.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = {"username": "admin", "password": "admin123"}
CASIER_USER = {"username": "casier", "password": "casier123"}


class TestAuthRoutes:
    """Test auth routes after refactoring - routes/auth.py"""
    
    def test_admin_login(self):
        """Test admin login with admin/admin123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["role"] == "admin", "User role should be admin"
        print(f"✓ Admin login successful - role: {data['user']['role']}")
        return data["token"]
    
    def test_casier_login(self):
        """Test casier login with casier/casier123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CASIER_USER)
        assert response.status_code == 200, f"Casier login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert data["user"]["role"] == "casier", "User role should be casier"
        print(f"✓ Casier login successful - role: {data['user']['role']}")
        return data["token"]
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "invalid", "password": "wrong"})
        assert response.status_code == 401, "Should return 401 for invalid credentials"
        print("✓ Invalid login correctly rejected with 401")


class TestProductsRoutes:
    """Test products routes after refactoring - routes/products.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_products_paginated(self):
        """GET /api/products returns paginated products"""
        response = requests.get(f"{BASE_URL}/api/products?page=1&limit=50", headers=self.headers)
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        data = response.json()
        assert "products" in data, "Response should have 'products' key"
        assert "total" in data, "Response should have 'total' key"
        assert "page" in data, "Response should have 'page' key"
        assert "limit" in data, "Response should have 'limit' key"
        print(f"✓ GET /api/products - {len(data['products'])} products, total: {data['total']}")
    
    def test_get_categories(self):
        """GET /api/categories returns categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200, f"Failed to get categories: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Categories should be a list"
        print(f"✓ GET /api/categories - {len(data)} categories")


class TestSuppliersRoutes:
    """Test suppliers routes after refactoring - routes/suppliers.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_suppliers(self):
        """GET /api/suppliers returns suppliers list"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=self.headers)
        assert response.status_code == 200, f"Failed to get suppliers: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Suppliers should be a list"
        print(f"✓ GET /api/suppliers - {len(data)} suppliers")


class TestCashRoutes:
    """Test cash operations routes after refactoring - routes/cash.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_opening_summary(self):
        """GET /api/daily/opening-summary returns summary with vanzari_card field"""
        response = requests.get(f"{BASE_URL}/api/daily/opening-summary", headers=self.headers)
        assert response.status_code == 200, f"Failed to get opening summary: {response.text}"
        data = response.json()
        # Check required fields
        assert "sold_casa" in data, "Response should have 'sold_casa'"
        assert "cash_in" in data, "Response should have 'cash_in'"
        assert "cash_out" in data, "Response should have 'cash_out'"
        assert "vanzari_card" in data, "Response should have 'vanzari_card' (P1 feature)"
        assert "numar_vanzari_card" in data, "Response should have 'numar_vanzari_card'"
        assert "bridge_connected" in data, "Response should have 'bridge_connected'"
        print(f"✓ GET /api/daily/opening-summary - sold_casa: {data['sold_casa']}, vanzari_card: {data['vanzari_card']}")
    
    def test_get_tva_settings(self):
        """GET /api/settings/tva returns TVA settings with 21% default"""
        response = requests.get(f"{BASE_URL}/api/settings/tva")
        assert response.status_code == 200, f"Failed to get TVA settings: {response.text}"
        data = response.json()
        assert "cote_tva" in data, "Response should have 'cote_tva'"
        # Check that 21% is the standard rate (P1 feature)
        standard_tva = next((t for t in data["cote_tva"] if t["cod"] == "A"), None)
        assert standard_tva is not None, "Should have standard TVA rate (cod A)"
        assert standard_tva["procent"] == 21.0, f"Standard TVA should be 21%, got {standard_tva['procent']}"
        print(f"✓ GET /api/settings/tva - Standard TVA: {standard_tva['procent']}%")
    
    def test_create_cash_operation(self):
        """POST /api/cash-operations creates cash operation (sold manual save)"""
        payload = {
            "type": "CASH_IN",
            "amount": 10.0,
            "description": "TEST_Sold inceput de zi (manual)",
            "operator_id": "test-user",
            "operator_name": "Test User"
        }
        response = requests.post(f"{BASE_URL}/api/cash-operations", json=payload, headers=self.headers)
        assert response.status_code == 200, f"Failed to create cash operation: {response.text}"
        data = response.json()
        assert data["type"] == "CASH_IN", "Type should be CASH_IN"
        assert data["amount"] == 10.0, "Amount should be 10.0"
        print(f"✓ POST /api/cash-operations - Created CASH_IN operation for {data['amount']} RON")


class TestReportsRoutes:
    """Test reports routes after refactoring - routes/reports.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_stock_dashboard(self):
        """GET /api/stock/dashboard returns stock dashboard"""
        response = requests.get(f"{BASE_URL}/api/stock/dashboard", headers=self.headers)
        assert response.status_code == 200, f"Failed to get stock dashboard: {response.text}"
        data = response.json()
        assert "total_products" in data, "Response should have 'total_products'"
        assert "low_stock" in data, "Response should have 'low_stock'"
        assert "out_of_stock" in data, "Response should have 'out_of_stock'"
        assert "total_value" in data, "Response should have 'total_value'"
        print(f"✓ GET /api/stock/dashboard - {data['total_products']} products, {data['low_stock']} low stock")
    
    def test_get_sales_report(self):
        """GET /api/reports/sales?period=today returns sales report"""
        response = requests.get(f"{BASE_URL}/api/reports/sales?period=today", headers=self.headers)
        assert response.status_code == 200, f"Failed to get sales report: {response.text}"
        data = response.json()
        assert "total_sales" in data, "Response should have 'total_sales'"
        assert "count" in data, "Response should have 'count'"
        assert "cash" in data, "Response should have 'cash'"
        assert "card" in data, "Response should have 'card'"
        print(f"✓ GET /api/reports/sales - Total: {data['total_sales']} RON, {data['count']} transactions")


class TestBridgeRoutes:
    """Test fiscal bridge routes after refactoring - routes/bridge.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_bridge_status(self):
        """GET /api/fiscal/bridge-status returns bridge status"""
        response = requests.get(f"{BASE_URL}/api/fiscal/bridge-status", headers=self.headers)
        assert response.status_code == 200, f"Failed to get bridge status: {response.text}"
        data = response.json()
        assert "connected" in data, "Response should have 'connected'"
        assert "last_poll" in data, "Response should have 'last_poll'"
        print(f"✓ GET /api/fiscal/bridge-status - connected: {data['connected']}")


class TestSalesRoutes:
    """Test sales routes after refactoring - routes/sales.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_sales_history(self):
        """GET /api/sales returns sales history"""
        response = requests.get(f"{BASE_URL}/api/sales", headers=self.headers)
        assert response.status_code == 200, f"Failed to get sales: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Sales should be a list"
        print(f"✓ GET /api/sales - {len(data)} sales records")


class TestNIRRoutes:
    """Test NIR routes after refactoring - routes/nir.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_nir_list(self):
        """GET /api/nir returns NIR list"""
        response = requests.get(f"{BASE_URL}/api/nir", headers=self.headers)
        assert response.status_code == 200, f"Failed to get NIR list: {response.text}"
        data = response.json()
        assert isinstance(data, list), "NIR should be a list"
        print(f"✓ GET /api/nir - {len(data)} NIR records")


class TestHeldOrdersRoutes:
    """Test held orders routes after refactoring - routes/held_orders.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_held_orders(self):
        """GET /api/held-orders returns held orders"""
        response = requests.get(f"{BASE_URL}/api/held-orders", headers=self.headers)
        assert response.status_code == 200, f"Failed to get held orders: {response.text}"
        data = response.json()
        assert "orders" in data, "Response should have 'orders'"
        print(f"✓ GET /api/held-orders - {len(data['orders'])} held orders")


class TestStockAlertsRoutes:
    """Test stock alerts routes after refactoring - routes/reports.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_stock_alerts(self):
        """GET /api/stock/alerts returns stock alerts"""
        response = requests.get(f"{BASE_URL}/api/stock/alerts", headers=self.headers)
        assert response.status_code == 200, f"Failed to get stock alerts: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Stock alerts should be a list"
        print(f"✓ GET /api/stock/alerts - {len(data)} alerts")


class TestAPIRoot:
    """Test API root endpoint"""
    
    def test_api_root(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"Failed to get API root: {response.text}"
        data = response.json()
        assert "message" in data, "Response should have 'message'"
        assert "version" in data, "Response should have 'version'"
        print(f"✓ GET /api/ - {data['message']} v{data['version']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
