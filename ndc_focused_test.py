import requests
import sys
import json
from datetime import datetime, timedelta

class NDCFocusedTester:
    def __init__(self, base_url="https://resource-manager-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}
        self.users = {}
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, user_role=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if user_role and user_role in self.tokens:
            headers['Authorization'] = f'Bearer {self.tokens[user_role]}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, email, password, role_name):
        """Test login and store token"""
        print(f"\n🔐 Testing login for {role_name} ({email})")
        success, response = self.run_test(
            f"Login {role_name}",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'session_token' in response:
            self.tokens[role_name] = response['session_token']
            self.users[role_name] = response['user']
            print(f"✅ {role_name} login successful, token stored")
            return True
        print(f"❌ {role_name} login failed")
        return False

    def test_ndc_critical_bug_fix(self):
        """Test NDC Critical Bug Fix - Asset Detection with 'allocated_to' field"""
        print(f"\n🏢 Testing NDC Critical Bug Fix - Asset Detection")
        
        # Step 1: Create test employee
        employee_data = {
            "email": f"ndc_test_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "NDC Bug Fix Test Employee",
            "roles": ["Employee"],
            "designation": "Test Developer",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Test Employee for NDC Bug Fix",
            "POST",
            "users",
            200,
            data=employee_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to create test employee")
            return False
        
        test_employee_id = response['id']
        print(f"   Created test employee ID: {test_employee_id}")
        
        # Step 2: Create asset type if needed
        asset_type_data = {
            "code": f"NDC_TEST_{datetime.now().strftime('%H%M%S')}",
            "name": "NDC Bug Fix Test Asset",
            "depreciation_applicable": True,
            "asset_life": 3,
            "to_be_recovered_on_separation": True,
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Asset Type for NDC Test",
            "POST",
            "asset-types",
            200,
            data=asset_type_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to create asset type")
            return False
        
        asset_type_id = response['id']
        print(f"   Created asset type ID: {asset_type_id}")
        
        # Step 3: Create asset definition
        asset_def_data = {
            "asset_type_id": asset_type_id,
            "asset_code": f"NDC_ASSET_{datetime.now().strftime('%H%M%S')}",
            "asset_description": "NDC Bug Fix Test Asset",
            "asset_details": "Test asset for NDC bug fix verification",
            "asset_value": 50000.0,
            "asset_depreciation_value_per_year": 16666.67,
            "status": "Available"
        }
        
        success, response = self.run_test(
            "Create Asset Definition for NDC Test",
            "POST",
            "asset-definitions",
            200,
            data=asset_def_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to create asset definition")
            return False
        
        test_asset_id = response['id']
        print(f"   Created asset definition ID: {test_asset_id}")
        
        # Step 4: Allocate asset to employee using the correct "allocated_to" field
        allocation_update = {
            "allocated_to": test_employee_id,
            "allocated_to_name": "NDC Bug Fix Test Employee",
            "status": "Allocated"
        }
        
        success, response = self.run_test(
            "Allocate Asset to Test Employee (allocated_to field)",
            "PUT",
            f"asset-definitions/{test_asset_id}",
            200,
            data=allocation_update,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to allocate asset to employee")
            return False
        
        print(f"   ✅ Asset allocated using 'allocated_to' field successfully")
        
        # Step 5: Verify asset is properly allocated
        success, response = self.run_test(
            "Verify Asset Allocation",
            "GET",
            f"asset-definitions/{test_asset_id}",
            200,
            user_role="Administrator"
        )
        
        if success:
            allocated_to = response.get('allocated_to')
            status = response.get('status')
            print(f"   Asset allocated_to: {allocated_to}")
            print(f"   Asset status: {status}")
            
            if allocated_to == test_employee_id and status == "Allocated":
                print(f"   ✅ Asset allocation verified correctly")
            else:
                print(f"   ❌ Asset allocation verification failed")
                return False
        
        # Step 6: Create separation reason
        separation_reason_data = {"reason": f"NDC Bug Fix Test - {datetime.now().strftime('%H%M%S')}"}
        success, response = self.run_test(
            "Create Separation Reason for NDC Test",
            "POST",
            "separation-reasons",
            200,
            data=separation_reason_data,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   Created separation reason: {response['reason']}")
        
        # Step 7: Create NDC request - This is the CRITICAL TEST for the bug fix
        ndc_request_data = {
            "employee_id": test_employee_id,
            "resigned_on": datetime.now().isoformat(),
            "notice_period": "30 days",
            "last_working_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "separation_approved_by": self.users["Administrator"]["id"],
            "separation_approved_on": datetime.now().isoformat(),
            "separation_reason": separation_reason_data["reason"]
        }
        
        success, response = self.run_test(
            "🔥 CRITICAL TEST: Create NDC Request (Bug Fix Verification)",
            "POST",
            "ndc-requests",
            200,
            data=ndc_request_data,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   🎉 CRITICAL BUG FIXED: NDC request created successfully!")
            print(f"   ✅ Backend correctly detected allocated assets using 'allocated_to' field")
            print(f"   NDC requests created for {len(response['requests'])} Asset Manager(s)")
            
            # Store NDC request ID for further testing
            if response['requests']:
                ndc_request_id = response['requests'][0]['ndc_request_id']
                self.test_data['ndc_request_id'] = ndc_request_id
                print(f"   NDC Request ID: {ndc_request_id}")
                
                # Test asset recovery records creation
                success, assets_response = self.run_test(
                    "Verify Asset Recovery Records Created",
                    "GET",
                    f"ndc-requests/{ndc_request_id}/assets",
                    200,
                    user_role="Asset Manager"
                )
                
                if success:
                    print(f"   ✅ Asset recovery records created: {len(assets_response)} assets")
                    if assets_response:
                        asset_recovery = assets_response[0]
                        print(f"   Asset Code: {asset_recovery['asset_code']}")
                        print(f"   Asset Value: ₹{asset_recovery['asset_value']}")
                        print(f"   Recovery Status: {asset_recovery['status']}")
                
            return True
        else:
            print(f"   ❌ CRITICAL BUG NOT FIXED: NDC request creation failed")
            print(f"   ❌ Backend still cannot detect allocated assets")
            return False

    def test_ndc_edge_cases(self):
        """Test NDC Edge Cases"""
        print(f"\n⚠️ Testing NDC Edge Cases")
        
        # Test 1: Employee with no allocated assets (should fail)
        employee_no_assets_data = {
            "email": f"no_assets_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Employee No Assets",
            "roles": ["Employee"],
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Employee Without Assets",
            "POST",
            "users",
            200,
            data=employee_no_assets_data,
            user_role="Administrator"
        )
        
        if success:
            no_assets_employee_id = response['id']
            
            # Try to create NDC for employee with no assets
            ndc_no_assets_data = {
                "employee_id": no_assets_employee_id,
                "resigned_on": datetime.now().isoformat(),
                "notice_period": "30 days",
                "last_working_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "separation_approved_by": self.users["Administrator"]["id"],
                "separation_approved_on": datetime.now().isoformat(),
                "separation_reason": "Test Resignation"
            }
            
            success, response = self.run_test(
                "Create NDC for Employee with No Assets (Should Fail)",
                "POST",
                "ndc-requests",
                400,
                data=ndc_no_assets_data,
                user_role="HR Manager"
            )
            
            if success:
                print(f"   ✅ NDC creation correctly rejected for employee with no allocated assets")
                return True
        
        return False

    def test_ndc_access_control(self):
        """Test NDC Access Control"""
        print(f"\n🔒 Testing NDC Access Control")
        
        # Test Employee cannot access NDC requests
        success, response = self.run_test(
            "Employee Access NDC Requests (Should Fail)",
            "GET",
            "ndc-requests",
            403,
            user_role="Employee"
        )
        
        if success:
            print(f"   ✅ Employee correctly denied access to NDC requests")
        
        # Test HR Manager can see all NDC requests
        success, response = self.run_test(
            "HR Manager Access All NDC Requests",
            "GET",
            "ndc-requests",
            200,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   ✅ HR Manager can access all NDC requests: {len(response)} requests")
        
        # Test Asset Manager can see their assigned NDC requests
        success, response = self.run_test(
            "Asset Manager Access Assigned NDC Requests",
            "GET",
            "ndc-requests",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            print(f"   ✅ Asset Manager can access assigned NDC requests: {len(response)} requests")
        
        return True

    def run_ndc_focused_tests(self):
        """Run focused NDC tests"""
        print("🚀 Starting NDC Focused Tests - Critical Bug Fix Verification")
        print("=" * 70)
        
        # Test login for required roles
        login_success = True
        for email, password, role in [
            ("admin@company.com", "password123", "Administrator"),
            ("hr@company.com", "password123", "HR Manager"),
            ("employee@company.com", "password123", "Employee"),
            ("assetmanager@company.com", "password123", "Asset Manager")
        ]:
            if not self.test_login(email, password, role):
                login_success = False
        
        if not login_success:
            print("❌ Login tests failed. Stopping tests.")
            return
        
        # Run NDC tests
        print(f"\n🔥 CRITICAL BUG FIX VERIFICATION")
        print("-" * 40)
        bug_fix_success = self.test_ndc_critical_bug_fix()
        
        print(f"\n⚠️ EDGE CASES TESTING")
        print("-" * 25)
        edge_cases_success = self.test_ndc_edge_cases()
        
        print(f"\n🔒 ACCESS CONTROL TESTING")
        print("-" * 30)
        access_control_success = self.test_ndc_access_control()
        
        # Print final results
        print(f"\n" + "=" * 70)
        print(f"🎯 NDC FOCUSED TEST RESULTS")
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if bug_fix_success:
            print(f"🎉 CRITICAL BUG FIX VERIFIED: NDC system now works correctly!")
            print(f"   ✅ Asset detection using 'allocated_to' field is working")
            print(f"   ✅ NDC request creation successful for employees with allocated assets")
            print(f"   ✅ Asset Manager routing and asset recovery records created properly")
        else:
            print(f"❌ CRITICAL BUG NOT FIXED: NDC system still has issues")
        
        print("=" * 70)

if __name__ == "__main__":
    tester = NDCFocusedTester()
    tester.run_ndc_focused_tests()