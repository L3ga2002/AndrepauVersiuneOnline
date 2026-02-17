#!/usr/bin/env python3
"""
ANDREPAU POS Backend API Test Suite
Tests all backend functionality including authentication, CRUD operations, POS, and reports.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Use the public endpoint from frontend .env
API_BASE_URL = "https://shop-manager-212.preview.emergentagent.com/api"

class ANDREPAUAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.admin_token = None
        self.casier_token = None
        self.admin_user = None
        self.casier_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.test_supplier_id = None
        self.test_product_id = None
        self.test_sale_id = None
        self.test_nir_id = None

    def log_test(self, name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {error}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "error": error
        })

    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None) -> tuple:
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            return response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return 0, {"error": str(e)}

    def test_api_health(self):
        """Test if API is accessible"""
        status, data = self.make_request('GET', '')
        success = status == 200 and 'ANDREPAU' in str(data)
        self.log_test("API Health Check", success, 
                     f"Status: {status}, Response: {data}" if success else "",
                     f"API not accessible: {status} - {data}" if not success else "")
        return success

    def test_database_seeding(self):
        """Test database seeding"""
        status, data = self.make_request('POST', 'seed')
        # 200 means seeded successfully, 400 means already seeded (both OK)
        success = status in [200, 400]
        self.log_test("Database Seeding", success,
                     f"Status: {status}, Message: {data.get('message', '')}" if success else "",
                     f"Seeding failed: {status} - {data}" if not success else "")
        return success

    def test_admin_login(self):
        """Test admin login"""
        login_data = {"username": "admin", "password": "admin123"}
        status, data = self.make_request('POST', 'auth/login', login_data)
        
        success = status == 200 and 'token' in data and 'user' in data
        if success:
            self.admin_token = data['token']
            self.admin_user = data['user']
            success = self.admin_user['role'] == 'admin'
        
        self.log_test("Admin Login", success,
                     f"User: {self.admin_user['username']}, Role: {self.admin_user['role']}" if success else "",
                     f"Login failed: {status} - {data}" if not success else "")
        return success

    def test_casier_login(self):
        """Test casier login"""
        login_data = {"username": "casier", "password": "casier123"}
        status, data = self.make_request('POST', 'auth/login', login_data)
        
        success = status == 200 and 'token' in data and 'user' in data
        if success:
            self.casier_token = data['token']
            self.casier_user = data['user']
            success = self.casier_user['role'] == 'casier'
        
        self.log_test("Casier Login", success,
                     f"User: {self.casier_user['username']}, Role: {self.casier_user['role']}" if success else "",
                     f"Login failed: {status} - {data}" if not success else "")
        return success

    def test_auth_me(self):
        """Test auth/me endpoint"""
        status, data = self.make_request('GET', 'auth/me', token=self.admin_token)
        success = status == 200 and data.get('username') == 'admin'
        self.log_test("Auth Me Endpoint", success,
                     f"Retrieved user: {data.get('username')}" if success else "",
                     f"Auth me failed: {status} - {data}" if not success else "")
        return success

    def test_suppliers_crud(self):
        """Test suppliers CRUD operations"""
        # Create supplier
        supplier_data = {
            "nume": "Test Supplier Ltd",
            "telefon": "0721123456",
            "email": "test@supplier.com",
            "adresa": "Test Address 123"
        }
        
        status, data = self.make_request('POST', 'suppliers', supplier_data, self.admin_token)
        success = status == 200 and 'id' in data
        if success:
            self.test_supplier_id = data['id']
        
        self.log_test("Create Supplier", success,
                     f"Created supplier ID: {self.test_supplier_id}" if success else "",
                     f"Create failed: {status} - {data}" if not success else "")
        
        if not success:
            return False

        # Read suppliers
        status, data = self.make_request('GET', 'suppliers', token=self.admin_token)
        success = status == 200 and isinstance(data, list) and len(data) > 0
        self.log_test("Read Suppliers", success,
                     f"Found {len(data)} suppliers" if success else "",
                     f"Read failed: {status} - {data}" if not success else "")

        # Update supplier
        update_data = {"nume": "Updated Test Supplier Ltd"}
        status, data = self.make_request('PUT', f'suppliers/{self.test_supplier_id}', update_data, self.admin_token)
        success = status == 200 and data.get('nume') == update_data['nume']
        self.log_test("Update Supplier", success,
                     f"Updated supplier name to: {data.get('nume')}" if success else "",
                     f"Update failed: {status} - {data}" if not success else "")

        return True

    def test_products_crud(self):
        """Test products CRUD operations"""
        # Create product
        product_data = {
            "nume": "Test Product",
            "categorie": "Test Category",
            "furnizor_id": self.test_supplier_id,
            "cod_bare": "1234567890123",
            "pret_achizitie": 10.0,
            "pret_vanzare": 15.0,
            "tva": 19.0,
            "unitate": "buc",
            "stoc": 100.0,
            "stoc_minim": 10.0,
            "descriere": "Test product description"
        }
        
        status, data = self.make_request('POST', 'products', product_data, self.admin_token)
        success = status == 201 and 'id' in data
        if success:
            self.test_product_id = data['id']
        
        self.log_test("Create Product", success,
                     f"Created product ID: {self.test_product_id}" if success else "",
                     f"Create failed: {status} - {data}" if not success else "")
        
        if not success:
            return False

        # Read products
        status, data = self.make_request('GET', 'products', token=self.admin_token)
        success = status == 200 and isinstance(data, list) and len(data) > 0
        self.log_test("Read Products", success,
                     f"Found {len(data)} products" if success else "",
                     f"Read failed: {status} - {data}" if not success else "")

        # Search products
        status, data = self.make_request('GET', 'products?search=Test', token=self.admin_token)
        success = status == 200 and isinstance(data, list)
        self.log_test("Search Products", success,
                     f"Search returned {len(data)} products" if success else "",
                     f"Search failed: {status} - {data}" if not success else "")

        # Get product by barcode
        status, data = self.make_request('GET', f'products/barcode/{product_data["cod_bare"]}', token=self.admin_token)
        success = status == 200 and data.get('id') == self.test_product_id
        self.log_test("Get Product by Barcode", success,
                     f"Found product by barcode: {data.get('nume')}" if success else "",
                     f"Barcode lookup failed: {status} - {data}" if not success else "")

        # Update product
        update_data = {"nume": "Updated Test Product", "pret_vanzare": 20.0}
        status, data = self.make_request('PUT', f'products/{self.test_product_id}', update_data, self.admin_token)
        success = status == 200 and data.get('nume') == update_data['nume']
        self.log_test("Update Product", success,
                     f"Updated product: {data.get('nume')}" if success else "",
                     f"Update failed: {status} - {data}" if not success else "")

        return True

    def test_categories(self):
        """Test categories endpoint"""
        status, data = self.make_request('GET', 'categories', token=self.admin_token)
        success = status == 200 and isinstance(data, list)
        self.log_test("Get Categories", success,
                     f"Found {len(data)} categories" if success else "",
                     f"Categories failed: {status} - {data}" if not success else "")
        return success

    def test_pos_sale(self):
        """Test POS sale creation"""
        sale_data = {
            "items": [{
                "product_id": self.test_product_id,
                "nume": "Updated Test Product",
                "cantitate": 2.0,
                "pret_unitar": 20.0,
                "tva": 19.0
            }],
            "subtotal": 40.0,
            "tva_total": 6.39,
            "total": 40.0,
            "discount_percent": 0.0,
            "metoda_plata": "numerar",
            "suma_numerar": 40.0,
            "suma_card": 0.0,
            "casier_id": self.casier_user['id']
        }
        
        status, data = self.make_request('POST', 'sales', sale_data, self.casier_token)
        success = status == 201 and 'id' in data and 'numar_bon' in data
        if success:
            self.test_sale_id = data['id']
        
        self.log_test("Create POS Sale", success,
                     f"Created sale ID: {self.test_sale_id}, Bon: {data.get('numar_bon')}" if success else "",
                     f"Sale creation failed: {status} - {data}" if not success else "")
        return success

    def test_sales_history(self):
        """Test sales history retrieval"""
        status, data = self.make_request('GET', 'sales', token=self.admin_token)
        success = status == 200 and isinstance(data, list) and len(data) > 0
        self.log_test("Get Sales History", success,
                     f"Found {len(data)} sales" if success else "",
                     f"Sales history failed: {status} - {data}" if not success else "")
        return success

    def test_nir_creation(self):
        """Test NIR (goods reception) creation"""
        nir_data = {
            "furnizor_id": self.test_supplier_id,
            "numar_factura": "TEST-001",
            "items": [{
                "product_id": self.test_product_id,
                "nume": "Updated Test Product",
                "cantitate": 50.0,
                "pret_achizitie": 10.0
            }],
            "total": 500.0
        }
        
        status, data = self.make_request('POST', 'nir', nir_data, self.admin_token)
        success = status == 201 and 'id' in data and 'numar_nir' in data
        if success:
            self.test_nir_id = data['id']
        
        self.log_test("Create NIR", success,
                     f"Created NIR ID: {self.test_nir_id}, Number: {data.get('numar_nir')}" if success else "",
                     f"NIR creation failed: {status} - {data}" if not success else "")
        return success

    def test_stock_dashboard(self):
        """Test stock dashboard"""
        status, data = self.make_request('GET', 'stock/dashboard', token=self.admin_token)
        success = status == 200 and 'total_products' in data and 'total_value' in data
        self.log_test("Stock Dashboard", success,
                     f"Products: {data.get('total_products')}, Value: {data.get('total_value')}" if success else "",
                     f"Dashboard failed: {status} - {data}" if not success else "")
        return success

    def test_stock_alerts(self):
        """Test stock alerts"""
        status, data = self.make_request('GET', 'stock/alerts', token=self.admin_token)
        success = status == 200 and isinstance(data, list)
        self.log_test("Stock Alerts", success,
                     f"Found {len(data)} stock alerts" if success else "",
                     f"Alerts failed: {status} - {data}" if not success else "")
        return success

    def test_reports(self):
        """Test reports functionality"""
        # Sales report
        status, data = self.make_request('GET', 'reports/sales?period=today', token=self.admin_token)
        success = status == 200 and 'total_sales' in data
        self.log_test("Sales Report", success,
                     f"Total sales: {data.get('total_sales')}" if success else "",
                     f"Sales report failed: {status} - {data}" if not success else "")

        # Top products
        status, data = self.make_request('GET', 'reports/top-products', token=self.admin_token)
        success = status == 200 and isinstance(data, list)
        self.log_test("Top Products Report", success,
                     f"Found {len(data)} top products" if success else "",
                     f"Top products failed: {status} - {data}" if not success else "")

        # Top categories
        status, data = self.make_request('GET', 'reports/top-categories', token=self.admin_token)
        success = status == 200 and isinstance(data, list)
        self.log_test("Top Categories Report", success,
                     f"Found {len(data)} top categories" if success else "",
                     f"Top categories failed: {status} - {data}" if not success else "")

        # Profit report (admin only)
        status, data = self.make_request('GET', 'reports/profit?period=today', token=self.admin_token)
        success = status == 200 and 'profit' in data
        self.log_test("Profit Report", success,
                     f"Profit: {data.get('profit')}" if success else "",
                     f"Profit report failed: {status} - {data}" if not success else "")

        # Daily sales
        status, data = self.make_request('GET', 'reports/daily-sales', token=self.admin_token)
        success = status == 200 and isinstance(data, list)
        self.log_test("Daily Sales Report", success,
                     f"Found {len(data)} daily records" if success else "",
                     f"Daily sales failed: {status} - {data}" if not success else "")

        return True

    def test_user_management(self):
        """Test user management (admin only)"""
        # Get users
        status, data = self.make_request('GET', 'users', token=self.admin_token)
        success = status == 200 and isinstance(data, list) and len(data) >= 2
        self.log_test("Get Users", success,
                     f"Found {len(data)} users" if success else "",
                     f"Get users failed: {status} - {data}" if not success else "")

        # Test casier cannot access users
        status, data = self.make_request('GET', 'users', token=self.casier_token)
        success = status == 403
        self.log_test("Casier Access Restriction", success,
                     "Casier correctly denied access to users" if success else "",
                     f"Casier should not access users: {status} - {data}" if not success else "")

        return True

    def test_backup(self):
        """Test database backup"""
        status, data = self.make_request('GET', 'backup', token=self.admin_token)
        success = status == 200 and 'products' in data and 'suppliers' in data
        self.log_test("Database Backup", success,
                     f"Backup contains {len(data.get('products', []))} products, {len(data.get('suppliers', []))} suppliers" if success else "",
                     f"Backup failed: {status} - {data}" if not success else "")
        return success

    def test_role_based_access(self):
        """Test role-based access control"""
        # Casier should not be able to create products
        product_data = {
            "nume": "Unauthorized Product",
            "categorie": "Test",
            "pret_achizitie": 10.0,
            "pret_vanzare": 15.0,
            "stoc": 10.0
        }
        
        status, data = self.make_request('POST', 'products', product_data, self.casier_token)
        success = status == 403
        self.log_test("Casier Product Creation Restriction", success,
                     "Casier correctly denied product creation" if success else "",
                     f"Casier should not create products: {status} - {data}" if not success else "")

        # Casier should not access profit reports
        status, data = self.make_request('GET', 'reports/profit', token=self.casier_token)
        success = status == 403
        self.log_test("Casier Profit Report Restriction", success,
                     "Casier correctly denied profit access" if success else "",
                     f"Casier should not access profit: {status} - {data}" if not success else "")

        return True

    def cleanup_test_data(self):
        """Clean up test data"""
        # Delete test product
        if self.test_product_id:
            status, data = self.make_request('DELETE', f'products/{self.test_product_id}', token=self.admin_token)
            success = status == 200
            self.log_test("Cleanup Test Product", success,
                         "Test product deleted" if success else "",
                         f"Product cleanup failed: {status} - {data}" if not success else "")

        # Delete test supplier
        if self.test_supplier_id:
            status, data = self.make_request('DELETE', f'suppliers/{self.test_supplier_id}', token=self.admin_token)
            success = status == 200
            self.log_test("Cleanup Test Supplier", success,
                         "Test supplier deleted" if success else "",
                         f"Supplier cleanup failed: {status} - {data}" if not success else "")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting ANDREPAU Backend API Tests")
        print(f"📡 Testing API at: {self.base_url}")
        print("=" * 60)

        # Core functionality tests
        if not self.test_api_health():
            print("❌ API not accessible, stopping tests")
            return False

        if not self.test_database_seeding():
            print("❌ Database seeding failed, stopping tests")
            return False

        if not self.test_admin_login():
            print("❌ Admin login failed, stopping tests")
            return False

        if not self.test_casier_login():
            print("❌ Casier login failed, stopping tests")
            return False

        # Authentication tests
        self.test_auth_me()

        # CRUD operations
        self.test_suppliers_crud()
        self.test_products_crud()
        self.test_categories()

        # POS functionality
        self.test_pos_sale()
        self.test_sales_history()

        # Stock management
        self.test_nir_creation()
        self.test_stock_dashboard()
        self.test_stock_alerts()

        # Reports
        self.test_reports()

        # User management
        self.test_user_management()

        # Security
        self.test_role_based_access()

        # Backup
        self.test_backup()

        # Cleanup
        self.cleanup_test_data()

        print("=" * 60)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

    def get_test_summary(self):
        """Get test summary for reporting"""
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = ANDREPAUAPITester()
    
    try:
        success = tester.run_all_tests()
        
        # Save detailed results
        summary = tester.get_test_summary()
        with open('/app/test_reports/backend_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())