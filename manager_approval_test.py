import requests
import sys
import json
from datetime import datetime, timedelta

class ManagerApprovalWorkflowTester:
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

    def setup_test_data(self):
        """Setup test data for manager approval workflow testing"""
        print(f"\n📋 Setting up test data for Manager Approval Workflow...")
        
        # Create asset type for testing
        asset_type_data = {
            "code": "MGRAPPROVAL",
            "name": "Manager Approval Test Asset",
            "depreciation_applicable": True,
            "asset_life": 3,
            "to_be_recovered_on_separation": True,
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Asset Type for Manager Approval Tests",
            "POST",
            "asset-types",
            200,
            data=asset_type_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_type_id'] = response['id']
            print(f"   Created asset type with ID: {response['id']}")
        else:
            print("❌ Failed to create asset type for testing")
            return False
        
        # Create test users with proper reporting structure
        # Create Manager User
        manager_data = {
            "email": f"testmanager_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Test Manager for Approval",
            "roles": ["Manager"],
            "designation": "Test Manager",
            "date_of_joining": "2023-01-15T00:00:00Z",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Test Manager User",
            "POST",
            "users",
            200,
            data=manager_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['test_manager_id'] = response['id']
            self.test_data['test_manager_email'] = manager_data['email']
            print(f"   Created test manager with ID: {response['id']}")
        else:
            print("❌ Failed to create test manager")
            return False
        
        # Create Employee User reporting to the test manager
        employee_data = {
            "email": f"testemp_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Test Employee for Approval",
            "roles": ["Employee"],
            "designation": "Test Employee",
            "date_of_joining": "2024-01-01T00:00:00Z",
            "reporting_manager_id": self.test_data['test_manager_id'],
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Test Employee User",
            "POST",
            "users",
            200,
            data=employee_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['test_employee_id'] = response['id']
            self.test_data['test_employee_email'] = employee_data['email']
            print(f"   Created test employee with ID: {response['id']}")
            print(f"   Employee reports to manager: {response.get('reporting_manager_name', 'Unknown')}")
        else:
            print("❌ Failed to create test employee")
            return False
        
        # Login as test employee to create requisitions
        if not self.test_login(self.test_data['test_employee_email'], "TestPassword123!", "TestEmployee"):
            print("❌ Failed to login as test employee")
            return False
        
        # Login as test manager for approval tests
        if not self.test_login(self.test_data['test_manager_email'], "TestPassword123!", "TestManager"):
            print("❌ Failed to login as test manager")
            return False
        
        return True

    def create_test_requisitions(self):
        """Create test requisitions for approval workflow testing"""
        print(f"\n📝 Creating test requisitions for approval workflow...")
        
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        # Create requisition 1: For manager approval testing
        requisition_data_1 = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Need laptop for manager approval workflow testing",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition 1 for Manager Approval",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data_1,
            user_role="TestEmployee"
        )
        
        if success:
            self.test_data['requisition_1_id'] = response['id']
            print(f"   Created requisition 1 ID: {response['id'][:8]}...")
            print(f"   Status: {response.get('status', 'Unknown')}")
        else:
            print("❌ Failed to create requisition 1")
            return False
        
        # Create requisition 2: For HR approval testing
        requisition_data_2 = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "Replacement",
            "reason_for_return_replacement": "Current laptop is damaged",
            "asset_details": "Dell Laptop, Serial: DL123456",
            "request_for": "Self",
            "justification": "Need replacement laptop for HR approval workflow testing",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition 2 for HR Approval",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data_2,
            user_role="TestEmployee"
        )
        
        if success:
            self.test_data['requisition_2_id'] = response['id']
            print(f"   Created requisition 2 ID: {response['id'][:8]}...")
        else:
            print("❌ Failed to create requisition 2")
            return False
        
        # Create requisition 3: For error handling testing
        requisition_data_3 = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Need laptop for error handling testing",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition 3 for Error Handling",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data_3,
            user_role="TestEmployee"
        )
        
        if success:
            self.test_data['requisition_3_id'] = response['id']
            print(f"   Created requisition 3 ID: {response['id'][:8]}...")
        
        return True

    def test_manager_action_endpoint(self):
        """Test POST /api/asset-requisitions/{id}/manager-action endpoint"""
        print(f"\n🎯 Testing Manager Action Endpoint")
        
        if 'requisition_1_id' not in self.test_data:
            print("❌ No requisition available for manager action testing")
            return False
        
        requisition_id = self.test_data['requisition_1_id']
        
        # Test 1: Manager Approve Action
        approve_data = {
            "action": "approve",
            "reason": "Request approved - employee needs laptop for project work"
        }
        
        success, response = self.run_test(
            "Manager Approve Action",
            "POST",
            f"asset-requisitions/{requisition_id}/manager-action",
            200,
            data=approve_data,
            user_role="TestManager"
        )
        
        if success:
            print(f"   ✅ Manager approval successful")
            print(f"   Message: {response.get('message', 'No message')}")
            requisition = response.get('requisition', {})
            print(f"   New Status: {requisition.get('status', 'Unknown')}")
            print(f"   Manager Action By: {requisition.get('manager_action_by_name', 'Unknown')}")
            print(f"   Approval Reason: {requisition.get('manager_approval_reason', 'No reason')}")
            print(f"   Approval Date: {requisition.get('manager_approval_date', 'No date')}")
        
        # Test 2: Manager Reject Action (create new requisition first)
        if 'requisition_2_id' in self.test_data:
            reject_data = {
                "action": "reject",
                "reason": "Request rejected - insufficient justification provided"
            }
            
            success, response = self.run_test(
                "Manager Reject Action",
                "POST",
                f"asset-requisitions/{self.test_data['requisition_2_id']}/manager-action",
                200,
                data=reject_data,
                user_role="TestManager"
            )
            
            if success:
                print(f"   ✅ Manager rejection successful")
                requisition = response.get('requisition', {})
                print(f"   New Status: {requisition.get('status', 'Unknown')}")
                print(f"   Rejection Reason: {requisition.get('manager_rejection_reason', 'No reason')}")
        
        # Test 3: Manager Hold Action (create new requisition first)
        if 'requisition_3_id' in self.test_data:
            hold_data = {
                "action": "hold",
                "reason": "Request on hold - need more information from employee"
            }
            
            success, response = self.run_test(
                "Manager Hold Action",
                "POST",
                f"asset-requisitions/{self.test_data['requisition_3_id']}/manager-action",
                200,
                data=hold_data,
                user_role="TestManager"
            )
            
            if success:
                print(f"   ✅ Manager hold successful")
                requisition = response.get('requisition', {})
                print(f"   New Status: {requisition.get('status', 'Unknown')}")
                print(f"   Hold Reason: {requisition.get('manager_hold_reason', 'No reason')}")
        
        # Test 4: Invalid Action
        invalid_data = {
            "action": "invalid_action",
            "reason": "This should fail"
        }
        
        success, response = self.run_test(
            "Manager Invalid Action (Should Fail)",
            "POST",
            f"asset-requisitions/{requisition_id}/manager-action",
            400,
            data=invalid_data,
            user_role="TestManager"
        )
        
        if success:
            print(f"   ✅ Invalid action correctly rejected")
        
        # Test 5: Missing Reason (Should Fail)
        no_reason_data = {
            "action": "approve"
            # Missing reason field
        }
        
        success, response = self.run_test(
            "Manager Action Without Reason (Should Fail)",
            "POST",
            f"asset-requisitions/{requisition_id}/manager-action",
            422,  # Validation error
            data=no_reason_data,
            user_role="TestManager"
        )
        
        if success:
            print(f"   ✅ Missing reason correctly rejected")
        
        return True

    def test_hr_action_endpoint(self):
        """Test POST /api/asset-requisitions/{id}/hr-action endpoint"""
        print(f"\n🏥 Testing HR Action Endpoint")
        
        if 'requisition_1_id' not in self.test_data:
            print("❌ No approved requisition available for HR action testing")
            return False
        
        # Use the manager-approved requisition for HR testing
        requisition_id = self.test_data['requisition_1_id']
        
        # Test 1: HR Approve Action on Manager-Approved Request
        hr_approve_data = {
            "action": "approve",
            "reason": "HR approved - all documentation complete"
        }
        
        success, response = self.run_test(
            "HR Approve Manager-Approved Request",
            "POST",
            f"asset-requisitions/{requisition_id}/hr-action",
            200,
            data=hr_approve_data,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   ✅ HR approval successful")
            requisition = response.get('requisition', {})
            print(f"   New Status: {requisition.get('status', 'Unknown')}")
            print(f"   HR Action By: {requisition.get('hr_action_by_name', 'Unknown')}")
            print(f"   HR Approval Reason: {requisition.get('hr_approval_reason', 'No reason')}")
            print(f"   HR Approval Date: {requisition.get('hr_approval_date', 'No date')}")
        
        # Test 2: HR Reject Action on On-Hold Request
        if 'requisition_3_id' in self.test_data:
            hr_reject_data = {
                "action": "reject",
                "reason": "HR rejected - policy violation detected"
            }
            
            success, response = self.run_test(
                "HR Reject On-Hold Request",
                "POST",
                f"asset-requisitions/{self.test_data['requisition_3_id']}/hr-action",
                200,
                data=hr_reject_data,
                user_role="HR Manager"
            )
            
            if success:
                print(f"   ✅ HR rejection successful")
                requisition = response.get('requisition', {})
                print(f"   New Status: {requisition.get('status', 'Unknown')}")
                print(f"   HR Rejection Reason: {requisition.get('hr_rejection_reason', 'No reason')}")
        
        # Test 3: HR Action on Pending Request (Should Fail)
        # Create a new pending requisition
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        pending_req_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Test requisition for HR pending test",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Pending Requisition for HR Test",
            "POST",
            "asset-requisitions",
            200,
            data=pending_req_data,
            user_role="TestEmployee"
        )
        
        if success:
            pending_req_id = response['id']
            
            hr_invalid_data = {
                "action": "approve",
                "reason": "This should fail - requisition is still pending"
            }
            
            success, response = self.run_test(
                "HR Action on Pending Request (Should Fail)",
                "POST",
                f"asset-requisitions/{pending_req_id}/hr-action",
                400,
                data=hr_invalid_data,
                user_role="HR Manager"
            )
            
            if success:
                print(f"   ✅ HR action on pending request correctly rejected")
        
        # Test 4: Invalid HR Action
        invalid_hr_data = {
            "action": "invalid_hr_action",
            "reason": "This should fail"
        }
        
        success, response = self.run_test(
            "HR Invalid Action (Should Fail)",
            "POST",
            f"asset-requisitions/{requisition_id}/hr-action",
            400,
            data=invalid_hr_data,
            user_role="HR Manager"
        )
        
        if success:
            print(f"   ✅ Invalid HR action correctly rejected")
        
        return True

    def test_role_based_access_control(self):
        """Test role-based access control for manager and HR actions"""
        print(f"\n🔒 Testing Role-Based Access Control")
        
        if 'requisition_1_id' not in self.test_data:
            print("❌ No requisition available for access control testing")
            return False
        
        requisition_id = self.test_data['requisition_1_id']
        
        # Test 1: Employee trying to access manager-action (Should Fail)
        employee_action_data = {
            "action": "approve",
            "reason": "Employee should not be able to do this"
        }
        
        success, response = self.run_test(
            "Employee Access Manager Action (Should Fail)",
            "POST",
            f"asset-requisitions/{requisition_id}/manager-action",
            403,
            data=employee_action_data,
            user_role="Employee"
        )
        
        if success:
            print(f"   ✅ Employee correctly denied access to manager-action")
        
        # Test 2: Employee trying to access hr-action (Should Fail)
        success, response = self.run_test(
            "Employee Access HR Action (Should Fail)",
            "POST",
            f"asset-requisitions/{requisition_id}/hr-action",
            403,
            data=employee_action_data,
            user_role="Employee"
        )
        
        if success:
            print(f"   ✅ Employee correctly denied access to hr-action")
        
        # Test 3: Manager trying to access hr-action (Should Fail)
        manager_hr_data = {
            "action": "approve",
            "reason": "Manager should not be able to do HR actions"
        }
        
        success, response = self.run_test(
            "Manager Access HR Action (Should Fail)",
            "POST",
            f"asset-requisitions/{requisition_id}/hr-action",
            403,
            data=manager_hr_data,
            user_role="Manager"
        )
        
        if success:
            print(f"   ✅ Manager correctly denied access to hr-action")
        
        # Test 4: Administrator can access manager-action
        admin_manager_data = {
            "action": "approve",
            "reason": "Administrator should be able to do manager actions"
        }
        
        # Create new requisition for admin test
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        admin_req_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Test requisition for admin manager action",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition for Admin Manager Test",
            "POST",
            "asset-requisitions",
            200,
            data=admin_req_data,
            user_role="TestEmployee"
        )
        
        if success:
            admin_req_id = response['id']
            
            success, response = self.run_test(
                "Administrator Access Manager Action",
                "POST",
                f"asset-requisitions/{admin_req_id}/manager-action",
                200,
                data=admin_manager_data,
                user_role="Administrator"
            )
            
            if success:
                print(f"   ✅ Administrator can access manager-action")
        
        # Test 5: Administrator can access hr-action
        admin_hr_data = {
            "action": "approve",
            "reason": "Administrator should be able to do HR actions"
        }
        
        success, response = self.run_test(
            "Administrator Access HR Action",
            "POST",
            f"asset-requisitions/{admin_req_id}/hr-action",
            200,
            data=admin_hr_data,
            user_role="Administrator"
        )
        
        if success:
            print(f"   ✅ Administrator can access hr-action")
        
        return True

    def test_direct_reports_validation(self):
        """Test that managers can only act on direct reports' requests"""
        print(f"\n👥 Testing Direct Reports Validation")
        
        # Create another manager and employee (not reporting to test manager)
        other_manager_data = {
            "email": f"othermanager_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Other Manager",
            "roles": ["Manager"],
            "designation": "Other Manager",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Other Manager User",
            "POST",
            "users",
            200,
            data=other_manager_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to create other manager")
            return False
        
        other_manager_id = response['id']
        
        # Create employee reporting to other manager
        other_employee_data = {
            "email": f"otheremployee_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Other Employee",
            "roles": ["Employee"],
            "designation": "Other Employee",
            "reporting_manager_id": other_manager_id,
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Other Employee User",
            "POST",
            "users",
            200,
            data=other_employee_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to create other employee")
            return False
        
        other_employee_email = other_employee_data['email']
        
        # Login as other employee
        if not self.test_login(other_employee_email, "TestPassword123!", "OtherEmployee"):
            print("❌ Failed to login as other employee")
            return False
        
        # Create requisition by other employee
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        other_req_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Test requisition by other employee",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition by Other Employee",
            "POST",
            "asset-requisitions",
            200,
            data=other_req_data,
            user_role="OtherEmployee"
        )
        
        if not success:
            print("❌ Failed to create requisition by other employee")
            return False
        
        other_req_id = response['id']
        print(f"   Created requisition by other employee: {other_req_id[:8]}...")
        
        # Test: Test manager tries to act on other employee's request (Should Fail)
        unauthorized_action_data = {
            "action": "approve",
            "reason": "This should fail - not my direct report"
        }
        
        success, response = self.run_test(
            "Manager Act on Non-Direct Report Request (Should Fail)",
            "POST",
            f"asset-requisitions/{other_req_id}/manager-action",
            403,
            data=unauthorized_action_data,
            user_role="TestManager"
        )
        
        if success:
            print(f"   ✅ Manager correctly denied access to non-direct report's request")
        
        # Test: Administrator can act on any request
        admin_action_data = {
            "action": "approve",
            "reason": "Administrator can act on any request"
        }
        
        success, response = self.run_test(
            "Administrator Act on Any Request",
            "POST",
            f"asset-requisitions/{other_req_id}/manager-action",
            200,
            data=admin_action_data,
            user_role="Administrator"
        )
        
        if success:
            print(f"   ✅ Administrator can act on any request (role hierarchy working)")
        
        return True

    def test_enhanced_requisition_model(self):
        """Test enhanced AssetRequisition model fields"""
        print(f"\n📋 Testing Enhanced AssetRequisition Model Fields")
        
        if 'requisition_1_id' not in self.test_data:
            print("❌ No requisition available for model testing")
            return False
        
        # Get requisition details to verify enhanced fields
        success, response = self.run_test(
            "Get Requisition Details",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to get requisition details")
            return False
        
        # Find our test requisition
        test_requisition = None
        for req in response:
            if req['id'] == self.test_data['requisition_1_id']:
                test_requisition = req
                break
        
        if not test_requisition:
            print("❌ Test requisition not found")
            return False
        
        print(f"   Found test requisition: {test_requisition['id'][:8]}...")
        
        # Check manager approval fields
        manager_fields = [
            'manager_approval_date', 'manager_approval_reason', 'manager_rejection_reason',
            'manager_hold_reason', 'manager_action_by', 'manager_action_by_name'
        ]
        
        present_manager_fields = [field for field in manager_fields if field in test_requisition]
        print(f"   Manager approval fields present: {present_manager_fields}")
        
        # Check HR approval fields
        hr_fields = [
            'hr_approval_date', 'hr_approval_reason', 'hr_rejection_reason',
            'hr_hold_reason', 'hr_action_by', 'hr_action_by_name'
        ]
        
        present_hr_fields = [field for field in hr_fields if field in test_requisition]
        print(f"   HR approval fields present: {present_hr_fields}")
        
        # Verify field values for approved requisition
        if test_requisition.get('status') == 'HR Approved':
            print(f"   ✅ Requisition status: {test_requisition['status']}")
            print(f"   Manager approved by: {test_requisition.get('manager_action_by_name', 'Not set')}")
            print(f"   Manager approval reason: {test_requisition.get('manager_approval_reason', 'Not set')}")
            print(f"   HR approved by: {test_requisition.get('hr_action_by_name', 'Not set')}")
            print(f"   HR approval reason: {test_requisition.get('hr_approval_reason', 'Not set')}")
            
            # Check timestamp fields
            if test_requisition.get('manager_approval_date'):
                print(f"   Manager approval date: {test_requisition['manager_approval_date']}")
            if test_requisition.get('hr_approval_date'):
                print(f"   HR approval date: {test_requisition['hr_approval_date']}")
        
        return True

    def test_error_handling_and_validation(self):
        """Test error handling and validation scenarios"""
        print(f"\n⚠️ Testing Error Handling and Validation")
        
        # Test 1: Acting on non-existent requisition
        non_existent_action = {
            "action": "approve",
            "reason": "This should fail - requisition doesn't exist"
        }
        
        success, response = self.run_test(
            "Act on Non-existent Requisition (Should Fail)",
            "POST",
            "asset-requisitions/non-existent-id/manager-action",
            404,
            data=non_existent_action,
            user_role="TestManager"
        )
        
        if success:
            print(f"   ✅ Non-existent requisition correctly returns 404")
        
        # Test 2: Acting on already processed requisition
        if 'requisition_1_id' in self.test_data:
            # This requisition should already be HR approved
            processed_action = {
                "action": "approve",
                "reason": "This should fail - already processed"
            }
            
            success, response = self.run_test(
                "Manager Act on Processed Requisition (Should Fail)",
                "POST",
                f"asset-requisitions/{self.test_data['requisition_1_id']}/manager-action",
                400,
                data=processed_action,
                user_role="TestManager"
            )
            
            if success:
                print(f"   ✅ Acting on processed requisition correctly rejected")
        
        # Test 3: Empty action field
        empty_action = {
            "action": "",
            "reason": "Empty action should fail"
        }
        
        success, response = self.run_test(
            "Empty Action Field (Should Fail)",
            "POST",
            f"asset-requisitions/{self.test_data.get('requisition_2_id', 'test')}/manager-action",
            400,
            data=empty_action,
            user_role="TestManager"
        )
        
        if success:
            print(f"   ✅ Empty action field correctly rejected")
        
        # Test 4: Empty reason field
        empty_reason = {
            "action": "approve",
            "reason": ""
        }
        
        success, response = self.run_test(
            "Empty Reason Field (Should Fail)",
            "POST",
            f"asset-requisitions/{self.test_data.get('requisition_2_id', 'test')}/manager-action",
            422,
            data=empty_reason,
            user_role="TestManager"
        )
        
        if success:
            print(f"   ✅ Empty reason field correctly rejected")
        
        return True

    def test_data_integrity_and_timestamps(self):
        """Test data integrity and timestamp accuracy"""
        print(f"\n🕐 Testing Data Integrity and Timestamps")
        
        # Create a new requisition for timestamp testing
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        timestamp_req_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Test requisition for timestamp verification",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Requisition for Timestamp Test",
            "POST",
            "asset-requisitions",
            200,
            data=timestamp_req_data,
            user_role="TestEmployee"
        )
        
        if not success:
            print("❌ Failed to create requisition for timestamp test")
            return False
        
        timestamp_req_id = response['id']
        creation_time = datetime.now()
        
        # Manager approval with timestamp verification
        approve_data = {
            "action": "approve",
            "reason": "Approved for timestamp testing"
        }
        
        success, response = self.run_test(
            "Manager Approve for Timestamp Test",
            "POST",
            f"asset-requisitions/{timestamp_req_id}/manager-action",
            200,
            data=approve_data,
            user_role="TestManager"
        )
        
        if success:
            manager_approval_time = datetime.now()
            requisition = response.get('requisition', {})
            
            # Verify manager approval timestamp
            if requisition.get('manager_approval_date'):
                approval_date_str = requisition['manager_approval_date']
                try:
                    # Parse the timestamp (assuming ISO format)
                    approval_date = datetime.fromisoformat(approval_date_str.replace('Z', '+00:00'))
                    
                    # Check if timestamp is reasonable (within last few seconds)
                    time_diff = abs((manager_approval_time - approval_date.replace(tzinfo=None)).total_seconds())
                    if time_diff < 60:  # Within 1 minute
                        print(f"   ✅ Manager approval timestamp accurate: {approval_date_str}")
                    else:
                        print(f"   ⚠️ Manager approval timestamp may be inaccurate: {approval_date_str}")
                except Exception as e:
                    print(f"   ⚠️ Error parsing manager approval timestamp: {e}")
            
            # Verify data persistence
            print(f"   Manager action by: {requisition.get('manager_action_by_name', 'Not set')}")
            print(f"   Manager approval reason: {requisition.get('manager_approval_reason', 'Not set')}")
            print(f"   Status after manager approval: {requisition.get('status', 'Unknown')}")
        
        # HR approval with timestamp verification
        hr_approve_data = {
            "action": "approve",
            "reason": "HR approved for timestamp testing"
        }
        
        success, response = self.run_test(
            "HR Approve for Timestamp Test",
            "POST",
            f"asset-requisitions/{timestamp_req_id}/hr-action",
            200,
            data=hr_approve_data,
            user_role="HR Manager"
        )
        
        if success:
            hr_approval_time = datetime.now()
            requisition = response.get('requisition', {})
            
            # Verify HR approval timestamp
            if requisition.get('hr_approval_date'):
                hr_approval_date_str = requisition['hr_approval_date']
                try:
                    hr_approval_date = datetime.fromisoformat(hr_approval_date_str.replace('Z', '+00:00'))
                    
                    time_diff = abs((hr_approval_time - hr_approval_date.replace(tzinfo=None)).total_seconds())
                    if time_diff < 60:  # Within 1 minute
                        print(f"   ✅ HR approval timestamp accurate: {hr_approval_date_str}")
                    else:
                        print(f"   ⚠️ HR approval timestamp may be inaccurate: {hr_approval_date_str}")
                except Exception as e:
                    print(f"   ⚠️ Error parsing HR approval timestamp: {e}")
            
            # Verify final data integrity
            print(f"   HR action by: {requisition.get('hr_action_by_name', 'Not set')}")
            print(f"   HR approval reason: {requisition.get('hr_approval_reason', 'Not set')}")
            print(f"   Final status: {requisition.get('status', 'Unknown')}")
        
        # Verify data persistence by fetching requisition again
        success, response = self.run_test(
            "Verify Data Persistence",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            # Find our timestamp test requisition
            for req in response:
                if req['id'] == timestamp_req_id:
                    print(f"   ✅ Data persisted correctly in database")
                    print(f"   Persisted status: {req.get('status', 'Unknown')}")
                    print(f"   Persisted manager approval: {req.get('manager_approval_reason', 'Not set')}")
                    print(f"   Persisted HR approval: {req.get('hr_approval_reason', 'Not set')}")
                    break
        
        return True

    def run_comprehensive_tests(self):
        """Run all manager approval workflow tests"""
        print("🚀 Starting Comprehensive Manager Approval Workflow Backend API Testing")
        print("=" * 80)
        
        # Setup
        if not self.test_login("admin@company.com", "password123", "Administrator"):
            print("❌ Failed to login as Administrator")
            return False
        
        if not self.test_login("hr@company.com", "password123", "HR Manager"):
            print("❌ Failed to login as HR Manager")
            return False
        
        if not self.test_login("manager@company.com", "password123", "Manager"):
            print("❌ Failed to login as Manager")
            return False
        
        if not self.test_login("employee@company.com", "password123", "Employee"):
            print("❌ Failed to login as Employee")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data")
            return False
        
        # Create test requisitions
        if not self.create_test_requisitions():
            print("❌ Failed to create test requisitions")
            return False
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_manager_action_endpoint())
        test_results.append(self.test_hr_action_endpoint())
        test_results.append(self.test_role_based_access_control())
        test_results.append(self.test_direct_reports_validation())
        test_results.append(self.test_enhanced_requisition_model())
        test_results.append(self.test_error_handling_and_validation())
        test_results.append(self.test_data_integrity_and_timestamps())
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 MANAGER APPROVAL WORKFLOW TESTING SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"📊 Overall Test Results: {self.tests_passed}/{self.tests_run} individual tests passed")
        print(f"📋 Test Categories: {passed_tests}/{total_tests} categories completed successfully")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Manager Approval Workflow is working correctly!")
        elif success_rate >= 75:
            print("✅ GOOD: Manager Approval Workflow is mostly working with minor issues")
        elif success_rate >= 50:
            print("⚠️ FAIR: Manager Approval Workflow has some issues that need attention")
        else:
            print("❌ POOR: Manager Approval Workflow has significant issues")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = ManagerApprovalWorkflowTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)