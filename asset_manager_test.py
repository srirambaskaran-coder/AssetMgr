#!/usr/bin/env python3
"""
Asset Manager Focused Test Suite
Tests the complete Asset Manager workflow including:
1. Asset Manager authentication and dashboard
2. Asset allocation from approved requisitions
3. Asset retrieval for employee separation
4. Role-based access control
"""

import requests
import sys
import json
from datetime import datetime

class AssetManagerTester:
    def __init__(self, base_url="https://inventree-6.preview.emergentagent.com"):
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

    def login_users(self):
        """Login all required users"""
        users = [
            ("admin@company.com", "password123", "Administrator"),
            ("hr@company.com", "password123", "HR Manager"),
            ("manager@company.com", "password123", "Manager"),
            ("employee@company.com", "password123", "Employee"),
            ("assetmanager@company.com", "password123", "Asset Manager")
        ]
        
        print("🔐 Logging in users...")
        for email, password, role in users:
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json={"email": email, "password": password})
            if response.status_code == 200:
                data = response.json()
                self.tokens[role] = data['session_token']
                self.users[role] = data['user']
                print(f"✅ {role} logged in successfully")
            else:
                print(f"❌ {role} login failed")
                return False
        return True

    def setup_test_data(self):
        """Set up test data for Asset Manager workflow"""
        print("\n📋 Setting up test data...")
        
        # Get existing asset types and definitions
        headers = {'Authorization': f'Bearer {self.tokens["Administrator"]}'}
        
        # Get asset types
        response = requests.get(f"{self.api_url}/asset-types", headers=headers)
        if response.status_code == 200:
            asset_types = response.json()
            if asset_types:
                self.test_data['asset_type_id'] = asset_types[0]['id']
                print(f"✅ Using asset type: {asset_types[0]['name']}")
        
        # Get asset definitions
        response = requests.get(f"{self.api_url}/asset-definitions", headers=headers)
        if response.status_code == 200:
            asset_defs = response.json()
            available_assets = [ad for ad in asset_defs if ad['status'] == 'Available']
            if available_assets:
                self.test_data['asset_def_id'] = available_assets[0]['id']
                print(f"✅ Using asset definition: {available_assets[0]['asset_code']}")
        
        # Create a test requisition
        if 'asset_type_id' in self.test_data:
            employee_headers = {'Authorization': f'Bearer {self.tokens["Employee"]}'}
            requisition_data = {
                "asset_type_id": self.test_data['asset_type_id'],
                "justification": "Need laptop for Asset Manager testing workflow"
            }
            
            response = requests.post(f"{self.api_url}/asset-requisitions", 
                                   json=requisition_data, headers=employee_headers)
            if response.status_code == 200:
                requisition = response.json()
                self.test_data['requisition_id'] = requisition['id']
                print(f"✅ Created test requisition: {requisition['id']}")
                
                # Approve the requisition (simulate manager approval)
                # Note: In a real scenario, this would be done through proper approval workflow
                print("   📝 Requisition created and ready for approval workflow")
        
        return len(self.test_data) >= 2  # Need at least asset_type_id and asset_def_id

    def test_asset_manager_dashboard(self):
        """Test Asset Manager dashboard statistics"""
        print("\n📊 Testing Asset Manager Dashboard")
        
        success, response = self.run_test(
            "Asset Manager Dashboard Stats",
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
            
            print("   Dashboard Statistics:")
            for key in expected_keys:
                if key in response:
                    print(f"     {key}: {response[key]}")
                else:
                    print(f"     ❌ Missing: {key}")
            
            # Check asset type breakdown
            if "asset_type_breakdown" in response:
                print("   Asset Type Breakdown:")
                for item in response["asset_type_breakdown"]:
                    print(f"     {item['_id']}: Total={item['total']}, Available={item['available']}, Allocated={item['allocated']}")
        
        return success

    def test_asset_allocations(self):
        """Test Asset Allocation functionality"""
        print("\n🎯 Testing Asset Allocation Operations")
        
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
            if response:
                print("   Pending allocations details:")
                for req in response[:3]:  # Show first 3
                    print(f"     ID: {req['id']}, Status: {req['status']}, Asset Type: {req.get('asset_type_name', 'N/A')}")
        
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
        
        # Test Create Asset Allocation (if we have test data)
        if 'requisition_id' in self.test_data and 'asset_def_id' in self.test_data:
            allocation_data = {
                "requisition_id": self.test_data['requisition_id'],
                "asset_definition_id": self.test_data['asset_def_id'],
                "remarks": "Allocated for Asset Manager testing",
                "reference_id": "AM-TEST-001",
                "document_id": "DOC-AM-001",
                "dispatch_details": "Test dispatch via automated testing"
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
                print(f"   ✅ Created allocation: {response['id']}")
                print(f"   Status: {response.get('status', 'Unknown')}")
                print(f"   Allocated to: {response.get('requested_for_name', 'Unknown')}")
            else:
                print("   ⚠️ Could not create allocation - may need approved requisition")
        
        return success

    def test_asset_retrievals(self):
        """Test Asset Retrieval functionality"""
        print("\n🔄 Testing Asset Retrieval Operations")
        
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
        
        # Test Create Asset Retrieval (if we have allocated asset)
        if 'asset_def_id' in self.test_data:
            employee_id = self.users.get("Employee", {}).get("id")
            if employee_id:
                retrieval_data = {
                    "employee_id": employee_id,
                    "asset_definition_id": self.test_data['asset_def_id'],
                    "remarks": "Employee separation - testing asset retrieval workflow"
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
                    print(f"   ✅ Created retrieval: {response['id']}")
                    print(f"   Employee: {response.get('employee_name', 'Unknown')}")
                    print(f"   Asset: {response.get('asset_definition_code', 'Unknown')}")
                    
                    # Test Update Asset Retrieval
                    update_data = {
                        "recovered": True,
                        "asset_condition": "Good Condition",
                        "recovery_value": 0.0,
                        "remarks": "Asset recovered in excellent condition during testing",
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
                        print(f"   ✅ Updated retrieval status: {response.get('status', 'Unknown')}")
                        print(f"   Recovered: {response.get('recovered', False)}")
                        print(f"   Condition: {response.get('asset_condition', 'Unknown')}")
                else:
                    print("   ⚠️ Could not create retrieval - asset may not be allocated to employee")
        
        return success

    def test_access_control(self):
        """Test role-based access control for Asset Manager features"""
        print("\n🔒 Testing Asset Manager Access Control")
        
        # Test Asset Manager can access all endpoints
        am_endpoints = [
            ("asset-allocations", "GET"),
            ("pending-allocations", "GET"),
            ("allocated-assets", "GET"),
            ("asset-retrievals", "GET"),
            ("dashboard/asset-manager-stats", "GET")
        ]
        
        print("   Asset Manager Access Tests:")
        for endpoint, method in am_endpoints:
            success, response = self.run_test(
                f"Asset Manager {method} {endpoint}",
                method,
                endpoint,
                200,
                user_role="Asset Manager"
            )
            
            if success:
                print(f"     ✅ Can access {endpoint}")
        
        # Test other roles cannot access Asset Manager endpoints
        restricted_roles = ["Employee", "Manager"]
        restricted_endpoints = ["asset-allocations", "asset-retrievals", "dashboard/asset-manager-stats"]
        
        print("   Access Restriction Tests:")
        for role in restricted_roles:
            if role in self.tokens:
                for endpoint in restricted_endpoints:
                    success, response = self.run_test(
                        f"{role} access {endpoint} (Should Fail)",
                        "GET",
                        endpoint,
                        403,
                        user_role=role
                    )
                    
                    if success:
                        print(f"     ✅ {role} correctly denied access to {endpoint}")

    def test_business_workflow(self):
        """Test the complete business workflow"""
        print("\n🔄 Testing Complete Business Workflow")
        
        workflow_steps = [
            "1. Admin/HR creates asset types and definitions ✅",
            "2. Employee submits asset requisition ✅", 
            "3. Manager/HR approves requisition (simulated)",
            "4. Asset Manager allocates specific asset to employee",
            "5. Employee separation triggers asset retrieval process",
            "6. Asset Manager processes retrieval and updates condition"
        ]
        
        print("   Workflow Steps:")
        for step in workflow_steps:
            print(f"     {step}")
        
        # Check if we completed the key steps
        completed_steps = 0
        if 'requisition_id' in self.test_data:
            completed_steps += 1
            print("   ✅ Requisition creation completed")
        
        if 'allocation_id' in self.test_data:
            completed_steps += 1
            print("   ✅ Asset allocation completed")
        
        if 'retrieval_id' in self.test_data:
            completed_steps += 1
            print("   ✅ Asset retrieval completed")
        
        print(f"   Workflow completion: {completed_steps}/3 key steps completed")
        return completed_steps >= 2

def main():
    print("🎯 Asset Manager Focused Test Suite")
    print("=" * 50)
    
    tester = AssetManagerTester()
    
    # Step 1: Login all users
    if not tester.login_users():
        print("❌ Failed to login users")
        return 1
    
    # Step 2: Setup test data
    if not tester.setup_test_data():
        print("❌ Failed to setup test data")
        return 1
    
    # Step 3: Test Asset Manager Dashboard
    tester.test_asset_manager_dashboard()
    
    # Step 4: Test Asset Allocations
    tester.test_asset_allocations()
    
    # Step 5: Test Asset Retrievals
    tester.test_asset_retrievals()
    
    # Step 6: Test Access Control
    tester.test_access_control()
    
    # Step 7: Test Business Workflow
    tester.test_business_workflow()
    
    # Final Results
    print("\n" + "=" * 50)
    print(f"📊 ASSET MANAGER TEST RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All Asset Manager tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())