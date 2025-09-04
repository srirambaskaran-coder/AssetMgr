#!/usr/bin/env python3
"""
Enhanced Asset Allocation Routing Logic Test
Tests the location-based routing system for approved asset requisitions
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class RoutingLogicTester:
    def __init__(self, base_url="https://asset-track-2.preview.emergentagent.com"):
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

    def test_enhanced_asset_allocation_routing(self):
        """Test Enhanced Asset Allocation Logic with location-based routing system"""
        print(f"\n🎯 Testing Enhanced Asset Allocation Logic with Location-Based Routing")
        
        # Step 1: Setup verification - Create test data
        print("📋 Step 1: Setting up test data for routing logic")
        
        # Create test locations
        location_data_1 = {
            "code": f"TEST{datetime.now().strftime('%H%M%S')}",
            "name": "Test Routing Office",
            "country": "USA",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Test Location",
            "POST",
            "locations",
            200,
            data=location_data_1,
            user_role="Administrator"
        )
        
        if success:
            self.test_data['location_id'] = response['id']
            print(f"   Created location: {response['name']} ({response['code']})")
        else:
            print("❌ Failed to create test location - cannot proceed with routing tests")
            return False
        
        # Create test employee with location
        test_employee_data = {
            "email": f"routing_test_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Routing Test Employee",
            "roles": ["Employee"],
            "designation": "Software Developer",
            "location_id": self.test_data['location_id'],
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
            self.test_data['employee_id'] = response['id']
            self.test_data['employee_email'] = response['email']
            print(f"   Created test employee: {response['name']} at {response.get('location_name', 'Unknown')}")
        else:
            print("❌ Failed to create test employee")
            return False
        
        # Create test Asset Manager with same location
        test_asset_manager_data = {
            "email": f"routing_am_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Routing Test Asset Manager",
            "roles": ["Asset Manager"],
            "designation": "Asset Manager",
            "location_id": self.test_data['location_id'],
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
            self.test_data['asset_manager_id'] = response['id']
            print(f"   Created test asset manager: {response['name']} at {response.get('location_name', 'Unknown')}")
        else:
            print("❌ Failed to create test asset manager")
            return False
        
        # Assign Asset Manager to location
        am_location_data = {
            "asset_manager_id": self.test_data['asset_manager_id'],
            "location_id": self.test_data['location_id']
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
        else:
            print("❌ Failed to assign Asset Manager to location")
            return False
        
        # Create asset type with assigned Asset Manager
        routing_asset_type_data = {
            "code": f"ROUTE{datetime.now().strftime('%H%M%S')}",
            "name": "Routing Test Asset Type",
            "depreciation_applicable": True,
            "asset_life": 3,
            "to_be_recovered_on_separation": True,
            "status": "Active",
            "assigned_asset_manager_id": self.test_data['asset_manager_id']
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
            self.test_data['asset_type_id'] = response['id']
            print(f"   Created asset type with assigned Asset Manager: {response['name']}")
        else:
            print("❌ Failed to create asset type")
            return False
        
        # Step 2: Test Primary Routing - Asset Manager with asset type + location match
        print("\n🎯 Step 2: Testing Primary Routing Logic")
        
        # Login as test employee to create requisition
        employee_login_success = self.test_login(
            self.test_data['employee_email'], 
            "TestPassword123!", 
            "Test_Employee"
        )
        
        if not employee_login_success:
            print("❌ Failed to login as test employee")
            return False
        
        # Create asset requisition
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        routing_requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
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
            user_role="Test_Employee"
        )
        
        if success:
            self.test_data['requisition_id'] = response['id']
            print(f"   Created requisition for routing test: {response['id'][:8]}...")
        else:
            print("❌ Failed to create requisition")
            return False
        
        # Manager approval to trigger routing
        manager_action_data = {
            "action": "approve",
            "reason": "Approved for routing logic testing"
        }
        
        success, response = self.run_test(
            "Manager Approve Requisition (Trigger Routing)",
            "POST",
            f"asset-requisitions/{self.test_data['requisition_id']}/manager-action",
            200,
            data=manager_action_data,
            user_role="Administrator"  # Using Administrator as they can approve any request
        )
        
        if success:
            print(f"   Manager approved requisition - routing should be triggered")
        else:
            print("❌ Failed to approve requisition")
            return False
        
        # Verify routing results by getting all requisitions and finding ours
        success, response = self.run_test(
            "Get All Requisitions to Verify Primary Routing Results",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            # Find our requisition in the list
            requisition = None
            for req in response:
                if req.get('id') == self.test_data['requisition_id']:
                    requisition = req
                    break
            
            if not requisition:
                print("❌ Could not find our requisition in the list")
                return False
            
            status = requisition.get('status')
            assigned_to = requisition.get('assigned_to')
            assigned_to_name = requisition.get('assigned_to_name')
            routing_reason = requisition.get('routing_reason')
            assigned_date = requisition.get('assigned_date')
            
            print(f"   Status: {status}")
            print(f"   Assigned to: {assigned_to_name} ({assigned_to})")
            print(f"   Routing reason: {routing_reason}")
            print(f"   Assigned date: {assigned_date}")
            
            # Verify routing worked correctly
            routing_success = True
            
            if status == "Assigned for Allocation":
                print("   ✅ Primary routing successful - Status set to 'Assigned for Allocation'")
            else:
                print(f"   ❌ Primary routing failed - Expected 'Assigned for Allocation', got '{status}'")
                routing_success = False
            
            if assigned_to == self.test_data.get('asset_manager_id'):
                print("   ✅ Primary routing successful - Assigned to correct Asset Manager")
            else:
                print(f"   ❌ Primary routing failed - Not assigned to expected Asset Manager")
                routing_success = False
            
            if routing_reason and "assigned to asset type and employee location" in routing_reason:
                print("   ✅ Primary routing reason correct")
            else:
                print(f"   ❌ Primary routing reason incorrect: {routing_reason}")
                routing_success = False
            
            if assigned_date:
                print("   ✅ Assigned date set correctly")
            else:
                print("   ❌ Assigned date not set")
                routing_success = False
            
            return routing_success
        else:
            print("❌ Failed to verify routing results")
            return False

    def test_secondary_routing(self):
        """Test secondary routing logic (Administrator fallback)"""
        print("\n🎯 Step 3: Testing Secondary Routing Logic (Administrator fallback)")
        
        # Create asset type without assigned Asset Manager
        secondary_asset_type_data = {
            "code": f"SEC{datetime.now().strftime('%H%M%S')}",
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
        else:
            print("❌ Failed to create secondary asset type")
            return False
        
        # Create Administrator and assign to same location as employee
        test_admin_data = {
            "email": f"routing_admin_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Routing Test Administrator",
            "roles": ["Administrator"],
            "designation": "System Administrator",
            "location_id": self.test_data.get('location_id'),
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
            self.test_data['admin_id'] = response['id']
            print(f"   Created test administrator: {response['name']}")
        else:
            print("❌ Failed to create test administrator")
            return False
        
        # Note: We can't assign Administrator to location via asset-manager-locations endpoint
        # as it requires Asset Manager role. The secondary routing will test fallback to any Administrator
        print(f"   Note: Administrator cannot be assigned to location via asset-manager-locations endpoint")
        print(f"   This will test the final fallback routing to any Administrator")
        
        # Create requisition with secondary asset type
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
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
            user_role="Test_Employee"
        )
        
        if success:
            self.test_data['secondary_requisition_id'] = response['id']
            print(f"   Created secondary requisition: {response['id'][:8]}...")
        else:
            print("❌ Failed to create secondary requisition")
            return False
        
        # Manager approval to trigger secondary routing
        manager_action_data = {
            "action": "approve",
            "reason": "Approved for secondary routing logic testing"
        }
        
        success, response = self.run_test(
            "Manager Approve Secondary Requisition (Trigger Secondary Routing)",
            "POST",
            f"asset-requisitions/{self.test_data['secondary_requisition_id']}/manager-action",
            200,
            data=manager_action_data,
            user_role="Administrator"
        )
        
        if success:
            print(f"   Manager approved secondary requisition - routing should be triggered")
        else:
            print("❌ Failed to approve secondary requisition")
            return False
        
        # Verify secondary routing results by getting all requisitions
        success, response = self.run_test(
            "Get All Requisitions to Verify Secondary Routing Results",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            # Find our secondary requisition in the list
            requisition = None
            for req in response:
                if req.get('id') == self.test_data['secondary_requisition_id']:
                    requisition = req
                    break
            
            if not requisition:
                print("❌ Could not find our secondary requisition in the list")
                return False
            
            status = requisition.get('status')
            assigned_to = requisition.get('assigned_to')
            assigned_to_name = requisition.get('assigned_to_name')
            routing_reason = requisition.get('routing_reason')
            
            print(f"   Status: {status}")
            print(f"   Assigned to: {assigned_to_name} ({assigned_to})")
            print(f"   Routing reason: {routing_reason}")
            
            routing_success = True
            
            if status == "Assigned for Allocation":
                print("   ✅ Secondary routing successful - Status set correctly")
            else:
                print(f"   ❌ Secondary routing failed - Expected 'Assigned for Allocation', got '{status}'")
                routing_success = False
            
            # Since we couldn't assign Administrator to location, this should fall back to general Administrator
            if assigned_to:
                print("   ✅ Secondary routing successful - Assigned to an Administrator")
            else:
                print(f"   ❌ Secondary routing failed - No assignment made")
                routing_success = False
            
            if routing_reason and ("general fallback" in routing_reason or "assigned to employee location" in routing_reason):
                print("   ✅ Secondary routing reason correct")
            else:
                print(f"   ❌ Secondary routing reason incorrect: {routing_reason}")
                routing_success = False
            
            return routing_success
        else:
            print("❌ Failed to verify secondary routing results")
            return False

    def test_edge_cases(self):
        """Test edge cases for routing logic"""
        print("\n🎯 Step 4: Testing Edge Cases")
        
        # Test rejection doesn't trigger routing
        edge_case_requisition_data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Testing edge case - rejection should not trigger routing",
            "required_by_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        success, response = self.run_test(
            "Create Requisition for Edge Case Test",
            "POST",
            "asset-requisitions",
            200,
            data=edge_case_requisition_data,
            user_role="Test_Employee"
        )
        
        if success:
            edge_case_req_id = response['id']
            print(f"   Created edge case requisition: {edge_case_req_id[:8]}...")
        else:
            print("❌ Failed to create edge case requisition")
            return False
        
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
            user_role="Administrator"
        )
        
        if success:
            print(f"   Manager rejected requisition - routing should NOT be triggered")
        else:
            print("❌ Failed to reject requisition")
            return False
        
        # Verify no routing occurred by getting all requisitions
        success, response = self.run_test(
            "Get All Requisitions to Verify No Routing on Rejection",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            # Find our edge case requisition in the list
            requisition = None
            for req in response:
                if req.get('id') == edge_case_req_id:
                    requisition = req
                    break
            
            if not requisition:
                print("❌ Could not find our edge case requisition in the list")
                return False
            
            status = requisition.get('status')
            assigned_to = requisition.get('assigned_to')
            routing_reason = requisition.get('routing_reason')
            
            print(f"   Status: {status}")
            print(f"   Assigned to: {assigned_to}")
            print(f"   Routing reason: {routing_reason}")
            
            edge_case_success = True
            
            if status == "Rejected":
                print("   ✅ Edge case successful - Rejection does not trigger routing")
            else:
                print(f"   ❌ Edge case failed - Expected 'Rejected', got '{status}'")
                edge_case_success = False
            
            if not assigned_to:
                print("   ✅ Edge case successful - No assignment on rejection")
            else:
                print(f"   ❌ Edge case failed - Assignment occurred on rejection: {assigned_to}")
                edge_case_success = False
            
            return edge_case_success
        else:
            print("❌ Failed to verify edge case results")
            return False

    def run_all_routing_tests(self):
        """Run all routing tests"""
        print("🚀 Starting Enhanced Asset Allocation Routing Logic Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Test authentication for required roles
        auth_success = True
        test_users = [
            ("admin@company.com", "password123", "Administrator"),
            ("manager@company.com", "password123", "Manager"),
            ("employee@company.com", "password123", "Employee"),
            ("assetmanager@company.com", "password123", "Asset Manager")
        ]
        
        for email, password, role in test_users:
            if not self.test_login(email, password, role):
                auth_success = False
        
        if not auth_success:
            print("\n❌ Authentication failed for some users. Stopping tests.")
            return False
        
        # Run routing tests
        test_results = []
        
        # Test 1: Primary routing logic
        result1 = self.test_enhanced_asset_allocation_routing()
        test_results.append(("Primary Routing Logic", result1))
        
        # Test 2: Secondary routing logic
        result2 = self.test_secondary_routing()
        test_results.append(("Secondary Routing Logic", result2))
        
        # Test 3: Edge cases
        result3 = self.test_edge_cases()
        test_results.append(("Edge Cases", result3))
        
        # Print final results
        print("\n" + "=" * 80)
        print("🏁 ENHANCED ASSET ALLOCATION ROUTING TESTS COMPLETED")
        print("=" * 80)
        print(f"📊 Total Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print("\n📋 Test Results Summary:")
        all_passed = True
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 ALL ROUTING TESTS PASSED! Enhanced Asset Allocation Logic is working correctly.")
        else:
            print("\n⚠️ Some routing tests failed. Please review the output above.")
        
        print("=" * 80)
        return all_passed

def main():
    tester = RoutingLogicTester()
    success = tester.run_all_routing_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())