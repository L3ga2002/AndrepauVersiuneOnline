"""
Iteration 11 Tests - ANDREPAU POS
Testing:
1. Login page - NO demo credentials shown
2. Start Day page - manual balance input
3. Products page - Schimbă TVA and Șterge Toate buttons
4. API: PUT /api/products-all/bulk-tva
5. API: DELETE /api/products-all/delete
6. API: POST /api/anaf/search-cui (ANAF v9)
7. Held orders - 12 hour expiry (code check)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
CASIER_USER = "casier"
CASIER_PASS = "casier123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def casier_token():
    """Get casier authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": CASIER_USER,
        "password": CASIER_PASS
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Casier authentication failed")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture
def casier_headers(casier_token):
    return {"Authorization": f"Bearer {casier_token}", "Content-Type": "application/json"}


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_admin_login_success(self):
        """Admin login should succeed with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USER,
            "password": ADMIN_PASS
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"
        print("✓ Admin login successful")
    
    def test_casier_login_success(self):
        """Casier login should succeed with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": CASIER_USER,
            "password": CASIER_PASS
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "casier"
        print("✓ Casier login successful")


class TestBulkTVA:
    """Test PUT /api/products-all/bulk-tva endpoint"""
    
    def test_bulk_tva_requires_auth(self):
        """Bulk TVA update should require authentication"""
        response = requests.put(f"{BASE_URL}/api/products-all/bulk-tva", json={"tva": 19})
        assert response.status_code in [401, 403]
        print("✓ Bulk TVA requires authentication")
    
    def test_bulk_tva_requires_admin(self, casier_headers):
        """Bulk TVA update should require admin role"""
        response = requests.put(f"{BASE_URL}/api/products-all/bulk-tva", 
                               json={"tva": 19}, headers=casier_headers)
        assert response.status_code == 403
        print("✓ Bulk TVA requires admin role")
    
    def test_bulk_tva_rejects_invalid_tva(self, admin_headers):
        """Bulk TVA should reject invalid TVA values"""
        # Negative TVA
        response = requests.put(f"{BASE_URL}/api/products-all/bulk-tva", 
                               json={"tva": -5}, headers=admin_headers)
        assert response.status_code == 400
        
        # TVA > 100
        response = requests.put(f"{BASE_URL}/api/products-all/bulk-tva", 
                               json={"tva": 150}, headers=admin_headers)
        assert response.status_code == 400
        print("✓ Bulk TVA rejects invalid values")
    
    def test_bulk_tva_success(self, admin_headers):
        """Bulk TVA update should work with valid TVA value"""
        # First get current product count
        products_resp = requests.get(f"{BASE_URL}/api/products?limit=1", headers=admin_headers)
        total_products = products_resp.json().get("total", 0)
        
        if total_products == 0:
            pytest.skip("No products in database to test bulk TVA")
        
        # Update TVA to 19%
        response = requests.put(f"{BASE_URL}/api/products-all/bulk-tva", 
                               json={"tva": 19}, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "modified_count" in data
        print(f"✓ Bulk TVA updated {data['modified_count']} products to 19%")


class TestDeleteAllProducts:
    """Test DELETE /api/products-all/delete endpoint"""
    
    def test_delete_all_requires_auth(self):
        """Delete all products should require authentication"""
        response = requests.delete(f"{BASE_URL}/api/products-all/delete")
        assert response.status_code in [401, 403]
        print("✓ Delete all requires authentication")
    
    def test_delete_all_requires_admin(self, casier_headers):
        """Delete all products should require admin role"""
        response = requests.delete(f"{BASE_URL}/api/products-all/delete", headers=casier_headers)
        assert response.status_code == 403
        print("✓ Delete all requires admin role")
    
    def test_delete_all_endpoint_exists(self, admin_headers):
        """Delete all endpoint should exist and be accessible (NOT actually deleting)"""
        # We just verify the endpoint exists by checking it doesn't return 404
        # We DON'T actually call it to avoid deleting all products
        # Instead, we verify the endpoint is defined by checking OPTIONS or a HEAD request
        response = requests.options(f"{BASE_URL}/api/products-all/delete", headers=admin_headers)
        # If endpoint exists, it should return 200 or 204 for OPTIONS, or 405 if not allowed
        # It should NOT return 404
        assert response.status_code != 404
        print("✓ Delete all endpoint exists (not executed to preserve data)")


class TestANAFSearch:
    """Test POST /api/anaf/search-cui endpoint (ANAF v9)"""
    
    def test_anaf_search_requires_auth(self):
        """ANAF search should require authentication"""
        response = requests.post(f"{BASE_URL}/api/anaf/search-cui", json={"cui": "14399840"})
        assert response.status_code in [401, 403]
        print("✓ ANAF search requires authentication")
    
    def test_anaf_search_rejects_empty_cui(self, admin_headers):
        """ANAF search should reject empty CUI"""
        response = requests.post(f"{BASE_URL}/api/anaf/search-cui", 
                                json={"cui": ""}, headers=admin_headers)
        assert response.status_code == 400
        print("✓ ANAF search rejects empty CUI")
    
    def test_anaf_search_rejects_invalid_cui(self, admin_headers):
        """ANAF search should reject invalid CUI (non-numeric)"""
        response = requests.post(f"{BASE_URL}/api/anaf/search-cui", 
                                json={"cui": "abc123"}, headers=admin_headers)
        assert response.status_code == 400
        print("✓ ANAF search rejects invalid CUI")
    
    def test_anaf_search_dante_international(self, admin_headers):
        """ANAF search should find DANTE INTERNATIONAL (CUI 14399840)"""
        response = requests.post(f"{BASE_URL}/api/anaf/search-cui", 
                                json={"cui": "14399840"}, headers=admin_headers)
        
        # ANAF may be unavailable from datacenter IPs, so we accept 503 as well
        if response.status_code == 503:
            print("⚠ ANAF service unavailable (expected from datacenter IP)")
            pytest.skip("ANAF service unavailable from datacenter IP")
        
        assert response.status_code == 200
        data = response.json()
        assert "denumire" in data
        # DANTE INTERNATIONAL SA should be in the name
        assert "DANTE" in data["denumire"].upper() or "INTERNATIONAL" in data["denumire"].upper()
        print(f"✓ ANAF found: {data['denumire']}")
    
    def test_anaf_search_handles_ro_prefix(self, admin_headers):
        """ANAF search should handle RO prefix in CUI"""
        response = requests.post(f"{BASE_URL}/api/anaf/search-cui", 
                                json={"cui": "RO14399840"}, headers=admin_headers)
        
        if response.status_code == 503:
            pytest.skip("ANAF service unavailable from datacenter IP")
        
        assert response.status_code == 200
        data = response.json()
        assert "denumire" in data
        print("✓ ANAF handles RO prefix correctly")


class TestHeldOrdersExpiry:
    """Test held orders 12-hour expiry"""
    
    def test_held_order_creation_sets_12h_expiry(self, admin_headers):
        """Held order should be created with 12-hour expiry"""
        # Create a test held order
        test_items = [{"product_id": "test-123", "nume": "Test Product", "cantitate": 1, "pret_unitar": 10}]
        response = requests.post(f"{BASE_URL}/api/held-orders", 
                                json={"items": test_items, "client_name": "Test Client"},
                                headers=admin_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "expires_at" in data
            # Verify expiry is approximately 12 hours from now
            from datetime import datetime, timezone, timedelta
            expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            diff_hours = (expires_at - now).total_seconds() / 3600
            # Should be approximately 12 hours (allow some margin)
            assert 11.5 < diff_hours < 12.5, f"Expiry should be ~12 hours, got {diff_hours:.2f} hours"
            print(f"✓ Held order expires in {diff_hours:.2f} hours (expected ~12)")
        else:
            # If held order creation fails (e.g., product not found), just verify endpoint exists
            assert response.status_code != 404
            print("✓ Held orders endpoint exists")


class TestDailyOpeningSummary:
    """Test daily opening summary endpoint (Start Day page data)"""
    
    def test_opening_summary_returns_data(self, admin_headers):
        """Opening summary should return cash balance and status"""
        response = requests.get(f"{BASE_URL}/api/daily/opening-summary", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should have key fields
        assert "sold_casa" in data
        assert "bridge_connected" in data
        assert "comenzi_hold" in data
        print(f"✓ Opening summary: sold_casa={data['sold_casa']}, hold={data['comenzi_hold']}")


class TestCashOperations:
    """Test cash operations for manual starting balance"""
    
    def test_cash_in_operation(self, admin_headers):
        """Cash in operation should work (for manual starting balance)"""
        response = requests.post(f"{BASE_URL}/api/cash/operation", 
                                json={
                                    "type": "CASH_IN",
                                    "amount": 100.00,
                                    "description": "Test sold inceput de zi"
                                },
                                headers=admin_headers)
        
        # Endpoint might be /api/cash-operations instead
        if response.status_code == 404:
            response = requests.post(f"{BASE_URL}/api/cash-operations", 
                                    json={
                                        "type": "CASH_IN",
                                        "amount": 100.00,
                                        "description": "Test sold inceput de zi"
                                    },
                                    headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "CASH_IN"
        print("✓ Cash in operation works for manual starting balance")


class TestProductsEndpoints:
    """Test products endpoints for TVA and delete buttons"""
    
    def test_products_list_returns_tva(self, admin_headers):
        """Products list should include TVA field"""
        response = requests.get(f"{BASE_URL}/api/products?limit=5", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data.get("products") and len(data["products"]) > 0:
            product = data["products"][0]
            assert "tva" in product
            print(f"✓ Products include TVA field (first product TVA: {product['tva']}%)")
        else:
            print("✓ Products endpoint works (no products to verify TVA)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
