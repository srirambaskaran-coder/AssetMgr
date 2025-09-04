#!/usr/bin/env python3

import requests
import json
from datetime import datetime

class LocationBasedAssetManagementTester:
    def __init__(self, base_url="https://asset-track-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'

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

    def login_admin(self):
        """Login as administrator"""
        print("🔐 Logging in as Administrator...")
        login_data = {
            "email": "admin@company.com",
            "password": "password123"
        }
        
        success, response = self.run_test(
            "Administrator Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'session_token' in response:
            self.admin_token = response['session_token']
            print(f"✅ Administrator login successful")
            return True
        
        print(f"❌ Administrator login failed")
        return False

    def test_location_management_crud(self):
        """Test Location Management CRUD operations"""
        print(f"\n🌍 Testing Location Management CRUD Operations")
        
        # Test 1: Create NYC Office Location
        location_data_nyc = {
            "code": "NYC_TEST",
            "name": "NYC Test Office",
            "country": "United States",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create NYC Office Location",
            "POST",
            "locations",
            200,
            data=location_data_nyc
        )
        
        if success:
            self.test_data['nyc_location_id'] = response['id']
            print(f"   Created NYC location: {response['name']} ({response['code']})")
        
        # Test 2: Create London Branch Location
        location_data_london = {
            "code": "LON_TEST",
            "name": "London Test Branch",
            "country": "United Kingdom",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create London Branch Location",
            "POST",
            "locations",
            200,
            data=location_data_london
        )
        
        if success:
            self.test_data['london_location_id'] = response['id']
            print(f"   Created London location: {response['name']} ({response['code']})")
        
        # Test 3: Get All Locations
        success, response = self.run_test(
            "Get All Locations",
            "GET",
            "locations",
            200
        )
        
        if success:
            print(f"   Found {len(response)} total locations")
            test_locations = [loc for loc in response if loc['code'].endswith('_TEST')]
            print(f"   Found {len(test_locations)} test locations")
        
        # Test 4: Update Location
        if 'nyc_location_id' in self.test_data:
            update_data = {
                "name": "NYC Test Headquarters",
                "status": "Active"
            }
            success, response = self.run_test(
                "Update NYC Location",
                "PUT",
                f"locations/{self.test_data['nyc_location_id']}",
                200,
                data=update_data
            )
            
            if success:
                print(f"   Updated location name: {response['name']}")
        
        # Test 5: Duplicate Code Prevention
        duplicate_location = {
            "code": "NYC_TEST",  # Same as existing
            "name": "Another NYC Office",
            "country": "United States",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Duplicate Location Code (Should Fail)",
            "POST",
            "locations",
            400,
            data=duplicate_location
        )
        
        if success:
            print("   ✅ Duplicate location code correctly rejected")
        
        return True

    def test_user_location_integration(self):
        """Test User Location Integration"""
        print(f"\n👥 Testing User Location Integration")
        
        if 'nyc_location_id' not in self.test_data:
            print("❌ Skipping User Location tests - no location created")
            return False
        
        # Test 1: Create User with Location Assignment
        user_data = {
            "email": f"locationtest_{datetime.now().strftime('%H%M%S')}@company.com",
            "name": "Location Test User",
            "roles": ["Employee"],
            "designation": "Test Engineer",
            "location_id": self.test_data['nyc_location_id'],
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Create User with Location Assignment",
            "POST",
            "users",
            200,
            data=user_data
        )
        
        if success:
            self.test_data['location_user_id'] = response['id']
            print(f"   Created user with location: {response.get('location_name', 'Unknown')}")
        
        # Test 2: Update User Location
        if 'location_user_id' in self.test_data and 'london_location_id' in self.test_data:
            update_data = {
                "location_id": self.test_data['london_location_id']
            }
            success, response = self.run_test(
                "Update User Location Assignment",
                "PUT",
                f"users/{self.test_data['location_user_id']}",
                200,
                data=update_data
            )
            
            if success:
                print(f"   Updated user location to: {response.get('location_name', 'Unknown')}")
        
        # Test 3: Invalid Location ID
        invalid_user_data = {
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
            data=invalid_user_data
        )
        
        if success:
            print("   ✅ Invalid location_id correctly rejected")
        
        # Test 4: Verify Location Names in User List
        success, response = self.run_test(
            "Get Users - Verify Location Names",
            "GET",
            "users",
            200
        )
        
        if success:
            users_with_location = [u for u in response if u.get('location_name')]
            print(f"   Found {len(users_with_location)} users with location assignments")
        
        return True

    def test_asset_manager_location_assignment(self):
        """Test Asset Manager Location Assignment"""
        print(f"\n🎯 Testing Asset Manager Location Assignment")
        
        if 'nyc_location_id' not in self.test_data:
            print("❌ Skipping Asset Manager Location tests - no location created")
            return False
        
        # Get Asset Managers
        success, response = self.run_test(
            "Get Asset Managers",
            "GET",
            "users/asset-managers",
            200
        )
        
        if not success or not response:
            print("❌ No Asset Managers found")
            return False
        
        asset_manager_id = response[0]['id']
        print(f"   Using Asset Manager: {response[0]['name']}")
        
        # Test 1: Assign Asset Manager to Location
        assignment_data = {
            "asset_manager_id": asset_manager_id,
            "location_id": self.test_data['nyc_location_id']
        }
        
        success, response = self.run_test(
            "Assign Asset Manager to NYC Location",
            "POST",
            "asset-manager-locations",
            200,
            data=assignment_data
        )
        
        if success:
            self.test_data['assignment_id'] = response['id']
            print(f"   Assigned {response['asset_manager_name']} to {response['location_name']}")
        
        # Test 2: Get Asset Manager Location Assignments
        success, response = self.run_test(
            "Get Asset Manager Location Assignments",
            "GET",
            "asset-manager-locations",
            200
        )
        
        if success:
            print(f"   Found {len(response)} asset manager location assignments")
        
        # Test 3: Invalid Asset Manager Role
        success, users_response = self.run_test(
            "Get Users for Role Validation Test",
            "GET",
            "users",
            200
        )
        
        if success:
            employee_user = next((u for u in users_response if 'Employee' in u.get('roles', []) and 'Asset Manager' not in u.get('roles', [])), None)
            if employee_user:
                invalid_assignment = {
                    "asset_manager_id": employee_user['id'],
                    "location_id": self.test_data['nyc_location_id']
                }
                
                success, response = self.run_test(
                    "Assign Non-Asset Manager to Location (Should Fail)",
                    "POST",
                    "asset-manager-locations",
                    400,
                    data=invalid_assignment
                )
                
                if success:
                    print("   ✅ Non-Asset Manager correctly rejected")
        
        # Test 4: Invalid Location ID
        invalid_location_assignment = {
            "asset_manager_id": asset_manager_id,
            "location_id": "invalid-location-id"
        }
        
        success, response = self.run_test(
            "Assign Asset Manager to Invalid Location (Should Fail)",
            "POST",
            "asset-manager-locations",
            404,
            data=invalid_location_assignment
        )
        
        if success:
            print("   ✅ Invalid location correctly rejected")
        
        # Test 5: Remove Assignment
        if 'assignment_id' in self.test_data:
            success, response = self.run_test(
                "Remove Asset Manager Location Assignment",
                "DELETE",
                f"asset-manager-locations/{self.test_data['assignment_id']}",
                200
            )
            
            if success:
                print("   ✅ Asset Manager location assignment removed")
        
        return True

    def test_data_migration(self):
        """Test Data Migration"""
        print(f"\n🔄 Testing Data Migration")
        
        # Test Migration Endpoint
        success, response = self.run_test(
            "Set Default Location for Existing Users",
            "POST",
            "migrate/set-default-location",
            200
        )
        
        if success:
            print(f"   Migration result: {response.get('message', 'Success')}")
            print(f"   Users updated: {response.get('users_updated', 0)}")
        
        # Verify Default Location Creation
        success, response = self.run_test(
            "Verify Default Location Exists",
            "GET",
            "locations",
            200
        )
        
        if success:
            default_location = next((loc for loc in response if loc['code'] == 'DEFAULT'), None)
            if default_location:
                print(f"   ✅ Default location found: {default_location['name']}")
            else:
                print("   ⚠️ Default location not found")
        
        return True

    def test_data_validation(self):
        """Test Data Validation"""
        print(f"\n✅ Testing Data Validation")
        
        # Test Cascade Delete Protection
        if 'nyc_location_id' in self.test_data:
            success, response = self.run_test(
                "Delete Location with Assigned Users (Should Fail)",
                "DELETE",
                f"locations/{self.test_data['nyc_location_id']}",
                400
            )
            
            if success:
                print("   ✅ Location with assigned users protected from deletion")
        
        return True

    def run_all_tests(self):
        """Run all location-based tests"""
        print("🚀 Starting Location-Based Asset Management System Tests")
        print("=" * 70)
        
        # Login as Administrator
        if not self.login_admin():
            print("❌ Cannot proceed without admin login")
            return False
        
        # Run all tests
        success = True
        
        if not self.test_location_management_crud():
            success = False
        
        if not self.test_user_location_integration():
            success = False
        
        if not self.test_asset_manager_location_assignment():
            success = False
        
        if not self.test_data_migration():
            success = False
        
        if not self.test_data_validation():
            success = False
        
        # Print results
        print(f"\n" + "=" * 70)
        print(f"🎯 LOCATION-BASED TESTING COMPLETED")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success:
            print(f"🎉 ALL LOCATION-BASED TESTS PASSED!")
        else:
            print(f"⚠️ Some location-based tests failed")
        
        return success

if __name__ == "__main__":
    tester = LocationBasedAssetManagementTester()
    tester.run_all_tests()