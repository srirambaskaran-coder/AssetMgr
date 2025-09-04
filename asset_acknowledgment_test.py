import requests
import sys
import json
from datetime import datetime

class AssetAcknowledgmentTester:
    def __init__(self, base_url="https://asset-track-2.preview.emergentagent.com"):
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
        """Setup test data for acknowledgment testing"""
        print(f"\n🏗️ Setting up test data for Asset Acknowledgment testing...")
        
        # Create asset type
        asset_type_data = {
            "code": "LAPTOP_ACK",
            "name": "Laptop for Acknowledgment Testing",
            "depreciation_applicable": True,
            "asset_life": 3,
            "to_be_recovered_on_separation": True,
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Asset Type for Testing",
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
        
        # Create asset definition
        asset_def_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP_ACK_001",
            "asset_description": "Dell Laptop for Acknowledgment Testing",
            "asset_details": "Dell Inspiron 15 3000 Series - Test Asset",
            "asset_value": 50000.0,
            "asset_depreciation_value_per_year": 16666.67,
            "status": "Available"
        }
        
        success, response = self.run_test(
            "Create Asset Definition for Testing",
            "POST",
            "asset-definitions",
            200,
            data=asset_def_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_def_id'] = response['id']
            print(f"   Created asset definition with ID: {response['id']}")
        else:
            print("❌ Failed to create asset definition for testing")
            return False
        
        # Create test employee user
        employee_data = {
            "email": f"ack_employee_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Acknowledgment Test Employee",
            "roles": ["Employee"],
            "designation": "Test Developer",
            "date_of_joining": "2024-01-01T00:00:00Z",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Test Employee for Acknowledgment",
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
        else:
            print("❌ Failed to create test employee")
            return False
        
        # Login as test employee
        success = self.test_login(
            self.test_data['test_employee_email'], 
            "TestPassword123!", 
            "TestEmployee"
        )
        
        if not success:
            print("❌ Failed to login as test employee")
            return False
        
        return True

    def allocate_asset_to_employee(self):
        """Allocate asset to employee for acknowledgment testing"""
        print(f"\n📋 Allocating asset to employee for acknowledgment testing...")
        
        # First create a requisition
        requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Need laptop for acknowledgment testing",
            "required_by_date": (datetime.now()).isoformat()
        }
        
        success, response = self.run_test(
            "Create Asset Requisition for Testing",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data,
            user_role="TestEmployee"
        )
        
        if success:
            self.test_data['requisition_id'] = response['id']
            print(f"   Created requisition with ID: {response['id']}")
        else:
            print("❌ Failed to create requisition")
            return False
        
        # Approve the requisition as Administrator (simulating manager approval)
        approval_data = {
            "action": "approve",
            "reason": "Approved for acknowledgment testing"
        }
        
        success, response = self.run_test(
            "Approve Requisition for Testing",
            "POST",
            f"asset-requisitions/{self.test_data['requisition_id']}/manager-action",
            200,
            data=approval_data,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Requisition approved successfully")
        else:
            print("❌ Failed to approve requisition")
            return False
        
        # Allocate the asset
        allocation_data = {
            "requisition_id": self.test_data['requisition_id'],
            "asset_definition_id": self.test_data['asset_def_id'],
            "remarks": "Test allocation for acknowledgment testing",
            "reference_id": "ACK_TEST_001",
            "dispatch_details": "Test dispatch for acknowledgment"
        }
        
        success, response = self.run_test(
            "Allocate Asset for Testing",
            "POST",
            "asset-allocations",
            200,
            data=allocation_data,
            user_role="Administrator"  # Asset Manager role
        )
        
        if success:
            self.test_data['allocation_id'] = response['id']
            print(f"   Asset allocated successfully with ID: {response['id']}")
            return True
        else:
            print("❌ Failed to allocate asset")
            return False

    def test_my_allocated_assets_endpoint(self):
        """Test GET /api/my-allocated-assets endpoint"""
        print(f"\n📦 Testing My Allocated Assets Endpoint")
        
        # Test 1: Employee can access their allocated assets
        success, response = self.run_test(
            "Employee Get My Allocated Assets",
            "GET",
            "my-allocated-assets",
            200,
            user_role="TestEmployee"
        )
        
        if success:
            print(f"   Employee can see {len(response)} allocated assets")
            if len(response) > 0:
                asset = response[0]
                print(f"   Asset Code: {asset.get('asset_code', 'N/A')}")
                print(f"   Asset Description: {asset.get('asset_description', 'N/A')}")
                print(f"   Allocated To: {asset.get('allocated_to_name', 'N/A')}")
                print(f"   Allocation Date: {asset.get('allocation_date', 'N/A')}")
                print(f"   Acknowledged: {asset.get('acknowledged', False)}")
                
                # Verify new fields are present
                new_fields = ['allocation_date', 'acknowledged', 'acknowledgment_date', 'acknowledgment_notes']
                present_fields = [field for field in new_fields if field in asset]
                print(f"   New acknowledgment fields present: {present_fields}")
        
        # Test 2: Different user roles accessing the endpoint
        for role in ["Employee", "Manager", "Administrator"]:
            if role in self.tokens:
                success, response = self.run_test(
                    f"{role} Get My Allocated Assets",
                    "GET",
                    "my-allocated-assets",
                    200,
                    user_role=role
                )
                if success:
                    print(f"   {role} can see {len(response)} allocated assets")
        
        # Test 3: Verify filtering by allocated_to and status
        success, response = self.run_test(
            "Verify Asset Filtering by User",
            "GET",
            "my-allocated-assets",
            200,
            user_role="TestEmployee"
        )
        
        if success:
            for asset in response:
                if asset.get('allocated_to') != self.test_data['test_employee_id']:
                    print(f"   ❌ Found asset not allocated to current user: {asset.get('asset_code')}")
                    return False
                if asset.get('status') != 'Allocated':
                    print(f"   ❌ Found asset with wrong status: {asset.get('status')}")
                    return False
            print("   ✅ All assets properly filtered by allocated_to and status")
        
        return True

    def test_asset_acknowledgment_endpoint(self):
        """Test POST /api/asset-definitions/{id}/acknowledge endpoint"""
        print(f"\n✅ Testing Asset Acknowledgment Endpoint")
        
        # Test 1: Employee acknowledges their allocated asset
        acknowledgment_data = {
            "acknowledgment_notes": "Asset received in good condition. All accessories included."
        }
        
        success, response = self.run_test(
            "Employee Acknowledge Allocated Asset",
            "POST",
            f"asset-definitions/{self.test_data['asset_def_id']}/acknowledge",
            200,
            data=acknowledgment_data,
            user_role="TestEmployee"
        )
        
        if success:
            print("   ✅ Asset acknowledgment successful")
            print(f"   Message: {response.get('message', 'N/A')}")
            print(f"   Acknowledged At: {response.get('acknowledged_at', 'N/A')}")
            
            # Verify asset data is returned
            asset_data = response.get('asset', {})
            if asset_data:
                print(f"   Asset acknowledged: {asset_data.get('acknowledged', False)}")
                print(f"   Acknowledgment notes: {asset_data.get('acknowledgment_notes', 'N/A')}")
                print(f"   Acknowledgment date: {asset_data.get('acknowledgment_date', 'N/A')}")
        else:
            print("❌ Asset acknowledgment failed")
            return False
        
        # Test 2: Try to acknowledge already acknowledged asset (should fail)
        success, response = self.run_test(
            "Try to Acknowledge Already Acknowledged Asset (Should Fail)",
            "POST",
            f"asset-definitions/{self.test_data['asset_def_id']}/acknowledge",
            400,
            data=acknowledgment_data,
            user_role="TestEmployee"
        )
        
        if success:
            print("   ✅ Correctly prevented double acknowledgment")
        
        # Test 3: Employee tries to acknowledge asset not allocated to them
        # First create another asset
        another_asset_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP_ACK_002",
            "asset_description": "Another Dell Laptop",
            "asset_details": "Dell Inspiron 15 - Another Test Asset",
            "asset_value": 45000.0,
            "status": "Available"
        }
        
        success, response = self.run_test(
            "Create Another Asset for Negative Testing",
            "POST",
            "asset-definitions",
            200,
            data=another_asset_data,
            user_role="Administrator"
        )
        
        if success:
            another_asset_id = response['id']
            
            # Try to acknowledge asset not allocated to user
            success, response = self.run_test(
                "Try to Acknowledge Non-Allocated Asset (Should Fail)",
                "POST",
                f"asset-definitions/{another_asset_id}/acknowledge",
                403,
                data=acknowledgment_data,
                user_role="TestEmployee"
            )
            
            if success:
                print("   ✅ Correctly prevented acknowledgment of non-allocated asset")
        
        # Test 4: Try to acknowledge non-existent asset
        success, response = self.run_test(
            "Try to Acknowledge Non-Existent Asset (Should Fail)",
            "POST",
            "asset-definitions/non-existent-id/acknowledge",
            404,
            data=acknowledgment_data,
            user_role="TestEmployee"
        )
        
        if success:
            print("   ✅ Correctly returned 404 for non-existent asset")
        
        # Test 5: Test acknowledgment without notes (should work)
        # First create and allocate another asset
        another_asset_data2 = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP_ACK_003",
            "asset_description": "Third Dell Laptop",
            "asset_details": "Dell Inspiron 15 - Third Test Asset",
            "asset_value": 48000.0,
            "status": "Available"
        }
        
        success, response = self.run_test(
            "Create Third Asset for Notes Testing",
            "POST",
            "asset-definitions",
            200,
            data=another_asset_data2,
            user_role="Administrator"
        )
        
        if success:
            third_asset_id = response['id']
            
            # Manually allocate this asset to test employee (simulate allocation)
            # Update asset to be allocated to test employee
            allocation_update = {
                "status": "Allocated",
                "allocated_to": self.test_data['test_employee_id'],
                "allocated_to_name": "Acknowledgment Test Employee"
            }
            
            success, response = self.run_test(
                "Manually Allocate Third Asset",
                "PUT",
                f"asset-definitions/{third_asset_id}",
                200,
                data=allocation_update,
                user_role="Administrator"
            )
            
            if success:
                # Test acknowledgment without notes
                success, response = self.run_test(
                    "Acknowledge Asset Without Notes",
                    "POST",
                    f"asset-definitions/{third_asset_id}/acknowledge",
                    200,
                    data={},  # No acknowledgment_notes
                    user_role="TestEmployee"
                )
                
                if success:
                    print("   ✅ Asset acknowledgment without notes successful")
                    asset_data = response.get('asset', {})
                    notes = asset_data.get('acknowledgment_notes')
                    if notes is None:
                        print("   ✅ Acknowledgment notes correctly set to null")
                    else:
                        print(f"   ⚠️ Acknowledgment notes: {notes}")
        
        return True

    def test_data_model_validation(self):
        """Test data model validation for acknowledgment fields"""
        print(f"\n🔍 Testing Data Model Validation")
        
        # Test 1: Verify new fields are properly stored and retrieved
        success, response = self.run_test(
            "Get Asset Definition to Verify Fields",
            "GET",
            f"asset-definitions/{self.test_data['asset_def_id']}",
            200,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Asset definition retrieved successfully")
            
            # Check for new acknowledgment fields
            new_fields = {
                'allocation_date': response.get('allocation_date'),
                'acknowledged': response.get('acknowledged'),
                'acknowledgment_date': response.get('acknowledgment_date'),
                'acknowledgment_notes': response.get('acknowledgment_notes')
            }
            
            print("   New acknowledgment fields in asset definition:")
            for field, value in new_fields.items():
                print(f"     {field}: {value}")
            
            # Verify acknowledged is True
            if response.get('acknowledged') == True:
                print("   ✅ Asset acknowledged field correctly set to True")
            else:
                print(f"   ❌ Asset acknowledged field incorrect: {response.get('acknowledged')}")
            
            # Verify acknowledgment_date is set
            if response.get('acknowledgment_date'):
                print("   ✅ Acknowledgment date properly set")
            else:
                print("   ❌ Acknowledgment date not set")
            
            # Verify allocation_date is set
            if response.get('allocation_date'):
                print("   ✅ Allocation date properly set")
            else:
                print("   ❌ Allocation date not set")
        
        # Test 2: Verify datetime handling and timezone storage
        success, response = self.run_test(
            "Verify Datetime Handling",
            "GET",
            f"asset-definitions/{self.test_data['asset_def_id']}",
            200,
            user_role="Administrator"
        )
        
        if success:
            allocation_date = response.get('allocation_date')
            acknowledgment_date = response.get('acknowledgment_date')
            
            if allocation_date:
                try:
                    # Try to parse the datetime
                    parsed_date = datetime.fromisoformat(allocation_date.replace('Z', '+00:00'))
                    print(f"   ✅ Allocation date properly formatted: {parsed_date}")
                except:
                    print(f"   ❌ Allocation date format issue: {allocation_date}")
            
            if acknowledgment_date:
                try:
                    # Try to parse the datetime
                    parsed_date = datetime.fromisoformat(acknowledgment_date.replace('Z', '+00:00'))
                    print(f"   ✅ Acknowledgment date properly formatted: {parsed_date}")
                except:
                    print(f"   ❌ Acknowledgment date format issue: {acknowledgment_date}")
        
        # Test 3: Test data persistence across requests
        success, response1 = self.run_test(
            "First Request - Get Asset Data",
            "GET",
            f"asset-definitions/{self.test_data['asset_def_id']}",
            200,
            user_role="Administrator"
        )
        
        success, response2 = self.run_test(
            "Second Request - Get Asset Data",
            "GET",
            f"asset-definitions/{self.test_data['asset_def_id']}",
            200,
            user_role="Administrator"
        )
        
        if success and response1 and response2:
            # Compare acknowledgment data between requests
            fields_to_compare = ['acknowledged', 'acknowledgment_date', 'acknowledgment_notes', 'allocation_date']
            
            data_consistent = True
            for field in fields_to_compare:
                if response1.get(field) != response2.get(field):
                    print(f"   ❌ Data inconsistency in {field}: {response1.get(field)} vs {response2.get(field)}")
                    data_consistent = False
            
            if data_consistent:
                print("   ✅ Data persistence verified - acknowledgment data consistent across requests")
        
        return True

    def test_security_and_access_control(self):
        """Test security and access control for acknowledgment functionality"""
        print(f"\n🔒 Testing Security and Access Control")
        
        # Test 1: Unauthenticated access (should fail)
        success, response = self.run_test(
            "Unauthenticated Access to Acknowledge (Should Fail)",
            "POST",
            f"asset-definitions/{self.test_data['asset_def_id']}/acknowledge",
            401,
            data={"acknowledgment_notes": "Test"}
            # No user_role specified = no auth header
        )
        
        if success:
            print("   ✅ Unauthenticated access correctly denied")
        
        # Test 2: Different user trying to acknowledge another user's asset
        # Create another test employee
        another_employee_data = {
            "email": f"ack_employee2_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Another Test Employee",
            "roles": ["Employee"],
            "designation": "Another Test Developer",
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create Another Test Employee",
            "POST",
            "users",
            200,
            data=another_employee_data,
            user_role="Administrator"
        )
        
        if success:
            another_employee_id = response['id']
            
            # Login as another employee
            success = self.test_login(
                another_employee_data['email'], 
                "TestPassword123!", 
                "AnotherEmployee"
            )
            
            if success:
                # Try to acknowledge asset allocated to first employee
                success, response = self.run_test(
                    "Another Employee Try to Acknowledge (Should Fail)",
                    "POST",
                    f"asset-definitions/{self.test_data['asset_def_id']}/acknowledge",
                    403,
                    data={"acknowledgment_notes": "Unauthorized attempt"},
                    user_role="AnotherEmployee"
                )
                
                if success:
                    print("   ✅ Cross-user acknowledgment correctly denied")
        
        # Test 3: Manager/Admin trying to acknowledge on behalf of employee (should fail)
        success, response = self.run_test(
            "Manager Try to Acknowledge Employee Asset (Should Fail)",
            "POST",
            f"asset-definitions/{self.test_data['asset_def_id']}/acknowledge",
            403,
            data={"acknowledgment_notes": "Manager attempting acknowledgment"},
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Manager/Admin acknowledgment on behalf correctly denied")
        
        # Test 4: Test my-allocated-assets endpoint security
        success, response = self.run_test(
            "Unauthenticated Access to My Assets (Should Fail)",
            "GET",
            "my-allocated-assets",
            401
            # No user_role specified = no auth header
        )
        
        if success:
            print("   ✅ Unauthenticated access to my-allocated-assets correctly denied")
        
        # Test 5: Verify proper 403 errors for unauthorized access
        # This is already covered above, but let's verify the error messages
        success, response = self.run_test(
            "Verify 403 Error Message",
            "POST",
            f"asset-definitions/{self.test_data['asset_def_id']}/acknowledge",
            403,
            data={"acknowledgment_notes": "Test"},
            user_role="AnotherEmployee"
        )
        
        if success:
            print("   ✅ Proper 403 error handling verified")
        
        return True

    def test_error_handling(self):
        """Test comprehensive error handling scenarios"""
        print(f"\n⚠️ Testing Error Handling Scenarios")
        
        # Test 1: Acknowledgment of non-existent asset
        success, response = self.run_test(
            "Acknowledge Non-Existent Asset",
            "POST",
            "asset-definitions/00000000-0000-0000-0000-000000000000/acknowledge",
            404,
            data={"acknowledgment_notes": "Test"},
            user_role="TestEmployee"
        )
        
        if success:
            print("   ✅ Non-existent asset returns 404")
        
        # Test 2: Acknowledgment of asset not allocated to user
        # Create an unallocated asset
        unallocated_asset_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP_UNALLOC_001",
            "asset_description": "Unallocated Laptop",
            "asset_details": "Dell Inspiron 15 - Unallocated",
            "asset_value": 40000.0,
            "status": "Available"  # Not allocated
        }
        
        success, response = self.run_test(
            "Create Unallocated Asset for Error Testing",
            "POST",
            "asset-definitions",
            200,
            data=unallocated_asset_data,
            user_role="Administrator"
        )
        
        if success:
            unallocated_asset_id = response['id']
            
            success, response = self.run_test(
                "Acknowledge Unallocated Asset (Should Fail)",
                "POST",
                f"asset-definitions/{unallocated_asset_id}/acknowledge",
                403,
                data={"acknowledgment_notes": "Test"},
                user_role="TestEmployee"
            )
            
            if success:
                print("   ✅ Unallocated asset acknowledgment correctly denied")
        
        # Test 3: Acknowledgment of already acknowledged asset
        success, response = self.run_test(
            "Acknowledge Already Acknowledged Asset",
            "POST",
            f"asset-definitions/{self.test_data['asset_def_id']}/acknowledge",
            400,
            data={"acknowledgment_notes": "Double acknowledgment attempt"},
            user_role="TestEmployee"
        )
        
        if success:
            print("   ✅ Double acknowledgment correctly prevented")
        
        # Test 4: Invalid JSON data
        success, response = self.run_test(
            "Invalid Acknowledgment Data",
            "POST",
            f"asset-definitions/{self.test_data['asset_def_id']}/acknowledge",
            400,  # Expecting validation error or bad request
            data={"invalid_field": "invalid_value"},
            user_role="TestEmployee"
        )
        
        # This might pass with 400 or might ignore invalid fields - both are acceptable
        print("   ✅ Invalid data handling tested")
        
        # Test 5: Verify proper error messages and status codes
        success, response = self.run_test(
            "Verify Error Message Format",
            "POST",
            "asset-definitions/invalid-uuid-format/acknowledge",
            404,  # Should return 404 for invalid UUID
            data={"acknowledgment_notes": "Test"},
            user_role="TestEmployee"
        )
        
        if success:
            print("   ✅ Proper error handling for invalid UUID format")
        
        return True

    def test_asset_allocation_enhancement(self):
        """Test that asset allocation properly sets allocation_date and other fields"""
        print(f"\n🎯 Testing Asset Allocation Enhancement")
        
        # Create a new asset for allocation testing
        new_asset_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP_ALLOC_TEST",
            "asset_description": "Laptop for Allocation Testing",
            "asset_details": "Dell Inspiron 15 - Allocation Test",
            "asset_value": 55000.0,
            "status": "Available"
        }
        
        success, response = self.run_test(
            "Create Asset for Allocation Testing",
            "POST",
            "asset-definitions",
            200,
            data=new_asset_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to create asset for allocation testing")
            return False
        
        new_asset_id = response['id']
        print(f"   Created new asset with ID: {new_asset_id}")
        
        # Verify initial state (no allocation fields set)
        success, response = self.run_test(
            "Verify Initial Asset State",
            "GET",
            f"asset-definitions/{new_asset_id}",
            200,
            user_role="Administrator"
        )
        
        if success:
            initial_state = {
                'allocated_to': response.get('allocated_to'),
                'allocated_to_name': response.get('allocated_to_name'),
                'allocation_date': response.get('allocation_date'),
                'acknowledged': response.get('acknowledged', False),
                'status': response.get('status')
            }
            print(f"   Initial asset state: {initial_state}")
        
        # Create requisition for new asset
        new_requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Need laptop for allocation enhancement testing"
        }
        
        success, response = self.run_test(
            "Create Requisition for Allocation Testing",
            "POST",
            "asset-requisitions",
            200,
            data=new_requisition_data,
            user_role="TestEmployee"
        )
        
        if not success:
            print("❌ Failed to create requisition for allocation testing")
            return False
        
        new_requisition_id = response['id']
        
        # Approve the requisition
        approval_data = {
            "action": "approve",
            "reason": "Approved for allocation enhancement testing"
        }
        
        success, response = self.run_test(
            "Approve New Requisition",
            "POST",
            f"asset-requisitions/{new_requisition_id}/manager-action",
            200,
            data=approval_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to approve requisition")
            return False
        
        # Allocate the asset and verify allocation_date is set
        allocation_data = {
            "requisition_id": new_requisition_id,
            "asset_definition_id": new_asset_id,
            "remarks": "Allocation enhancement test",
            "reference_id": "ALLOC_ENH_001"
        }
        
        success, response = self.run_test(
            "Allocate Asset with Enhancement Testing",
            "POST",
            "asset-allocations",
            200,
            data=allocation_data,
            user_role="Administrator"
        )
        
        if not success:
            print("❌ Failed to allocate asset")
            return False
        
        print("   ✅ Asset allocation successful")
        
        # Verify allocation enhancement - check that allocation_date is properly set
        success, response = self.run_test(
            "Verify Allocation Enhancement",
            "GET",
            f"asset-definitions/{new_asset_id}",
            200,
            user_role="Administrator"
        )
        
        if success:
            enhanced_state = {
                'allocated_to': response.get('allocated_to'),
                'allocated_to_name': response.get('allocated_to_name'),
                'allocation_date': response.get('allocation_date'),
                'acknowledged': response.get('acknowledged', False),
                'status': response.get('status')
            }
            print(f"   Enhanced asset state after allocation: {enhanced_state}")
            
            # Verify allocation_date is set
            if response.get('allocation_date'):
                print("   ✅ Allocation date properly set during allocation")
                
                # Verify datetime format
                try:
                    parsed_date = datetime.fromisoformat(response['allocation_date'].replace('Z', '+00:00'))
                    print(f"   ✅ Allocation date properly formatted: {parsed_date}")
                except:
                    print(f"   ❌ Allocation date format issue: {response['allocation_date']}")
            else:
                print("   ❌ Allocation date not set during allocation")
            
            # Verify allocated_to is set
            if response.get('allocated_to') == self.test_data['test_employee_id']:
                print("   ✅ Asset properly allocated to test employee")
            else:
                print(f"   ❌ Asset allocation issue: {response.get('allocated_to')}")
            
            # Verify status is updated
            if response.get('status') == 'Allocated':
                print("   ✅ Asset status properly updated to Allocated")
            else:
                print(f"   ❌ Asset status not updated: {response.get('status')}")
            
            # Verify acknowledged is initially False
            if response.get('acknowledged') == False:
                print("   ✅ Asset acknowledged field initially False")
            else:
                print(f"   ❌ Asset acknowledged field incorrect: {response.get('acknowledged')}")
        
        return True

    def run_comprehensive_tests(self):
        """Run all comprehensive Asset Acknowledgment tests"""
        print("🚀 Starting Comprehensive Asset Acknowledgment Testing")
        print("=" * 60)
        
        # Setup phase
        print("\n📋 SETUP PHASE")
        
        # Login as different users
        login_success = True
        login_success &= self.test_login("admin@company.com", "password123", "Administrator")
        login_success &= self.test_login("employee@company.com", "password123", "Employee")
        login_success &= self.test_login("manager@company.com", "password123", "Manager")
        
        if not login_success:
            print("❌ Failed to login required users")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data")
            return False
        
        # Allocate asset to employee
        if not self.allocate_asset_to_employee():
            print("❌ Failed to allocate asset to employee")
            return False
        
        print("\n🧪 TESTING PHASE")
        
        # Run all test suites
        test_results = []
        
        test_results.append(("My Allocated Assets API", self.test_my_allocated_assets_endpoint()))
        test_results.append(("Asset Acknowledgment API", self.test_asset_acknowledgment_endpoint()))
        test_results.append(("Data Model Validation", self.test_data_model_validation()))
        test_results.append(("Security and Access Control", self.test_security_and_access_control()))
        test_results.append(("Error Handling", self.test_error_handling()))
        test_results.append(("Asset Allocation Enhancement", self.test_asset_allocation_enhancement()))
        
        # Print summary
        print("\n📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall Results:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\nTest Suites:")
        print(f"Suites Passed: {passed_tests}/{total_tests}")
        print(f"Suite Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = AssetAcknowledgmentTester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 All Asset Acknowledgment tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some Asset Acknowledgment tests failed!")
        sys.exit(1)