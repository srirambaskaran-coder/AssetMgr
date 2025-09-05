import requests
import sys
import json
from datetime import datetime, timedelta

class RestructuredAssetManagementTester:
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

    def test_asset_type_restructured_crud(self):
        """Test Asset Type CRUD - Should NOT accept Asset Manager fields"""
        print(f"\n📋 PRIORITY 1: Testing Asset Type CRUD (Restructured - No Asset Manager Fields)")
        
        # Test 1: Create Asset Type WITHOUT Asset Manager fields (should work)
        import time
        timestamp = str(int(time.time()))
        asset_type_data = {
            "code": f"LAPTOP_TEST_{timestamp}",
            "name": "Test Laptop Computers",
            "depreciation_applicable": True,
            "asset_life": 3,
            "to_be_recovered_on_separation": True,
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Asset Type Without Asset Manager Fields",
            "POST",
            "asset-types",
            200,
            data=asset_type_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_type_id'] = response['id']
            print(f"   ✅ Created asset type ID: {response['id']}")
            
            # Verify Asset Manager fields are NOT in response
            asset_manager_fields = ['assigned_asset_manager_id', 'assigned_asset_manager_name']
            found_fields = [field for field in asset_manager_fields if field in response and response[field] is not None]
            if not found_fields:
                print("   ✅ Asset Type correctly has NO Asset Manager fields")
            else:
                print(f"   ❌ Asset Type incorrectly has Asset Manager fields: {found_fields}")
        
        # Test 2: Try to create Asset Type WITH Asset Manager fields (should be ignored)
        asset_type_with_manager = {
            "code": "MOBILE_TEST",
            "name": "Test Mobile Devices",
            "depreciation_applicable": True,
            "asset_life": 2,
            "to_be_recovered_on_separation": True,
            "status": "Active",
            "assigned_asset_manager_id": "some-manager-id",  # This should be ignored
            "assigned_asset_manager_name": "Some Manager"    # This should be ignored
        }
        
        success, response = self.run_test(
            "Create Asset Type With Asset Manager Fields (Should Ignore)",
            "POST",
            "asset-types",
            200,
            data=asset_type_with_manager,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_type_id_2'] = response['id']
            print(f"   ✅ Created asset type ID: {response['id']}")
            
            # Verify Asset Manager fields are NOT in response (should be ignored)
            asset_manager_fields = ['assigned_asset_manager_id', 'assigned_asset_manager_name']
            found_fields = [field for field in asset_manager_fields if field in response and response[field] is not None]
            if not found_fields:
                print("   ✅ Asset Manager fields correctly ignored in Asset Type creation")
            else:
                print(f"   ❌ Asset Manager fields incorrectly accepted: {found_fields}")
        
        # Test 3: Update Asset Type - Asset Manager fields should be ignored
        if 'asset_type_id' in self.test_data:
            update_data = {
                "name": "Updated Test Laptop Computers",
                "assigned_asset_manager_id": "some-manager-id",  # Should be ignored
                "assigned_asset_manager_name": "Some Manager"    # Should be ignored
            }
            
            success, response = self.run_test(
                "Update Asset Type With Asset Manager Fields (Should Ignore)",
                "PUT",
                f"asset-types/{self.test_data['asset_type_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )
            
            if success:
                print(f"   ✅ Updated asset type name: {response.get('name')}")
                
                # Verify Asset Manager fields are still NOT in response
                asset_manager_fields = ['assigned_asset_manager_id', 'assigned_asset_manager_name']
                found_fields = [field for field in asset_manager_fields if field in response and response[field] is not None]
                if not found_fields:
                    print("   ✅ Asset Manager fields correctly ignored in Asset Type update")
                else:
                    print(f"   ❌ Asset Manager fields incorrectly accepted in update: {found_fields}")
        
        # Test 4: Get Asset Types - Verify no Asset Manager fields in any response
        success, response = self.run_test(
            "Get All Asset Types - Verify No Asset Manager Fields",
            "GET",
            "asset-types",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} asset types")
            asset_manager_fields = ['assigned_asset_manager_id', 'assigned_asset_manager_name']
            
            for i, asset_type in enumerate(response):
                found_fields = [field for field in asset_manager_fields if field in asset_type and asset_type[field] is not None]
                if found_fields:
                    print(f"   ❌ Asset Type {i+1} has Asset Manager fields: {found_fields}")
                else:
                    print(f"   ✅ Asset Type {i+1} correctly has no Asset Manager fields")

    def test_asset_definition_enhanced_crud(self):
        """Test Asset Definition CRUD - Should accept Asset Manager and Location fields"""
        print(f"\n💻 PRIORITY 2: Testing Asset Definition CRUD (Enhanced - With Asset Manager & Location)")
        
        if 'asset_type_id' not in self.test_data:
            print("❌ Skipping Asset Definition tests - no asset type created")
            return
        
        # First, get Asset Managers and Locations for testing
        success, asset_managers = self.run_test(
            "Get Asset Managers for Testing",
            "GET",
            "users/asset-managers",
            200,
            user_role="Administrator"
        )
        
        success, locations = self.run_test(
            "Get Locations for Testing",
            "GET",
            "locations",
            200,
            user_role="Administrator"
        )
        
        asset_manager_id = None
        location_id = None
        
        if asset_managers and len(asset_managers) > 0:
            asset_manager_id = asset_managers[0]['id']
            print(f"   Using Asset Manager: {asset_managers[0]['name']} (ID: {asset_manager_id})")
        
        if locations and len(locations) > 0:
            location_id = locations[0]['id']
            print(f"   Using Location: {locations[0]['name']} (ID: {location_id})")
        
        # Test 1: Create Asset Definition WITH Asset Manager and Location
        asset_def_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP001_TEST",
            "asset_description": "Test Dell Laptop",
            "asset_details": "Dell Inspiron 15 3000 Series - Test Asset",
            "asset_value": 50000.0,
            "asset_depreciation_value_per_year": 16666.67,
            "status": "Available",
            "assigned_asset_manager_id": asset_manager_id,
            "location_id": location_id
        }
        
        success, response = self.run_test(
            "Create Asset Definition With Asset Manager and Location",
            "POST",
            "asset-definitions",
            200,
            data=asset_def_data,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_def_id'] = response['id']
            print(f"   ✅ Created asset definition ID: {response['id']}")
            
            # Verify Asset Manager and Location names are populated
            if asset_manager_id and response.get('assigned_asset_manager_name'):
                print(f"   ✅ Asset Manager name populated: {response['assigned_asset_manager_name']}")
            elif asset_manager_id:
                print("   ❌ Asset Manager name NOT populated")
            
            if location_id and response.get('location_name'):
                print(f"   ✅ Location name populated: {response['location_name']}")
            elif location_id:
                print("   ❌ Location name NOT populated")
            
            # Verify IDs are stored correctly
            if response.get('assigned_asset_manager_id') == asset_manager_id:
                print("   ✅ Asset Manager ID stored correctly")
            elif asset_manager_id:
                print("   ❌ Asset Manager ID NOT stored correctly")
            
            if response.get('location_id') == location_id:
                print("   ✅ Location ID stored correctly")
            elif location_id:
                print("   ❌ Location ID NOT stored correctly")
        
        # Test 2: Create Asset Definition WITHOUT Asset Manager and Location (should work)
        asset_def_no_assignments = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP002_TEST",
            "asset_description": "Test Dell Laptop No Assignments",
            "asset_details": "Dell Inspiron 15 3000 Series - No Assignments",
            "asset_value": 45000.0,
            "asset_depreciation_value_per_year": 15000.0,
            "status": "Available"
        }
        
        success, response = self.run_test(
            "Create Asset Definition Without Assignments",
            "POST",
            "asset-definitions",
            200,
            data=asset_def_no_assignments,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['asset_def_id_2'] = response['id']
            print(f"   ✅ Created asset definition without assignments: {response['id']}")
            
            # Verify fields are null when not provided
            if response.get('assigned_asset_manager_id') is None:
                print("   ✅ Asset Manager ID correctly null when not provided")
            else:
                print("   ❌ Asset Manager ID should be null when not provided")
            
            if response.get('location_id') is None:
                print("   ✅ Location ID correctly null when not provided")
            else:
                print("   ❌ Location ID should be null when not provided")
        
        # Test 3: Validation - Invalid Asset Manager ID
        invalid_asset_def = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP003_TEST",
            "asset_description": "Test Invalid Asset Manager",
            "asset_details": "Test with invalid Asset Manager ID",
            "asset_value": 40000.0,
            "status": "Available",
            "assigned_asset_manager_id": "invalid-manager-id"
        }
        
        success, response = self.run_test(
            "Create Asset Definition With Invalid Asset Manager ID (Should Fail)",
            "POST",
            "asset-definitions",
            400,
            data=invalid_asset_def,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Invalid Asset Manager ID correctly rejected")
        
        # Test 4: Validation - Invalid Location ID
        invalid_location_def = {
            "asset_type_id": self.test_data['asset_type_id'],
            "asset_code": "LAP004_TEST",
            "asset_description": "Test Invalid Location",
            "asset_details": "Test with invalid Location ID",
            "asset_value": 40000.0,
            "status": "Available",
            "location_id": "invalid-location-id"
        }
        
        success, response = self.run_test(
            "Create Asset Definition With Invalid Location ID (Should Fail)",
            "POST",
            "asset-definitions",
            400,
            data=invalid_location_def,
            user_role="Administrator"
        )
        
        if success:
            print("   ✅ Invalid Location ID correctly rejected")
        
        # Test 5: Update Asset Definition - Change Asset Manager and Location
        if 'asset_def_id' in self.test_data and asset_manager_id and location_id:
            update_data = {
                "assigned_asset_manager_id": None,  # Clear Asset Manager
                "location_id": None  # Clear Location
            }
            
            success, response = self.run_test(
                "Update Asset Definition - Clear Assignments",
                "PUT",
                f"asset-definitions/{self.test_data['asset_def_id']}",
                200,
                data=update_data,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Asset Definition updated successfully")
                
                # Verify assignments were cleared
                if response.get('assigned_asset_manager_id') is None:
                    print("   ✅ Asset Manager assignment cleared")
                else:
                    print("   ❌ Asset Manager assignment NOT cleared")
                
                if response.get('location_id') is None:
                    print("   ✅ Location assignment cleared")
                else:
                    print("   ❌ Location assignment NOT cleared")
                
                if response.get('assigned_asset_manager_name') is None:
                    print("   ✅ Asset Manager name cleared")
                else:
                    print("   ❌ Asset Manager name NOT cleared")
                
                if response.get('location_name') is None:
                    print("   ✅ Location name cleared")
                else:
                    print("   ❌ Location name NOT cleared")
        
        # Test 6: Get Asset Definitions - Verify enhanced fields are present
        success, response = self.run_test(
            "Get All Asset Definitions - Verify Enhanced Fields",
            "GET",
            "asset-definitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} asset definitions")
            enhanced_fields = ['assigned_asset_manager_id', 'assigned_asset_manager_name', 'location_id', 'location_name']
            
            for i, asset_def in enumerate(response):
                present_fields = [field for field in enhanced_fields if field in asset_def]
                if len(present_fields) == len(enhanced_fields):
                    print(f"   ✅ Asset Definition {i+1} has all enhanced fields")
                else:
                    missing_fields = [field for field in enhanced_fields if field not in asset_def]
                    print(f"   ❌ Asset Definition {i+1} missing fields: {missing_fields}")

    def test_enhanced_allocation_routing(self):
        """Test Enhanced Asset Allocation Logic - Should use Asset Definition's assignments"""
        print(f"\n🎯 PRIORITY 3: Testing Enhanced Allocation Routing (Asset Definition-based)")
        
        if 'asset_type_id' not in self.test_data:
            print("❌ Skipping Enhanced Allocation tests - no asset type created")
            return
        
        # Test 1: Create Asset Requisition
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Testing enhanced allocation routing with Asset Definition assignments",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Asset Requisition for Enhanced Routing Test",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data,
            user_role="Employee"
        )
        
        if success:
            self.test_data['routing_requisition_id'] = response['id']
            print(f"   ✅ Created requisition ID: {response['id']}")
            print(f"   Status: {response.get('status', 'Unknown')}")
        
        # Test 2: Manager Approval (should trigger enhanced routing)
        if 'routing_requisition_id' in self.test_data:
            approval_data = {
                "action": "approve",
                "reason": "Approved for enhanced allocation routing test"
            }
            
            success, response = self.run_test(
                "Manager Approval - Should Trigger Enhanced Routing",
                "POST",
                f"asset-requisitions/{self.test_data['routing_requisition_id']}/manager-action",
                200,
                data=approval_data,
                user_role="Manager"
            )
            
            if success:
                print(f"   ✅ Manager approval successful")
                print(f"   New Status: {response.get('status', 'Unknown')}")
                
                # Check if routing fields are populated
                routing_fields = ['assigned_to', 'assigned_to_name', 'routing_reason', 'assigned_date']
                populated_fields = [field for field in routing_fields if field in response and response[field] is not None]
                
                if len(populated_fields) > 0:
                    print(f"   ✅ Enhanced routing triggered - populated fields: {populated_fields}")
                    for field in populated_fields:
                        print(f"     {field}: {response[field]}")
                else:
                    print("   ❌ Enhanced routing NOT triggered - no routing fields populated")
                
                # Verify status is 'Assigned for Allocation'
                if response.get('status') == 'Assigned for Allocation':
                    print("   ✅ Status correctly set to 'Assigned for Allocation'")
                else:
                    print(f"   ❌ Status should be 'Assigned for Allocation', got: {response.get('status')}")
        
        # Test 3: Get Asset Requisitions - Verify routing information is visible
        success, response = self.run_test(
            "Get Asset Requisitions - Verify Routing Information",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Found {len(response)} requisitions")
            
            # Find our test requisition
            test_requisition = None
            if 'routing_requisition_id' in self.test_data:
                test_requisition = next((req for req in response if req['id'] == self.test_data['routing_requisition_id']), None)
            
            if test_requisition:
                print("   ✅ Test requisition found in list")
                
                # Check routing fields
                routing_fields = ['assigned_to', 'assigned_to_name', 'routing_reason', 'assigned_date']
                for field in routing_fields:
                    if field in test_requisition and test_requisition[field] is not None:
                        print(f"     {field}: {test_requisition[field]}")
                    else:
                        print(f"     {field}: Not set")
            else:
                print("   ❌ Test requisition NOT found in list")

    def test_data_consistency(self):
        """Test data consistency after restructuring"""
        print(f"\n🔍 PRIORITY 4: Testing Data Consistency After Restructuring")
        
        # Test 1: Verify Asset Types no longer have Asset Manager fields
        success, response = self.run_test(
            "Verify Asset Types Have No Asset Manager Fields",
            "GET",
            "asset-types",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Checking {len(response)} asset types for Asset Manager fields...")
            asset_manager_fields = ['assigned_asset_manager_id', 'assigned_asset_manager_name']
            
            all_clean = True
            for i, asset_type in enumerate(response):
                found_fields = [field for field in asset_manager_fields if field in asset_type and asset_type[field] is not None]
                if found_fields:
                    print(f"   ❌ Asset Type '{asset_type.get('name', 'Unknown')}' has Asset Manager fields: {found_fields}")
                    all_clean = False
            
            if all_clean:
                print("   ✅ All Asset Types correctly have NO Asset Manager fields")
        
        # Test 2: Verify Asset Definitions can have Asset Manager assignments
        success, response = self.run_test(
            "Verify Asset Definitions Can Have Asset Manager Fields",
            "GET",
            "asset-definitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Checking {len(response)} asset definitions for enhanced fields...")
            enhanced_fields = ['assigned_asset_manager_id', 'assigned_asset_manager_name', 'location_id', 'location_name']
            
            all_have_fields = True
            assets_with_assignments = 0
            
            for i, asset_def in enumerate(response):
                # Check if all enhanced fields exist (even if null)
                missing_fields = [field for field in enhanced_fields if field not in asset_def]
                if missing_fields:
                    print(f"   ❌ Asset Definition '{asset_def.get('asset_code', 'Unknown')}' missing fields: {missing_fields}")
                    all_have_fields = False
                
                # Count assets with actual assignments
                if asset_def.get('assigned_asset_manager_id') or asset_def.get('location_id'):
                    assets_with_assignments += 1
            
            if all_have_fields:
                print("   ✅ All Asset Definitions have enhanced fields structure")
            
            print(f"   📊 {assets_with_assignments} out of {len(response)} assets have assignments")
        
        # Test 3: Test routing works with new structure
        success, response = self.run_test(
            "Verify Routing Uses Asset Definition Structure",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            routed_requisitions = [req for req in response if req.get('status') == 'Assigned for Allocation']
            print(f"   Found {len(routed_requisitions)} requisitions with 'Assigned for Allocation' status")
            
            for req in routed_requisitions:
                routing_fields = ['assigned_to', 'assigned_to_name', 'routing_reason']
                populated_routing = [field for field in routing_fields if req.get(field)]
                
                if len(populated_routing) == len(routing_fields):
                    print(f"   ✅ Requisition {req['id'][:8]}... has complete routing information")
                else:
                    missing_routing = [field for field in routing_fields if not req.get(field)]
                    print(f"   ❌ Requisition {req['id'][:8]}... missing routing fields: {missing_routing}")

    def test_edge_cases(self):
        """Test edge cases for the restructured system"""
        print(f"\n🧪 PRIORITY 5: Testing Edge Cases")
        
        if 'asset_type_id' not in self.test_data:
            print("❌ Skipping Edge Case tests - no asset type created")
            return
        
        # Test 1: Asset Definition with Asset Manager but no Location
        success, asset_managers = self.run_test(
            "Get Asset Managers for Edge Case Test",
            "GET",
            "users/asset-managers",
            200,
            user_role="Administrator"
        )
        
        if asset_managers and len(asset_managers) > 0:
            asset_manager_id = asset_managers[0]['id']
            
            edge_case_1_data = {
                "asset_type_id": self.test_data['asset_type_id'],
                "asset_code": "EDGE_CASE_1",
                "asset_description": "Asset Manager Only Test",
                "asset_details": "Asset with Asset Manager but no Location",
                "asset_value": 30000.0,
                "status": "Available",
                "assigned_asset_manager_id": asset_manager_id
                # No location_id
            }
            
            success, response = self.run_test(
                "Edge Case 1: Asset Manager Only (No Location)",
                "POST",
                "asset-definitions",
                200,
                data=edge_case_1_data,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Asset Definition with Asset Manager only created successfully")
                if response.get('assigned_asset_manager_name'):
                    print(f"     Asset Manager: {response['assigned_asset_manager_name']}")
                if response.get('location_id') is None:
                    print("     ✅ Location correctly null")
        
        # Test 2: Asset Definition with Location but no Asset Manager
        success, locations = self.run_test(
            "Get Locations for Edge Case Test",
            "GET",
            "locations",
            200,
            user_role="Administrator"
        )
        
        if locations and len(locations) > 0:
            location_id = locations[0]['id']
            
            edge_case_2_data = {
                "asset_type_id": self.test_data['asset_type_id'],
                "asset_code": "EDGE_CASE_2",
                "asset_description": "Location Only Test",
                "asset_details": "Asset with Location but no Asset Manager",
                "asset_value": 25000.0,
                "status": "Available",
                "location_id": location_id
                # No assigned_asset_manager_id
            }
            
            success, response = self.run_test(
                "Edge Case 2: Location Only (No Asset Manager)",
                "POST",
                "asset-definitions",
                200,
                data=edge_case_2_data,
                user_role="Administrator"
            )
            
            if success:
                print("   ✅ Asset Definition with Location only created successfully")
                if response.get('location_name'):
                    print(f"     Location: {response['location_name']}")
                if response.get('assigned_asset_manager_id') is None:
                    print("     ✅ Asset Manager correctly null")
        
        # Test 3: Requisition routing when no Asset Definitions have Asset Manager assigned
        # This tests the fallback routing logic
        requisition_fallback_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Testing fallback routing when no Asset Manager assigned to Asset Definitions",
            "required_by_date": (datetime.now() + timedelta(days=5)).isoformat()
        }
        
        success, response = self.run_test(
            "Edge Case 3: Create Requisition for Fallback Routing Test",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_fallback_data,
            user_role="Employee"
        )
        
        if success:
            fallback_req_id = response['id']
            print(f"   ✅ Created fallback test requisition: {fallback_req_id}")
            
            # Approve it to trigger routing
            approval_data = {
                "action": "approve",
                "reason": "Testing fallback routing logic"
            }
            
            success, response = self.run_test(
                "Edge Case 3: Approve for Fallback Routing",
                "POST",
                f"asset-requisitions/{fallback_req_id}/manager-action",
                200,
                data=approval_data,
                user_role="Manager"
            )
            
            if success:
                print("   ✅ Fallback routing approval successful")
                
                # Check routing reason to understand fallback logic
                routing_reason = response.get('routing_reason', '')
                if 'fallback' in routing_reason.lower():
                    print(f"   ✅ Fallback routing triggered: {routing_reason}")
                elif response.get('assigned_to'):
                    print(f"   ✅ Routing successful: {routing_reason}")
                else:
                    print("   ❌ No routing occurred")

    def run_comprehensive_test(self):
        """Run all restructured asset management tests"""
        print("🚀 Starting Comprehensive Restructured Asset Management System Testing")
        print("=" * 80)
        
        # Login all required users
        users_to_login = [
            ("admin@company.com", "password123", "Administrator"),
            ("hr@company.com", "password123", "HR Manager"),
            ("manager@company.com", "password123", "Manager"),
            ("employee@company.com", "password123", "Employee"),
            ("assetmanager@company.com", "password123", "Asset Manager")
        ]
        
        login_success = True
        for email, password, role in users_to_login:
            if not self.test_login(email, password, role):
                login_success = False
        
        if not login_success:
            print("❌ Some logins failed. Cannot proceed with testing.")
            return
        
        print(f"\n✅ All users logged in successfully")
        
        # Run tests in priority order
        try:
            self.test_asset_type_restructured_crud()
            self.test_asset_definition_enhanced_crud()
            self.test_enhanced_allocation_routing()
            self.test_data_consistency()
            self.test_edge_cases()
            
        except Exception as e:
            print(f"\n❌ Test execution error: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 RESTRUCTURED ASSET MANAGEMENT TESTING SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Restructured Asset Management System is working correctly.")
        else:
            print("⚠️ Some tests failed. Please review the output above for details.")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = RestructuredAssetManagementTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)