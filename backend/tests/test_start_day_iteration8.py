"""
Test cases for Start Day Dashboard (Iteration 8)
- GET /api/daily/opening-summary endpoint
- Response structure validation
- Data accuracy checks
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOpeningSummaryAPI:
    """Tests for GET /api/daily/opening-summary endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_opening_summary_returns_200(self):
        """Test that opening-summary endpoint returns 200"""
        resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASS: Opening summary returns 200")
    
    def test_opening_summary_has_required_fields(self):
        """Test that response contains all required fields"""
        resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert resp.status_code == 200
        data = resp.json()
        
        required_fields = [
            "data",           # Current date
            "sold_casa",      # Cash balance
            "cash_in",        # Cash in operations
            "cash_out",       # Cash out operations
            "vanzari_numerar",# Cash sales
            "total_vanzari",  # Total sales
            "numar_vanzari",  # Number of sales
            "bridge_connected",# Bridge status
            "comenzi_hold",   # Held orders count
            "alerte_stoc",    # Stock alerts count
            "fara_stoc",      # Out of stock count
            "ora"             # Current time
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            print(f"  - Field '{field}' present: {data[field]}")
        
        print("PASS: All required fields present in opening summary")
    
    def test_opening_summary_field_types(self):
        """Test that fields have correct types"""
        resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # String fields
        assert isinstance(data["data"], str), "data should be string"
        assert isinstance(data["ora"], str), "ora should be string"
        
        # Numeric fields
        assert isinstance(data["sold_casa"], (int, float)), "sold_casa should be numeric"
        assert isinstance(data["cash_in"], (int, float)), "cash_in should be numeric"
        assert isinstance(data["cash_out"], (int, float)), "cash_out should be numeric"
        assert isinstance(data["vanzari_numerar"], (int, float)), "vanzari_numerar should be numeric"
        assert isinstance(data["total_vanzari"], (int, float)), "total_vanzari should be numeric"
        assert isinstance(data["numar_vanzari"], int), "numar_vanzari should be int"
        assert isinstance(data["comenzi_hold"], int), "comenzi_hold should be int"
        assert isinstance(data["alerte_stoc"], int), "alerte_stoc should be int"
        assert isinstance(data["fara_stoc"], int), "fara_stoc should be int"
        
        # Boolean field
        assert isinstance(data["bridge_connected"], bool), "bridge_connected should be bool"
        
        print("PASS: All field types are correct")
    
    def test_opening_summary_date_format(self):
        """Test that date is in YYYY-MM-DD format"""
        resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Check date format
        import re
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        assert re.match(date_pattern, data["data"]), f"Date format invalid: {data['data']}"
        
        # Check time format (HH:MM)
        time_pattern = r'^\d{2}:\d{2}$'
        assert re.match(time_pattern, data["ora"]), f"Time format invalid: {data['ora']}"
        
        print(f"PASS: Date format correct: {data['data']}, Time: {data['ora']}")
    
    def test_opening_summary_cash_balance_calculation(self):
        """Test that sold_casa = cash_in - cash_out + vanzari_numerar"""
        resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert resp.status_code == 200
        data = resp.json()
        
        expected_balance = data["cash_in"] - data["cash_out"] + data["vanzari_numerar"]
        actual_balance = data["sold_casa"]
        
        # Allow small floating point differences
        assert abs(expected_balance - actual_balance) < 0.01, \
            f"Cash balance mismatch: expected {expected_balance}, got {actual_balance}"
        
        print(f"PASS: Cash balance calculation correct: {actual_balance} = {data['cash_in']} - {data['cash_out']} + {data['vanzari_numerar']}")
    
    def test_opening_summary_bridge_status_is_false(self):
        """Test that bridge_connected is false (bridge not running in test env)"""
        resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Bridge is not running in test environment
        assert data["bridge_connected"] == False, "Bridge should be disconnected in test env"
        print("PASS: Bridge status correctly shows disconnected")
    
    def test_opening_summary_requires_auth(self):
        """Test that endpoint requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/daily/opening-summary")
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"
        print("PASS: Opening summary requires authentication")
    
    def test_opening_summary_casier_access(self):
        """Test that casier role can access opening summary"""
        # Login as casier
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "casier", "password": "casier123"}
        )
        assert login_resp.status_code == 200, f"Casier login failed: {login_resp.text}"
        casier_token = login_resp.json()["token"]
        
        resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert resp.status_code == 200, f"Casier should access opening summary, got {resp.status_code}"
        print("PASS: Casier can access opening summary")
    
    def test_opening_summary_non_negative_counts(self):
        """Test that count fields are non-negative"""
        resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["numar_vanzari"] >= 0, "numar_vanzari should be >= 0"
        assert data["comenzi_hold"] >= 0, "comenzi_hold should be >= 0"
        assert data["alerte_stoc"] >= 0, "alerte_stoc should be >= 0"
        assert data["fara_stoc"] >= 0, "fara_stoc should be >= 0"
        
        print(f"PASS: All counts non-negative: sales={data['numar_vanzari']}, hold={data['comenzi_hold']}, alerts={data['alerte_stoc']}, out_of_stock={data['fara_stoc']}")


class TestHeldOrdersCount:
    """Test held orders count in opening summary"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert login_resp.status_code == 200
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_held_orders_count_matches_api(self):
        """Test that comenzi_hold matches actual held orders count"""
        # Get opening summary
        summary_resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert summary_resp.status_code == 200
        summary_data = summary_resp.json()
        
        # Get held orders directly
        held_resp = requests.get(
            f"{BASE_URL}/api/held-orders",
            headers=self.headers
        )
        assert held_resp.status_code == 200
        held_data = held_resp.json()
        
        assert summary_data["comenzi_hold"] == held_data["total"], \
            f"Held orders count mismatch: summary={summary_data['comenzi_hold']}, actual={held_data['total']}"
        
        print(f"PASS: Held orders count matches: {summary_data['comenzi_hold']}")


class TestStockAlertsCount:
    """Test stock alerts count in opening summary"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert login_resp.status_code == 200
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_stock_alerts_count_is_valid(self):
        """Test that alerte_stoc is a valid count (alerts API has 200 limit)"""
        # Get opening summary
        summary_resp = requests.get(
            f"{BASE_URL}/api/daily/opening-summary",
            headers=self.headers
        )
        assert summary_resp.status_code == 200
        summary_data = summary_resp.json()
        
        # Get stock alerts directly (limited to 200)
        alerts_resp = requests.get(
            f"{BASE_URL}/api/stock/alerts",
            headers=self.headers
        )
        assert alerts_resp.status_code == 200
        alerts_data = alerts_resp.json()
        
        # Opening summary shows actual count, alerts API is limited to 200
        # So summary count should be >= alerts API count
        assert summary_data["alerte_stoc"] >= len(alerts_data), \
            f"Stock alerts count should be >= API results: summary={summary_data['alerte_stoc']}, api={len(alerts_data)}"
        
        # Also verify fara_stoc <= alerte_stoc (out of stock is subset of alerts)
        assert summary_data["fara_stoc"] <= summary_data["alerte_stoc"], \
            f"Out of stock should be <= alerts: fara_stoc={summary_data['fara_stoc']}, alerte_stoc={summary_data['alerte_stoc']}"
        
        print(f"PASS: Stock alerts count valid: {summary_data['alerte_stoc']} (API limited to {len(alerts_data)})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
