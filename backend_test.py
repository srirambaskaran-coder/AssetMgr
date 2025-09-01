import requests
import sys
import json
from datetime import datetime

class AssetInventoryAPITester:
    def __init__(self, base_url="https://inventoryhub-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.test_data = {}  # Store created test data
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_auth_me(self, role_name):
        """Test /auth/me endpoint"""
        success, response = self.run_test(
            f"Get current user info ({role_name})",
            "GET",
            "auth/me",
            200,
            user_role=role_name
        )
        return success

    def test_dashboard_stats(self, role_name):
        """Test dashboard stats endpoint"""
        success, response = self.run_test(
            f"Get dashboard stats ({role_name})",
            "GET",
            "dashboard/stats",
            200,
            user_role=role_name
        )
        if success:
            print(f"   Stats received: {list(response.keys())}")
        return success

    def test_asset_type_crud(self):
        """Test Asset Type CRUD operations"""
        print(f"\n📋 Testing Asset Type CRUD Operations")
        
        # Test Create (Admin)
        asset_type_data = {
            "code": "LAPTOP",
            "name": "Laptop Computers",
            "depreciation_applicable": True,
            "asset_life": 3,
            "to_be_recovered_on_separation": True,
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Asset Type",
            "POST",
            "asset-types",
            200,
            data=asset_type_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_type_id'] = response['id']
            print(f"   Created asset type with ID: {response['id']}")
        
        # Test Get All Asset Types
        success, response = self.run_test(
            "Get All Asset Types",
            "GET",
            "asset-types",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} asset types")
        
        # Test Get Single Asset Type
        if 'asset_type_id' in self.test_data:
            success, response = self.run_test(
                "Get Single Asset Type",
                "GET",
                f"asset-types/{self.test_data['asset_type_id']}",
                200,
                user_role="Administrator"
            )
        
        # Test Update Asset Type
        if 'asset_type_id' in self.test_data:
            update_data = {"name": "Updated Laptop Computers"}
            success, response = self.run_test(
                "Update Asset Type",
                "PUT",
                f"asset-types/{self.test_data['asset_type_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )

    def test_asset_definition_crud(self):
        """Test Asset Definition CRUD operations"""
        print(f"\n💻 Testing Asset Definition CRUD Operations")
        
        if 'asset_type_id' not in self.test_data:
            print("❌ Skipping Asset Definition tests - no asset type created")
            return
        
        # Test Create Asset Definition
        asset_def_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP001",
            "asset_description": "Dell Laptop",
            "asset_details": "Dell Inspiron 15 3000 Series",
            "asset_value": 50000.0,
            "asset_depreciation_value_per_year": 16666.67,
            "status": "Available"
        }
        
        success, response = self.run_test(
            "Create Asset Definition",
            "POST",
            "asset-definitions",
            200,
            data=asset_def_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_def_id'] = response['id']
            print(f"   Created asset definition with ID: {response['id']}")
        
        # Test Get All Asset Definitions
        success, response = self.run_test(
            "Get All Asset Definitions",
            "GET",
            "asset-definitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} asset definitions")

    def test_asset_requisition_workflow(self):
        """Test Enhanced Asset Requisition workflow"""
        print(f"\n📝 Testing Enhanced Asset Requisition Workflow")
        
        if 'asset_type_id' not in self.test_data:
            print("❌ Skipping Requisition tests - no asset type created")
            return
        
        # Test 1: New Allocation Request (Self)
        from datetime import datetime, timedelta
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Need laptop for development work",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create New Allocation Request (Employee)",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data,
            user_role="Employee"
        )
        
        if success:
            self.test_data['requisition_id'] = response['id']
            print(f"   Created requisition ID: {response['id'][:8]}...")
            print(f"   Request type: {response['request_type']}")
            print(f"   Request for: {response['request_for']}")
            print(f"   Required by: {response.get('required_by_date', 'Not set')}")
        
        # Test 2: Replacement Request with conditional fields
        replacement_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "Replacement",
            "reason_for_return_replacement": "Current laptop screen is damaged",
            "asset_details": "Dell Inspiron 15, Serial: DL123456, screen has cracks",
            "request_for": "Self",
            "justification": "Need replacement laptop due to hardware failure",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Replacement Request (Employee)",
            "POST",
            "asset-requisitions",
            200,
            data=replacement_data,
            user_role="Employee"
        )
        
        if success:
            print(f"   Replacement request ID: {response['id'][:8]}...")
            print(f"   Reason: {response['reason_for_return_replacement'][:30]}...")
            print(f"   Asset details: {response['asset_details'][:30]}...")
        
        # Test 3: Return Request
        return_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "Return",
            "reason_for_return_replacement": "Project completed, no longer needed",
            "asset_details": "MacBook Pro 16, Serial: MP789012, good condition",
            "request_for": "Self",
            "justification": "Returning equipment after project completion"
        }
        
        success, response = self.run_test(
            "Create Return Request (Employee)",
            "POST",
            "asset-requisitions",
            200,
            data=return_data,
            user_role="Employee"
        )
        
        if success:
            print(f"   Return request ID: {response['id'][:8]}...")
        
        # Test 4: Team Member Request (if we have team members)
        if "Administrator" in self.tokens:
            # Get users to find a team member
            success, users_response = self.run_test(
                "Get Users for Team Member Test",
                "GET",
                "users",
                200,
                user_role="Administrator"
            )
            
            if success and users_response:
                team_member = None
                for user in users_response:
                    if user['role'] in ['Employee', 'Manager'] and user['id'] != self.users.get('Employee', {}).get('id'):
                        team_member = user
                        break
                
                if team_member:
                    team_member_data = {
                        "asset_type_id": self.test_data['asset_type_id'],
                        "request_type": "New Allocation",
                        "request_for": "Team Member",
                        "team_member_employee_id": team_member['id'],
                        "justification": "New team member needs laptop for onboarding",
                        "required_by_date": required_by_date
                    }
                    
                    success, response = self.run_test(
                        "Create Team Member Request (Employee)",
                        "POST",
                        "asset-requisitions",
                        200,
                        data=team_member_data,
                        user_role="Employee"
                    )
                    
                    if success:
                        print(f"   Team member request ID: {response['id'][:8]}...")
                        print(f"   Team member: {response.get('team_member_name', 'Unknown')}")
        
        # Test 5: Validation - Replacement without conditional fields (should fail)
        invalid_replacement = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "Replacement",
            "request_for": "Self",
            "justification": "Need replacement"
            # Missing reason_for_return_replacement and asset_details
        }
        
        success, response = self.run_test(
            "Invalid Replacement Request (Should Fail)",
            "POST",
            "asset-requisitions",
            422,  # Expecting validation error
            data=invalid_replacement,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Validation correctly rejected replacement without conditional fields")
        
        # Test 6: Team Member request without member ID (should fail)
        invalid_team_request = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Team Member",
            "justification": "Need for team member"
            # Missing team_member_employee_id
        }
        
        success, response = self.run_test(
            "Invalid Team Member Request (Should Fail)",
            "POST",
            "asset-requisitions",
            400,  # Expecting validation error
            data=invalid_team_request,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Validation correctly rejected team member request without member ID")
        
        # Test Get Requisitions for different roles
        for role in ["Employee", "Manager", "HR Manager", "Administrator"]:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Get Asset Requisitions ({role})",
                    "GET",
                    "asset-requisitions",
                    200,
                    user_role=role
                )
                if success:
                    print(f"   {role} can see {len(response)} requisitions")
                    # Check if enhanced fields are present
                    if response and len(response) > 0:
                        req = response[0]
                        enhanced_fields = ['request_type', 'request_for', 'required_by_date']
                        present_fields = [field for field in enhanced_fields if field in req]
                        print(f"   Enhanced fields present: {present_fields}")

    def test_role_based_access(self):
        """Test role-based access control"""
        print(f"\n🔒 Testing Role-Based Access Control")
        
        # Test Employee trying to create asset type (should fail)
        asset_type_data = {
            "code": "TEST",
            "name": "Test Asset",
            "depreciation_applicable": False
        }
        
        success, response = self.run_test(
            "Employee Create Asset Type (Should Fail)",
            "POST",
            "asset-types",
            403,  # Expecting forbidden
            data=asset_type_data,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to create asset type")
        
        # Test Manager trying to create asset type (should fail)
        success, response = self.run_test(
            "Manager Create Asset Type (Should Fail)",
            "POST",
            "asset-types",
            403,  # Expecting forbidden
            data=asset_type_data,
            user_role="Manager"
        )
        
        if success:
            print("   ✅ Manager correctly denied access to create asset type")

    def test_validation_rules(self):
        """Test business validation rules"""
        print(f"\n✅ Testing Validation Rules")
        
        # Test asset type with depreciation but no asset life
        invalid_asset_type = {
            "code": "INVALID",
            "name": "Invalid Asset",
            "depreciation_applicable": True,
            # Missing asset_life
        }
        
        success, response = self.run_test(
            "Create Asset Type Without Asset Life (Should Fail)",
            "POST",
            "asset-types",
            400,  # Expecting bad request
            data=invalid_asset_type,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Validation correctly rejected asset type without asset life")
        
        # Test duplicate asset type code
        if 'asset_type_id' in self.test_data:
            duplicate_asset_type = {
                "code": "LAPTOP",  # Same as existing
                "name": "Duplicate Laptop",
                "depreciation_applicable": False
            }
            
            success, response = self.run_test(
                "Create Duplicate Asset Type Code (Should Fail)",
                "POST",
                "asset-types",
                400,  # Expecting bad request
                data=duplicate_asset_type,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Validation correctly rejected duplicate asset type code")

    def test_user_management(self):
        """Test Multi-Role User Management CRUD operations with new fields"""
        print(f"\n👥 Testing Multi-Role User Management Operations")
        
        # Test 1: Create Manager User with single role (for reporting manager tests)
        manager_data = {
            "email": f"manager_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Test Manager",
            "roles": ["Manager"],
            "designation": "Senior Manager",
            "date_of_joining": "2023-01-15T00:00:00Z",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Manager User with New Fields",
            "POST",
            "users",
            200,
            data=manager_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['manager_user_id'] = response['id']
            print(f"   Created manager with ID: {response['id']}")
            print(f"   Designation: {response.get('designation', 'Not set')}")
            print(f"   Date of Joining: {response.get('date_of_joining', 'Not set')}")
            print(f"   Roles: {response.get('roles', [])}")
        
        # Test 2: Create User with multiple roles
        multi_role_data = {
            "email": f"multirole_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Multi Role User",
            "roles": ["Manager", "Employee"],
            "designation": "Team Lead",
            "date_of_joining": "2024-01-01T00:00:00Z",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create User with Multiple Roles",
            "POST",
            "users",
            200,
            data=multi_role_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['multi_role_user_id'] = response['id']
            print(f"   Created multi-role user with ID: {response['id']}")
            print(f"   Roles: {response.get('roles', [])}")
        
        # Test 3: Create Employee User with all new fields including reporting manager
        employee_data = {
            "email": f"employee_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Test Employee",
            "roles": ["Employee"],
            "designation": "Software Developer",
            "date_of_joining": "2024-03-01T00:00:00Z",
            "reporting_manager_id": self.test_data.get('manager_user_id'),
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Employee with Reporting Manager",
            "POST",
            "users",
            200,
            data=employee_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['employee_user_id'] = response['id']
            print(f"   Created employee with ID: {response['id']}")
            print(f"   Designation: {response.get('designation', 'Not set')}")
            print(f"   Reporting Manager ID: {response.get('reporting_manager_id', 'Not set')}")
            print(f"   Reporting Manager Name: {response.get('reporting_manager_name', 'Not set')}")
        
        # Test 4: Create User without optional fields (should default to Employee role)
        basic_user_data = {
            "email": f"basic_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Basic User",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create User Without Optional Fields",
            "POST",
            "users",
            200,
            data=basic_user_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['basic_user_id'] = response['id']
            print(f"   Created basic user with ID: {response['id']}")
            print(f"   Default roles: {response.get('roles', [])}")
        
        # Test 5: Get Managers API
        success, response = self.run_test(
            "Get All Managers",
            "GET",
            "users/managers",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} managers")
            manager_found = False
            for manager in response:
                if manager.get('id') == self.test_data.get('manager_user_id'):
                    manager_found = True
                    print(f"   ✅ Created manager found in managers list")
                    break
            if not manager_found and self.test_data.get('manager_user_id'):
                print(f"   ⚠️ Created manager not found in managers list")
        
        # Test 6: Validation - Invalid reporting manager (not marked as manager)
        invalid_reporting_data = {
            "email": f"invalid_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Invalid Reporting Test",
            "roles": ["Employee"],
            "reporting_manager_id": self.test_data.get('basic_user_id'),  # Basic user is not a manager
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create User with Invalid Reporting Manager (Should Fail)",
            "POST",
            "users",
            400,
            data=invalid_reporting_data,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Validation correctly rejected non-manager as reporting manager")
        
        # Test 7: Validation - Non-existent reporting manager
        nonexistent_reporting_data = {
            "email": f"nonexist_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Non-existent Reporting Test",
            "roles": ["Employee"],
            "reporting_manager_id": "non-existent-id",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create User with Non-existent Reporting Manager (Should Fail)",
            "POST",
            "users",
            400,
            data=nonexistent_reporting_data,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Validation correctly rejected non-existent reporting manager")
        
        # Test 8: Update User with new fields and roles
        if 'employee_user_id' in self.test_data:
            update_data = {
                "designation": "Senior Software Developer",
                "roles": ["Manager", "Employee"],  # Promote to manager with multiple roles
                "reporting_manager_id": None  # Clear reporting manager
            }
            success, response = self.run_test(
                "Update User with Multiple Roles",
                "PUT",
                f"users/{self.test_data['employee_user_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )
            
            if success:
                print(f"   Updated designation: {response.get('designation', 'Not set')}")
                print(f"   Updated roles: {response.get('roles', [])}")
                print(f"   Cleared reporting manager: {response.get('reporting_manager_id', 'Not cleared')}")
        
        # Test 9: Update User - Set new reporting manager
        if 'basic_user_id' in self.test_data and 'manager_user_id' in self.test_data:
            update_data = {
                "reporting_manager_id": self.test_data['manager_user_id'],
                "designation": "Junior Developer"
            }
            success, response = self.run_test(
                "Update User - Set Reporting Manager",
                "PUT",
                f"users/{self.test_data['basic_user_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )
            
            if success:
                print(f"   Set reporting manager: {response.get('reporting_manager_name', 'Not set')}")
        
        # Test 10: Update User - Invalid reporting manager validation
        if 'basic_user_id' in self.test_data and 'employee_user_id' in self.test_data:
            invalid_update_data = {
                "reporting_manager_id": self.test_data['basic_user_id']  # Basic user is not a manager
            }
            success, response = self.run_test(
                "Update User with Invalid Reporting Manager (Should Fail)",
                "PUT",
                f"users/{self.test_data['employee_user_id']}",
                400,
                data=invalid_update_data,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Update validation correctly rejected non-manager as reporting manager")
        
        # Test 11: Get All Users and verify new fields are present
        success, response = self.run_test(
            "Get All Users - Verify New Fields",
            "GET",
            "users",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} users")
            if response:
                user = response[0]
                new_fields = ['designation', 'date_of_joining', 'roles', 'reporting_manager_id', 'reporting_manager_name']
                present_fields = [field for field in new_fields if field in user]
                print(f"   New fields present in user data: {present_fields}")
        
        # Test 12: Get Single User and verify all fields
        if 'employee_user_id' in self.test_data:
            success, response = self.run_test(
                "Get Single User - Verify All Fields",
                "GET",
                f"users/{self.test_data['employee_user_id']}",
                200,
                user_role="Administrator"
            )
            
            if success:
                print(f"   User details:")
                print(f"     Name: {response.get('name', 'Not set')}")
                print(f"     Designation: {response.get('designation', 'Not set')}")
                print(f"     Date of Joining: {response.get('date_of_joining', 'Not set')}")
                print(f"     Roles: {response.get('roles', [])}")
                print(f"     Reporting Manager: {response.get('reporting_manager_name', 'None')}")
        
        # Test 13: Employee trying to access user management (should fail)
        success, response = self.run_test(
            "Employee Get Users (Should Fail)",
            "GET",
            "users",
            403,  # Expecting forbidden
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to user management")
        
        # Test 14: Employee trying to access managers endpoint (should fail)
        success, response = self.run_test(
            "Employee Get Managers (Should Fail)",
            "GET",
            "users/managers",
            403,  # Expecting forbidden
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to managers endpoint")

    def test_multi_role_system(self):
        """Test Multi-Role System functionality"""
        print(f"\n🎭 Testing Multi-Role System")
        
        # Test 1: Role hierarchy - Administrator access
        success, response = self.run_test(
            "Administrator Access to Employee Functions",
            "GET",
            "dashboard/stats",
            200,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Administrator can access employee functions (role hierarchy)")
        
        # Test 2: Role hierarchy - HR Manager access to Employee functions
        if "HR Manager" in self.tokens:
            success, response = self.run_test(
                "HR Manager Access to Employee Functions",
                "GET",
                "dashboard/stats",
                200,
                user_role="HR Manager"
            )
            
            if success:
                print("   ✅ HR Manager can access employee functions (role hierarchy)")
        
        # Test 3: Role hierarchy - Manager access to Employee functions
        if "Manager" in self.tokens:
            success, response = self.run_test(
                "Manager Access to Employee Functions",
                "GET",
                "dashboard/stats",
                200,
                user_role="Manager"
            )
            
            if success:
                print("   ✅ Manager can access employee functions (role hierarchy)")
        
        # Test 4: Test demo user login with roles array
        demo_login_data = {
            "email": "admin@company.com",
            "password": "password123"
        }
        
        success, response = self.run_test(
            "Demo User Login with Roles Array",
            "POST",
            "auth/login",
            200,
            data=demo_login_data
        )
        
        if success:
            user_roles = response.get('user', {}).get('roles', [])
            print(f"   Demo user roles: {user_roles}")
            if isinstance(user_roles, list) and len(user_roles) > 0:
                print("   ✅ Demo user has roles array")
            else:
                print("   ❌ Demo user missing roles array")
        
        # Test 5: Managers endpoint filtering by roles array
        success, response = self.run_test(
            "Managers Endpoint Filtering by Roles Array",
            "GET",
            "users/managers",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} managers")
            for manager in response:
                manager_roles = manager.get('roles', [])
                if 'Manager' in manager_roles:
                    print(f"   ✅ Manager {manager.get('name', 'Unknown')} has Manager role in roles array")
                else:
                    print(f"   ❌ Manager {manager.get('name', 'Unknown')} missing Manager role in roles array")
        
        # Test 6: Multi-role validation - User with multiple roles accessing different endpoints
        if 'multi_role_user_id' in self.test_data:
            # Create a session for the multi-role user
            multi_role_login = {
                "email": f"multirole_{datetime.now().strftime('%H%M%S')}@company.com",
                "password": "TestPassword123!"
            }
            
            # Note: This would require the user to actually exist and be able to login
            # For now, we'll test the creation and retrieval of multi-role users
            success, response = self.run_test(
                "Get Multi-Role User Details",
                "GET",
                f"users/{self.test_data['multi_role_user_id']}",
                200,
                user_role="Administrator"
            )
            
            if success:
                user_roles = response.get('roles', [])
                print(f"   Multi-role user roles: {user_roles}")
                if len(user_roles) > 1:
                    print("   ✅ User successfully created with multiple roles")
                else:
                    print("   ❌ User does not have multiple roles")

    def test_company_profile(self):
        """Test Company Profile operations (Administrator only)"""
        print(f"\n🏢 Testing Company Profile Operations")
        
        # Test Get Company Profile (public endpoint)
        success, response = self.run_test(
            "Get Company Profile (Public)",
            "GET",
            "company-profile",
            200
        )
        
        if success:
            print(f"   Retrieved company profile: {response.get('company_name', 'Default')}")
        
        # Test Create/Update Company Profile (Administrator only)
        profile_data = {
            "company_name": "Test Company Inc.",
            "company_address": "123 Test Street, Test City",
            "company_phone": "+1-555-0123",
            "company_email": "info@testcompany.com",
            "company_website": "https://testcompany.com"
        }
        
        success, response = self.run_test(
            "Create/Update Company Profile (Administrator)",
            "POST",
            "company-profile",
            200,
            data=profile_data,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Created/Updated company profile with ID: {response['id']}")
        
        # Test Update Company Profile (Administrator only)
        update_data = {"company_name": "Updated Test Company Inc."}
        success, response = self.run_test(
            "Update Company Profile (Administrator)",
            "PUT",
            "company-profile",
            200,
            data=update_data,
            user_role="Administrator"
        )
        
        # Test Employee trying to update company profile (should fail)
        success, response = self.run_test(
            "Employee Update Company Profile (Should Fail)",
            "POST",
            "company-profile",
            403,  # Expecting forbidden
            data=profile_data,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to company profile management")

    def test_password_change(self):
        """Test Password Change functionality (All authenticated users)"""
        print(f"\n🔑 Testing Password Change Operations")
        
        # Test password change for Administrator
        password_data = {
            "current_password": "password123",
            "new_password": "NewPassword123!"
        }
        
        success, response = self.run_test(
            "Change Password (Administrator)",
            "POST",
            "auth/change-password",
            200,
            data=password_data,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Administrator password change successful")
        
        # Test password change with wrong current password (should fail)
        wrong_password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewPassword123!"
        }
        
        success, response = self.run_test(
            "Change Password Wrong Current (Should Fail)",
            "POST",
            "auth/change-password",
            400,  # Expecting bad request
            data=wrong_password_data,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Wrong current password correctly rejected")

    def test_bulk_import_template(self):
        """Test Bulk Import Template Download (Administrator/HR Manager only)"""
        print(f"\n📥 Testing Bulk Import Template Operations")
        
        # Test template download (Administrator)
        success, response = self.run_test(
            "Download Asset Definitions Template (Administrator)",
            "GET",
            "asset-definitions/template",
            200,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Template download successful for Administrator")
        
        # Test template download (HR Manager)
        if "HR Manager" in self.tokens:
            success, response = self.run_test(
                "Download Asset Definitions Template (HR Manager)",
                "GET",
                "asset-definitions/template",
                200,
                user_role="HR Manager"
            )
            
            if success:
                print("   ✅ Template download successful for HR Manager")
        
        # Test Employee trying to download template (should fail)
        success, response = self.run_test(
            "Employee Download Template (Should Fail)",
            "GET",
            "asset-definitions/template",
            403,  # Expecting forbidden
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to template download")

    def test_new_admin_features_access_control(self):
        """Test access control for all new administrator features"""
        print(f"\n🔐 Testing New Admin Features Access Control")
        
        # Test various roles trying to access admin-only endpoints
        test_cases = [
            ("users", "GET", "Employee", 403),
            ("users", "GET", "Manager", 403),
            ("users", "GET", "HR Manager", 403),
            ("company-profile", "POST", "Employee", 403),
            ("company-profile", "POST", "Manager", 403),
            ("company-profile", "POST", "HR Manager", 403),
            ("asset-definitions/template", "GET", "Employee", 403),
            ("asset-definitions/template", "GET", "Manager", 403),
        ]
        
        for endpoint, method, role, expected_status in test_cases:
            if role in self.tokens:
                success, response = self.run_test(
                    f"{role} access {endpoint} (Should Fail)",
                    method,
                    endpoint,
                    expected_status,
                    user_role=role
                )
                
                if success:
                    print(f"   ✅ {role} correctly denied access to {endpoint}")

    def test_asset_manager_dashboard_stats(self):
        """Test Asset Manager dashboard statistics"""
        print(f"\n📊 Testing Asset Manager Dashboard Stats")
        
        success, response = self.run_test(
            "Get Asset Manager Dashboard Stats",
            "GET",
            "dashboard/asset-manager-stats",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            expected_keys = [
                "total_assets", "available_assets", "allocated_assets", 
                "damaged_assets", "lost_assets", "under_repair",
                "pending_allocations", "total_allocations", 
                "pending_retrievals", "completed_retrievals",
                "asset_type_breakdown", "allocation_rate", "availability_rate"
            ]
            missing_keys = [key for key in expected_keys if key not in response]
            if missing_keys:
                print(f"   ⚠️ Missing keys in response: {missing_keys}")
            else:
                print(f"   ✅ All expected dashboard stats present")
                print(f"   Total Assets: {response.get('total_assets', 0)}")
                print(f"   Available: {response.get('available_assets', 0)}")
                print(f"   Allocated: {response.get('allocated_assets', 0)}")
                print(f"   Pending Allocations: {response.get('pending_allocations', 0)}")
        
        return success

    def test_asset_allocations(self):
        """Test Asset Allocation functionality"""
        print(f"\n🎯 Testing Asset Allocation Operations")
        
        # First, ensure we have test data
        if 'requisition_id' not in self.test_data or 'asset_def_id' not in self.test_data:
            print("❌ Skipping Asset Allocation tests - missing requisition or asset definition")
            return False
        
        # Test Get Asset Allocations
        success, response = self.run_test(
            "Get Asset Allocations",
            "GET",
            "asset-allocations",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            print(f"   Found {len(response)} existing allocations")
        
        # Test Get Pending Allocations
        success, response = self.run_test(
            "Get Pending Allocations",
            "GET",
            "pending-allocations",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            print(f"   Found {len(response)} pending allocations")
        
        # Test Create Asset Allocation
        allocation_data = {
            "requisition_id": self.test_data['requisition_id'],
            "asset_definition_id": self.test_data['asset_def_id'],
            "remarks": "Test allocation for automated testing",
            "reference_id": "REF001",
            "document_id": "DOC001",
            "dispatch_details": "Dispatched via courier"
        }
        
        success, response = self.run_test(
            "Create Asset Allocation",
            "POST",
            "asset-allocations",
            200,
            data=allocation_data,
            user_role="Asset Manager"
        )
        
        if success:
            self.test_data['allocation_id'] = response['id']
            print(f"   Created allocation with ID: {response['id']}")
            print(f"   Status: {response.get('status', 'Unknown')}")
        
        # Test Get Allocated Assets
        success, response = self.run_test(
            "Get Allocated Assets",
            "GET",
            "allocated-assets",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            print(f"   Found {len(response)} allocated assets")
        
        return success

    def test_asset_retrievals(self):
        """Test Asset Retrieval functionality"""
        print(f"\n🔄 Testing Asset Retrieval Operations")
        
        if 'asset_def_id' not in self.test_data:
            print("❌ Skipping Asset Retrieval tests - missing asset definition")
            return False
        
        # Get employee ID for retrieval test
        employee_id = self.users.get("Employee", {}).get("id")
        if not employee_id:
            print("❌ Skipping Asset Retrieval tests - no employee user found")
            return False
        
        # Test Get Asset Retrievals
        success, response = self.run_test(
            "Get Asset Retrievals",
            "GET",
            "asset-retrievals",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            print(f"   Found {len(response)} existing retrievals")
        
        # Test Create Asset Retrieval
        retrieval_data = {
            "employee_id": employee_id,
            "asset_definition_id": self.test_data['asset_def_id'],
            "remarks": "Employee separation - asset recovery required"
        }
        
        success, response = self.run_test(
            "Create Asset Retrieval",
            "POST",
            "asset-retrievals",
            200,
            data=retrieval_data,
            user_role="Asset Manager"
        )
        
        if success:
            self.test_data['retrieval_id'] = response['id']
            print(f"   Created retrieval with ID: {response['id']}")
            print(f"   Status: {response.get('status', 'Unknown')}")
        
        # Test Update Asset Retrieval
        if 'retrieval_id' in self.test_data:
            update_data = {
                "recovered": True,
                "asset_condition": "Good Condition",
                "recovery_value": 0.0,
                "remarks": "Asset recovered in good condition",
                "status": "Recovered"
            }
            
            success, response = self.run_test(
                "Update Asset Retrieval",
                "PUT",
                f"asset-retrievals/{self.test_data['retrieval_id']}",
                200,
                data=update_data,
                user_role="Asset Manager"
            )
            
            if success:
                print(f"   Updated retrieval status: {response.get('status', 'Unknown')}")
                print(f"   Recovered: {response.get('recovered', False)}")
        
        return success

    def test_asset_manager_access_control(self):
        """Test Asset Manager role-based access control"""
        print(f"\n🔒 Testing Asset Manager Access Control")
        
        # Test Asset Manager accessing allocation endpoints
        endpoints_should_work = [
            ("asset-allocations", "GET"),
            ("pending-allocations", "GET"),
            ("allocated-assets", "GET"),
            ("asset-retrievals", "GET"),
            ("dashboard/asset-manager-stats", "GET")
        ]
        
        for endpoint, method in endpoints_should_work:
            success, response = self.run_test(
                f"Asset Manager {method} {endpoint}",
                method,
                endpoint,
                200,
                user_role="Asset Manager"
            )
            
            if success:
                print(f"   ✅ Asset Manager can access {endpoint}")
        
        # Test other roles trying to access Asset Manager endpoints
        restricted_tests = [
            ("Employee", "asset-allocations", "GET", 403),
            ("Manager", "asset-allocations", "GET", 403),
            ("Employee", "asset-retrievals", "GET", 403),
            ("Manager", "asset-retrievals", "GET", 403),
            ("Employee", "dashboard/asset-manager-stats", "GET", 403),
            ("Manager", "dashboard/asset-manager-stats", "GET", 403)
        ]
        
        for role, endpoint, method, expected_status in restricted_tests:
            if role in self.tokens:
                success, response = self.run_test(
                    f"{role} {method} {endpoint} (Should Fail)",
                    method,
                    endpoint,
                    expected_status,
                    user_role=role
                )
                
                if success:
                    print(f"   ✅ {role} correctly denied access to {endpoint}")

    def test_asset_manager_workflow(self):
        """Test complete Asset Manager workflow"""
        print(f"\n🔄 Testing Complete Asset Manager Workflow")
        
        # This test requires the full workflow to be set up
        # 1. Asset type and definition should exist
        # 2. Requisition should be created and approved
        # 3. Asset Manager allocates asset
        # 4. Asset Manager processes retrieval
        
        workflow_success = True
        
        # Check if we have the necessary test data
        required_data = ['asset_type_id', 'asset_def_id', 'requisition_id']
        missing_data = [key for key in required_data if key not in self.test_data]
        
        if missing_data:
            print(f"   ⚠️ Missing test data for workflow: {missing_data}")
            workflow_success = False
        
        # Test Asset Manager dashboard stats
        if not self.test_asset_manager_dashboard_stats():
            workflow_success = False
        
        # Test Asset Allocations
        if not self.test_asset_allocations():
            workflow_success = False
        
        # Test Asset Retrievals
        if not self.test_asset_retrievals():
            workflow_success = False
        
        # Test Access Control
        self.test_asset_manager_access_control()
        
        if workflow_success:
            print("   ✅ Asset Manager workflow completed successfully")
        else:
            print("   ⚠️ Asset Manager workflow had some issues")
        
        return workflow_success

def main():
    print("🚀 Starting Asset Inventory Management System API Tests")
    print("=" * 60)
    
    tester = AssetInventoryAPITester()
    
    # Test user credentials
    test_users = [
        ("admin@company.com", "password123", "Administrator"),
        ("hr@company.com", "password123", "HR Manager"),
        ("manager@company.com", "password123", "Manager"),
        ("employee@company.com", "password123", "Employee"),
        ("assetmanager@company.com", "password123", "Asset Manager")
    ]
    
    # Test authentication for all users
    print("\n🔐 AUTHENTICATION TESTS")
    print("-" * 30)
    login_success = True
    for email, password, role in test_users:
        if not tester.test_login(email, password, role):
            login_success = False
    
    if not any(role in tester.tokens for role in ["HR Manager", "Administrator"]):
        print("\n❌ No admin-level users logged in. Cannot proceed with CRUD tests.")
        return 1
    
    # Test /auth/me for all users
    for role in ["Administrator", "HR Manager", "Manager", "Employee", "Asset Manager"]:
        if role in tester.tokens:
            tester.test_auth_me(role)
    
    # Test dashboard stats for all users
    print("\n📊 DASHBOARD TESTS")
    print("-" * 20)
    for role in ["Administrator", "HR Manager", "Manager", "Employee", "Asset Manager"]:
        if role in tester.tokens:
            tester.test_dashboard_stats(role)
    
    # Test CRUD operations
    print("\n🔧 CRUD OPERATIONS TESTS")
    print("-" * 25)
    tester.test_asset_type_crud()
    tester.test_asset_definition_crud()
    tester.test_asset_requisition_workflow()
    
    # Test access control
    tester.test_role_based_access()
    
    # Test validation rules
    tester.test_validation_rules()
    
    # Test new Administrator features
    print("\n🆕 NEW ADMINISTRATOR FEATURES TESTS")
    print("-" * 35)
    tester.test_user_management()
    tester.test_multi_role_system()
    tester.test_company_profile()
    tester.test_password_change()
    tester.test_bulk_import_template()
    tester.test_new_admin_features_access_control()
    
    # Test Asset Manager features
    print("\n🎯 ASSET MANAGER FEATURES TESTS")
    print("-" * 32)
    if "Asset Manager" in tester.tokens:
        tester.test_asset_manager_workflow()
    else:
        print("❌ Asset Manager not logged in - skipping Asset Manager tests")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())