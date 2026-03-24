"""
ANDREPAU POS - Held Orders API Tests
Tests for held orders functionality with stock reservation
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHeldOrdersAPI:
    """Held Orders endpoint tests - stock reservation feature"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture
    def casier_token(self):
        """Get casier authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "casier",
            "password": "casier123"
        })
        assert response.status_code == 200, f"Casier login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture
    def test_product(self, admin_token):
        """Get a test product with stock"""
        response = requests.get(
            f"{BASE_URL}/api/products?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        products = response.json().get("products", [])
        assert len(products) > 0, "No products found for testing"
        return products[0]
    
    def test_create_held_order_success(self, casier_token, test_product):
        """Test creating a held order - should deduct stock"""
        # Get initial stock
        initial_stock = test_product["stoc"]
        product_id = test_product["id"]
        
        # Create held order
        response = requests.post(
            f"{BASE_URL}/api/held-orders",
            headers={"Authorization": f"Bearer {casier_token}", "Content-Type": "application/json"},
            json={
                "items": [{
                    "product_id": product_id,
                    "nume": test_product["nume"],
                    "cantitate": 1,
                    "pret_unitar": test_product["pret_vanzare"],
                    "tva": test_product["tva"],
                    "unitate": test_product.get("unitate", "buc")
                }],
                "discount": 0
            }
        )
        assert response.status_code == 200, f"Create held order failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "items" in data
        assert "status" in data
        assert data["status"] == "active"
        assert "created_at" in data
        assert "expires_at" in data
        assert "created_by_name" in data
        
        # Verify stock was deducted
        product_response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert product_response.status_code == 200
        new_stock = product_response.json()["stoc"]
        assert new_stock == initial_stock - 1, f"Stock not deducted: expected {initial_stock - 1}, got {new_stock}"
        
        # Cleanup - cancel the held order to restore stock
        cancel_response = requests.post(
            f"{BASE_URL}/api/held-orders/{data['id']}/cancel",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert cancel_response.status_code == 200
    
    def test_create_held_order_empty_cart(self, casier_token):
        """Test creating held order with empty cart - should fail"""
        response = requests.post(
            f"{BASE_URL}/api/held-orders",
            headers={"Authorization": f"Bearer {casier_token}", "Content-Type": "application/json"},
            json={"items": [], "discount": 0}
        )
        assert response.status_code == 400
        assert "Nu sunt produse" in response.json().get("detail", "")
    
    def test_get_held_orders_list(self, casier_token):
        """Test fetching held orders list"""
        response = requests.get(
            f"{BASE_URL}/api/held-orders",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total" in data
        assert isinstance(data["orders"], list)
    
    def test_restore_held_order(self, casier_token, test_product):
        """Test restoring a held order - should restore stock"""
        product_id = test_product["id"]
        quantity_to_hold = 2
        
        # Get initial stock (fresh read)
        product_response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        initial_stock = product_response.json()["stoc"]
        
        # Create held order (deducts stock)
        create_response = requests.post(
            f"{BASE_URL}/api/held-orders",
            headers={"Authorization": f"Bearer {casier_token}", "Content-Type": "application/json"},
            json={
                "items": [{
                    "product_id": product_id,
                    "nume": test_product["nume"],
                    "cantitate": quantity_to_hold,
                    "pret_unitar": test_product["pret_vanzare"],
                    "tva": test_product["tva"],
                    "unitate": test_product.get("unitate", "buc")
                }],
                "discount": 5
            }
        )
        assert create_response.status_code == 200
        order_id = create_response.json()["id"]
        
        # Verify stock was deducted by the correct amount
        product_response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        stock_after_hold = product_response.json()["stoc"]
        assert stock_after_hold == initial_stock - quantity_to_hold, f"Stock not deducted correctly: expected {initial_stock - quantity_to_hold}, got {stock_after_hold}"
        
        # Restore the held order
        restore_response = requests.post(
            f"{BASE_URL}/api/held-orders/{order_id}/restore",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert restore_response.status_code == 200
        restored_order = restore_response.json()
        
        # Verify order data returned
        assert "items" in restored_order
        assert len(restored_order["items"]) == 1
        assert restored_order["items"][0]["cantitate"] == quantity_to_hold
        
        # Verify stock was restored (should be back to stock_after_hold + quantity_to_hold = initial_stock)
        product_response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        stock_after_restore = product_response.json()["stoc"]
        # Stock should be restored by the quantity that was held
        assert stock_after_restore == stock_after_hold + quantity_to_hold, f"Stock not restored correctly: expected {stock_after_hold + quantity_to_hold}, got {stock_after_restore}"
    
    def test_cancel_held_order(self, casier_token, test_product):
        """Test cancelling a held order - should restore stock"""
        product_id = test_product["id"]
        
        # Get initial stock
        product_response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        initial_stock = product_response.json()["stoc"]
        
        # Create held order
        create_response = requests.post(
            f"{BASE_URL}/api/held-orders",
            headers={"Authorization": f"Bearer {casier_token}", "Content-Type": "application/json"},
            json={
                "items": [{
                    "product_id": product_id,
                    "nume": test_product["nume"],
                    "cantitate": 3,
                    "pret_unitar": test_product["pret_vanzare"],
                    "tva": test_product["tva"],
                    "unitate": test_product.get("unitate", "buc")
                }],
                "discount": 0
            }
        )
        assert create_response.status_code == 200
        order_id = create_response.json()["id"]
        
        # Verify stock was deducted
        product_response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        stock_after_hold = product_response.json()["stoc"]
        assert stock_after_hold == initial_stock - 3
        
        # Cancel the held order
        cancel_response = requests.post(
            f"{BASE_URL}/api/held-orders/{order_id}/cancel",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert cancel_response.status_code == 200
        assert "stoc restaurat" in cancel_response.json().get("message", "").lower()
        
        # Verify stock was restored
        product_response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        stock_after_cancel = product_response.json()["stoc"]
        assert stock_after_cancel == initial_stock, f"Stock not restored after cancel: expected {initial_stock}, got {stock_after_cancel}"
    
    def test_restore_nonexistent_order(self, casier_token):
        """Test restoring a non-existent order - should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/held-orders/nonexistent-id-12345/restore",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 404
    
    def test_cancel_nonexistent_order(self, casier_token):
        """Test cancelling a non-existent order - should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/held-orders/nonexistent-id-12345/cancel",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        assert response.status_code == 404
    
    def test_held_order_requires_auth(self):
        """Test that held orders endpoints require authentication"""
        # GET without auth
        response = requests.get(f"{BASE_URL}/api/held-orders")
        assert response.status_code == 403
        
        # POST without auth
        response = requests.post(
            f"{BASE_URL}/api/held-orders",
            json={"items": [], "discount": 0}
        )
        assert response.status_code == 403
    
    def test_held_order_with_discount(self, casier_token, test_product):
        """Test creating held order with discount"""
        response = requests.post(
            f"{BASE_URL}/api/held-orders",
            headers={"Authorization": f"Bearer {casier_token}", "Content-Type": "application/json"},
            json={
                "items": [{
                    "product_id": test_product["id"],
                    "nume": test_product["nume"],
                    "cantitate": 1,
                    "pret_unitar": test_product["pret_vanzare"],
                    "tva": test_product["tva"],
                    "unitate": test_product.get("unitate", "buc")
                }],
                "discount": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("discount") == 10
        
        # Cleanup
        requests.post(
            f"{BASE_URL}/api/held-orders/{data['id']}/cancel",
            headers={"Authorization": f"Bearer {casier_token}"}
        )


class TestSalesNoReceiptPreview:
    """Test that sales complete without showing receipt preview dialog"""
    
    @pytest.fixture
    def casier_token(self):
        """Get casier authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "casier",
            "password": "casier123"
        })
        return response.json()["token"]
    
    @pytest.fixture
    def casier_user(self, casier_token):
        """Get casier user info"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        return response.json()
    
    @pytest.fixture
    def test_product(self, casier_token):
        """Get a test product"""
        response = requests.get(
            f"{BASE_URL}/api/products?limit=1",
            headers={"Authorization": f"Bearer {casier_token}"}
        )
        products = response.json().get("products", [])
        return products[0] if products else None
    
    def test_sale_completes_successfully(self, casier_token, casier_user, test_product):
        """Test that a sale can be created successfully"""
        if not test_product:
            pytest.skip("No products available for testing")
        
        response = requests.post(
            f"{BASE_URL}/api/sales",
            headers={"Authorization": f"Bearer {casier_token}", "Content-Type": "application/json"},
            json={
                "items": [{
                    "product_id": test_product["id"],
                    "nume": test_product["nume"],
                    "cantitate": 1,
                    "pret_unitar": test_product["pret_vanzare"],
                    "tva": test_product["tva"]
                }],
                "subtotal": test_product["pret_vanzare"],
                "tva_total": test_product["pret_vanzare"] * test_product["tva"] / (100 + test_product["tva"]),
                "total": test_product["pret_vanzare"],
                "discount_percent": 0,
                "metoda_plata": "numerar",
                "suma_numerar": test_product["pret_vanzare"],
                "suma_card": 0,
                "casier_id": casier_user["id"],
                "fiscal_status": "none"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "numar_bon" in data
        assert "id" in data
        assert data["fiscal_status"] == "none"
