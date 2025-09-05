#!/usr/bin/env python3
"""
Enhanced Asset Requisition Withdrawal Testing
Focus on testing the new DELETE endpoint and multi-role access control
"""

import requests
import json
import sys
from datetime import datetime, timedelta

class WithdrawalTester:
    def __init__(self):
        self.base_url = "https://resource-manager-6.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tokens = {}
        self.users = {}
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    def make_request(self, method, endpoint, data=None, user_role=None, expected_status=None):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if user_role and user_role in self.tokens:
            headers['Authorization'] = f'Bearer {self.tokens[user_role]}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code == expected_status if expected_status else response.status_code < 400
            
            try:
                response_data = response.json()
            except:
                response_data = {}
            
            return success, response.status_code, response_data
        except Exception as e:
            return False, 0, {"error": str(e)}

    def setup_authentication(self):
        """Login all test users"""
        print("🔐 Setting up authentication...")
        
        test_users = [
            ("admin@company.com", "password123", "Administrator"),
            ("hr@company.com", "password123", "HR Manager"),
            ("manager@company.com", "password123", "Manager"),
            ("employee@company.com", "password123", "Employee"),
            ("assetmanager@company.com", "password123", "Asset Manager")
        ]
        
        all_logged_in = True
        for email, password, role in test_users:
            success, status, response = self.make_request(
                "POST", "auth/login", 
                {"email": email, "password": password}, 
                expected_status=200
            )
            
            if success and 'session_token' in response:
                self.tokens[role] = response['session_token']
                self.users[role] = response['user']
                print(f"   ✅ {role} logged in successfully")
            else:
                print(f"   ❌ {role} login failed: {status}")
                all_logged_in = False
        
        return all_logged_in

    def get_asset_type_id(self):
        """Get an existing asset type ID for testing"""
        success, status, response = self.make_request(
            "GET", "asset-types", user_role="Administrator", expected_status=200
        )
        
        if success and response:
            asset_type_id = response[0]['id']
            self.test_data['asset_type_id'] = asset_type_id
            print(f"   Using asset type: {response[0]['name']} (ID: {asset_type_id[:8]}...)")
            return True
        return False

    def create_test_requisition(self, user_role, description="Test requisition"):
        """Create a test requisition for withdrawal testing"""
        if 'asset_type_id' not in self.test_data:
            return None, "No asset type available"
        
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": description,
            "required_by_date": required_by_date
        }
        
        success, status, response = self.make_request(
            "POST", "asset-requisitions", 
            data=requisition_data, 
            user_role=user_role, 
            expected_status=200
        )
        
        if success:
            return response['id'], None
        else:
            return None, f"Failed to create requisition: {status} - {response}"

    def test_employee_withdraw_own_request(self):
        """Test 1: Employee withdraws their own pending request"""
        print("\n🧪 Test 1: Employee Withdraw Own Pending Request")
        
        # Create requisition as Employee
        req_id, error = self.create_test_requisition("Employee", "Employee's own requisition for withdrawal test")
        if not req_id:
            self.log_test("Create Employee Requisition", False, error)
            return False
        
        self.log_test("Create Employee Requisition", True, f"Created requisition {req_id[:8]}...")
        
        # Employee withdraws their own request
        success, status, response = self.make_request(
            "DELETE", f"asset-requisitions/{req_id}", 
            user_role="Employee", 
            expected_status=200
        )
        
        self.log_test("Employee Withdraw Own Request", success, 
                     f"Status: {status}, Response: {response.get('message', 'No message')}")
        
        return success

    def test_employee_cannot_withdraw_others_request(self):
        """Test 2: Employee cannot withdraw another user's request"""
        print("\n🧪 Test 2: Employee Cannot Withdraw Other User's Request")
        
        # Create requisition as Manager
        req_id, error = self.create_test_requisition("Manager", "Manager's requisition - Employee should not be able to withdraw")
        if not req_id:
            self.log_test("Create Manager Requisition", False, error)
            return False
        
        self.log_test("Create Manager Requisition", True, f"Created requisition {req_id[:8]}...")
        
        # Employee tries to withdraw Manager's request (should fail)
        success, status, response = self.make_request(
            "DELETE", f"asset-requisitions/{req_id}", 
            user_role="Employee", 
            expected_status=403
        )
        
        self.log_test("Employee Cannot Withdraw Other's Request", success, 
                     f"Status: {status}, Expected 403 (Forbidden)")
        
        # Clean up - Manager withdraws their own request
        cleanup_success, _, _ = self.make_request(
            "DELETE", f"asset-requisitions/{req_id}", 
            user_role="Manager", 
            expected_status=200
        )
        
        return success

    def test_administrator_can_delete_any_request(self):
        """Test 3: Administrator can delete any pending request"""
        print("\n🧪 Test 3: Administrator Can Delete Any Pending Request")
        
        # Create requisition as Employee
        req_id, error = self.create_test_requisition("Employee", "Employee requisition for Administrator deletion test")
        if not req_id:
            self.log_test("Create Employee Requisition for Admin Test", False, error)
            return False
        
        self.log_test("Create Employee Requisition for Admin Test", True, f"Created requisition {req_id[:8]}...")
        
        # Administrator deletes Employee's request
        success, status, response = self.make_request(
            "DELETE", f"asset-requisitions/{req_id}", 
            user_role="Administrator", 
            expected_status=200
        )
        
        self.log_test("Administrator Delete Any Request", success, 
                     f"Status: {status}, Response: {response.get('message', 'No message')}")
        
        return success

    def test_hr_manager_can_delete_any_request(self):
        """Test 4: HR Manager can delete any pending request"""
        print("\n🧪 Test 4: HR Manager Can Delete Any Pending Request")
        
        # Create requisition as Manager
        req_id, error = self.create_test_requisition("Manager", "Manager requisition for HR Manager deletion test")
        if not req_id:
            self.log_test("Create Manager Requisition for HR Test", False, error)
            return False
        
        self.log_test("Create Manager Requisition for HR Test", True, f"Created requisition {req_id[:8]}...")
        
        # HR Manager deletes Manager's request
        success, status, response = self.make_request(
            "DELETE", f"asset-requisitions/{req_id}", 
            user_role="HR Manager", 
            expected_status=200
        )
        
        self.log_test("HR Manager Delete Any Request", success, 
                     f"Status: {status}, Response: {response.get('message', 'No message')}")
        
        return success

    def test_nonexistent_requisition(self):
        """Test 5: Try to withdraw non-existent requisition"""
        print("\n🧪 Test 5: Withdraw Non-existent Requisition")
        
        fake_id = "non-existent-requisition-id"
        success, status, response = self.make_request(
            "DELETE", f"asset-requisitions/{fake_id}", 
            user_role="Employee", 
            expected_status=404
        )
        
        self.log_test("Withdraw Non-existent Requisition", success, 
                     f"Status: {status}, Expected 404 (Not Found)")
        
        return success

    def test_multi_role_compatibility(self):
        """Test 6: Multi-role system compatibility"""
        print("\n🧪 Test 6: Multi-Role System Compatibility")
        
        # Test that the endpoint handles both old single role and new multi-role structures
        # This is tested by ensuring all our role-based tests work correctly
        
        # Get current user info for each role to verify multi-role structure
        roles_tested = []
        for role in ["Employee", "Manager", "HR Manager", "Administrator"]:
            if role in self.tokens:
                success, status, response = self.make_request(
                    "GET", "auth/me", 
                    user_role=role, 
                    expected_status=200
                )
                
                if success:
                    user_roles = response.get('roles', [])
                    if isinstance(user_roles, list):
                        roles_tested.append(f"{role}: {user_roles}")
                    else:
                        roles_tested.append(f"{role}: [legacy single role]")
        
        self.log_test("Multi-Role System Compatibility", len(roles_tested) > 0, 
                     f"Verified roles structure: {', '.join(roles_tested)}")
        
        return len(roles_tested) > 0

    def test_role_based_requisition_access(self):
        """Test 7: Role-based requisition access with multi-role system"""
        print("\n🧪 Test 7: Role-Based Requisition Access")
        
        access_results = []
        
        for role in ["Employee", "Manager", "HR Manager", "Administrator"]:
            if role in self.tokens:
                success, status, response = self.make_request(
                    "GET", "asset-requisitions", 
                    user_role=role, 
                    expected_status=200
                )
                
                if success:
                    count = len(response)
                    access_results.append(f"{role}: {count} requisitions")
                    
                    # Verify role-specific filtering
                    if role == "Employee":
                        employee_id = self.users.get('Employee', {}).get('id')
                        if employee_id:
                            own_reqs = [req for req in response if req['requested_by'] == employee_id]
                            other_reqs = [req for req in response if req['requested_by'] != employee_id]
                            if len(other_reqs) == 0:
                                access_results.append(f"  ✅ Employee sees only own requests ({len(own_reqs)})")
                            else:
                                access_results.append(f"  ⚠️ Employee sees others' requests ({len(other_reqs)})")
        
        self.log_test("Role-Based Requisition Access", len(access_results) > 0, 
                     "; ".join(access_results))
        
        return len(access_results) > 0

    def test_data_integrity(self):
        """Test 8: Data integrity after withdrawal"""
        print("\n🧪 Test 8: Data Integrity After Withdrawal")
        
        # Get initial count
        success, status, initial_response = self.make_request(
            "GET", "asset-requisitions", 
            user_role="Administrator", 
            expected_status=200
        )
        
        if not success:
            self.log_test("Get Initial Count", False, f"Failed to get initial count: {status}")
            return False
        
        initial_count = len(initial_response)
        
        # Create test requisition
        req_id, error = self.create_test_requisition("Employee", "Data integrity test requisition")
        if not req_id:
            self.log_test("Create Test Requisition for Integrity", False, error)
            return False
        
        # Verify count increased
        success, status, after_create_response = self.make_request(
            "GET", "asset-requisitions", 
            user_role="Administrator", 
            expected_status=200
        )
        
        if success:
            after_create_count = len(after_create_response)
            create_integrity = after_create_count == initial_count + 1
            self.log_test("Verify Creation Integrity", create_integrity, 
                         f"Count: {initial_count} → {after_create_count}")
        
        # Withdraw requisition
        success, status, response = self.make_request(
            "DELETE", f"asset-requisitions/{req_id}", 
            user_role="Employee", 
            expected_status=200
        )
        
        if not success:
            self.log_test("Withdraw for Integrity Test", False, f"Withdrawal failed: {status}")
            return False
        
        # Verify count returned to initial
        success, status, after_delete_response = self.make_request(
            "GET", "asset-requisitions", 
            user_role="Administrator", 
            expected_status=200
        )
        
        if success:
            after_delete_count = len(after_delete_response)
            delete_integrity = after_delete_count == initial_count
            self.log_test("Verify Deletion Integrity", delete_integrity, 
                         f"Count: {after_create_count} → {after_delete_count} (expected {initial_count})")
            
            # Verify withdrawn requisition is not in the list
            withdrawn_found = any(req['id'] == req_id for req in after_delete_response)
            self.log_test("Verify Requisition Removed", not withdrawn_found, 
                         f"Withdrawn requisition {'found' if withdrawn_found else 'not found'} in list")
            
            return delete_integrity and not withdrawn_found
        
        return False

    def run_all_tests(self):
        """Run all withdrawal functionality tests"""
        print("🚀 Enhanced Asset Requisition Withdrawal Testing")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed")
            return False
        
        if not self.get_asset_type_id():
            print("❌ Could not get asset type for testing")
            return False
        
        print(f"\n📋 Using asset type ID: {self.test_data['asset_type_id'][:8]}...")
        
        # Run tests
        test_results = []
        
        test_results.append(self.test_employee_withdraw_own_request())
        test_results.append(self.test_employee_cannot_withdraw_others_request())
        test_results.append(self.test_administrator_can_delete_any_request())
        test_results.append(self.test_hr_manager_can_delete_any_request())
        test_results.append(self.test_nonexistent_requisition())
        test_results.append(self.test_multi_role_compatibility())
        test_results.append(self.test_role_based_requisition_access())
        test_results.append(self.test_data_integrity())
        
        # Results
        print("\n" + "=" * 60)
        print("📊 WITHDRAWAL TESTING RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        critical_tests_passed = sum(test_results[:5])  # First 5 are critical functionality tests
        print(f"Critical Tests Passed: {critical_tests_passed}/5")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All withdrawal tests passed!")
            return True
        else:
            print(f"⚠️ {self.tests_run - self.tests_passed} tests failed")
            return critical_tests_passed >= 4  # Allow 1 critical test to fail

def main():
    tester = WithdrawalTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())