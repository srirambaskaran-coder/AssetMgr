import requests
import sys
import json
from datetime import datetime, timedelta

class ManagerEmployeeDebugTester:
    def __init__(self, base_url="https://asset-track-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.test_data = {}  # Store created test data
        self.tests_run = 0
        self.tests_passed = 0
        self.debug_findings = []

    def log_finding(self, finding):
        """Log a debug finding"""
        self.debug_findings.append(finding)
        print(f"🔍 FINDING: {finding}")

    def run_test(self, name, method, endpoint, expected_status, data=None, user_role=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add auth header if user role specified
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

    def debug_user_relationship_verification(self):
        """Debug User Relationship Verification as requested"""
        print(f"\n🔍 === USER RELATIONSHIP VERIFICATION DEBUG ===")
        
        # 1. Check if user "sriram@company.com" exists in the database
        print(f"\n1️⃣ Checking if user 'sriram@company.com' exists...")
        success, users_response = self.run_test(
            "Get All Users to Find Sriram",
            "GET",
            "users",
            200,
            user_role="Administrator"
        )
        
        sriram_user = None
        if success:
            for user in users_response:
                if user.get('email') == 'sriram@company.com':
                    sriram_user = user
                    break
            
            if sriram_user:
                self.log_finding(f"✅ User 'sriram@company.com' EXISTS in database")
                self.log_finding(f"   - User ID: {sriram_user.get('id')}")
                self.log_finding(f"   - Name: {sriram_user.get('name')}")
                self.log_finding(f"   - Roles: {sriram_user.get('roles', [])}")
                self.log_finding(f"   - Reporting Manager ID: {sriram_user.get('reporting_manager_id', 'None')}")
                self.log_finding(f"   - Reporting Manager Name: {sriram_user.get('reporting_manager_name', 'None')}")
                self.test_data['sriram_user'] = sriram_user
            else:
                self.log_finding(f"❌ User 'sriram@company.com' NOT FOUND in database")
                self.log_finding(f"   - Total users found: {len(users_response)}")
                # List first few users for reference
                for i, user in enumerate(users_response[:5]):
                    self.log_finding(f"   - User {i+1}: {user.get('email', 'No email')} ({user.get('name', 'No name')})")
        
        # 2. Check if user "manager@company.com" (Kiran) exists and get their user ID
        print(f"\n2️⃣ Checking if user 'manager@company.com' (Kiran) exists...")
        kiran_user = None
        if success:
            for user in users_response:
                if user.get('email') == 'manager@company.com':
                    kiran_user = user
                    break
            
            if kiran_user:
                self.log_finding(f"✅ User 'manager@company.com' (Kiran) EXISTS in database")
                self.log_finding(f"   - User ID: {kiran_user.get('id')}")
                self.log_finding(f"   - Name: {kiran_user.get('name')}")
                self.log_finding(f"   - Roles: {kiran_user.get('roles', [])}")
                self.test_data['kiran_user'] = kiran_user
            else:
                self.log_finding(f"❌ User 'manager@company.com' (Kiran) NOT FOUND in database")
        
        # 3. Verify if Sriram has Kiran set as reporting manager
        print(f"\n3️⃣ Verifying manager-employee relationship...")
        if sriram_user and kiran_user:
            sriram_manager_id = sriram_user.get('reporting_manager_id')
            kiran_id = kiran_user.get('id')
            
            if sriram_manager_id == kiran_id:
                self.log_finding(f"✅ RELATIONSHIP VERIFIED: Sriram has Kiran as reporting manager")
                self.log_finding(f"   - Sriram's reporting_manager_id: {sriram_manager_id}")
                self.log_finding(f"   - Kiran's user ID: {kiran_id}")
            else:
                self.log_finding(f"❌ RELATIONSHIP ISSUE: Sriram does NOT have Kiran as reporting manager")
                self.log_finding(f"   - Sriram's reporting_manager_id: {sriram_manager_id}")
                self.log_finding(f"   - Kiran's user ID: {kiran_id}")
                if sriram_manager_id:
                    # Find who is actually set as Sriram's manager
                    for user in users_response:
                        if user.get('id') == sriram_manager_id:
                            self.log_finding(f"   - Sriram's actual manager: {user.get('name')} ({user.get('email')})")
                            break
        elif sriram_user and not kiran_user:
            self.log_finding(f"❌ Cannot verify relationship: Kiran user not found")
        elif not sriram_user and kiran_user:
            self.log_finding(f"❌ Cannot verify relationship: Sriram user not found")
        else:
            self.log_finding(f"❌ Cannot verify relationship: Both users not found")

    def debug_asset_requisition_data_analysis(self):
        """Debug Asset Requisition Data Analysis as requested"""
        print(f"\n🔍 === ASSET REQUISITION DATA ANALYSIS DEBUG ===")
        
        # 1. Check existing asset requisitions in the database
        print(f"\n1️⃣ Checking existing asset requisitions...")
        success, requisitions_response = self.run_test(
            "Get All Asset Requisitions",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            self.log_finding(f"✅ Found {len(requisitions_response)} asset requisitions in database")
            
            # 2. Verify if any requisitions have manager_id field populated
            print(f"\n2️⃣ Analyzing manager_id field population...")
            requisitions_with_manager_id = 0
            requisitions_without_manager_id = 0
            sriram_requisitions = []
            
            for req in requisitions_response:
                if req.get('manager_id'):
                    requisitions_with_manager_id += 1
                else:
                    requisitions_without_manager_id += 1
                
                # 3. Look for requisitions created by Sriram
                if 'sriram_user' in self.test_data:
                    sriram_id = self.test_data['sriram_user'].get('id')
                    if req.get('requested_by') == sriram_id:
                        sriram_requisitions.append(req)
            
            self.log_finding(f"📊 Manager ID Field Analysis:")
            self.log_finding(f"   - Requisitions WITH manager_id: {requisitions_with_manager_id}")
            self.log_finding(f"   - Requisitions WITHOUT manager_id: {requisitions_without_manager_id}")
            
            if requisitions_with_manager_id > 0:
                self.log_finding(f"✅ Some requisitions have manager_id populated")
                # Show examples
                for i, req in enumerate(requisitions_response):
                    if req.get('manager_id') and i < 3:  # Show first 3 examples
                        self.log_finding(f"   - Example {i+1}: Req ID {req.get('id', 'Unknown')[:8]}... has manager_id: {req.get('manager_id')}")
            else:
                self.log_finding(f"❌ NO requisitions have manager_id populated - this is the issue!")
            
            # 3. Analyze Sriram's requisitions specifically
            print(f"\n3️⃣ Analyzing Sriram's requisitions...")
            if sriram_requisitions:
                self.log_finding(f"✅ Found {len(sriram_requisitions)} requisitions created by Sriram")
                for i, req in enumerate(sriram_requisitions):
                    self.log_finding(f"   - Sriram Req {i+1}:")
                    self.log_finding(f"     * ID: {req.get('id', 'Unknown')[:8]}...")
                    self.log_finding(f"     * Status: {req.get('status', 'Unknown')}")
                    self.log_finding(f"     * Manager ID: {req.get('manager_id', 'None')}")
                    self.log_finding(f"     * Manager Name: {req.get('manager_name', 'None')}")
                    self.log_finding(f"     * Created: {req.get('created_at', 'Unknown')}")
                    
                    if not req.get('manager_id'):
                        self.log_finding(f"     ❌ ISSUE: This requisition missing manager_id field")
            else:
                if 'sriram_user' in self.test_data:
                    self.log_finding(f"❌ NO requisitions found for Sriram (ID: {self.test_data['sriram_user'].get('id')})")
                else:
                    self.log_finding(f"❌ Cannot check Sriram's requisitions - user not found")
            
            self.test_data['all_requisitions'] = requisitions_response
            self.test_data['sriram_requisitions'] = sriram_requisitions

    def debug_test_updated_asset_requisition_creation(self):
        """Test Updated Asset Requisition Creation Logic"""
        print(f"\n🔍 === TESTING UPDATED ASSET REQUISITION CREATION ===")
        
        # First, we need to get asset types to create a requisition
        success, asset_types_response = self.run_test(
            "Get Asset Types for Requisition Test",
            "GET",
            "asset-types",
            200,
            user_role="Administrator"
        )
        
        if not success or not asset_types_response:
            self.log_finding(f"❌ Cannot test requisition creation - no asset types available")
            return
        
        asset_type_id = asset_types_response[0].get('id')
        self.log_finding(f"✅ Using asset type: {asset_types_response[0].get('name')} (ID: {asset_type_id})")
        
        # Test 1: Create requisition as Sriram (if exists) to test manager_id population
        if 'sriram_user' in self.test_data:
            print(f"\n1️⃣ Testing requisition creation as Sriram...")
            
            # First login as Sriram
            sriram_login_success = self.test_login("sriram@company.com", "testpass123", "Sriram")
            
            if sriram_login_success:
                requisition_data = {
                    "asset_type_id": asset_type_id,
                    "request_type": "New Allocation",
                    "request_for": "Self",
                    "justification": "Testing manager_id population in new requisition",
                    "required_by_date": (datetime.now() + timedelta(days=7)).isoformat()
                }
                
                success, response = self.run_test(
                    "Create New Requisition as Sriram",
                    "POST",
                    "asset-requisitions",
                    200,
                    data=requisition_data,
                    user_role="Sriram"
                )
                
                if success:
                    self.log_finding(f"✅ Sriram successfully created new requisition")
                    self.log_finding(f"   - Requisition ID: {response.get('id', 'Unknown')[:8]}...")
                    self.log_finding(f"   - Manager ID populated: {response.get('manager_id', 'None')}")
                    self.log_finding(f"   - Manager Name populated: {response.get('manager_name', 'None')}")
                    
                    # Check if manager_id matches Kiran's ID
                    if 'kiran_user' in self.test_data:
                        kiran_id = self.test_data['kiran_user'].get('id')
                        req_manager_id = response.get('manager_id')
                        
                        if req_manager_id == kiran_id:
                            self.log_finding(f"✅ FIXED: New requisition correctly has Kiran as manager_id")
                        else:
                            self.log_finding(f"❌ ISSUE: New requisition manager_id ({req_manager_id}) doesn't match Kiran's ID ({kiran_id})")
                    
                    self.test_data['new_sriram_requisition'] = response
                else:
                    self.log_finding(f"❌ Failed to create requisition as Sriram")
            else:
                self.log_finding(f"❌ Cannot test as Sriram - login failed (user may not exist or wrong password)")
        
        # Test 2: Create requisition as a different employee to verify general logic
        print(f"\n2️⃣ Testing requisition creation as Employee (general test)...")
        
        employee_login_success = self.test_login("employee@company.com", "password123", "Employee")
        
        if employee_login_success:
            requisition_data = {
                "asset_type_id": asset_type_id,
                "request_type": "New Allocation",
                "request_for": "Self",
                "justification": "Testing manager_id population logic for general employee",
                "required_by_date": (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            success, response = self.run_test(
                "Create New Requisition as Employee",
                "POST",
                "asset-requisitions",
                200,
                data=requisition_data,
                user_role="Employee"
            )
            
            if success:
                self.log_finding(f"✅ Employee successfully created new requisition")
                self.log_finding(f"   - Requisition ID: {response.get('id', 'Unknown')[:8]}...")
                self.log_finding(f"   - Manager ID populated: {response.get('manager_id', 'None')}")
                self.log_finding(f"   - Manager Name populated: {response.get('manager_name', 'None')}")
                
                # Check if employee has a reporting manager set
                employee_user = self.users.get('Employee', {})
                employee_manager_id = employee_user.get('reporting_manager_id')
                
                if employee_manager_id:
                    self.log_finding(f"   - Employee's reporting_manager_id: {employee_manager_id}")
                    if response.get('manager_id') == employee_manager_id:
                        self.log_finding(f"✅ WORKING: Requisition manager_id correctly matches employee's reporting_manager_id")
                    else:
                        self.log_finding(f"❌ ISSUE: Requisition manager_id doesn't match employee's reporting_manager_id")
                else:
                    self.log_finding(f"   - Employee has no reporting_manager_id set")
                    if not response.get('manager_id'):
                        self.log_finding(f"✅ CORRECT: No manager_id in requisition since employee has no reporting manager")
                    else:
                        self.log_finding(f"❌ UNEXPECTED: Requisition has manager_id but employee has no reporting manager")
                
                self.test_data['new_employee_requisition'] = response

    def debug_manager_filtering_logic_test(self):
        """Test Manager Filtering Logic"""
        print(f"\n🔍 === TESTING MANAGER FILTERING LOGIC ===")
        
        # Test 1: Login as Kiran (Manager) and test filtering
        print(f"\n1️⃣ Testing GET /api/asset-requisitions as Manager (Kiran)...")
        
        kiran_login_success = self.test_login("manager@company.com", "password123", "Manager")
        
        if kiran_login_success:
            success, response = self.run_test(
                "Get Asset Requisitions as Manager",
                "GET",
                "asset-requisitions",
                200,
                user_role="Manager"
            )
            
            if success:
                self.log_finding(f"✅ Manager successfully retrieved requisitions")
                self.log_finding(f"   - Total requisitions visible to manager: {len(response)}")
                
                # Analyze which requisitions the manager can see
                if 'kiran_user' in self.test_data:
                    kiran_id = self.test_data['kiran_user'].get('id')
                    direct_report_reqs = []
                    other_reqs = []
                    
                    for req in response:
                        if req.get('manager_id') == kiran_id:
                            direct_report_reqs.append(req)
                        else:
                            other_reqs.append(req)
                    
                    self.log_finding(f"   - Requisitions from direct reports: {len(direct_report_reqs)}")
                    self.log_finding(f"   - Other requisitions: {len(other_reqs)}")
                    
                    if len(direct_report_reqs) > 0:
                        self.log_finding(f"✅ Manager can see requisitions from direct reports")
                        for i, req in enumerate(direct_report_reqs[:3]):  # Show first 3
                            self.log_finding(f"     - Direct Report Req {i+1}: {req.get('id', 'Unknown')[:8]}... by {req.get('requested_by_name', 'Unknown')}")
                    else:
                        self.log_finding(f"❌ Manager cannot see any requisitions from direct reports")
                    
                    if len(other_reqs) > 0:
                        self.log_finding(f"⚠️ Manager can see {len(other_reqs)} requisitions NOT from direct reports")
                        for i, req in enumerate(other_reqs[:3]):  # Show first 3
                            self.log_finding(f"     - Other Req {i+1}: {req.get('id', 'Unknown')[:8]}... by {req.get('requested_by_name', 'Unknown')} (manager_id: {req.get('manager_id', 'None')})")
                    else:
                        self.log_finding(f"✅ Manager correctly sees only direct report requisitions")
                
                self.test_data['manager_visible_requisitions'] = response
            else:
                self.log_finding(f"❌ Manager failed to retrieve requisitions")
        else:
            self.log_finding(f"❌ Cannot test manager filtering - Kiran login failed")
        
        # Test 2: Compare with Administrator view to verify filtering
        print(f"\n2️⃣ Comparing with Administrator view...")
        
        admin_login_success = self.test_login("admin@company.com", "password123", "Administrator")
        
        if admin_login_success:
            success, admin_response = self.run_test(
                "Get Asset Requisitions as Administrator",
                "GET",
                "asset-requisitions",
                200,
                user_role="Administrator"
            )
            
            if success:
                self.log_finding(f"✅ Administrator can see {len(admin_response)} total requisitions")
                
                if 'manager_visible_requisitions' in self.test_data:
                    manager_count = len(self.test_data['manager_visible_requisitions'])
                    admin_count = len(admin_response)
                    
                    if manager_count < admin_count:
                        self.log_finding(f"✅ FILTERING WORKING: Manager sees fewer requisitions ({manager_count}) than Administrator ({admin_count})")
                    elif manager_count == admin_count:
                        self.log_finding(f"⚠️ POTENTIAL ISSUE: Manager sees same number of requisitions as Administrator")
                    else:
                        self.log_finding(f"❌ ERROR: Manager sees more requisitions than Administrator (impossible)")

    def debug_data_fix_verification(self):
        """Verify Data Fix and End-to-End Flow"""
        print(f"\n🔍 === DATA FIX VERIFICATION ===")
        
        # Test 1: Check if existing requisitions have manager_id populated
        print(f"\n1️⃣ Checking if existing requisitions need manager_id fix...")
        
        if 'all_requisitions' in self.test_data:
            requisitions_needing_fix = []
            
            for req in self.test_data['all_requisitions']:
                if not req.get('manager_id') and req.get('requested_by'):
                    requisitions_needing_fix.append(req)
            
            self.log_finding(f"📊 Existing Requisitions Analysis:")
            self.log_finding(f"   - Total existing requisitions: {len(self.test_data['all_requisitions'])}")
            self.log_finding(f"   - Requisitions missing manager_id: {len(requisitions_needing_fix)}")
            
            if len(requisitions_needing_fix) > 0:
                self.log_finding(f"❌ DATA FIX NEEDED: {len(requisitions_needing_fix)} existing requisitions missing manager_id")
                
                # Show examples of requisitions that need fixing
                for i, req in enumerate(requisitions_needing_fix[:3]):
                    self.log_finding(f"   - Needs Fix {i+1}: Req {req.get('id', 'Unknown')[:8]}... by {req.get('requested_by_name', 'Unknown')}")
            else:
                self.log_finding(f"✅ All existing requisitions have manager_id populated")
        
        # Test 2: Verify new requisitions work correctly
        print(f"\n2️⃣ Verifying new requisition creation works...")
        
        if 'new_sriram_requisition' in self.test_data:
            new_req = self.test_data['new_sriram_requisition']
            if new_req.get('manager_id'):
                self.log_finding(f"✅ NEW REQUISITIONS WORKING: New requisitions correctly populate manager_id")
            else:
                self.log_finding(f"❌ NEW REQUISITIONS ISSUE: New requisitions still not populating manager_id")
        
        # Test 3: End-to-End Flow Test
        print(f"\n3️⃣ Testing End-to-End Flow: Employee creates request → Manager sees request...")
        
        if 'new_sriram_requisition' in self.test_data and 'manager_visible_requisitions' in self.test_data:
            new_req_id = self.test_data['new_sriram_requisition'].get('id')
            manager_reqs = self.test_data['manager_visible_requisitions']
            
            manager_can_see_new_req = any(req.get('id') == new_req_id for req in manager_reqs)
            
            if manager_can_see_new_req:
                self.log_finding(f"✅ END-TO-END SUCCESS: Manager can see Sriram's new requisition")
            else:
                self.log_finding(f"❌ END-TO-END FAILURE: Manager cannot see Sriram's new requisition")
                self.log_finding(f"   - New requisition ID: {new_req_id}")
                self.log_finding(f"   - Manager can see {len(manager_reqs)} requisitions")

    def run_comprehensive_debug(self):
        """Run comprehensive debugging of manager-employee relationship issue"""
        print(f"\n🚀 === STARTING COMPREHENSIVE MANAGER-EMPLOYEE RELATIONSHIP DEBUG ===")
        
        # Setup: Login as Administrator to access all data
        admin_login_success = self.test_login("admin@company.com", "password123", "Administrator")
        
        if not admin_login_success:
            print("❌ CRITICAL: Cannot login as Administrator - cannot proceed with debug")
            return
        
        # Run all debug tests
        self.debug_user_relationship_verification()
        self.debug_asset_requisition_data_analysis()
        self.debug_test_updated_asset_requisition_creation()
        self.debug_manager_filtering_logic_test()
        self.debug_data_fix_verification()
        
        # Summary
        print(f"\n📋 === DEBUG SUMMARY ===")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🔍 === KEY FINDINGS ===")
        for i, finding in enumerate(self.debug_findings, 1):
            print(f"{i}. {finding}")
        
        # Recommendations
        print(f"\n💡 === RECOMMENDATIONS ===")
        
        # Check if users exist
        if 'sriram_user' not in self.test_data:
            print("1. ❌ CRITICAL: Create user 'sriram@company.com' in the system")
        
        if 'kiran_user' not in self.test_data:
            print("2. ❌ CRITICAL: Verify user 'manager@company.com' exists and has Manager role")
        
        # Check relationship
        if 'sriram_user' in self.test_data and 'kiran_user' in self.test_data:
            sriram_manager_id = self.test_data['sriram_user'].get('reporting_manager_id')
            kiran_id = self.test_data['kiran_user'].get('id')
            if sriram_manager_id != kiran_id:
                print("3. ❌ CRITICAL: Set Kiran as Sriram's reporting manager in user profile")
        
        # Check requisition logic
        if 'all_requisitions' in self.test_data:
            missing_manager_id_count = sum(1 for req in self.test_data['all_requisitions'] if not req.get('manager_id'))
            if missing_manager_id_count > 0:
                print(f"4. ❌ DATA FIX NEEDED: {missing_manager_id_count} existing requisitions missing manager_id field")
        
        # Check new requisition creation
        if 'new_sriram_requisition' in self.test_data:
            if not self.test_data['new_sriram_requisition'].get('manager_id'):
                print("5. ❌ CODE FIX NEEDED: New requisition creation not populating manager_id from reporting_manager_id")
        
        print(f"\n✅ Debug analysis complete!")

if __name__ == "__main__":
    tester = ManagerEmployeeDebugTester()
    tester.run_comprehensive_debug()