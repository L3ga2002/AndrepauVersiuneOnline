"""
Iteration 15: Test sync/receive endpoint with incomplete sale data
Focus: Verify that sync/receive adds default values for missing fields:
- subtotal, tva_total, discount_percent, suma_numerar, suma_card
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SYNC_SECRET = "andrepau-sync-2026"

@pytest.fixture(scope="session")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")  # API returns 'token' not 'access_token'

@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestSyncHealth:
    """Test sync health endpoint"""
    
    def test_sync_health_returns_ok(self):
        """GET /api/sync/health returns ok:true"""
        response = requests.get(f"{BASE_URL}/api/sync/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True
        assert "timestamp" in data
        print(f"PASS: sync/health returns ok:true with timestamp")


class TestSyncPendingCount:
    """Test sync pending-count endpoint"""
    
    def test_pending_count_requires_auth(self):
        """GET /api/sync/pending-count requires authentication"""
        response = requests.get(f"{BASE_URL}/api/sync/pending-count")
        assert response.status_code in [401, 403]
        print(f"PASS: pending-count requires auth (status {response.status_code})")
    
    def test_pending_count_with_auth(self, auth_headers):
        """GET /api/sync/pending-count works with auth"""
        response = requests.get(f"{BASE_URL}/api/sync/pending-count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert isinstance(data["pending"], int)
        print(f"PASS: pending-count returns {data['pending']} pending sales")


class TestSyncReceiveDefaults:
    """Test sync/receive endpoint adds default values for missing fields"""
    
    def test_receive_rejects_invalid_secret(self):
        """POST /api/sync/receive rejects invalid sync_secret"""
        response = requests.post(f"{BASE_URL}/api/sync/receive", json={
            "sync_secret": "wrong-secret",
            "sales": []
        })
        assert response.status_code == 401
        print(f"PASS: sync/receive rejects invalid secret")
    
    def test_receive_accepts_valid_secret_empty_sales(self):
        """POST /api/sync/receive accepts valid sync_secret with empty sales"""
        response = requests.post(f"{BASE_URL}/api/sync/receive", json={
            "sync_secret": SYNC_SECRET,
            "sales": []
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("received") == 0
        assert data.get("duplicates") == 0
        print(f"PASS: sync/receive accepts empty sales list")
    
    def test_receive_adds_defaults_for_numerar_payment(self):
        """POST /api/sync/receive adds default values for cash payment sale"""
        # Create minimal sale with only required fields - missing subtotal, tva_total, etc.
        txn_id = f"TEST_SYNC_NUMERAR_{uuid.uuid4().hex[:8]}"
        minimal_sale = {
            "id": txn_id,
            "transaction_id": txn_id,
            "total": 150.50,
            "metoda_plata": "numerar",
            "created_at": datetime.now().isoformat(),
            "items": [
                {"product_id": "test-prod-1", "cantitate": 2, "pret": 75.25}
            ]
            # Missing: subtotal, tva_total, discount_percent, suma_numerar, suma_card
        }
        
        response = requests.post(f"{BASE_URL}/api/sync/receive", json={
            "sync_secret": SYNC_SECRET,
            "sales": [minimal_sale]
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("received") == 1
        print(f"PASS: sync/receive accepted minimal numerar sale (received=1)")
    
    def test_receive_adds_defaults_for_card_payment(self):
        """POST /api/sync/receive adds default values for card payment sale"""
        txn_id = f"TEST_SYNC_CARD_{uuid.uuid4().hex[:8]}"
        minimal_sale = {
            "id": txn_id,
            "transaction_id": txn_id,
            "total": 250.00,
            "metoda_plata": "card",
            "created_at": datetime.now().isoformat(),
            "items": []
            # Missing: subtotal, tva_total, discount_percent, suma_numerar, suma_card
        }
        
        response = requests.post(f"{BASE_URL}/api/sync/receive", json={
            "sync_secret": SYNC_SECRET,
            "sales": [minimal_sale]
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("received") == 1
        print(f"PASS: sync/receive accepted minimal card sale (received=1)")
    
    def test_receive_adds_defaults_for_missing_items(self):
        """POST /api/sync/receive adds default empty items array if missing"""
        txn_id = f"TEST_SYNC_NOITEMS_{uuid.uuid4().hex[:8]}"
        minimal_sale = {
            "id": txn_id,
            "transaction_id": txn_id,
            "total": 100.00,
            "created_at": datetime.now().isoformat()
            # Missing: items, metoda_plata, subtotal, tva_total, etc.
        }
        
        response = requests.post(f"{BASE_URL}/api/sync/receive", json={
            "sync_secret": SYNC_SECRET,
            "sales": [minimal_sale]
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("received") == 1
        print(f"PASS: sync/receive accepted sale without items array (received=1)")
    
    def test_receive_detects_duplicate_by_transaction_id(self):
        """POST /api/sync/receive detects duplicate sales by transaction_id"""
        txn_id = f"TEST_SYNC_DUP_{uuid.uuid4().hex[:8]}"
        sale = {
            "id": txn_id,
            "transaction_id": txn_id,
            "total": 50.00,
            "created_at": datetime.now().isoformat()
        }
        
        # First submission
        response1 = requests.post(f"{BASE_URL}/api/sync/receive", json={
            "sync_secret": SYNC_SECRET,
            "sales": [sale]
        })
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get("received") == 1
        
        # Second submission (duplicate)
        response2 = requests.post(f"{BASE_URL}/api/sync/receive", json={
            "sync_secret": SYNC_SECRET,
            "sales": [sale]
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get("received") == 0
        assert data2.get("duplicates") == 1
        print(f"PASS: sync/receive correctly detects duplicate (duplicates=1)")


class TestBridgeDownload:
    """Test bridge download endpoint"""
    
    def test_bridge_download_returns_zip(self, auth_headers):
        """GET /api/bridge/download returns valid ZIP file"""
        response = requests.get(f"{BASE_URL}/api/bridge/download", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers.get("content-type") in ["application/zip", "application/x-zip-compressed", "application/octet-stream"]
        # Check ZIP magic bytes
        assert response.content[:4] == b'PK\x03\x04', "Response is not a valid ZIP file"
        print(f"PASS: bridge/download returns valid ZIP ({len(response.content)} bytes)")


class TestAPIRoot:
    """Test API root endpoint"""
    
    def test_api_root_returns_version(self):
        """GET /api/ returns version info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        print(f"PASS: API root returns version {data.get('version')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
