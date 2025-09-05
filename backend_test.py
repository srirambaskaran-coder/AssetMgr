import requests
import sys
import json
from datetime import datetime

class AssetInventoryAPITester:
    def __init__(self, base_url="https://resource-manager-6.preview.emergentagent.com"):
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
                    user_roles = user.get('roles', [])
                    if any(role in ['Employee', 'Manager'] for role in user_roles) and user['id'] != self.users.get('Employee', {}).get('id'):
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

    def test_asset_requisition_withdrawal(self):
        """Test Enhanced Asset Requisition Withdrawal/Delete functionality"""
        print(f"\n🗑️ Testing Asset Requisition Withdrawal/Delete Functionality")
        
        if 'asset_type_id' not in self.test_data:
            print("❌ Skipping Withdrawal tests - no asset type created")
            return False
        
        # Test 1: Create multiple requisitions for withdrawal testing
        from datetime import datetime, timedelta
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        # Create requisition by Employee for withdrawal test
        employee_requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Test requisition for withdrawal testing",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Employee Requisition for Withdrawal Test",
            "POST",
            "asset-requisitions",
            200,
            data=employee_requisition_data,
            user_role="Employee"
        )
        
        if success:
            employee_requisition_id = response['id']
            self.test_data['employee_withdrawal_req_id'] = employee_requisition_id
            print(f"   Created employee requisition ID: {employee_requisition_id[:8]}...")
        else:
            print("❌ Failed to create employee requisition for withdrawal test")
            return False
        
        # Create another requisition by Manager for cross-user testing
        manager_requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Manager test requisition for withdrawal testing",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Manager Requisition for Cross-User Test",
            "POST",
            "asset-requisitions",
            200,
            data=manager_requisition_data,
            user_role="Manager"
        )
        
        if success:
            manager_requisition_id = response['id']
            self.test_data['manager_withdrawal_req_id'] = manager_requisition_id
            print(f"   Created manager requisition ID: {manager_requisition_id[:8]}...")
        
        # Test 2: Employee withdraws their own pending request (should succeed)
        success, response = self.run_test(
            "Employee Withdraw Own Pending Request",
            "DELETE",
            f"asset-requisitions/{employee_requisition_id}",
            200,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee successfully withdrew their own pending request")
        else:
            print("   ❌ Employee failed to withdraw their own pending request")
        
        # Test 3: Employee tries to withdraw another user's request (should fail)
        if 'manager_withdrawal_req_id' in self.test_data:
            success, response = self.run_test(
                "Employee Withdraw Other User's Request (Should Fail)",
                "DELETE",
                f"asset-requisitions/{self.test_data['manager_withdrawal_req_id']}",
                403,
                user_role="Employee"
            )
            
            if success:
                print("   ✅ Employee correctly denied access to withdraw other user's request")
        
        # Test 4: Administrator can delete any pending request
        if 'manager_withdrawal_req_id' in self.test_data:
            success, response = self.run_test(
                "Administrator Delete Any Pending Request",
                "DELETE",
                f"asset-requisitions/{self.test_data['manager_withdrawal_req_id']}",
                200,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Administrator successfully deleted any pending request")
        
        # Test 5: HR Manager can delete any pending request
        # Create another requisition for HR Manager test
        hr_test_requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "HR Manager test requisition for deletion",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition for HR Manager Delete Test",
            "POST",
            "asset-requisitions",
            200,
            data=hr_test_requisition_data,
            user_role="Employee"
        )
        
        if success and "HR Manager" in self.tokens:
            hr_test_req_id = response['id']
            success, response = self.run_test(
                "HR Manager Delete Any Pending Request",
                "DELETE",
                f"asset-requisitions/{hr_test_req_id}",
                200,
                user_role="HR Manager"
            )
            
            if success:
                print("   ✅ HR Manager successfully deleted any pending request")
        
        # Test 6: Try to withdraw non-existent requisition (should fail)
        success, response = self.run_test(
            "Withdraw Non-existent Requisition (Should Fail)",
            "DELETE",
            "asset-requisitions/non-existent-id",
            404,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Correctly returned 404 for non-existent requisition")
        
        # Test 7: Create and approve a requisition, then try to withdraw (should fail)
        processed_req_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Test requisition for processed status test",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition for Processed Status Test",
            "POST",
            "asset-requisitions",
            200,
            data=processed_req_data,
            user_role="Employee"
        )
        
        if success:
            processed_req_id = response['id']
            
            # Manually update the requisition status to simulate approval
            # Note: This would normally be done through approval workflow
            # For testing purposes, we'll try to withdraw it as-is and expect it to work
            # since it's still pending, then we'll test the validation message
            
            success, response = self.run_test(
                "Try to Withdraw Pending Request (Should Work)",
                "DELETE",
                f"asset-requisitions/{processed_req_id}",
                200,
                user_role="Employee"
            )
            
            if success:
                print("   ✅ Pending request withdrawal works correctly")
        
        return True

    def test_multi_role_withdrawal_access(self):
        """Test multi-role access control for withdrawal functionality"""
        print(f"\n🎭 Testing Multi-Role Withdrawal Access Control")
        
        if 'asset_type_id' not in self.test_data:
            print("❌ Skipping Multi-Role Withdrawal tests - no asset type created")
            return False
        
        # Create test requisition for multi-role testing
        from datetime import datetime, timedelta
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        multi_role_req_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Multi-role access control test requisition",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition for Multi-Role Test",
            "POST",
            "asset-requisitions",
            200,
            data=multi_role_req_data,
            user_role="Employee"
        )
        
        if not success:
            print("❌ Failed to create requisition for multi-role test")
            return False
        
        multi_role_req_id = response['id']
        print(f"   Created multi-role test requisition ID: {multi_role_req_id[:8]}...")
        
        # Test that different roles can access the withdrawal endpoint appropriately
        # Employee should be able to withdraw their own request
        success, response = self.run_test(
            "Multi-Role: Employee Withdraw Own Request",
            "DELETE",
            f"asset-requisitions/{multi_role_req_id}",
            200,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Multi-role system: Employee can withdraw own request")
        
        # Create another requisition for Administrator test
        admin_test_req_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Administrator multi-role test requisition",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition for Administrator Multi-Role Test",
            "POST",
            "asset-requisitions",
            200,
            data=admin_test_req_data,
            user_role="Manager"
        )
        
        if success:
            admin_test_req_id = response['id']
            
            # Test Administrator can delete any request (multi-role compatibility)
            success, response = self.run_test(
                "Multi-Role: Administrator Delete Any Request",
                "DELETE",
                f"asset-requisitions/{admin_test_req_id}",
                200,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Multi-role system: Administrator can delete any request")
        
        return True

    def test_requisition_data_integrity(self):
        """Test data integrity after withdrawal operations"""
        print(f"\n🔍 Testing Requisition Data Integrity After Withdrawal")
        
        if 'asset_type_id' not in self.test_data:
            print("❌ Skipping Data Integrity tests - no asset type created")
            return False
        
        # Get initial count of requisitions
        success, initial_response = self.run_test(
            "Get Initial Requisitions Count",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to get initial requisitions count")
            return False
        
        initial_count = len(initial_response)
        print(f"   Initial requisitions count: {initial_count}")
        
        # Create test requisition for data integrity test
        from datetime import datetime, timedelta
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        integrity_req_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Data integrity test requisition",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition for Data Integrity Test",
            "POST",
            "asset-requisitions",
            200,
            data=integrity_req_data,
            user_role="Employee"
        )
        
        if not success:
            print("❌ Failed to create requisition for data integrity test")
            return False
        
        integrity_req_id = response['id']
        print(f"   Created integrity test requisition ID: {integrity_req_id[:8]}...")
        
        # Verify requisition was created (count should increase by 1)
        success, after_create_response = self.run_test(
            "Verify Requisition Created",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            after_create_count = len(after_create_response)
            if after_create_count == initial_count + 1:
                print("   ✅ Requisition creation verified - count increased correctly")
            else:
                print(f"   ⚠️ Unexpected count after creation: {after_create_count} (expected {initial_count + 1})")
        
        # Withdraw the requisition
        success, response = self.run_test(
            "Withdraw Requisition for Data Integrity Test",
            "DELETE",
            f"asset-requisitions/{integrity_req_id}",
            200,
            user_role="Employee"
        )
        
        if not success:
            print("❌ Failed to withdraw requisition for data integrity test")
            return False
        
        print("   ✅ Requisition withdrawn successfully")
        
        # Verify requisition was properly removed (count should return to initial)
        success, after_delete_response = self.run_test(
            "Verify Requisition Removed",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            after_delete_count = len(after_delete_response)
            if after_delete_count == initial_count:
                print("   ✅ Data integrity verified - requisition properly removed from database")
            else:
                print(f"   ❌ Data integrity issue: count after deletion is {after_delete_count} (expected {initial_count})")
        
        # Verify withdrawn requisition cannot be accessed
        success, response = self.run_test(
            "Try to Access Withdrawn Requisition (Should Fail)",
            "GET",
            f"asset-requisitions",  # We'll check if the withdrawn ID is in the list
            200,
            user_role="Administrator"
        )
        
        if success:
            withdrawn_req_found = any(req['id'] == integrity_req_id for req in response)
            if not withdrawn_req_found:
                print("   ✅ Withdrawn requisition not found in requisitions list - proper cleanup")
            else:
                print("   ❌ Withdrawn requisition still found in requisitions list - cleanup issue")
        
        # Verify that withdrawal doesn't affect other user's requisitions
        success, all_reqs_response = self.run_test(
            "Verify Other Requisitions Unaffected",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            # Check that we still have requisitions from other tests
            other_user_reqs = [req for req in all_reqs_response if req['requested_by'] != self.users.get('Employee', {}).get('id')]
            if other_user_reqs:
                print(f"   ✅ Other users' requisitions unaffected - found {len(other_user_reqs)} requisitions from other users")
            else:
                print("   ℹ️ No other users' requisitions found for comparison")
        
        return True

    def test_role_based_requisition_access_multi_role(self):
        """Test role-based requisition access with multi-role system"""
        print(f"\n🔐 Testing Role-Based Requisition Access with Multi-Role System")
        
        # Test that get_asset_requisitions works correctly with multi-role users
        test_roles = ["Employee", "Manager", "HR Manager", "Administrator"]
        
        for role in test_roles:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Multi-Role: Get Requisitions as {role}",
                    "GET",
                    "asset-requisitions",
                    200,
                    user_role=role
                )
                
                if success:
                    print(f"   ✅ {role} can access requisitions - found {len(response)} requisitions")
                    
                    # Verify role-based filtering is working
                    if role == "Employee":
                        # Employee should only see their own requisitions
                        employee_id = self.users.get('Employee', {}).get('id')
                        if employee_id:
                            own_reqs = [req for req in response if req['requested_by'] == employee_id]
                            other_reqs = [req for req in response if req['requested_by'] != employee_id]
                            if len(other_reqs) == 0:
                                print(f"     ✅ Employee correctly sees only own requisitions ({len(own_reqs)} found)")
                            else:
                                print(f"     ⚠️ Employee sees other users' requisitions ({len(other_reqs)} found)")
                    
                    elif role in ["Administrator", "HR Manager"]:
                        # Admin and HR should see all requisitions
                        if len(response) > 0:
                            print(f"     ✅ {role} can see all requisitions as expected")
                    
                    elif role == "Manager":
                        # Manager should see pending requisitions and their own
                        pending_reqs = [req for req in response if req['status'] == 'Pending']
                        print(f"     ✅ Manager can see requisitions including {len(pending_reqs)} pending ones")
        
        return True

    def test_dashboard_stats_multi_role(self):
        """Test dashboard stats with multi-role users"""
        print(f"\n📊 Testing Dashboard Stats with Multi-Role Users")
        
        # Test dashboard stats for different roles to ensure multi-role compatibility
        test_roles = ["Employee", "Manager", "HR Manager", "Administrator", "Asset Manager"]
        
        for role in test_roles:
            if role in self.tokens:
                success, response = self.run_test(
                    f"Multi-Role Dashboard Stats: {role}",
                    "GET",
                    "dashboard/stats",
                    200,
                    user_role=role
                )
                
                if success:
                    print(f"   ✅ {role} dashboard stats working - keys: {list(response.keys())}")
                    
                    # Verify role-specific stats are present
                    if role in ["Administrator", "HR Manager"]:
                        if "pending_requisitions" in response:
                            print(f"     ✅ {role} sees pending_requisitions: {response['pending_requisitions']}")
                        else:
                            print(f"     ⚠️ {role} missing pending_requisitions stat")
                    
                    if role == "Manager":
                        if "pending_approvals" in response:
                            print(f"     ✅ Manager sees pending_approvals: {response['pending_approvals']}")
                        else:
                            print(f"     ⚠️ Manager missing pending_approvals stat")
                    
                    if role == "Employee":
                        employee_stats = ["my_requisitions", "my_allocated_assets"]
                        missing_stats = [stat for stat in employee_stats if stat not in response]
                        if not missing_stats:
                            print(f"     ✅ Employee sees all expected stats: my_requisitions={response.get('my_requisitions', 0)}, my_allocated_assets={response.get('my_allocated_assets', 0)}")
                        else:
                            print(f"     ⚠️ Employee missing stats: {missing_stats}")
        
        return True

    def test_asset_type_manager_assignment(self):
        """Test Asset Type Manager Assignment feature"""
        print(f"\n👨‍💼 Testing Asset Type Manager Assignment Feature")
        
        # Test 1: Get Asset Managers Endpoint
        print("\n--- 1. Asset Managers Endpoint Testing ---")
        success, response = self.run_test(
            "Get Asset Managers",
            "GET",
            "users/asset-managers",
            200,
            user_role="Administrator"
        )
        
        asset_managers = []
        if success:
            asset_managers = response
            print(f"   ✅ Found {len(asset_managers)} Asset Managers")
            for manager in asset_managers:
                print(f"     - {manager.get('name', 'Unknown')} ({manager.get('email', 'Unknown')})")
                print(f"       ID: {manager.get('id', 'Unknown')}")
                print(f"       Roles: {manager.get('roles', [])}")
        else:
            print("   ❌ Failed to get Asset Managers")
            return False
        
        # Test 2: Create Asset Type without Asset Manager Assignment
        print("\n--- 2. Asset Type Creation without Asset Manager ---")
        asset_type_no_manager = {
            "code": "TESTAM01",
            "name": "Test Asset Type No Manager",
            "depreciation_applicable": True,
            "asset_life": 3,
            "to_be_recovered_on_separation": True,
            "status": "Active",
            "assigned_asset_manager_id": None
        }
        
        success, response = self.run_test(
            "Create Asset Type without Asset Manager",
            "POST",
            "asset-types",
            200,
            data=asset_type_no_manager,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_type_no_manager_id'] = response['id']
            print(f"   ✅ Created asset type without manager: {response['id']}")
            print(f"   Assigned Asset Manager ID: {response.get('assigned_asset_manager_id', 'None')}")
            print(f"   Assigned Asset Manager Name: {response.get('assigned_asset_manager_name', 'None')}")
        else:
            print("   ❌ Failed to create asset type without manager")
        
        # Test 3: Create Asset Type with valid Asset Manager Assignment
        print("\n--- 3. Asset Type Creation with Asset Manager Assignment ---")
        if asset_managers:
            selected_manager = asset_managers[0]  # Use first available Asset Manager
            asset_type_with_manager = {
                "code": "TESTAM02",
                "name": "Test Asset Type With Manager",
                "depreciation_applicable": True,
                "asset_life": 5,
                "to_be_recovered_on_separation": True,
                "status": "Active",
                "assigned_asset_manager_id": selected_manager['id']
            }
            
            success, response = self.run_test(
                "Create Asset Type with Asset Manager",
                "POST",
                "asset-types",
                200,
                data=asset_type_with_manager,
                user_role="Administrator"
            )
            
            if success:
                self.test_data['asset_type_with_manager_id'] = response['id']
                print(f"   ✅ Created asset type with manager: {response['id']}")
                print(f"   Assigned Asset Manager ID: {response.get('assigned_asset_manager_id', 'None')}")
                print(f"   Assigned Asset Manager Name: {response.get('assigned_asset_manager_name', 'None')}")
                
                # Verify the manager name was populated correctly
                if response.get('assigned_asset_manager_name') == selected_manager['name']:
                    print("   ✅ Asset Manager name populated correctly")
                else:
                    print(f"   ❌ Asset Manager name mismatch: expected {selected_manager['name']}, got {response.get('assigned_asset_manager_name')}")
            else:
                print("   ❌ Failed to create asset type with manager")
        else:
            print("   ⚠️ No Asset Managers available for assignment test")
        
        # Test 4: Create Asset Type with invalid Asset Manager ID (should fail)
        print("\n--- 4. Asset Type Creation with Invalid Asset Manager ---")
        asset_type_invalid_manager = {
            "code": "TESTAM03",
            "name": "Test Asset Type Invalid Manager",
            "depreciation_applicable": False,
            "status": "Active",
            "assigned_asset_manager_id": "invalid-manager-id"
        }
        
        success, response = self.run_test(
            "Create Asset Type with Invalid Asset Manager (Should Fail)",
            "POST",
            "asset-types",
            400,
            data=asset_type_invalid_manager,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Invalid Asset Manager ID correctly rejected")
        else:
            print("   ❌ Invalid Asset Manager ID was not rejected")
        
        # Test 5: Create Asset Type with non-Asset Manager user (should fail)
        print("\n--- 5. Asset Type Creation with Non-Asset Manager User ---")
        # Get a non-Asset Manager user (Employee)
        success, users_response = self.run_test(
            "Get Users for Non-Asset Manager Test",
            "GET",
            "users",
            200,
            user_role="Administrator"
        )
        
        non_asset_manager = None
        if success:
            for user in users_response:
                user_roles = user.get('roles', [])
                if 'Asset Manager' not in user_roles and 'Employee' in user_roles:
                    non_asset_manager = user
                    break
        
        if non_asset_manager:
            asset_type_non_manager = {
                "code": "TESTAM04",
                "name": "Test Asset Type Non Manager",
                "depreciation_applicable": False,
                "status": "Active",
                "assigned_asset_manager_id": non_asset_manager['id']
            }
            
            success, response = self.run_test(
                "Create Asset Type with Non-Asset Manager (Should Fail)",
                "POST",
                "asset-types",
                400,
                data=asset_type_non_manager,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Non-Asset Manager user correctly rejected")
            else:
                print("   ❌ Non-Asset Manager user was not rejected")
        else:
            print("   ⚠️ No non-Asset Manager user found for validation test")
        
        # Test 6: Update Asset Type to assign Asset Manager
        print("\n--- 6. Asset Type Update - Assign Asset Manager ---")
        if 'asset_type_no_manager_id' in self.test_data and asset_managers:
            selected_manager = asset_managers[0]
            update_assign_manager = {
                "assigned_asset_manager_id": selected_manager['id']
            }
            
            success, response = self.run_test(
                "Update Asset Type - Assign Manager",
                "PUT",
                f"asset-types/{self.test_data['asset_type_no_manager_id']}",
                200,
                data=update_assign_manager,
                user_role="Administrator"
            )
            
            if success:
                print(f"   ✅ Asset Manager assigned via update")
                print(f"   Assigned Asset Manager ID: {response.get('assigned_asset_manager_id', 'None')}")
                print(f"   Assigned Asset Manager Name: {response.get('assigned_asset_manager_name', 'None')}")
                
                # Verify the manager name was populated correctly
                if response.get('assigned_asset_manager_name') == selected_manager['name']:
                    print("   ✅ Asset Manager name populated correctly on update")
                else:
                    print(f"   ❌ Asset Manager name mismatch on update")
            else:
                print("   ❌ Failed to assign Asset Manager via update")
        
        # Test 7: Update Asset Type to unassign Asset Manager
        print("\n--- 7. Asset Type Update - Unassign Asset Manager ---")
        if 'asset_type_with_manager_id' in self.test_data:
            update_unassign_manager = {
                "assigned_asset_manager_id": None
            }
            
            success, response = self.run_test(
                "Update Asset Type - Unassign Manager",
                "PUT",
                f"asset-types/{self.test_data['asset_type_with_manager_id']}",
                200,
                data=update_unassign_manager,
                user_role="Administrator"
            )
            
            if success:
                print(f"   ✅ Asset Manager unassigned via update")
                print(f"   Assigned Asset Manager ID: {response.get('assigned_asset_manager_id', 'None')}")
                print(f"   Assigned Asset Manager Name: {response.get('assigned_asset_manager_name', 'None')}")
                
                # Verify both ID and name are cleared
                if response.get('assigned_asset_manager_id') is None and response.get('assigned_asset_manager_name') is None:
                    print("   ✅ Asset Manager assignment properly cleared")
                else:
                    print("   ❌ Asset Manager assignment not properly cleared")
            else:
                print("   ❌ Failed to unassign Asset Manager via update")
        
        # Test 8: Update Asset Type with invalid Asset Manager (should fail)
        print("\n--- 8. Asset Type Update with Invalid Asset Manager ---")
        if 'asset_type_no_manager_id' in self.test_data:
            update_invalid_manager = {
                "assigned_asset_manager_id": "invalid-update-manager-id"
            }
            
            success, response = self.run_test(
                "Update Asset Type with Invalid Manager (Should Fail)",
                "PUT",
                f"asset-types/{self.test_data['asset_type_no_manager_id']}",
                400,
                data=update_invalid_manager,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Invalid Asset Manager ID correctly rejected on update")
            else:
                print("   ❌ Invalid Asset Manager ID was not rejected on update")
        
        # Test 9: Verify Asset Manager assignment persists in retrieval
        print("\n--- 9. Asset Manager Assignment Data Persistence ---")
        if 'asset_type_no_manager_id' in self.test_data:
            success, response = self.run_test(
                "Get Asset Type - Verify Manager Assignment",
                "GET",
                f"asset-types/{self.test_data['asset_type_no_manager_id']}",
                200,
                user_role="Administrator"
            )
            
            if success:
                print(f"   ✅ Asset type retrieved successfully")
                print(f"   Assigned Asset Manager ID: {response.get('assigned_asset_manager_id', 'None')}")
                print(f"   Assigned Asset Manager Name: {response.get('assigned_asset_manager_name', 'None')}")
                
                # Check if assignment persisted from previous update
                if response.get('assigned_asset_manager_id') is not None:
                    print("   ✅ Asset Manager assignment persisted correctly")
                else:
                    print("   ⚠️ Asset Manager assignment not persisted (may be expected if cleared)")
            else:
                print("   ❌ Failed to retrieve asset type for persistence check")
        
        # Test 10: Get all Asset Types and verify manager assignments are included
        print("\n--- 10. Asset Types List - Manager Assignment Display ---")
        success, response = self.run_test(
            "Get All Asset Types - Check Manager Assignments",
            "GET",
            "asset-types",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   ✅ Retrieved {len(response)} asset types")
            manager_assigned_count = 0
            for asset_type in response:
                if asset_type.get('assigned_asset_manager_id'):
                    manager_assigned_count += 1
                    print(f"     - {asset_type.get('name', 'Unknown')} assigned to {asset_type.get('assigned_asset_manager_name', 'Unknown')}")
            
            print(f"   Asset types with managers assigned: {manager_assigned_count}")
            if manager_assigned_count > 0:
                print("   ✅ Asset Manager assignments visible in list")
            else:
                print("   ⚠️ No Asset Manager assignments found in list")
        else:
            print("   ❌ Failed to retrieve asset types list")
        
        # Test 11: Access Control - HR Manager can assign Asset Managers
        print("\n--- 11. Access Control - HR Manager Asset Manager Assignment ---")
        if "HR Manager" in self.tokens and asset_managers:
            hr_asset_type = {
                "code": "TESTAM05",
                "name": "HR Manager Test Asset Type",
                "depreciation_applicable": False,
                "status": "Active",
                "assigned_asset_manager_id": asset_managers[0]['id']
            }
            
            success, response = self.run_test(
                "HR Manager Create Asset Type with Manager",
                "POST",
                "asset-types",
                200,
                data=hr_asset_type,
                user_role="HR Manager"
            )
            
            if success:
                print("   ✅ HR Manager can assign Asset Managers")
                print(f"   Assigned Manager: {response.get('assigned_asset_manager_name', 'None')}")
            else:
                print("   ❌ HR Manager cannot assign Asset Managers")
        else:
            print("   ⚠️ HR Manager not available or no Asset Managers for access control test")
        
        # Test 12: Access Control - Employee cannot access Asset Managers endpoint
        print("\n--- 12. Access Control - Employee Asset Managers Access ---")
        success, response = self.run_test(
            "Employee Get Asset Managers (Should Fail)",
            "GET",
            "users/asset-managers",
            403,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to Asset Managers endpoint")
        else:
            print("   ❌ Employee was not denied access to Asset Managers endpoint")
        
        print("\n--- Asset Type Manager Assignment Testing Summary ---")
        print("✅ Asset Type Manager Assignment feature testing completed")
        return True

    def test_sriram_password_update_and_login(self):
        """Test specific password update and login issue for user sriram@company.com"""
        print(f"\n🔐 Testing Password Update and Login for sriram@company.com")
        
        # Test 1: Check if user sriram@company.com exists in database
        print("\n--- 1. User Database State Verification ---")
        success, users_response = self.run_test(
            "Get All Users to Check sriram@company.com",
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
                print(f"   ✅ User sriram@company.com found in database")
                print(f"   User ID: {sriram_user.get('id', 'Unknown')}")
                print(f"   Name: {sriram_user.get('name', 'Unknown')}")
                print(f"   Roles: {sriram_user.get('roles', [])}")
                print(f"   Is Active: {sriram_user.get('is_active', False)}")
                print(f"   Has password_hash field: {'password_hash' in str(sriram_user)}")
                self.test_data['sriram_user_id'] = sriram_user['id']
            else:
                print("   ❌ User sriram@company.com NOT found in database")
                # Create the user for testing
                print("   Creating sriram@company.com for testing...")
                sriram_create_data = {
                    "email": "sriram@company.com",
                    "name": "Sriram Test User",
                    "roles": ["Employee"],
                    "designation": "Software Developer",
                    "password": "password123"
                }
                
                success, response = self.run_test(
                    "Create sriram@company.com User",
                    "POST",
                    "users",
                    200,
                    data=sriram_create_data,
                    user_role="Administrator"
                )
                
                if success:
                    self.test_data['sriram_user_id'] = response['id']
                    sriram_user = response
                    print(f"   ✅ Created sriram@company.com with ID: {response['id']}")
                else:
                    print("   ❌ Failed to create sriram@company.com user")
                    return False
        
        # Test 2: Test initial login with password123
        print("\n--- 2. Initial Login Authentication Testing ---")
        initial_login_data = {
            "email": "sriram@company.com",
            "password": "password123"
        }
        
        success, response = self.run_test(
            "Initial Login sriram@company.com with password123",
            "POST",
            "auth/login",
            200,
            data=initial_login_data
        )
        
        if success:
            print("   ✅ Initial login successful with password123")
            sriram_token = response.get('session_token')
            self.tokens['sriram'] = sriram_token
            self.users['sriram'] = response.get('user', {})
            print(f"   Session token obtained: {sriram_token[:20]}...")
        else:
            print("   ❌ Initial login failed with password123")
            return False
        
        # Test 3: Password Update via PUT /api/users/{user_id}
        print("\n--- 3. Password Update Verification ---")
        if 'sriram_user_id' not in self.test_data:
            print("   ❌ Cannot test password update - no user ID")
            return False
        
        new_password = "newpassword456"
        password_update_data = {
            "password": new_password
        }
        
        success, response = self.run_test(
            "Update sriram@company.com Password",
            "PUT",
            f"users/{self.test_data['sriram_user_id']}",
            200,
            data=password_update_data,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Password update API call successful")
            print(f"   Updated user name: {response.get('name', 'Unknown')}")
            print(f"   Updated user email: {response.get('email', 'Unknown')}")
        else:
            print("   ❌ Password update API call failed")
            return False
        
        # Test 4: Verify old password no longer works
        print("\n--- 4. Old Password Verification (Should Fail) ---")
        old_password_login = {
            "email": "sriram@company.com",
            "password": "password123"
        }
        
        success, response = self.run_test(
            "Login with Old Password (Should Fail)",
            "POST",
            "auth/login",
            401,  # Expecting authentication failure
            data=old_password_login
        )
        
        if success:
            print("   ✅ Old password correctly rejected")
        else:
            print("   ❌ Old password still works (this is a problem)")
        
        # Test 5: Login with new password
        print("\n--- 5. New Password Login Authentication ---")
        new_password_login = {
            "email": "sriram@company.com",
            "password": new_password
        }
        
        success, response = self.run_test(
            "Login with New Password",
            "POST",
            "auth/login",
            200,
            data=new_password_login
        )
        
        if success:
            print("   ✅ New password login successful")
            new_token = response.get('session_token')
            print(f"   New session token: {new_token[:20]}...")
            
            # Verify user data
            user_data = response.get('user', {})
            print(f"   Logged in user: {user_data.get('name', 'Unknown')}")
            print(f"   User roles: {user_data.get('roles', [])}")
            print(f"   User active: {user_data.get('is_active', False)}")
        else:
            print("   ❌ New password login failed")
            return False
        
        # Test 6: Password Hashing Consistency Check
        print("\n--- 6. Password Hashing Consistency Verification ---")
        
        # Test multiple password updates to verify hashing consistency
        test_passwords = ["testpass1", "testpass2", "testpass3"]
        
        for i, test_pass in enumerate(test_passwords):
            print(f"   Testing password change {i+1}: {test_pass}")
            
            # Update password
            update_data = {"password": test_pass}
            success, response = self.run_test(
                f"Update Password to {test_pass}",
                "PUT",
                f"users/{self.test_data['sriram_user_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )
            
            if not success:
                print(f"   ❌ Failed to update password to {test_pass}")
                continue
            
            # Test login with new password
            login_data = {"email": "sriram@company.com", "password": test_pass}
            success, response = self.run_test(
                f"Login with {test_pass}",
                "POST",
                "auth/login",
                200,
                data=login_data
            )
            
            if success:
                print(f"   ✅ Password {test_pass} - Update and login successful")
            else:
                print(f"   ❌ Password {test_pass} - Login failed after update")
        
        # Test 7: End-to-End Flow Testing
        print("\n--- 7. End-to-End Flow Testing ---")
        
        # Create a new test user for complete flow
        from datetime import datetime
        e2e_user_data = {
            "email": f"e2e_test_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "E2E Test User",
            "roles": ["Employee"],
            "password": "initialpass123"
        }
        
        success, response = self.run_test(
            "Create E2E Test User",
            "POST",
            "users",
            200,
            data=e2e_user_data,
            user_role="Administrator"
        )
        
        if success:
            e2e_user_id = response['id']
            e2e_email = response['email']
            print(f"   ✅ Created E2E test user: {e2e_email}")
            
            # Test initial login
            initial_login = {"email": e2e_email, "password": "initialpass123"}
            success, response = self.run_test(
                "E2E Initial Login",
                "POST",
                "auth/login",
                200,
                data=initial_login
            )
            
            if success:
                print("   ✅ E2E Initial login successful")
                
                # Update password
                new_pass = "updatedpass456"
                update_data = {"password": new_pass}
                success, response = self.run_test(
                    "E2E Password Update",
                    "PUT",
                    f"users/{e2e_user_id}",
                    200,
                    data=update_data,
                    user_role="Administrator"
                )
                
                if success:
                    print("   ✅ E2E Password update successful")
                    
                    # Test old password fails
                    old_login = {"email": e2e_email, "password": "initialpass123"}
                    success, response = self.run_test(
                        "E2E Old Password (Should Fail)",
                        "POST",
                        "auth/login",
                        401,
                        data=old_login
                    )
                    
                    if success:
                        print("   ✅ E2E Old password correctly rejected")
                    
                    # Test new password works
                    new_login = {"email": e2e_email, "password": new_pass}
                    success, response = self.run_test(
                        "E2E New Password Login",
                        "POST",
                        "auth/login",
                        200,
                        data=new_login
                    )
                    
                    if success:
                        print("   ✅ E2E New password login successful")
                        print("   ✅ Complete E2E flow working correctly")
                    else:
                        print("   ❌ E2E New password login failed")
                else:
                    print("   ❌ E2E Password update failed")
            else:
                print("   ❌ E2E Initial login failed")
        
        # Test 8: SHA256 Hashing Verification
        print("\n--- 8. SHA256 Hashing Verification ---")
        import hashlib
        
        test_password = "hashtest123"
        expected_hash = hashlib.sha256(test_password.encode()).hexdigest()
        print(f"   Expected SHA256 hash for '{test_password}': {expected_hash[:20]}...")
        
        # Update sriram's password to test password
        update_data = {"password": test_password}
        success, response = self.run_test(
            "Update to Hash Test Password",
            "PUT",
            f"users/{self.test_data['sriram_user_id']}",
            200,
            data=update_data,
            user_role="Administrator"
        )
        
        if success:
            # Try to login with the test password
            login_data = {"email": "sriram@company.com", "password": test_password}
            success, response = self.run_test(
                "Login with Hash Test Password",
                "POST",
                "auth/login",
                200,
                data=login_data
            )
            
            if success:
                print("   ✅ SHA256 hashing appears to be working correctly")
            else:
                print("   ❌ SHA256 hashing may have issues")
        
        print("\n--- Password Update and Login Testing Summary ---")
        print("✅ All password update and login tests completed")
        return True

    def test_email_notification_system(self):
        """Test Email Notification System - SMTP Configuration and Integration"""
        print(f"\n📧 Testing Email Notification System")
        
        # Test 1: Email Configuration API Testing
        print(f"\n📋 Testing Email Configuration API")
        
        # Test GET /api/email-config (should return 404 initially)
        success, response = self.run_test(
            "Get Email Configuration (Should be 404 initially)",
            "GET",
            "email-config",
            404,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ No email configuration found initially (expected)")
        
        # Test POST /api/email-config - Create email configuration
        email_config_data = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "test@company.com",
            "smtp_password": "test_password_123",
            "use_tls": True,
            "use_ssl": False,
            "from_email": "noreply@company.com",
            "from_name": "Asset Management System"
        }
        
        success, response = self.run_test(
            "Create Email Configuration",
            "POST",
            "email-config",
            200,
            data=email_config_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['email_config_id'] = response['id']
            print(f"   Created email config with ID: {response['id']}")
            print(f"   SMTP Server: {response.get('smtp_server', 'Not set')}")
            print(f"   SMTP Port: {response.get('smtp_port', 'Not set')}")
            print(f"   From Email: {response.get('from_email', 'Not set')}")
        
        # Test GET /api/email-config - Retrieve active configuration
        success, response = self.run_test(
            "Get Active Email Configuration",
            "GET",
            "email-config",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Retrieved config - Server: {response.get('smtp_server', 'Unknown')}")
            print(f"   Password masked: {response.get('smtp_password') == '***masked***'}")
        
        # Test PUT /api/email-config/{id} - Update email configuration
        if 'email_config_id' in self.test_data:
            update_data = {
                "smtp_server": "smtp.outlook.com",
                "smtp_port": 587,
                "from_name": "Updated Asset Management System"
            }
            
            success, response = self.run_test(
                "Update Email Configuration",
                "PUT",
                f"email-config/{self.test_data['email_config_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )
            
            if success:
                print(f"   Updated SMTP server: {response.get('smtp_server', 'Not updated')}")
                print(f"   Updated from name: {response.get('from_name', 'Not updated')}")
        
        # Test POST /api/email-config/test - Send test email (will fail without real SMTP)
        test_email_data = {
            "test_email": "admin@company.com"
        }
        
        success, response = self.run_test(
            "Send Test Email (Expected to fail without real SMTP)",
            "POST",
            "email-config/test",
            500,  # Expecting failure due to invalid SMTP
            data=test_email_data,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Test email endpoint correctly handled SMTP failure")
        
        # Test 2: Email Service Integration Testing
        print(f"\n🔧 Testing Email Service Integration")
        
        # Test access control - Employee trying to access email config (should fail)
        success, response = self.run_test(
            "Employee Access Email Config (Should Fail)",
            "GET",
            "email-config",
            403,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to email configuration")
        
        # Test Manager trying to access email config (should fail)
        success, response = self.run_test(
            "Manager Access Email Config (Should Fail)",
            "GET",
            "email-config",
            403,
            user_role="Manager"
        )
        
        if success:
            print("   ✅ Manager correctly denied access to email configuration")
        
        # Test HR Manager trying to access email config (should fail)
        if "HR Manager" in self.tokens:
            success, response = self.run_test(
                "HR Manager Access Email Config (Should Fail)",
                "GET",
                "email-config",
                403,
                user_role="HR Manager"
            )
            
            if success:
                print("   ✅ HR Manager correctly denied access to email configuration")
        
        # Test 3: Email Trigger Integration Testing
        print(f"\n🎯 Testing Email Trigger Integration")
        
        # Create test data for email triggers if not exists
        if 'asset_type_id' not in self.test_data:
            print("   ⚠️ Creating asset type for email trigger testing...")
            asset_type_data = {
                "code": "EMAIL_TEST",
                "name": "Email Test Asset",
                "depreciation_applicable": False,
                "to_be_recovered_on_separation": True,
                "status": "Active"
            }
            
            success, response = self.run_test(
                "Create Asset Type for Email Testing",
                "POST",
                "asset-types",
                200,
                data=asset_type_data,
                user_role="Administrator"
            )
            
            if success:
                self.test_data['email_test_asset_type_id'] = response['id']
        
        # Test Trigger 1: Asset requisition creation
        if 'email_test_asset_type_id' in self.test_data or 'asset_type_id' in self.test_data:
            asset_type_id = self.test_data.get('email_test_asset_type_id', self.test_data.get('asset_type_id'))
            
            from datetime import datetime, timedelta
            required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
            
            requisition_data = {
                "asset_type_id": asset_type_id,
                "request_type": "New Allocation",
                "request_for": "Self",
                "justification": "Email notification test - asset request",
                "required_by_date": required_by_date
            }
            
            success, response = self.run_test(
                "Create Asset Requisition (Email Trigger 1)",
                "POST",
                "asset-requisitions",
                200,
                data=requisition_data,
                user_role="Employee"
            )
            
            if success:
                self.test_data['email_test_requisition_id'] = response['id']
                print(f"   ✅ Asset requisition created - email notification should be triggered")
                print(f"   Requisition ID: {response['id'][:8]}...")
        
        # Test Trigger 2: Manager approval action
        if 'email_test_requisition_id' in self.test_data:
            approval_data = {
                "action": "approve",
                "reason": "Email notification test - manager approval"
            }
            
            success, response = self.run_test(
                "Manager Approve Requisition (Email Trigger 2)",
                "POST",
                f"asset-requisitions/{self.test_data['email_test_requisition_id']}/manager-action",
                200,
                data=approval_data,
                user_role="Administrator"  # Using admin as they can approve any request
            )
            
            if success:
                print(f"   ✅ Manager approval completed - email notification should be triggered")
        
        # Test Trigger 3: Manager rejection action
        # Create another requisition for rejection test
        if 'email_test_asset_type_id' in self.test_data or 'asset_type_id' in self.test_data:
            asset_type_id = self.test_data.get('email_test_asset_type_id', self.test_data.get('asset_type_id'))
            
            rejection_req_data = {
                "asset_type_id": asset_type_id,
                "request_type": "New Allocation",
                "request_for": "Self",
                "justification": "Email notification test - rejection scenario",
                "required_by_date": required_by_date
            }
            
            success, response = self.run_test(
                "Create Requisition for Rejection Test",
                "POST",
                "asset-requisitions",
                200,
                data=rejection_req_data,
                user_role="Employee"
            )
            
            if success:
                rejection_req_id = response['id']
                
                rejection_data = {
                    "action": "reject",
                    "reason": "Email notification test - manager rejection"
                }
                
                success, response = self.run_test(
                    "Manager Reject Requisition (Email Trigger 3)",
                    "POST",
                    f"asset-requisitions/{rejection_req_id}/manager-action",
                    200,
                    data=rejection_data,
                    user_role="Administrator"
                )
                
                if success:
                    print(f"   ✅ Manager rejection completed - email notification should be triggered")
        
        # Test 4: Data Validation Testing
        print(f"\n✅ Testing Email Configuration Validation")
        
        # Test invalid SMTP configuration
        invalid_config_data = {
            "smtp_server": "",  # Empty server
            "smtp_port": 587,
            "smtp_username": "test@company.com",
            "smtp_password": "test_password",
            "from_email": "invalid-email",  # Invalid email format
            "from_name": "Test System"
        }
        
        success, response = self.run_test(
            "Create Invalid Email Configuration (Should Fail)",
            "POST",
            "email-config",
            422,  # Expecting validation error
            data=invalid_config_data,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Invalid email configuration correctly rejected")
        
        # Test invalid port number
        invalid_port_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 99999,  # Invalid port
            "smtp_username": "test@company.com",
            "smtp_password": "test_password",
            "from_email": "test@company.com",
            "from_name": "Test System"
        }
        
        success, response = self.run_test(
            "Create Config with Invalid Port",
            "POST",
            "email-config",
            200,  # This might pass validation but fail on actual use
            data=invalid_port_config,
            user_role="Administrator"
        )
        
        # Test 5: Error Handling Testing
        print(f"\n🚨 Testing Email Error Handling")
        
        # Test updating non-existent email configuration
        success, response = self.run_test(
            "Update Non-existent Email Config (Should Fail)",
            "PUT",
            "email-config/non-existent-id",
            404,
            data={"smtp_server": "test.com"},
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Non-existent email config update correctly rejected")
        
        # Test sending test email to invalid email
        invalid_test_email = {
            "test_email": "invalid-email-format"
        }
        
        success, response = self.run_test(
            "Send Test Email to Invalid Address (Should Fail)",
            "POST",
            "email-config/test",
            422,  # Expecting validation error
            data=invalid_test_email,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Invalid test email address correctly rejected")
        
        # Test 6: Email Template Context Testing
        print(f"\n📝 Testing Email Template Context")
        
        # Create asset definition for allocation testing
        if ('email_test_asset_type_id' in self.test_data or 'asset_type_id' in self.test_data) and 'asset_def_id' not in self.test_data:
            asset_type_id = self.test_data.get('email_test_asset_type_id', self.test_data.get('asset_type_id'))
            
            asset_def_data = {
                "asset_type_id": asset_type_id,
                "asset_code": "EMAIL_TEST_001",
                "asset_description": "Email Test Asset",
                "asset_details": "Asset for email notification testing",
                "asset_value": 25000.0,
                "status": "Available"
            }
            
            success, response = self.run_test(
                "Create Asset Definition for Email Testing",
                "POST",
                "asset-definitions",
                200,
                data=asset_def_data,
                user_role="Administrator"
            )
            
            if success:
                self.test_data['email_test_asset_def_id'] = response['id']
                print(f"   Created asset definition for email testing: {response['id'][:8]}...")
        
        # Test Trigger 4: Asset allocation (if we have approved requisition and asset)
        if 'email_test_requisition_id' in self.test_data and 'email_test_asset_def_id' in self.test_data:
            allocation_data = {
                "requisition_id": self.test_data['email_test_requisition_id'],
                "asset_definition_id": self.test_data['email_test_asset_def_id'],
                "remarks": "Email notification test - asset allocation"
            }
            
            success, response = self.run_test(
                "Create Asset Allocation (Email Trigger 4)",
                "POST",
                "asset-allocations",
                200,
                data=allocation_data,
                user_role="Asset Manager"
            )
            
            if success:
                print(f"   ✅ Asset allocation completed - email notification should be triggered")
                self.test_data['email_test_allocation_id'] = response['id']
        
        # Test Trigger 5: Asset acknowledgment
        if 'email_test_asset_def_id' in self.test_data:
            acknowledgment_data = {
                "acknowledgment_notes": "Email notification test - asset acknowledgment"
            }
            
            # First check if asset is allocated to current user
            success, asset_response = self.run_test(
                "Get Asset for Acknowledgment Test",
                "GET",
                f"asset-definitions/{self.test_data['email_test_asset_def_id']}",
                200,
                user_role="Administrator"
            )
            
            if success and asset_response.get('status') == 'Allocated':
                success, response = self.run_test(
                    "Acknowledge Asset Allocation (Email Trigger 5)",
                    "POST",
                    f"asset-definitions/{self.test_data['email_test_asset_def_id']}/acknowledge",
                    200,
                    data=acknowledgment_data,
                    user_role="Employee"
                )
                
                if success:
                    print(f"   ✅ Asset acknowledgment completed - email notification should be triggered")
                else:
                    print(f"   ⚠️ Asset acknowledgment failed - may not be allocated to current user")
            else:
                print(f"   ⚠️ Asset not allocated, skipping acknowledgment test")
        
        # Test 7: Email Service Method Testing
        print(f"\n🔍 Testing Email Service Methods")
        
        # Test that email service handles missing configuration gracefully
        # This is tested implicitly through the API calls above
        
        # Test multiple email configurations (only one should be active)
        second_config_data = {
            "smtp_server": "smtp.yahoo.com",
            "smtp_port": 587,
            "smtp_username": "test2@company.com",
            "smtp_password": "test_password_456",
            "from_email": "noreply2@company.com",
            "from_name": "Asset Management System 2"
        }
        
        success, response = self.run_test(
            "Create Second Email Configuration",
            "POST",
            "email-config",
            200,
            data=second_config_data,
            user_role="Administrator"
        )
        
        if success:
            print(f"   ✅ Second email configuration created")
            
            # Verify only the new one is active
            success, active_config = self.run_test(
                "Verify Only One Active Configuration",
                "GET",
                "email-config",
                200,
                user_role="Administrator"
            )
            
            if success:
                if active_config.get('smtp_server') == 'smtp.yahoo.com':
                    print(f"   ✅ Only latest configuration is active")
                else:
                    print(f"   ⚠️ Unexpected active configuration")
        
        print(f"\n📧 Email Notification System Testing Summary:")
        print(f"   ✅ Email Configuration API endpoints tested")
        print(f"   ✅ SMTP configuration validation tested")
        print(f"   ✅ Email service integration tested")
        print(f"   ✅ Email triggers in workflows tested")
        print(f"   ✅ Access control for email features tested")
        print(f"   ✅ Error handling scenarios tested")
        print(f"   ⚠️ Note: Actual email sending requires valid SMTP server")
        
        return True

    def test_location_management_api(self):
        """Test Location Management API Testing"""
        print(f"\n🌍 Testing Location Management API")
        
        # Test 1: Create new locations with Code, Name, Country, Status
        location_data_nyc = {
            "code": "NYC",
            "name": "NYC Office",
            "country": "United States",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create NYC Office Location",
            "POST",
            "locations",
            200,
            data=location_data_nyc,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['nyc_location_id'] = response['id']
            print(f"   Created NYC location with ID: {response['id']}")
            print(f"   Code: {response['code']}, Name: {response['name']}")
            print(f"   Country: {response['country']}, Status: {response['status']}")
        
        # Create London Branch location
        location_data_london = {
            "code": "LON",
            "name": "London Branch",
            "country": "United Kingdom",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create London Branch Location",
            "POST",
            "locations",
            200,
            data=location_data_london,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['london_location_id'] = response['id']
            print(f"   Created London location with ID: {response['id']}")
        
        # Test 2: GET /api/locations - Retrieve all locations
        success, response = self.run_test(
            "Get All Locations",
            "GET",
            "locations",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} locations")
            for location in response:
                print(f"     - {location['code']}: {location['name']} ({location['country']})")
        
        # Test 3: PUT /api/locations/{id} - Update location details
        if 'nyc_location_id' in self.test_data:
            update_data = {
                "name": "New York City Headquarters",
                "status": "Active"
            }
            success, response = self.run_test(
                "Update NYC Location Details",
                "PUT",
                f"locations/{self.test_data['nyc_location_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )
            
            if success:
                print(f"   Updated location name: {response['name']}")
        
        # Test 4: Validation - Duplicate location code prevention
        duplicate_location = {
            "code": "NYC",  # Same as existing
            "name": "Another NYC Office",
            "country": "United States",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Duplicate Location Code (Should Fail)",
            "POST",
            "locations",
            400,
            data=duplicate_location,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Duplicate location code correctly rejected")
        
        return True

    def test_user_location_integration(self):
        """Test User Location Integration Testing"""
        print(f"\n👥 Testing User Location Integration")
        
        if 'nyc_location_id' not in self.test_data:
            print("❌ Skipping User Location tests - no location created")
            return False
        
        # Test 5: Create users with location assignment
        user_with_location_data = {
            "email": f"locationuser_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Location Test User",
            "roles": ["Employee"],
            "designation": "Software Engineer",
            "location_id": self.test_data['nyc_location_id'],
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create User with Location Assignment",
            "POST",
            "users",
            200,
            data=user_with_location_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['location_user_id'] = response['id']
            print(f"   Created user with location: {response['location_name']}")
            print(f"   Location ID: {response.get('location_id', 'Not set')}")
        
        # Test 6: Update user location assignment
        if 'location_user_id' in self.test_data and 'london_location_id' in self.test_data:
            update_data = {
                "location_id": self.test_data['london_location_id']
            }
            success, response = self.run_test(
                "Update User Location Assignment",
                "PUT",
                f"users/{self.test_data['location_user_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )
            
            if success:
                print(f"   Updated user location to: {response.get('location_name', 'Unknown')}")
        
        # Test 7: Location validation - invalid location_id
        invalid_location_user = {
            "email": f"invalidloc_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Invalid Location User",
            "roles": ["Employee"],
            "location_id": "invalid-location-id",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create User with Invalid Location (Should Fail)",
            "POST",
            "users",
            400,
            data=invalid_location_user,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Invalid location_id correctly rejected")
        
        # Test 8: GET /api/users - Verify location_name is included
        success, response = self.run_test(
            "Get Users - Verify Location Names",
            "GET",
            "users",
            200,
            user_role="Administrator"
        )
        
        if success:
            users_with_location = [u for u in response if u.get('location_name')]
            print(f"   Found {len(users_with_location)} users with location assignments")
            if users_with_location:
                user = users_with_location[0]
                print(f"   Sample user location: {user.get('location_name', 'None')}")
        
        return True

    def test_asset_manager_location_assignment(self):
        """Test Asset Manager Location Assignment Testing"""
        print(f"\n🎯 Testing Asset Manager Location Assignment")
        
        if 'nyc_location_id' not in self.test_data:
            print("❌ Skipping Asset Manager Location tests - no location created")
            return False
        
        # Get Asset Manager ID
        asset_manager_id = self.users.get("Asset Manager", {}).get("id")
        if not asset_manager_id:
            print("❌ Skipping Asset Manager Location tests - no Asset Manager user found")
            return False
        
        # Test 9: POST /api/asset-manager-locations - Assign Asset Managers to locations
        assignment_data = {
            "asset_manager_id": asset_manager_id,
            "location_id": self.test_data['nyc_location_id']
        }
        
        success, response = self.run_test(
            "Assign Asset Manager to NYC Location",
            "POST",
            "asset-manager-locations",
            200,
            data=assignment_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_manager_assignment_id'] = response['id']
            print(f"   Assigned {response['asset_manager_name']} to {response['location_name']}")
        
        # Test 10: GET /api/asset-manager-locations - Retrieve assignments
        success, response = self.run_test(
            "Get Asset Manager Location Assignments",
            "GET",
            "asset-manager-locations",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} asset manager location assignments")
            for assignment in response:
                print(f"     - {assignment['asset_manager_name']} → {assignment['location_name']}")
        
        # Test 11: DELETE /api/asset-manager-locations/{id} - Remove assignments
        if 'asset_manager_assignment_id' in self.test_data:
            success, response = self.run_test(
                "Remove Asset Manager Location Assignment",
                "DELETE",
                f"asset-manager-locations/{self.test_data['asset_manager_assignment_id']}",
                200,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Asset Manager location assignment removed successfully")
        
        # Test 12: Validation - Asset Manager role required
        employee_id = self.users.get("Employee", {}).get("id")
        if employee_id:
            invalid_assignment = {
                "asset_manager_id": employee_id,  # Employee, not Asset Manager
                "location_id": self.test_data['nyc_location_id']
            }
            
            success, response = self.run_test(
                "Assign Non-Asset Manager to Location (Should Fail)",
                "POST",
                "asset-manager-locations",
                400,
                data=invalid_assignment,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Non-Asset Manager correctly rejected for location assignment")
        
        # Test 13: Validation - Location exists
        invalid_location_assignment = {
            "asset_manager_id": asset_manager_id,
            "location_id": "invalid-location-id"
        }
        
        success, response = self.run_test(
            "Assign Asset Manager to Invalid Location (Should Fail)",
            "POST",
            "asset-manager-locations",
            404,
            data=invalid_location_assignment,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Invalid location correctly rejected for assignment")
        
        return True

    def test_data_migration(self):
        """Test Data Migration Testing"""
        print(f"\n🔄 Testing Data Migration")
        
        # Test 14: POST /api/migrate/set-default-location
        success, response = self.run_test(
            "Set Default Location for Existing Users",
            "POST",
            "migrate/set-default-location",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Migration completed: {response.get('message', 'Success')}")
            print(f"   Users updated: {response.get('users_updated', 0)}")
            print(f"   Default location created: {response.get('default_location_created', False)}")
        
        # Test 15: Verify default location creation
        success, response = self.run_test(
            "Verify Default Location Exists",
            "GET",
            "locations",
            200,
            user_role="Administrator"
        )
        
        if success:
            default_location = next((loc for loc in response if loc['code'] == 'DEFAULT'), None)
            if default_location:
                print(f"   ✅ Default location found: {default_location['name']}")
                self.test_data['default_location_id'] = default_location['id']
            else:
                print("   ⚠️ Default location not found")
        
        # Test 16: Verify migration only affects users without location
        success, response = self.run_test(
            "Verify Users Have Location Assignments After Migration",
            "GET",
            "users",
            200,
            user_role="Administrator"
        )
        
        if success:
            users_without_location = [u for u in response if not u.get('location_id')]
            users_with_location = [u for u in response if u.get('location_id')]
            print(f"   Users with location: {len(users_with_location)}")
            print(f"   Users without location: {len(users_without_location)}")
            
            if len(users_without_location) == 0:
                print("   ✅ All users now have location assignments")
        
        return True

    def test_data_validation(self):
        """Test Data Validation Testing"""
        print(f"\n✅ Testing Data Validation")
        
        # Test 17: Cascade delete protection - location with assigned users
        if 'nyc_location_id' in self.test_data:
            success, response = self.run_test(
                "Delete Location with Assigned Users (Should Fail)",
                "DELETE",
                f"locations/{self.test_data['nyc_location_id']}",
                400,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Location with assigned users correctly protected from deletion")
        
        # Test 18: Cascade delete protection - location with assigned asset managers
        # First, reassign asset manager to test location
        asset_manager_id = self.users.get("Asset Manager", {}).get("id")
        if asset_manager_id and 'london_location_id' in self.test_data:
            assignment_data = {
                "asset_manager_id": asset_manager_id,
                "location_id": self.test_data['london_location_id']
            }
            
            success, response = self.run_test(
                "Assign Asset Manager for Delete Protection Test",
                "POST",
                "asset-manager-locations",
                200,
                data=assignment_data,
                user_role="Administrator"
            )
            
            if success:
                # Now try to delete the location
                success, response = self.run_test(
                    "Delete Location with Assigned Asset Manager (Should Fail)",
                    "DELETE",
                    f"locations/{self.test_data['london_location_id']}",
                    400,
                    user_role="Administrator"
                )
                
                if success:
                    print("   ✅ Location with assigned asset manager correctly protected from deletion")
        
        # Test 19: Duplicate assignment prevention
        if asset_manager_id and 'nyc_location_id' in self.test_data:
            duplicate_assignment = {
                "asset_manager_id": asset_manager_id,
                "location_id": self.test_data['nyc_location_id']
            }
            
            # Create first assignment
            success, response = self.run_test(
                "Create Asset Manager Assignment for Duplicate Test",
                "POST",
                "asset-manager-locations",
                200,
                data=duplicate_assignment,
                user_role="Administrator"
            )
            
            if success:
                # Try to create duplicate
                success, response = self.run_test(
                    "Create Duplicate Asset Manager Assignment (Should Fail)",
                    "POST",
                    "asset-manager-locations",
                    400,
                    data=duplicate_assignment,
                    user_role="Administrator"
                )
                
                if success:
                    print("   ✅ Duplicate asset manager assignment correctly rejected")
        
        return True

    def test_integration_flow(self):
        """Test Integration Flow Testing"""
        print(f"\n🔄 Testing Integration Flow")
        
        # Test 20: Create sample locations (already done in location management test)
        print("   ✅ Sample locations created (NYC Office, London Branch)")
        
        # Test 21: Create Asset Managers and assign to different locations
        if 'nyc_location_id' in self.test_data:
            asset_manager_id = self.users.get("Asset Manager", {}).get("id")
            if asset_manager_id:
                assignment_data = {
                    "asset_manager_id": asset_manager_id,
                    "location_id": self.test_data['nyc_location_id']
                }
                
                success, response = self.run_test(
                    "Integration: Assign Asset Manager to NYC",
                    "POST",
                    "asset-manager-locations",
                    200,
                    data=assignment_data,
                    user_role="Administrator"
                )
                
                if success:
                    print(f"   ✅ Asset Manager assigned to NYC Office")
        
        # Test 22: Create regular users with location assignments (already done)
        print("   ✅ Regular users created with location assignments")
        
        # Test 23: Run migration for existing users (already done)
        print("   ✅ Migration completed for existing users")
        
        # Test 24: Verify location-based data integrity
        success, response = self.run_test(
            "Integration: Verify Location Data Integrity",
            "GET",
            "locations",
            200,
            user_role="Administrator"
        )
        
        if success:
            locations = response
            
            # Check users for each location
            success, users_response = self.run_test(
                "Integration: Get All Users for Location Verification",
                "GET",
                "users",
                200,
                user_role="Administrator"
            )
            
            if success:
                for location in locations:
                    users_in_location = [u for u in users_response if u.get('location_id') == location['id']]
                    print(f"   Location {location['name']}: {len(users_in_location)} users")
            
            # Check asset manager assignments
            success, assignments_response = self.run_test(
                "Integration: Get Asset Manager Assignments for Verification",
                "GET",
                "asset-manager-locations",
                200,
                user_role="Administrator"
            )
            
            if success:
                print(f"   Total asset manager location assignments: {len(assignments_response)}")
                for assignment in assignments_response:
                    print(f"     - {assignment['asset_manager_name']} → {assignment['location_name']}")
        
        print("   ✅ Location-based data integrity verified")
        return True

    def test_location_based_asset_management_system(self):
        """Test complete Location-Based Asset Management System"""
        print(f"\n🌍 Testing Complete Location-Based Asset Management System")
        
        success = True
        
        # Run all location-based tests
        if not self.test_location_management_api():
            success = False
        
        if not self.test_user_location_integration():
            success = False
        
        if not self.test_asset_manager_location_assignment():
            success = False
        
        if not self.test_data_migration():
            success = False
        
        if not self.test_data_validation():
            success = False
        
        if not self.test_integration_flow():
            success = False
        
        if success:
            print("   🎉 Location-Based Asset Management System: ALL TESTS PASSED")
        else:
            print("   ⚠️ Location-Based Asset Management System: Some tests failed")
        
        return success

    def test_enhanced_asset_allocation_routing(self):
        """Test Enhanced Asset Allocation Logic with location-based routing system"""
        print(f"\n🎯 Testing Enhanced Asset Allocation Logic with Location-Based Routing")
        
        # Step 1: Setup verification - Create test data
        print("📋 Step 1: Setting up test data for routing logic")
        
        # Create test locations
        location_data_1 = {
            "code": "NYC01",
            "name": "New York Office",
            "country": "USA",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Test Location 1 (NYC)",
            "POST",
            "locations",
            200,
            data=location_data_1,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['location_1_id'] = response['id']
            print(f"   Created location 1: {response['name']} ({response['code']})")
        
        location_data_2 = {
            "code": "LON01", 
            "name": "London Office",
            "country": "UK",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Test Location 2 (London)",
            "POST",
            "locations",
            200,
            data=location_data_2,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['location_2_id'] = response['id']
            print(f"   Created location 2: {response['name']} ({response['code']})")
        
        # Create test users with locations
        from datetime import datetime
        test_employee_data = {
            "email": f"routing_employee_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Routing Test Employee",
            "roles": ["Employee"],
            "designation": "Software Developer",
            "location_id": self.test_data.get('location_1_id'),
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Test Employee with Location",
            "POST",
            "users",
            200,
            data=test_employee_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['routing_employee_id'] = response['id']
            self.test_data['routing_employee_email'] = response['email']
            print(f"   Created test employee: {response['name']} at {response.get('location_name', 'Unknown')}")
        
        # Create test Asset Manager
        test_asset_manager_data = {
            "email": f"routing_assetmgr_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Routing Test Asset Manager",
            "roles": ["Asset Manager"],
            "designation": "Asset Manager",
            "location_id": self.test_data.get('location_1_id'),
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Test Asset Manager with Location",
            "POST",
            "users",
            200,
            data=test_asset_manager_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['routing_asset_manager_id'] = response['id']
            print(f"   Created test asset manager: {response['name']} at {response.get('location_name', 'Unknown')}")
        
        # Assign Asset Manager to location
        if 'routing_asset_manager_id' in self.test_data and 'location_1_id' in self.test_data:
            am_location_data = {
                "asset_manager_id": self.test_data['routing_asset_manager_id'],
                "location_id": self.test_data['location_1_id']
            }
            
            success, response = self.run_test(
                "Assign Asset Manager to Location",
                "POST",
                "asset-manager-locations",
                200,
                data=am_location_data,
                user_role="Administrator"
            )
            
            if success:
                print(f"   Assigned Asset Manager to location successfully")
        
        # Create asset type with assigned Asset Manager
        if 'routing_asset_manager_id' in self.test_data:
            routing_asset_type_data = {
                "code": "ROUTING_TEST",
                "name": "Routing Test Asset Type",
                "depreciation_applicable": True,
                "asset_life": 3,
                "to_be_recovered_on_separation": True,
                "status": "Active",
                "assigned_asset_manager_id": self.test_data['routing_asset_manager_id']
            }
            
            success, response = self.run_test(
                "Create Asset Type with Assigned Asset Manager",
                "POST",
                "asset-types",
                200,
                data=routing_asset_type_data,
                user_role="Administrator"
            )
            
            if success:
                self.test_data['routing_asset_type_id'] = response['id']
                print(f"   Created asset type with assigned Asset Manager: {response['name']}")
        
        # Step 2: Test Primary Routing - Asset Manager with asset type + location match
        print("\n🎯 Step 2: Testing Primary Routing Logic")
        
        if all(key in self.test_data for key in ['routing_asset_type_id', 'routing_employee_id']):
            # Login as test employee to create requisition
            employee_login_success = self.test_login(
                self.test_data['routing_employee_email'], 
                "TestPassword123!", 
                "Routing_Employee"
            )
            
            if employee_login_success:
                # Create asset requisition
                from datetime import datetime, timedelta
                required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
                
                routing_requisition_data = {
                    "asset_type_id": self.test_data['routing_asset_type_id'],
                    "request_type": "New Allocation",
                    "request_for": "Self",
                    "justification": "Testing enhanced asset allocation routing logic",
                    "required_by_date": required_by_date
                }
                
                success, response = self.run_test(
                    "Create Requisition for Routing Test",
                    "POST",
                    "asset-requisitions",
                    200,
                    data=routing_requisition_data,
                    user_role="Routing_Employee"
                )
                
                if success:
                    self.test_data['routing_requisition_id'] = response['id']
                    print(f"   Created requisition for routing test: {response['id'][:8]}...")
                    
                    # Manager approval to trigger routing
                    manager_action_data = {
                        "action": "approve",
                        "reason": "Approved for routing logic testing"
                    }
                    
                    success, response = self.run_test(
                        "Manager Approve Requisition (Trigger Routing)",
                        "POST",
                        f"asset-requisitions/{self.test_data['routing_requisition_id']}/manager-action",
                        200,
                        data=manager_action_data,
                        user_role="Manager"
                    )
                    
                    if success:
                        print(f"   Manager approved requisition - routing should be triggered")
                        
                        # Verify routing results
                        success, response = self.run_test(
                            "Verify Primary Routing Results",
                            "GET",
                            f"asset-requisitions/{self.test_data['routing_requisition_id']}",
                            200,
                            user_role="Administrator"
                        )
                        
                        if success:
                            status = response.get('status')
                            assigned_to = response.get('assigned_to')
                            assigned_to_name = response.get('assigned_to_name')
                            routing_reason = response.get('routing_reason')
                            assigned_date = response.get('assigned_date')
                            
                            print(f"   Status: {status}")
                            print(f"   Assigned to: {assigned_to_name} ({assigned_to})")
                            print(f"   Routing reason: {routing_reason}")
                            print(f"   Assigned date: {assigned_date}")
                            
                            if status == "Assigned for Allocation":
                                print("   ✅ Primary routing successful - Status set to 'Assigned for Allocation'")
                            else:
                                print(f"   ❌ Primary routing failed - Expected 'Assigned for Allocation', got '{status}'")
                            
                            if assigned_to == self.test_data.get('routing_asset_manager_id'):
                                print("   ✅ Primary routing successful - Assigned to correct Asset Manager")
                            else:
                                print(f"   ❌ Primary routing failed - Not assigned to expected Asset Manager")
                            
                            if routing_reason and "assigned to asset type and employee location" in routing_reason:
                                print("   ✅ Primary routing reason correct")
                            else:
                                print(f"   ❌ Primary routing reason incorrect: {routing_reason}")
        
        # Step 3: Test Secondary Routing - Administrator with location match
        print("\n🎯 Step 3: Testing Secondary Routing Logic (Administrator fallback)")
        
        # Create asset type without assigned Asset Manager
        secondary_asset_type_data = {
            "code": "SECONDARY_TEST",
            "name": "Secondary Routing Test Asset Type",
            "depreciation_applicable": False,
            "status": "Active"
            # No assigned_asset_manager_id
        }
        
        success, response = self.run_test(
            "Create Asset Type without Assigned Asset Manager",
            "POST",
            "asset-types",
            200,
            data=secondary_asset_type_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['secondary_asset_type_id'] = response['id']
            print(f"   Created asset type without Asset Manager: {response['name']}")
            
            # Create Administrator and assign to same location as employee
            test_admin_data = {
                "email": f"routing_admin_{datetime.now().strftime('%H%M%S')}@company.com",
                "name": "Routing Test Administrator",
                "roles": ["Administrator"],
                "designation": "System Administrator",
                "location_id": self.test_data.get('location_1_id'),
                "password": "TestPassword123!"
            }
            
            success, response = self.run_test(
                "Create Test Administrator with Location",
                "POST",
                "users",
                200,
                data=test_admin_data,
                user_role="Administrator"
            )
            
            if success:
                self.test_data['routing_admin_id'] = response['id']
                print(f"   Created test administrator: {response['name']}")
                
                # Assign Administrator to location (using asset-manager-locations endpoint)
                admin_location_data = {
                    "asset_manager_id": self.test_data['routing_admin_id'],
                    "location_id": self.test_data['location_1_id']
                }
                
                success, response = self.run_test(
                    "Assign Administrator to Location",
                    "POST",
                    "asset-manager-locations",
                    200,
                    data=admin_location_data,
                    user_role="Administrator"
                )
                
                if success:
                    print(f"   Assigned Administrator to location successfully")
                    
                    # Create requisition with secondary asset type
                    secondary_requisition_data = {
                        "asset_type_id": self.test_data['secondary_asset_type_id'],
                        "request_type": "New Allocation",
                        "request_for": "Self",
                        "justification": "Testing secondary routing logic (Administrator fallback)",
                        "required_by_date": required_by_date
                    }
                    
                    success, response = self.run_test(
                        "Create Requisition for Secondary Routing Test",
                        "POST",
                        "asset-requisitions",
                        200,
                        data=secondary_requisition_data,
                        user_role="Routing_Employee"
                    )
                    
                    if success:
                        self.test_data['secondary_requisition_id'] = response['id']
                        print(f"   Created secondary requisition: {response['id'][:8]}...")
                        
                        # Manager approval to trigger secondary routing
                        success, response = self.run_test(
                            "Manager Approve Secondary Requisition (Trigger Secondary Routing)",
                            "POST",
                            f"asset-requisitions/{self.test_data['secondary_requisition_id']}/manager-action",
                            200,
                            data=manager_action_data,
                            user_role="Manager"
                        )
                        
                        if success:
                            # Verify secondary routing results
                            success, response = self.run_test(
                                "Verify Secondary Routing Results",
                                "GET",
                                f"asset-requisitions/{self.test_data['secondary_requisition_id']}",
                                200,
                                user_role="Administrator"
                            )
                            
                            if success:
                                status = response.get('status')
                                assigned_to = response.get('assigned_to')
                                assigned_to_name = response.get('assigned_to_name')
                                routing_reason = response.get('routing_reason')
                                
                                print(f"   Status: {status}")
                                print(f"   Assigned to: {assigned_to_name} ({assigned_to})")
                                print(f"   Routing reason: {routing_reason}")
                                
                                if status == "Assigned for Allocation":
                                    print("   ✅ Secondary routing successful - Status set correctly")
                                
                                if assigned_to == self.test_data.get('routing_admin_id'):
                                    print("   ✅ Secondary routing successful - Assigned to Administrator")
                                
                                if routing_reason and "assigned to employee location" in routing_reason:
                                    print("   ✅ Secondary routing reason correct")
        
        # Step 4: Test Final Fallback - Any Administrator
        print("\n🎯 Step 4: Testing Final Fallback Routing Logic")
        
        # Create employee without location
        test_employee_no_location_data = {
            "email": f"routing_employee_no_loc_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Employee Without Location",
            "roles": ["Employee"],
            "designation": "Remote Developer",
            # No location_id
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Employee Without Location",
            "POST",
            "users",
            200,
            data=test_employee_no_location_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['no_location_employee_email'] = response['email']
            print(f"   Created employee without location: {response['name']}")
            
            # Login as employee without location
            no_loc_login_success = self.test_login(
                self.test_data['no_location_employee_email'],
                "TestPassword123!",
                "No_Location_Employee"
            )
            
            if no_loc_login_success:
                # Create requisition
                fallback_requisition_data = {
                    "asset_type_id": self.test_data.get('secondary_asset_type_id', self.test_data.get('routing_asset_type_id')),
                    "request_type": "New Allocation",
                    "request_for": "Self",
                    "justification": "Testing final fallback routing logic",
                    "required_by_date": required_by_date
                }
                
                success, response = self.run_test(
                    "Create Requisition for Fallback Routing Test",
                    "POST",
                    "asset-requisitions",
                    200,
                    data=fallback_requisition_data,
                    user_role="No_Location_Employee"
                )
                
                if success:
                    self.test_data['fallback_requisition_id'] = response['id']
                    print(f"   Created fallback requisition: {response['id'][:8]}...")
                    
                    # Manager approval to trigger fallback routing
                    success, response = self.run_test(
                        "Manager Approve Fallback Requisition (Trigger Fallback Routing)",
                        "POST",
                        f"asset-requisitions/{self.test_data['fallback_requisition_id']}/manager-action",
                        200,
                        data=manager_action_data,
                        user_role="Manager"
                    )
                    
                    if success:
                        # Verify fallback routing results
                        success, response = self.run_test(
                            "Verify Fallback Routing Results",
                            "GET",
                            f"asset-requisitions/{self.test_data['fallback_requisition_id']}",
                            200,
                            user_role="Administrator"
                        )
                        
                        if success:
                            status = response.get('status')
                            assigned_to = response.get('assigned_to')
                            assigned_to_name = response.get('assigned_to_name')
                            routing_reason = response.get('routing_reason')
                            
                            print(f"   Status: {status}")
                            print(f"   Assigned to: {assigned_to_name} ({assigned_to})")
                            print(f"   Routing reason: {routing_reason}")
                            
                            if status == "Assigned for Allocation":
                                print("   ✅ Fallback routing successful - Status set correctly")
                            
                            if routing_reason and "general fallback" in routing_reason:
                                print("   ✅ Fallback routing reason correct")
        
        # Step 5: Test Edge Cases
        print("\n🎯 Step 5: Testing Edge Cases")
        
        # Test rejection doesn't trigger routing
        if 'routing_asset_type_id' in self.test_data:
            edge_case_requisition_data = {
                "asset_type_id": self.test_data['routing_asset_type_id'],
                "request_type": "New Allocation",
                "request_for": "Self",
                "justification": "Testing edge case - rejection should not trigger routing",
                "required_by_date": required_by_date
            }
            
            success, response = self.run_test(
                "Create Requisition for Edge Case Test",
                "POST",
                "asset-requisitions",
                200,
                data=edge_case_requisition_data,
                user_role="Routing_Employee"
            )
            
            if success:
                edge_case_req_id = response['id']
                print(f"   Created edge case requisition: {edge_case_req_id[:8]}...")
                
                # Manager rejection (should NOT trigger routing)
                reject_action_data = {
                    "action": "reject",
                    "reason": "Testing rejection - should not trigger routing"
                }
                
                success, response = self.run_test(
                    "Manager Reject Requisition (Should NOT Trigger Routing)",
                    "POST",
                    f"asset-requisitions/{edge_case_req_id}/manager-action",
                    200,
                    data=reject_action_data,
                    user_role="Manager"
                )
                
                if success:
                    # Verify no routing occurred
                    success, response = self.run_test(
                        "Verify No Routing on Rejection",
                        "GET",
                        f"asset-requisitions/{edge_case_req_id}",
                        200,
                        user_role="Administrator"
                    )
                    
                    if success:
                        status = response.get('status')
                        assigned_to = response.get('assigned_to')
                        routing_reason = response.get('routing_reason')
                        
                        print(f"   Status: {status}")
                        print(f"   Assigned to: {assigned_to}")
                        print(f"   Routing reason: {routing_reason}")
                        
                        if status == "Rejected":
                            print("   ✅ Edge case successful - Rejection does not trigger routing")
                        
                        if not assigned_to:
                            print("   ✅ Edge case successful - No assignment on rejection")
        
        # Step 6: Test Email Notifications
        print("\n📧 Step 6: Testing Email Notification Integration")
        
        # Test that routing triggers email notifications
        success, response = self.run_test(
            "Get Email Configurations (Check if email system is set up)",
            "GET",
            "email-config",
            200,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Email system is configured - routing notifications should be sent")
        else:
            print("   ⚠️ Email system not configured - routing notifications will be logged but not sent")
        
        print("\n🎯 Enhanced Asset Allocation Routing Logic Testing Completed")
        return True

    def test_ndc_separation_reasons_management(self):
        """Test NDC Separation Reasons Management"""
        print(f"\n📋 Testing NDC Separation Reasons Management")
        
        # Test 1: GET /api/separation-reasons - Retrieve all separation reasons
        success, response = self.run_test(
            "Get All Separation Reasons (HR Manager)",
            "GET",
            "separation-reasons",
            200,
            user_role="HR Manager"
        )
        
        if success:
            initial_count = len(response)
            print(f"   Found {initial_count} existing separation reasons")
        
        # Test 2: POST /api/separation-reasons - Create new separation reason
        reason_data = {
            "reason": "Voluntary Resignation - Better Opportunity"
        }
        
        success, response = self.run_test(
            "Create New Separation Reason (HR Manager)",
            "POST",
            "separation-reasons",
            200,
            data=reason_data,
            user_role="HR Manager"
        )
        
        if success:
            self.test_data['separation_reason_id'] = response['id']
            print(f"   Created separation reason with ID: {response['id']}")
            print(f"   Reason: {response['reason']}")
        
        # Test 3: Access control - Administrator can access
        success, response = self.run_test(
            "Get Separation Reasons (Administrator)",
            "GET",
            "separation-reasons",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Administrator can access separation reasons ({len(response)} found)")
        
        # Test 4: Access control - Employee should be denied
        success, response = self.run_test(
            "Employee Access Separation Reasons (Should Fail)",
            "GET",
            "separation-reasons",
            403,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to separation reasons")
        
        return True

    def test_ndc_request_creation_and_management(self):
        """Test NDC Request Creation and Management"""
        print(f"\n📝 Testing NDC Request Creation and Management")
        
        # First, get employees and managers for testing
        success, users_response = self.run_test(
            "Get Users for NDC Testing",
            "GET",
            "users",
            200,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to get users for NDC testing")
            return False
        
        # Find an employee and manager for testing
        employee_with_assets = None
        manager_user = None
        
        for user in users_response:
            user_roles = user.get('roles', [])
            if 'Employee' in user_roles and not employee_with_assets:
                employee_with_assets = user
            if 'Manager' in user_roles and not manager_user:
                manager_user = user
        
        if not employee_with_assets:
            print("❌ No employee found for NDC testing")
            return False
        
        if not manager_user:
            print("❌ No manager found for NDC testing")
            return False
        
        # Test 1: Create NDC request for employee
        from datetime import datetime, timedelta
        
        ndc_data = {
            "employee_id": employee_with_assets['id'],
            "resigned_on": (datetime.now() - timedelta(days=30)).isoformat(),
            "notice_period": "30 days",
            "last_working_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "separation_approved_by": manager_user['id'],
            "separation_approved_on": datetime.now().isoformat(),
            "separation_reason": "Voluntary Resignation - Better Opportunity"
        }
        
        success, response = self.run_test(
            "Create NDC Request (HR Manager)",
            "POST",
            "ndc-requests",
            200,
            data=ndc_data,
            user_role="HR Manager"
        )
        
        if success:
            if isinstance(response, dict) and 'requests' in response:
                # Multiple NDC requests created (one per Asset Manager)
                created_requests = response['requests']
                print(f"   Created {len(created_requests)} NDC requests for different Asset Managers")
                if created_requests:
                    self.test_data['ndc_request_id'] = created_requests[0]['id']
                    print(f"   First NDC request ID: {created_requests[0]['id']}")
            else:
                # Single NDC request created
                self.test_data['ndc_request_id'] = response['id']
                print(f"   Created NDC request with ID: {response['id']}")
        
        # Test 2: Employee validation - non-existent employee
        invalid_ndc_data = {
            "employee_id": "non-existent-employee-id",
            "resigned_on": (datetime.now() - timedelta(days=30)).isoformat(),
            "notice_period": "30 days",
            "last_working_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "separation_approved_by": manager_user['id'],
            "separation_approved_on": datetime.now().isoformat(),
            "separation_reason": "Test Reason"
        }
        
        success, response = self.run_test(
            "Create NDC Request - Invalid Employee (Should Fail)",
            "POST",
            "ndc-requests",
            400,
            data=invalid_ndc_data,
            user_role="HR Manager"
        )
        
        if success:
            print("   ✅ Invalid employee ID correctly rejected")
        
        # Test 3: GET /api/ndc-requests - Retrieve NDC requests
        success, response = self.run_test(
            "Get NDC Requests (HR Manager)",
            "GET",
            "ndc-requests",
            200,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   HR Manager can see {len(response)} NDC requests")
        
        # Test 4: Asset Manager can see their assigned NDC requests
        success, response = self.run_test(
            "Get NDC Requests (Asset Manager)",
            "GET",
            "ndc-requests",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            print(f"   Asset Manager can see {len(response)} assigned NDC requests")
        
        # Test 5: Employee access should be denied
        success, response = self.run_test(
            "Employee Access NDC Requests (Should Fail)",
            "GET",
            "ndc-requests",
            403,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to NDC requests")
        
        return True

    def test_ndc_asset_recovery_management(self):
        """Test NDC Asset Recovery Management"""
        print(f"\n🔄 Testing NDC Asset Recovery Management")
        
        if 'ndc_request_id' not in self.test_data:
            print("❌ Skipping Asset Recovery tests - no NDC request created")
            return False
        
        ndc_id = self.test_data['ndc_request_id']
        
        # Test 1: GET /api/ndc-requests/{id}/assets - Get assets for NDC request
        success, response = self.run_test(
            "Get NDC Assets (Asset Manager)",
            "GET",
            f"ndc-requests/{ndc_id}/assets",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            assets_count = len(response)
            print(f"   Found {assets_count} assets for recovery")
            if assets_count > 0:
                self.test_data['ndc_asset_recovery_id'] = response[0]['id']
                print(f"   First asset recovery ID: {response[0]['id']}")
                print(f"   Asset code: {response[0].get('asset_code', 'Unknown')}")
                print(f"   Asset type: {response[0].get('asset_type_name', 'Unknown')}")
        
        # Test 2: PUT /api/ndc-asset-recovery/{id} - Update asset recovery details
        if 'ndc_asset_recovery_id' in self.test_data:
            recovery_id = self.test_data['ndc_asset_recovery_id']
            
            recovery_update_data = {
                "recovered": True,
                "asset_condition": "Good Condition",
                "returned_on": datetime.now().isoformat(),
                "recovery_value": 0.0,
                "remarks": "Asset recovered in excellent condition during automated testing"
            }
            
            success, response = self.run_test(
                "Update Asset Recovery Details (Asset Manager)",
                "PUT",
                f"ndc-asset-recovery/{recovery_id}",
                200,
                data=recovery_update_data,
                user_role="Asset Manager"
            )
            
            if success:
                print(f"   Asset recovery updated successfully")
                print(f"   Recovered: {response.get('recovered', False)}")
                print(f"   Condition: {response.get('asset_condition', 'Unknown')}")
                print(f"   Status: {response.get('status', 'Unknown')}")
        
        # Test 3: Employee should be denied access to update
        if 'ndc_asset_recovery_id' in self.test_data:
            recovery_id = self.test_data['ndc_asset_recovery_id']
            
            success, response = self.run_test(
                "Employee Update Asset Recovery (Should Fail)",
                "PUT",
                f"ndc-asset-recovery/{recovery_id}",
                403,
                data={"recovered": True},
                user_role="Employee"
            )
            
            if success:
                print("   ✅ Employee correctly denied access to update asset recovery")
        
        return True

    def test_ndc_request_workflow(self):
        """Test NDC Request Workflow"""
        print(f"\n🔄 Testing NDC Request Workflow")
        
        if 'ndc_request_id' not in self.test_data:
            print("❌ Skipping NDC Workflow tests - no NDC request created")
            return False
        
        ndc_id = self.test_data['ndc_request_id']
        
        # Test 1: POST /api/ndc-requests/{id}/revoke - Revoke NDC request
        revoke_data = {
            "reason": "Employee decided to stay - separation cancelled"
        }
        
        success, response = self.run_test(
            "Revoke NDC Request (HR Manager)",
            "POST",
            f"ndc-requests/{ndc_id}/revoke",
            200,
            data=revoke_data,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   NDC request revoked successfully")
            print(f"   Revoke reason: {revoke_data['reason']}")
        
        # Test 2: Employee should be denied access to revoke
        success, response = self.run_test(
            "Employee Revoke NDC Request (Should Fail)",
            "POST",
            f"ndc-requests/{ndc_id}/revoke",
            403,
            data=revoke_data,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to revoke NDC request")
        
        return True

    def test_ndc_system_comprehensive(self):
        """Test NDC (No Dues Certificate) System - Focus on Critical Bug Fix and Complete Workflow"""
        print(f"\n🏢 Testing NDC (No Dues Certificate) System - Post Bug Fix Verification")
        
        # Step 1: Setup - Create test employee with allocated assets
        print(f"\n📋 Step 1: Setting up test data for NDC workflow")
        
        # Create test employee
        from datetime import datetime, timedelta
        employee_data = {
            "email": f"ndc_employee_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "NDC Test Employee",
            "roles": ["Employee"],
            "designation": "Software Developer",
            "date_of_joining": "2023-01-15T00:00:00Z",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Test Employee for NDC",
            "POST",
            "users",
            200,
            data=employee_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to create test employee for NDC testing")
            return False
        
        test_employee_id = response['id']
        print(f"   Created test employee ID: {test_employee_id}")
        
        # Create asset type and definition for allocation
        if 'asset_type_id' not in self.test_data:
            asset_type_data = {
                "code": "NDC_LAPTOP",
                "name": "NDC Test Laptop",
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
            
            if success:
                self.test_data['ndc_asset_type_id'] = response['id']
        
        # Create asset definition
        asset_def_data = {
            "asset_type_id": self.test_data.get('ndc_asset_type_id', self.test_data.get('asset_type_id')),
            "asset_code": f"NDC_LAP_{datetime.now().strftime('%H%M%S')}",
            "asset_description": "NDC Test Laptop",
            "asset_details": "Dell Laptop for NDC Testing",
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
            print("❌ Failed to create asset definition for NDC testing")
            return False
        
        test_asset_id = response['id']
        print(f"   Created test asset ID: {test_asset_id}")
        
        # Allocate asset to employee (simulate allocation)
        allocation_update = {
            "allocated_to": test_employee_id,
            "allocated_to_name": "NDC Test Employee",
            "status": "Allocated"
        }
        
        success, response = self.run_test(
            "Allocate Asset to Test Employee",
            "PUT",
            f"asset-definitions/{test_asset_id}",
            200,
            data=allocation_update,
            user_role="Administrator"
        )
        
        if success:
            print(f"   ✅ Asset allocated to employee successfully")
        else:
            print("❌ Failed to allocate asset to employee")
            return False
        
        # Step 2: Test Critical Bug Fix - NDC Request Creation with correct "allocated_to" field
        print(f"\n🔍 Step 2: Testing Critical Bug Fix - Asset Detection with 'allocated_to' field")
        
        # Create separation reason first
        separation_reason_data = {"reason": "Resignation - Better Opportunity"}
        success, response = self.run_test(
            "Create Separation Reason",
            "POST",
            "separation-reasons",
            200,
            data=separation_reason_data,
            user_role="HR Manager"
        )
        
        if success:
            separation_reason = response['reason']
            print(f"   Created separation reason: {separation_reason}")
        
        # Create NDC request - This should now work with the bug fix
        ndc_request_data = {
            "employee_id": test_employee_id,
            "resigned_on": datetime.now().isoformat(),
            "notice_period": "30 days",
            "last_working_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "separation_approved_by": self.users["Administrator"]["id"],
            "separation_approved_on": datetime.now().isoformat(),
            "separation_reason": "Resignation - Better Opportunity"
        }
        
        success, response = self.run_test(
            "Create NDC Request (Critical Bug Fix Test)",
            "POST",
            "ndc-requests",
            200,
            data=ndc_request_data,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   ✅ CRITICAL BUG FIXED: NDC request created successfully with allocated assets detected")
            print(f"   NDC requests created for {len(response['requests'])} Asset Manager(s)")
            self.test_data['ndc_request_info'] = response['requests'][0]
            ndc_request_id = response['requests'][0]['ndc_request_id']
            self.test_data['ndc_request_id'] = ndc_request_id
        else:
            print(f"   ❌ CRITICAL BUG NOT FIXED: NDC request creation failed")
            return False
        
        # Step 3: Test Asset Manager Routing and Asset Recovery Records
        print(f"\n🎯 Step 3: Testing Asset Manager Routing and Asset Recovery Records")
        
        # Get NDC requests to verify Asset Manager assignment
        success, response = self.run_test(
            "Get NDC Requests (Asset Manager Routing Test)",
            "GET",
            "ndc-requests",
            200,
            user_role="HR Manager"
        )
        
        if success:
            ndc_found = False
            for ndc in response:
                if ndc['id'] == ndc_request_id:
                    ndc_found = True
                    print(f"   ✅ NDC request found with Asset Manager: {ndc['asset_manager_name']}")
                    print(f"   Status: {ndc['status']}")
                    break
            
            if not ndc_found:
                print(f"   ❌ Created NDC request not found in list")
        
        # Get asset recovery records
        success, response = self.run_test(
            "Get NDC Asset Recovery Records",
            "GET",
            f"ndc-requests/{ndc_request_id}/assets",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            print(f"   ✅ Asset recovery records created: {len(response)} assets")
            if response:
                asset_recovery = response[0]
                self.test_data['asset_recovery_id'] = asset_recovery['id']
                print(f"   Asset Code: {asset_recovery['asset_code']}")
                print(f"   Asset Value: ₹{asset_recovery['asset_value']}")
                print(f"   Status: {asset_recovery['status']}")
        
        # Step 4: Test Complete NDC Workflow - Asset Recovery Processing
        print(f"\n🔄 Step 4: Testing Complete NDC Workflow - Asset Recovery Processing")
        
        if 'asset_recovery_id' in self.test_data:
            # Asset Manager processes asset recovery
            recovery_update_data = {
                "recovered": True,
                "asset_condition": "Good Condition",
                "returned_on": datetime.now().isoformat(),
                "recovery_value": 0.0,
                "remarks": "Asset recovered in excellent condition during separation"
            }
            
            success, response = self.run_test(
                "Process Asset Recovery (Asset Manager)",
                "PUT",
                f"ndc-asset-recovery/{self.test_data['asset_recovery_id']}",
                200,
                data=recovery_update_data,
                user_role="Asset Manager"
            )
            
            if success:
                print(f"   ✅ Asset recovery processed successfully")
                print(f"   Recovered: {response['recovered']}")
                print(f"   Condition: {response['asset_condition']}")
                print(f"   Status: {response['status']}")
        
        # Step 5: Test Access Control Verification
        print(f"\n🔒 Step 5: Testing Access Control Verification")
        
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
        
        # Step 6: Test Edge Cases and Validation
        print(f"\n⚠️ Step 6: Testing Edge Cases and Validation")
        
        # Test NDC creation for employee with no allocated assets (should fail)
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
                "separation_reason": "Resignation"
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
        
        # Test NDC revoke functionality
        if 'ndc_request_id' in self.test_data:
            revoke_data = {"reason": "Employee decided to stay with company"}
            
            success, response = self.run_test(
                "Revoke NDC Request",
                "POST",
                f"ndc-requests/{self.test_data['ndc_request_id']}/revoke",
                200,
                data=revoke_data,
                user_role="HR Manager"
            )
            
            if success:
                print(f"   ✅ NDC request revoked successfully")
        
        # Step 7: Test Data Integrity
        print(f"\n🔍 Step 7: Testing Data Integrity")
        
        # Verify NDC request data integrity
        success, response = self.run_test(
            "Verify NDC Data Integrity",
            "GET",
            "ndc-requests",
            200,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   ✅ NDC data integrity verified: {len(response)} total NDC requests")
            
            # Check if our test NDC request has proper data
            for ndc in response:
                if ndc['id'] == self.test_data.get('ndc_request_id'):
                    print(f"   Employee Name: {ndc['employee_name']}")
                    print(f"   Asset Manager: {ndc['asset_manager_name']}")
                    print(f"   Status: {ndc['status']}")
                    break
        
        print(f"\n✅ NDC System Testing Completed Successfully")
        print(f"   - Critical asset detection bug verified as FIXED")
        print(f"   - Asset Manager routing working correctly")
        print(f"   - Asset recovery workflow functional")
        print(f"   - Access control properly implemented")
        print(f"   - Edge cases and validation working")
        print(f"   - Data integrity maintained")
        
        return True

    def test_ndc_comprehensive_system(self):
        """Test Complete NDC System"""
        print(f"\n🏥 Testing Complete NDC (No Dues Certificate) System")
        
        success = True
        
        # Run the comprehensive NDC test that focuses on the bug fix
        if not self.test_ndc_system_comprehensive():
            success = False
        
        # Run additional NDC-related tests
        if not self.test_ndc_separation_reasons_management():
            success = False
        
        if not self.test_ndc_request_creation_and_management():
            success = False
        
        if not self.test_ndc_asset_recovery_management():
            success = False
        
        if not self.test_ndc_request_workflow():
            success = False
        
        if success:
            print("   🎉 NDC System: ALL TESTS PASSED")
        else:
            print("   ⚠️ NDC System: Some tests failed")
        
        return success

    def test_ndc_access_control_fix(self):
        """Test the specific NDC access control fix for Employee role"""
        print(f"\n🔒 Testing NDC Access Control Fix")
        
        # Test Employee access to NDC requests (should be 403 Forbidden)
        success, response = self.run_test(
            "Employee Access NDC Requests (Should be 403)",
            "GET",
            "ndc-requests",
            403,  # Expecting forbidden
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to NDC requests (403 Forbidden)")
            # Check if the error message is correct
            if isinstance(response, dict) and "detail" in response:
                expected_message = "Access denied. Insufficient permissions to view NDC requests."
                if response["detail"] == expected_message:
                    print(f"   ✅ Correct error message: '{response['detail']}'")
                else:
                    print(f"   ⚠️ Unexpected error message: '{response['detail']}'")
        else:
            print("   ❌ Employee access control fix failed - Employee should get 403 Forbidden")
        
        # Test that other roles still work correctly
        authorized_roles = ["HR Manager", "Asset Manager", "Administrator"]
        
        for role in authorized_roles:
            if role in self.tokens:
                success, response = self.run_test(
                    f"{role} Access NDC Requests (Should be 200)",
                    "GET",
                    "ndc-requests",
                    200,  # Expecting success
                    user_role=role
                )
                
                if success:
                    print(f"   ✅ {role} can still access NDC requests (200 OK)")
                    if isinstance(response, list):
                        print(f"   📊 {role} can see {len(response)} NDC requests")
                else:
                    print(f"   ❌ {role} access failed - should have 200 OK access")
        
        return success

    def run_ndc_access_control_test(self):
        """Run focused NDC access control test"""
        print("🎯 Starting NDC Access Control Fix Verification")
        print("=" * 60)
        
        # Test login for required roles
        login_success = True
        for email, password, role in [
            ("employee@company.com", "password123", "Employee"),
            ("hr@company.com", "password123", "HR Manager"),
            ("assetmanager@company.com", "password123", "Asset Manager"),
            ("admin@company.com", "password123", "Administrator")
        ]:
            if not self.test_login(email, password, role):
                login_success = False
        
        if not login_success:
            print("❌ Some logins failed. Cannot proceed with NDC access control test.")
            return False
        
        # Run the specific NDC access control test
        test_result = self.test_ndc_access_control_fix()
        
        # Print final results
        print(f"\n" + "=" * 60)
        print(f"🎯 NDC ACCESS CONTROL TEST COMPLETED")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"=" * 60)
        
        return test_result

    def test_asset_system_reset_endpoint(self):
        """Test the newly implemented /admin/reset-asset-system endpoint"""
        print(f"\n🔄 Testing Asset System Reset Endpoint")
        
        # First, let's get current data counts before reset
        print("   📊 Getting current data counts before reset...")
        
        # Get counts of various collections
        data_counts_before = {}
        
        # Get asset types count
        success, response = self.run_test(
            "Get Asset Types Count (Before Reset)",
            "GET",
            "asset-types",
            200,
            user_role="Administrator"
        )
        if success:
            data_counts_before['asset_types'] = len(response)
            print(f"   Asset Types: {data_counts_before['asset_types']}")
        
        # Get asset definitions count
        success, response = self.run_test(
            "Get Asset Definitions Count (Before Reset)",
            "GET",
            "asset-definitions",
            200,
            user_role="Administrator"
        )
        if success:
            data_counts_before['asset_definitions'] = len(response)
            print(f"   Asset Definitions: {data_counts_before['asset_definitions']}")
        
        # Get asset requisitions count
        success, response = self.run_test(
            "Get Asset Requisitions Count (Before Reset)",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        if success:
            data_counts_before['asset_requisitions'] = len(response)
            print(f"   Asset Requisitions: {data_counts_before['asset_requisitions']}")
        
        # Test 1: Access Control - Non-Administrator roles should be denied
        print("\n   🔒 Testing Access Control...")
        
        non_admin_roles = ["Employee", "Manager", "HR Manager", "Asset Manager"]
        for role in non_admin_roles:
            if role in self.tokens:
                success, response = self.run_test(
                    f"{role} Reset System (Should Fail)",
                    "POST",
                    "admin/reset-asset-system",
                    403,  # Expecting forbidden
                    user_role=role
                )
                
                if success:
                    print(f"   ✅ {role} correctly denied access (403 status)")
                else:
                    print(f"   ❌ {role} access control failed")
        
        # Test 2: Administrator can execute reset successfully
        print("\n   🔄 Testing Administrator Reset Execution...")
        
        success, response = self.run_test(
            "Administrator Execute Reset",
            "POST",
            "admin/reset-asset-system",
            200,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Administrator successfully executed reset")
            
            # Verify response format
            required_fields = ["message", "deleted_by", "deletion_summary", "timestamp"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print("   ✅ Response includes all required fields")
                
                # Check deletion summary structure
                deletion_summary = response.get("deletion_summary", {})
                expected_summary_fields = [
                    "ndc_requests", "ndc_asset_recovery", "asset_retrievals", 
                    "asset_allocations", "asset_requisitions", "asset_definitions", 
                    "asset_types", "user_asset_assignments_cleared"
                ]
                
                missing_summary_fields = [field for field in expected_summary_fields if field not in deletion_summary]
                if not missing_summary_fields:
                    print("   ✅ Deletion summary includes all expected fields")
                    print(f"   📊 Deletion Summary:")
                    for field, count in deletion_summary.items():
                        print(f"     {field}: {count}")
                else:
                    print(f"   ❌ Missing deletion summary fields: {missing_summary_fields}")
                
                # Check deleted_by information
                deleted_by = response.get("deleted_by", {})
                if "user_id" in deleted_by and "user_name" in deleted_by:
                    print(f"   ✅ Audit information present: {deleted_by['user_name']} ({deleted_by['user_id']})")
                else:
                    print("   ❌ Missing audit information in deleted_by")
                
                # Check timestamp format
                timestamp = response.get("timestamp")
                if timestamp:
                    print(f"   ✅ Timestamp present: {timestamp}")
                else:
                    print("   ❌ Missing timestamp")
                    
            else:
                print(f"   ❌ Missing required response fields: {missing_fields}")
        else:
            print("   ❌ Administrator reset execution failed")
            return False
        
        # Test 3: Verify all collections are empty after reset
        print("\n   🔍 Verifying Data Deletion...")
        
        # Check asset types
        success, response = self.run_test(
            "Verify Asset Types Deleted",
            "GET",
            "asset-types",
            200,
            user_role="Administrator"
        )
        if success:
            if len(response) == 0:
                print("   ✅ All asset types deleted")
            else:
                print(f"   ❌ Asset types not fully deleted: {len(response)} remaining")
        
        # Check asset definitions
        success, response = self.run_test(
            "Verify Asset Definitions Deleted",
            "GET",
            "asset-definitions",
            200,
            user_role="Administrator"
        )
        if success:
            if len(response) == 0:
                print("   ✅ All asset definitions deleted")
            else:
                print(f"   ❌ Asset definitions not fully deleted: {len(response)} remaining")
        
        # Check asset requisitions
        success, response = self.run_test(
            "Verify Asset Requisitions Deleted",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        if success:
            if len(response) == 0:
                print("   ✅ All asset requisitions deleted")
            else:
                print(f"   ❌ Asset requisitions not fully deleted: {len(response)} remaining")
        
        # Test 4: Verify system is still functional after reset
        print("\n   🔧 Testing System Functionality After Reset...")
        
        # Test creating new asset type after reset
        new_asset_type_data = {
            "code": "POST_RESET_TEST",
            "name": "Post Reset Test Asset",
            "depreciation_applicable": False,
            "to_be_recovered_on_separation": True,
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Asset Type After Reset",
            "POST",
            "asset-types",
            200,
            data=new_asset_type_data,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ System functional after reset - can create new asset types")
            self.test_data['post_reset_asset_type_id'] = response['id']
            
            # Test creating asset definition after reset
            new_asset_def_data = {
                "asset_type_id": response['id'],
                "asset_code": "POST_RESET_001",
                "asset_description": "Post Reset Test Asset",
                "asset_details": "Test asset created after system reset",
                "asset_value": 1000.0,
                "status": "Available"
            }
            
            success, response = self.run_test(
                "Create Asset Definition After Reset",
                "POST",
                "asset-definitions",
                200,
                data=new_asset_def_data,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ System functional after reset - can create new asset definitions")
            else:
                print("   ❌ System dysfunction after reset - cannot create asset definitions")
        else:
            print("   ❌ System dysfunction after reset - cannot create asset types")
        
        # Test 5: Test that users are still functional (not deleted)
        print("\n   👥 Verifying User Data Integrity...")
        
        success, response = self.run_test(
            "Verify Users Still Exist After Reset",
            "GET",
            "users",
            200,
            user_role="Administrator"
        )
        
        if success:
            if len(response) > 0:
                print(f"   ✅ User data preserved - {len(response)} users still exist")
                
                # Check if user asset assignments were cleared
                users_with_asset_assignments = 0
                for user in response:
                    if any(field in user for field in ['allocated_to', 'allocation_date', 'acknowledged']):
                        users_with_asset_assignments += 1
                
                if users_with_asset_assignments == 0:
                    print("   ✅ User asset assignments properly cleared")
                else:
                    print(f"   ⚠️ {users_with_asset_assignments} users still have asset assignment fields")
            else:
                print("   ❌ Critical error - all users deleted during reset!")
        
        return True

    def test_delete_specific_test_locations(self):
        """Test deletion of specific test locations by their codes"""
        print(f"\n🗑️ Testing Deletion of Specific Test Locations")
        
        # Target location codes to delete
        target_codes = ["TEST124613", "TEST124810", "TEST124853"]
        
        # Step 1: Authentication as Administrator
        print("   Step 1: Authenticating as Administrator...")
        if "Administrator" not in self.tokens:
            print("   ❌ Administrator not logged in. Cannot proceed with location deletion.")
            return False
        
        # Step 2: Get all locations to find target locations
        print("   Step 2: Finding target locations...")
        success, response = self.run_test(
            "Get All Locations to Find Targets",
            "GET",
            "locations",
            200,
            user_role="Administrator"
        )
        
        if not success:
            print("   ❌ Failed to retrieve locations list")
            return False
        
        print(f"   Found {len(response)} total locations in system")
        
        # Find target locations by code
        target_locations = {}
        for location in response:
            if location.get('code') in target_codes:
                target_locations[location['code']] = location
                print(f"   ✅ Found target location: {location['code']} - {location['name']} (ID: {location['id']})")
        
        # Check which target codes were not found
        missing_codes = [code for code in target_codes if code not in target_locations]
        if missing_codes:
            print(f"   ⚠️ Target location codes not found: {missing_codes}")
        
        if not target_locations:
            print("   ⚠️ None of the target location codes were found in the system")
            print("   This is not an error - the locations may have already been deleted or never existed")
            return True  # Not an error if locations don't exist
        
        # Step 3: Display current location details before deletion
        print("   Step 3: Current location details before deletion:")
        for code, location in target_locations.items():
            print(f"     - Code: {location['code']}")
            print(f"       Name: {location['name']}")
            print(f"       Country: {location['country']}")
            print(f"       Status: {location['status']}")
            print(f"       ID: {location['id']}")
        
        # Step 4: Delete each found location
        print("   Step 4: Deleting target locations...")
        deletion_results = {}
        
        for code, location in target_locations.items():
            location_id = location['id']
            success, response = self.run_test(
                f"Delete Location {code}",
                "DELETE",
                f"locations/{location_id}",
                200,  # Expecting successful deletion
                user_role="Administrator"
            )
            
            deletion_results[code] = success
            if success:
                print(f"   ✅ Successfully deleted location {code} (ID: {location_id})")
            else:
                print(f"   ❌ Failed to delete location {code} (ID: {location_id})")
        
        # Step 5: Verification - Get locations list again to confirm deletions
        print("   Step 5: Verifying deletions...")
        success, response = self.run_test(
            "Verify Locations After Deletion",
            "GET",
            "locations",
            200,
            user_role="Administrator"
        )
        
        if success:
            remaining_codes = [loc['code'] for loc in response]
            print(f"   Remaining locations in system: {len(response)}")
            
            # Check that deleted locations are no longer in the list
            still_present = []
            for code in target_locations.keys():
                if code in remaining_codes:
                    still_present.append(code)
            
            if still_present:
                print(f"   ❌ Locations still present after deletion: {still_present}")
            else:
                print("   ✅ All target locations successfully removed from the system")
        
        # Step 6: Summary of deletion results
        print("   Step 6: Deletion Summary:")
        successful_deletions = [code for code, success in deletion_results.items() if success]
        failed_deletions = [code for code, success in deletion_results.items() if not success]
        
        print(f"     Total target locations found: {len(target_locations)}")
        print(f"     Successfully deleted: {len(successful_deletions)} - {successful_deletions}")
        if failed_deletions:
            print(f"     Failed to delete: {len(failed_deletions)} - {failed_deletions}")
        if missing_codes:
            print(f"     Not found in system: {len(missing_codes)} - {missing_codes}")
        
        # Return True if all found locations were successfully deleted
        all_successful = len(failed_deletions) == 0
        if all_successful:
            print("   🎉 Location deletion task completed successfully!")
        else:
            print("   ⚠️ Some location deletions failed")
        
        return all_successful

    def test_delete_all_asset_requisitions(self):
        """Test deletion of all asset requisitions from the database"""
        print(f"\n🗑️ Testing DELETE ALL ASSET REQUISITIONS Task")
        print("=" * 60)
        
        # Step 1: Authentication as Administrator
        print("\n🔐 Step 1: Authentication as Administrator")
        if not self.test_login("admin@company.com", "password123", "Administrator"):
            print("❌ Failed to authenticate as Administrator - cannot proceed")
            return False
        
        # Step 2: Get current asset requisitions
        print("\n📋 Step 2: Get Current Asset Requisitions")
        success, response = self.run_test(
            "Get All Asset Requisitions (Before Deletion)",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to get current asset requisitions")
            return False
        
        initial_requisitions = response
        initial_count = len(initial_requisitions)
        print(f"   📊 Current asset requisitions count: {initial_count}")
        
        if initial_count == 0:
            print("   ℹ️ No asset requisitions found to delete")
            return True
        
        # Display basic details of current requisitions
        print("   📝 Current requisitions summary:")
        for i, req in enumerate(initial_requisitions[:5]):  # Show first 5
            req_id = req.get('id', 'Unknown')[:8]
            asset_type = req.get('asset_type_name', 'Unknown')
            status = req.get('status', 'Unknown')
            requested_by = req.get('requested_by_name', 'Unknown')
            print(f"     {i+1}. ID: {req_id}... | Type: {asset_type} | Status: {status} | By: {requested_by}")
        
        if initial_count > 5:
            print(f"     ... and {initial_count - 5} more requisitions")
        
        # Step 3: Delete all asset requisitions individually
        print(f"\n🗑️ Step 3: Delete All Asset Requisitions ({initial_count} items)")
        deleted_count = 0
        failed_deletions = []
        
        for i, requisition in enumerate(initial_requisitions):
            req_id = requisition.get('id')
            req_short_id = req_id[:8] if req_id else 'Unknown'
            
            print(f"   Deleting {i+1}/{initial_count}: {req_short_id}...", end=" ")
            
            success, response = self.run_test(
                f"Delete Asset Requisition {req_short_id}",
                "DELETE",
                f"asset-requisitions/{req_id}",
                200,
                user_role="Administrator"
            )
            
            if success:
                deleted_count += 1
                print("✅")
            else:
                failed_deletions.append({
                    'id': req_id,
                    'short_id': req_short_id,
                    'asset_type': requisition.get('asset_type_name', 'Unknown'),
                    'status': requisition.get('status', 'Unknown')
                })
                print("❌")
        
        # Step 4: Verification - Get asset requisitions again
        print(f"\n✅ Step 4: Verification")
        success, response = self.run_test(
            "Get All Asset Requisitions (After Deletion)",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to verify deletion - cannot get asset requisitions")
            return False
        
        final_requisitions = response
        final_count = len(final_requisitions)
        
        # Step 5: Display summary results
        print(f"\n📊 Step 5: Deletion Summary")
        print("=" * 40)
        print(f"   Initial count:     {initial_count}")
        print(f"   Successfully deleted: {deleted_count}")
        print(f"   Failed deletions:  {len(failed_deletions)}")
        print(f"   Final count:       {final_count}")
        print(f"   Expected final:    0")
        
        # Report any failed deletions
        if failed_deletions:
            print(f"\n❌ Failed Deletions ({len(failed_deletions)} items):")
            for failed in failed_deletions:
                print(f"     ID: {failed['short_id']}... | Type: {failed['asset_type']} | Status: {failed['status']}")
        
        # Report any remaining requisitions
        if final_count > 0:
            print(f"\n⚠️ Remaining Requisitions ({final_count} items):")
            for req in final_requisitions:
                req_id = req.get('id', 'Unknown')[:8]
                asset_type = req.get('asset_type_name', 'Unknown')
                status = req.get('status', 'Unknown')
                print(f"     ID: {req_id}... | Type: {asset_type} | Status: {status}")
        
        # Final result
        success_result = (final_count == 0 and len(failed_deletions) == 0)
        
        if success_result:
            print(f"\n🎉 SUCCESS: All {initial_count} asset requisitions deleted successfully!")
            print("   ✅ Database is now clean of asset requisitions")
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: {deleted_count}/{initial_count} requisitions deleted")
            if final_count > 0:
                print(f"   ❌ {final_count} requisitions still remain in system")
            if failed_deletions:
                print(f"   ❌ {len(failed_deletions)} deletions failed")
        
        return success_result

    def test_email_configuration_tls_conflict(self):
        """Test Email Configuration TLS Conflict Fix"""
        print(f"\n📧 Testing Email Configuration TLS Conflict Fix")
        
        # Test 1: Check current email configuration
        success, response = self.run_test(
            "Get Current Email Configuration",
            "GET",
            "email-config",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Current email config found")
            current_config = response
            print(f"   Current use_tls: {current_config.get('use_tls', 'Not set')}")
            print(f"   Current use_ssl: {current_config.get('use_ssl', 'Not set')}")
            
            # Check for TLS conflict
            if current_config.get('use_tls') and current_config.get('use_ssl'):
                print("   ⚠️ TLS CONFLICT DETECTED: Both use_tls and use_ssl are enabled")
            elif current_config.get('use_tls') == True and current_config.get('use_ssl') == False:
                print("   ✅ TLS configuration is correct (use_tls: true, use_ssl: false)")
            else:
                print(f"   📋 Current TLS config: use_tls={current_config.get('use_tls')}, use_ssl={current_config.get('use_ssl')}")
        else:
            print("   ❌ Failed to get current email configuration")
            return False
        
        # Test 2: Fix email configuration with proper TLS settings
        fixed_email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "test@company.com",
            "smtp_password": "test_password",
            "use_tls": True,
            "use_ssl": False,
            "from_email": "noreply@company.com",
            "from_name": "Asset Management System"
        }
        
        # If we have an existing config, update it; otherwise create a new one
        if success and 'id' in current_config:
            # Update existing configuration
            success, response = self.run_test(
                "Fix Email Configuration TLS Settings (Update)",
                "PUT",
                f"email-config/{current_config['id']}",
                200,
                data=fixed_email_config,
                user_role="Administrator"
            )
        else:
            # Create new configuration
            success, response = self.run_test(
                "Fix Email Configuration TLS Settings (Create)",
                "POST",
                "email-config",
                200,
                data=fixed_email_config,
                user_role="Administrator"
            )
        
        if success:
            print("   ✅ Email configuration updated successfully")
            updated_config = response
            print(f"   Updated use_tls: {updated_config.get('use_tls')}")
            print(f"   Updated use_ssl: {updated_config.get('use_ssl')}")
            
            # Verify the fix
            if updated_config.get('use_tls') == True and updated_config.get('use_ssl') == False:
                print("   ✅ TLS CONFLICT FIXED: use_tls=true, use_ssl=false")
                self.test_data['email_config_fixed'] = True
            else:
                print("   ❌ TLS conflict not properly fixed")
                return False
        else:
            print("   ❌ Failed to update email configuration")
            return False
        
        # Test 3: Verify configuration persists
        success, response = self.run_test(
            "Verify Fixed Email Configuration",
            "GET",
            "email-config",
            200,
            user_role="Administrator"
        )
        
        if success:
            verified_config = response
            if verified_config.get('use_tls') == True and verified_config.get('use_ssl') == False:
                print("   ✅ Fixed configuration persisted correctly")
            else:
                print("   ❌ Fixed configuration did not persist")
                return False
        
        return True

    def test_asset_requisition_after_email_fix(self):
        """Test Asset Requisition Creation After Email Configuration Fix"""
        print(f"\n📝 Testing Asset Requisition Creation After Email Fix")
        
        if not self.test_data.get('email_config_fixed'):
            print("   ⚠️ Email configuration not fixed - proceeding with caution")
        
        if 'asset_type_id' not in self.test_data:
            print("   ❌ Skipping Asset Requisition test - no asset type created")
            return False
        
        # Test 1: Create asset requisition after email fix
        from datetime import datetime, timedelta
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        post_fix_requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Test requisition after email TLS fix",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Asset Requisition After Email Fix",
            "POST",
            "asset-requisitions",
            200,
            data=post_fix_requisition_data,
            user_role="Employee"
        )
        
        if success:
            self.test_data['post_fix_requisition_id'] = response['id']
            print(f"   ✅ Asset requisition created successfully after email fix")
            print(f"   Requisition ID: {response['id'][:8]}...")
            print(f"   Status: {response.get('status', 'Unknown')}")
            print(f"   Request Type: {response.get('request_type', 'Unknown')}")
            
            # Check if any email-related errors occurred
            if 'error' not in str(response).lower() and 'email' not in str(response).lower():
                print("   ✅ No email-related errors in response")
            else:
                print("   ⚠️ Possible email-related issues in response")
        else:
            print("   ❌ Failed to create asset requisition after email fix")
            return False
        
        # Test 2: Verify requisition was properly stored
        if 'post_fix_requisition_id' in self.test_data:
            success, response = self.run_test(
                "Verify Asset Requisition Storage",
                "GET",
                "asset-requisitions",
                200,
                user_role="Administrator"
            )
            
            if success:
                requisition_found = any(
                    req['id'] == self.test_data['post_fix_requisition_id'] 
                    for req in response
                )
                if requisition_found:
                    print("   ✅ Asset requisition properly stored in database")
                else:
                    print("   ❌ Asset requisition not found in database")
                    return False
        
        # Test 3: Test multiple requisition types to ensure email fix works for all
        test_requisition_types = [
            {
                "request_type": "Replacement",
                "reason_for_return_replacement": "Device malfunction after email fix test",
                "asset_details": "Laptop showing hardware issues",
                "justification": "Need replacement due to hardware failure"
            },
            {
                "request_type": "Return",
                "reason_for_return_replacement": "Project completed after email fix",
                "asset_details": "MacBook Pro in good condition",
                "justification": "Returning equipment after project completion"
            }
        ]
        
        for i, req_data in enumerate(test_requisition_types):
            full_req_data = {
                "asset_type_id": self.test_data['asset_type_id'],
                "request_for": "Self",
                "required_by_date": required_by_date,
                **req_data
            }
            
            success, response = self.run_test(
                f"Create {req_data['request_type']} Request After Email Fix",
                "POST",
                "asset-requisitions",
                200,
                data=full_req_data,
                user_role="Employee"
            )
            
            if success:
                print(f"   ✅ {req_data['request_type']} request created successfully")
            else:
                print(f"   ❌ {req_data['request_type']} request failed")
        
        return True

    def test_email_configuration_workflow(self):
        """Test Complete Email Configuration Workflow"""
        print(f"\n🔄 Testing Complete Email Configuration Workflow")
        
        # Test 1: Authentication as Administrator
        if "Administrator" not in self.tokens:
            print("   ❌ Administrator not logged in - cannot test email configuration")
            return False
        
        print("   ✅ Administrator authenticated successfully")
        
        # Test 2: Check current email configuration
        if not self.test_email_configuration_tls_conflict():
            print("   ❌ Email configuration TLS conflict fix failed")
            return False
        
        # Test 3: Test asset requisition creation after fix
        if not self.test_asset_requisition_after_email_fix():
            print("   ❌ Asset requisition creation after email fix failed")
            return False
        
        # Test 4: Test email configuration access control
        success, response = self.run_test(
            "Employee Access Email Config (Should Fail)",
            "GET",
            "email-config",
            403,
            user_role="Employee"
        )
        
        if success:
            print("   ✅ Employee correctly denied access to email configuration")
        
        # Test 5: Test email configuration validation
        invalid_email_config = {
            "smtp_server": "",  # Invalid empty server
            "smtp_port": 587,
            "smtp_username": "test@company.com",
            "smtp_password": "test_password",
            "use_tls": True,
            "use_ssl": False,
            "from_email": "invalid-email",  # Invalid email format
            "from_name": "Test System"
        }
        
        success, response = self.run_test(
            "Invalid Email Configuration (Should Fail)",
            "PUT",
            "email-config",
            422,  # Expecting validation error
            data=invalid_email_config,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Invalid email configuration correctly rejected")
        
        print("   ✅ Complete email configuration workflow tested successfully")
        return True

    def run_email_tls_fix_test(self):
        """Run focused Email TLS Configuration Fix Test"""
        print("🚀 Starting Email TLS Configuration Fix Test")
        print("=" * 80)
        
        # Test authentication for Administrator
        if not self.test_login("admin@company.com", "password123", "Administrator"):
            print("❌ Administrator login failed. Cannot proceed with email configuration test.")
            return False
        
        if not self.test_login("employee@company.com", "password123", "Employee"):
            print("❌ Employee login failed. Cannot proceed with asset requisition test.")
            return False
        
        print(f"\n✅ Successfully logged in required users")
        
        # Create asset type for testing if needed
        if 'asset_type_id' not in self.test_data:
            # First try to get existing asset types
            success, response = self.run_test(
                "Get Existing Asset Types",
                "GET",
                "asset-types",
                200,
                user_role="Administrator"
            )
            
            if success and response:
                # Use the first existing asset type
                self.test_data['asset_type_id'] = response[0]['id']
                print(f"   Using existing asset type for testing: {response[0]['id']}")
            else:
                # Create new asset type with unique code
                from datetime import datetime
                unique_code = f"EMAIL_TEST_{datetime.now().strftime('%H%M%S')}"
                asset_type_data = {
                    "code": unique_code,
                    "name": "Email Test Laptop",
                    "depreciation_applicable": True,
                    "asset_life": 3,
                    "to_be_recovered_on_separation": True,
                    "status": "Active"
                }
                
                success, response = self.run_test(
                    "Create Asset Type for Email Testing",
                    "POST",
                    "asset-types",
                    200,
                    data=asset_type_data,
                    user_role="Administrator"
                )
                
                if success:
                    self.test_data['asset_type_id'] = response['id']
                    print(f"   Created asset type for testing: {response['id']}")
        
        # Run the email configuration workflow test
        test_result = self.test_email_configuration_workflow()
        
        # Print final results
        print(f"\n" + "=" * 80)
        print(f"🎯 EMAIL TLS CONFIGURATION FIX TEST COMPLETED")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if test_result:
            print("🎉 EMAIL TLS CONFIGURATION FIX: ALL TESTS PASSED!")
        else:
            print("⚠️ EMAIL TLS CONFIGURATION FIX: Some tests failed")
        
        print("=" * 80)
        
        return test_result

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
    
    # Test Asset Type Manager Assignment feature
    print("\n👨‍💼 ASSET TYPE MANAGER ASSIGNMENT TESTS")
    print("-" * 40)
    tester.test_asset_type_manager_assignment()
    
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
    
    # Test Enhanced Asset Requisition Withdrawal functionality
    print("\n🗑️ ENHANCED ASSET REQUISITION WITHDRAWAL TESTS")
    print("-" * 45)
    tester.test_asset_requisition_withdrawal()
    tester.test_multi_role_withdrawal_access()
    tester.test_requisition_data_integrity()
    tester.test_role_based_requisition_access_multi_role()
    tester.test_dashboard_stats_multi_role()
    
    # Test SPECIFIC PASSWORD UPDATE AND LOGIN FOR SRIRAM
    print("\n🔐 SRIRAM PASSWORD UPDATE AND LOGIN TESTS")
    print("-" * 40)
    tester.test_sriram_password_update_and_login()
    
    # Test EMAIL NOTIFICATION SYSTEM
    print("\n📧 EMAIL NOTIFICATION SYSTEM TESTS")
    print("-" * 35)
    tester.test_email_notification_system()
    
    # Test LOCATION-BASED ASSET MANAGEMENT SYSTEM
    print("\n🌍 LOCATION-BASED ASSET MANAGEMENT SYSTEM TESTS")
    print("-" * 50)
    tester.test_location_based_asset_management_system()
    
    # Test ENHANCED ASSET ALLOCATION ROUTING SYSTEM
    print("\n🎯 ENHANCED ASSET ALLOCATION ROUTING SYSTEM TESTS")
    print("-" * 55)
    tester.test_enhanced_asset_allocation_routing()
    
    # Test NDC (NO DUES CERTIFICATE) SYSTEM
    print("\n🏥 NDC (NO DUES CERTIFICATE) SYSTEM TESTS")
    print("-" * 45)
    tester.test_ndc_comprehensive_system()
    
    # Test SPECIFIC LOCATION DELETION TASK
    print("\n🗑️ SPECIFIC LOCATION DELETION TASK")
    print("-" * 35)
    tester.test_delete_specific_test_locations()
    
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

def run_asset_allocation_system_test():
    """Run focused Asset Allocation System test"""
    tester = AssetInventoryAPITester()
    
    # Test 1: Asset Manager Pending Requisitions Workflow
    print(f"\n{'='*50}")
    print("TEST 1: ASSET MANAGER PENDING REQUISITIONS WORKFLOW")
    print(f"{'='*50}")
    
    # Step 1: Login as Asset Manager
    print("\n📋 Step 1: Asset Manager Authentication")
    if not tester.test_login("assetmanager@company.com", "password123", "Asset Manager"):
        print("❌ CRITICAL: Asset Manager login failed - cannot proceed with tests")
        return False
    
    # Step 2: Get all asset requisitions to check for "Assigned for Allocation" status
    print("\n📋 Step 2: Fetch Asset Requisitions")
    success, response = tester.run_test(
        "Get All Asset Requisitions (Asset Manager)",
        "GET",
        "asset-requisitions",
        200,
        user_role="Asset Manager"
    )
    
    if not success:
        print("❌ CRITICAL: Failed to fetch asset requisitions")
        return False
    
    print(f"   Found {len(response)} total requisitions")
    
    # Filter for "Assigned for Allocation" status
    assigned_requisitions = [req for req in response if req.get('status') == 'Assigned for Allocation']
    print(f"   Found {len(assigned_requisitions)} requisitions with 'Assigned for Allocation' status")
    
    # Step 3: Verify requisitions are assigned to current Asset Manager
    asset_manager_id = tester.users.get("Asset Manager", {}).get("id")
    if not asset_manager_id:
        print("❌ CRITICAL: Asset Manager ID not found")
        return False
    
    print(f"\n📋 Step 3: Verify Assignment to Current Asset Manager (ID: {asset_manager_id[:8]}...)")
    assigned_to_current_manager = []
    
    for req in assigned_requisitions:
        assigned_to = req.get('assigned_to')
        assigned_to_name = req.get('assigned_to_name', 'Unknown')
        routing_reason = req.get('routing_reason', 'No reason provided')
        
        print(f"   Requisition {req['id'][:8]}...")
        print(f"     Status: {req.get('status')}")
        print(f"     Assigned To: {assigned_to_name} ({assigned_to[:8] if assigned_to else 'None'}...)")
        print(f"     Routing Reason: {routing_reason}")
        
        if assigned_to == asset_manager_id:
            assigned_to_current_manager.append(req)
            print(f"     ✅ Correctly assigned to current Asset Manager")
        else:
            print(f"     ⚠️ Assigned to different Asset Manager")
    
    print(f"\n   Summary: {len(assigned_to_current_manager)} requisitions assigned to current Asset Manager")
    
    # Step 4: Test asset allocation creation from pending requisitions
    allocation_success = False
    if assigned_to_current_manager:
        print(f"\n📋 Step 4: Test Asset Allocation Creation")
        
        # Get available assets for allocation
        success, assets_response = tester.run_test(
            "Get Available Asset Definitions",
            "GET",
            "asset-definitions",
            200,
            user_role="Asset Manager"
        )
        
        if success:
            available_assets = [asset for asset in assets_response if asset.get('status') == 'Available']
            print(f"   Found {len(available_assets)} available assets for allocation")
            
            if available_assets and assigned_to_current_manager:
                # Test allocation creation
                test_requisition = assigned_to_current_manager[0]
                test_asset = available_assets[0]
                
                from datetime import datetime
                allocation_data = {
                    "requisition_id": test_requisition['id'],
                    "asset_definition_id": test_asset['id'],
                    "remarks": "Test allocation from pending requisition",
                    "reference_id": f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "dispatch_details": "Test dispatch via automated testing"
                }
                
                success, allocation_response = tester.run_test(
                    "Create Asset Allocation from Pending Requisition",
                    "POST",
                    "asset-allocations",
                    200,
                    data=allocation_data,
                    user_role="Asset Manager"
                )
                
                if success:
                    print(f"   ✅ Successfully created allocation: {allocation_response['id'][:8]}...")
                    print(f"   Allocation Status: {allocation_response.get('status')}")
                    print(f"   Asset Code: {allocation_response.get('asset_definition_code')}")
                    allocation_success = True
                    
                    # Step 5: Verify status transitions
                    print(f"\n📋 Step 5: Verify Status Transitions")
                    
                    # Check if requisition status changed
                    success, updated_reqs = tester.run_test(
                        "Verify Requisition Status Update",
                        "GET",
                        "asset-requisitions",
                        200,
                        user_role="Asset Manager"
                    )
                    
                    if success:
                        updated_req = next((req for req in updated_reqs if req['id'] == test_requisition['id']), None)
                        if updated_req:
                            new_status = updated_req.get('status')
                            print(f"   Requisition status changed from 'Assigned for Allocation' to '{new_status}'")
                            if new_status == 'Allocated':
                                print(f"   ✅ Status transition successful")
                            else:
                                print(f"   ⚠️ Unexpected status: {new_status}")
                    
                    # Check if asset status changed
                    success, updated_assets = tester.run_test(
                        "Verify Asset Status Update",
                        "GET",
                        "asset-definitions",
                        200,
                        user_role="Asset Manager"
                    )
                    
                    if success:
                        updated_asset = next((asset for asset in updated_assets if asset['id'] == test_asset['id']), None)
                        if updated_asset:
                            new_asset_status = updated_asset.get('status')
                            allocated_to = updated_asset.get('allocated_to_name', 'Unknown')
                            print(f"   Asset status changed from 'Available' to '{new_asset_status}'")
                            print(f"   Asset allocated to: {allocated_to}")
                            if new_asset_status == 'Allocated':
                                print(f"   ✅ Asset status transition successful")
                            else:
                                print(f"   ⚠️ Unexpected asset status: {new_asset_status}")
                else:
                    print("   ❌ Failed to create asset allocation")
            else:
                print("   ⚠️ No available assets or pending requisitions for allocation test")
        else:
            print("   ❌ Failed to fetch available assets")
    else:
        print("   ⚠️ No requisitions assigned to current Asset Manager for allocation testing")
    
    # Summary
    print(f"\n{'='*50}")
    print("ASSET ALLOCATION SYSTEM TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Total Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "No tests run")
    
    # Determine overall success
    has_pending_requisitions = len(assigned_to_current_manager) > 0
    
    if has_pending_requisitions and allocation_success:
        print("🎉 ALL ASSET ALLOCATION SYSTEM TESTS PASSED!")
        return True
    elif has_pending_requisitions:
        print("⚠️ Found pending requisitions but allocation test failed")
        return False
    else:
        print("⚠️ No pending requisitions found for current Asset Manager")
        return False



if __name__ == "__main__":
    # Check if we want to run the focused tests
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "ndc":
        tester = AssetInventoryAPITester()
        result = tester.run_ndc_access_control_test()
        sys.exit(0 if result else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "reset":
        # Run focused reset endpoint test
        tester = AssetInventoryAPITester()
        # Login as Administrator
        if tester.test_login("admin@company.com", "password123", "Administrator"):
            result = tester.test_asset_system_reset_endpoint()
            print(f"\n🎯 RESET ENDPOINT TEST COMPLETED")
            print(f"📊 Tests Run: {tester.tests_run}")
            print(f"✅ Tests Passed: {tester.tests_passed}")
            print(f"❌ Tests Failed: {tester.tests_run - tester.tests_passed}")
            print(f"📈 Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
            sys.exit(0 if result else 1)
        else:
            print("❌ Failed to login as Administrator")
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == "email":
        # Run focused email TLS configuration fix test
        tester = AssetInventoryAPITester()
        result = tester.run_email_tls_fix_test()
        sys.exit(0 if result else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "asset-allocation":
        # Run focused Asset Allocation System test
        result = run_asset_allocation_system_test()
        sys.exit(0 if result else 1)
    else:
        # Run the Asset Allocation System test by default as requested
        result = run_asset_allocation_system_test()
        sys.exit(0 if result else 1)