"""
ANDREPAU POS - Cash Operations & Fiscal Settings API Tests
Tests for:
- GET/POST /api/settings/fiscal - Fiscal settings management
- GET /api/cash-operations/daily-stats - Daily cash statistics
- GET /api/cash-operations/history - Operations history
- POST /api/cash-operations - Create cash operation record
- POST /api/sales/{id}/cancel - Cancel sale (404 for non-existing)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestFiscalSettings:
    """Fiscal settings endpoint tests (GET/POST /api/settings/fiscal)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def casier_token(self):
        """Get casier authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "casier",
            "password": "casier123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_fiscal_settings_returns_defaults(self, admin_token):
        """GET /api/settings/fiscal returns default fiscal settings"""
        response = requests.get(
            f"{BASE_URL}/api/settings/fiscal",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Check default fields are present
        assert "bridge_url" in data or "fiscal_mode" in data
        print(f"Fiscal settings response: {data}")
    
    def test_casier_can_read_fiscal_settings(self, casier_token):
        """Casier should be able to read fiscal settings"""
        response = requests.get(
            f"{BASE_URL}/api/settings/fiscal",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 200
    
    def test_post_fiscal_settings_admin_only(self, admin_token):
        """POST /api/settings/fiscal saves and returns fiscal settings (admin only)"""
        test_settings = {
            "fiscal_mode": True,
            "bridge_url": "http://localhost:5555",
            "auto_print": True
        }
        response = requests.post(
            f"{BASE_URL}/api/settings/fiscal",
            json=test_settings,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "settings" in data
        print(f"Save fiscal settings response: {data}")
    
    def test_post_fiscal_settings_casier_forbidden(self, casier_token):
        """Casier cannot update fiscal settings - admin only"""
        test_settings = {
            "fiscal_mode": False,
            "bridge_url": "http://localhost:9999"
        }
        response = requests.post(
            f"{BASE_URL}/api/settings/fiscal",
            json=test_settings,
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 403


class TestCashOperationsDailyStats:
    """Daily stats endpoint tests (GET /api/cash-operations/daily-stats)"""
    
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
    
    def test_daily_stats_returns_correct_structure(self, admin_token):
        """GET /api/cash-operations/daily-stats returns daily statistics"""
        response = requests.get(
            f"{BASE_URL}/api/cash-operations/daily-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Check expected fields
        assert "totalCash" in data
        assert "totalCard" in data
        assert "totalVoucher" in data
        assert "cashIn" in data
        assert "cashOut" in data
        assert "receiptsCount" in data
        # Check types
        assert isinstance(data["totalCash"], (int, float))
        assert isinstance(data["totalCard"], (int, float))
        assert isinstance(data["receiptsCount"], int)
        print(f"Daily stats: {data}")
    
    def test_casier_can_access_daily_stats(self, casier_token):
        """Casier can access daily stats"""
        response = requests.get(
            f"{BASE_URL}/api/cash-operations/daily-stats",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 200


class TestCashOperationsHistory:
    """Operations history endpoint tests (GET /api/cash-operations/history)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_history_returns_operations_list(self, admin_token):
        """GET /api/cash-operations/history returns operations history"""
        response = requests.get(
            f"{BASE_URL}/api/cash-operations/history?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "operations" in data
        assert isinstance(data["operations"], list)
        print(f"Operations history count: {len(data['operations'])}")
    
    def test_history_with_date_filter(self, admin_token):
        """GET /api/cash-operations/history supports date filtering"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/cash-operations/history?limit=50&date={today}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "operations" in data


class TestCreateCashOperation:
    """Create cash operation tests (POST /api/cash-operations)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture
    def admin_user(self):
        """Get admin user details"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["user"]
    
    def test_create_cash_in_operation(self, admin_token, admin_user):
        """POST /api/cash-operations creates CASH_IN operation"""
        operation_data = {
            "type": "CASH_IN",
            "amount": 100.50,
            "description": "TEST_Cash In - Sold initial",
            "operator_id": admin_user["id"],
            "operator_name": admin_user["username"]
        }
        response = requests.post(
            f"{BASE_URL}/api/cash-operations",
            json=operation_data,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["type"] == "CASH_IN"
        assert data["amount"] == 100.50
        print(f"Created CASH_IN operation: {data['id']}")
    
    def test_create_cash_out_operation(self, admin_token, admin_user):
        """POST /api/cash-operations creates CASH_OUT operation"""
        operation_data = {
            "type": "CASH_OUT",
            "amount": 50.00,
            "description": "TEST_Cash Out - Plata furnizor",
            "operator_id": admin_user["id"],
            "operator_name": admin_user["username"]
        }
        response = requests.post(
            f"{BASE_URL}/api/cash-operations",
            json=operation_data,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["type"] == "CASH_OUT"
        assert data["amount"] == 50.00
    
    def test_create_report_x_operation(self, admin_token, admin_user):
        """POST /api/cash-operations creates REPORT_X operation"""
        operation_data = {
            "type": "REPORT_X",
            "amount": 0,
            "description": "TEST_Raport X zilnic",
            "operator_id": admin_user["id"],
            "operator_name": admin_user["username"]
        }
        response = requests.post(
            f"{BASE_URL}/api/cash-operations",
            json=operation_data,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "REPORT_X"
    
    def test_create_report_z_operation(self, admin_token, admin_user):
        """POST /api/cash-operations creates REPORT_Z operation"""
        operation_data = {
            "type": "REPORT_Z",
            "amount": 0,
            "description": "TEST_Inchidere zi fiscala",
            "operator_id": admin_user["id"],
            "operator_name": admin_user["username"]
        }
        response = requests.post(
            f"{BASE_URL}/api/cash-operations",
            json=operation_data,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "REPORT_Z"


class TestCancelSale:
    """Cancel sale endpoint tests (POST /api/sales/{id}/cancel)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["token"]
    
    def test_cancel_non_existing_sale_returns_404(self, admin_token):
        """POST /api/sales/{id}/cancel returns 404 for non-existing sale"""
        fake_sale_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/sales/{fake_sale_id}/cancel",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        print(f"404 response for non-existing sale: {data}")
    
    def test_cancel_with_invalid_uuid(self, admin_token):
        """POST /api/sales/{id}/cancel handles invalid UUID gracefully"""
        response = requests.post(
            f"{BASE_URL}/api/sales/invalid-id-format/cancel",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 404 since sale not found (not 500 crash)
        assert response.status_code == 404


class TestUnauthorizedAccess:
    """Test unauthorized access to cash operations endpoints"""
    
    def test_daily_stats_requires_auth(self):
        """Daily stats endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/cash-operations/daily-stats")
        assert response.status_code in [401, 403]
    
    def test_history_requires_auth(self):
        """History endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/cash-operations/history")
        assert response.status_code in [401, 403]
    
    def test_create_operation_requires_auth(self):
        """Create operation endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/cash-operations",
            json={"type": "CASH_IN", "amount": 100}
        )
        assert response.status_code in [401, 403]
    
    def test_fiscal_settings_requires_auth(self):
        """Fiscal settings endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/settings/fiscal")
        assert response.status_code in [401, 403]
