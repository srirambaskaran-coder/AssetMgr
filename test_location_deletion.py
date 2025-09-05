#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class LocationDeletionTester:
    def __init__(self, base_url="https://resource-manager-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add auth header if admin token available
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
        """Login as Administrator"""
        print(f"\n🔐 Logging in as Administrator...")
        success, response = self.run_test(
            "Administrator Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@company.com", "password": "password123"}
        )
        
        if success and 'session_token' in response:
            self.admin_token = response['session_token']
            print(f"✅ Administrator login successful")
            return True
        
        print(f"❌ Administrator login failed")
        return False

    def test_delete_specific_test_locations(self):
        """Test deletion of specific test locations by their codes"""
        print(f"\n🗑️ DELETE SPECIFIC TEST LOCATIONS")
        print("=" * 50)
        
        # Target location codes to delete
        target_codes = ["TEST124613", "TEST124810", "TEST124853"]
        
        # Step 1: Authentication as Administrator
        print("Step 1: Authentication as Administrator")
        if not self.admin_token:
            print("❌ Administrator not authenticated. Cannot proceed with location deletion.")
            return False
        
        # Step 2: Get all locations to find target locations
        print("\nStep 2: Finding target locations...")
        success, response = self.run_test(
            "Get All Locations to Find Targets",
            "GET",
            "locations",
            200
        )
        
        if not success:
            print("❌ Failed to retrieve locations list")
            return False
        
        print(f"Found {len(response)} total locations in system")
        
        # Find target locations by code
        target_locations = {}
        for location in response:
            if location.get('code') in target_codes:
                target_locations[location['code']] = location
                print(f"✅ Found target location: {location['code']} - {location['name']} (ID: {location['id']})")
        
        # Check which target codes were not found
        missing_codes = [code for code in target_codes if code not in target_locations]
        if missing_codes:
            print(f"⚠️ Target location codes not found: {missing_codes}")
        
        if not target_locations:
            print("⚠️ None of the target location codes were found in the system")
            print("This is not an error - the locations may have already been deleted or never existed")
            return True  # Not an error if locations don't exist
        
        # Step 3: Display current location details before deletion
        print("\nStep 3: Current location details before deletion:")
        for code, location in target_locations.items():
            print(f"  - Code: {location['code']}")
            print(f"    Name: {location['name']}")
            print(f"    Country: {location['country']}")
            print(f"    Status: {location['status']}")
            print(f"    ID: {location['id']}")
        
        # Step 3.5: Check and remove asset manager assignments for these locations
        print("\nStep 3.5: Checking and removing asset manager assignments...")
        success, am_assignments = self.run_test(
            "Get Asset Manager Location Assignments",
            "GET",
            "asset-manager-locations",
            200
        )
        
        if success:
            target_location_ids = [loc['id'] for loc in target_locations.values()]
            assignments_to_remove = []
            
            for assignment in am_assignments:
                if assignment.get('location_id') in target_location_ids:
                    assignments_to_remove.append(assignment)
                    print(f"  Found assignment: {assignment.get('asset_manager_name')} -> {assignment.get('location_name')}")
            
            # Remove assignments
            for assignment in assignments_to_remove:
                success, response = self.run_test(
                    f"Remove Asset Manager Assignment {assignment['id']}",
                    "DELETE",
                    f"asset-manager-locations/{assignment['id']}",
                    200
                )
                
                if success:
                    print(f"  ✅ Removed assignment: {assignment.get('asset_manager_name')} from {assignment.get('location_name')}")
                else:
                    print(f"  ❌ Failed to remove assignment: {assignment.get('asset_manager_name')} from {assignment.get('location_name')}")
        
        # Step 4: Delete each found location
        print("\nStep 4: Deleting target locations...")
        deletion_results = {}
        
        for code, location in target_locations.items():
            location_id = location['id']
            success, response = self.run_test(
                f"Delete Location {code}",
                "DELETE",
                f"locations/{location_id}",
                200  # Expecting successful deletion
            )
            
            deletion_results[code] = success
            if success:
                print(f"✅ Successfully deleted location {code} (ID: {location_id})")
            else:
                print(f"❌ Failed to delete location {code} (ID: {location_id})")
        
        # Step 5: Verification - Get locations list again to confirm deletions
        print("\nStep 5: Verifying deletions...")
        success, response = self.run_test(
            "Verify Locations After Deletion",
            "GET",
            "locations",
            200
        )
        
        if success:
            remaining_codes = [loc['code'] for loc in response]
            print(f"Remaining locations in system: {len(response)}")
            
            # Check that deleted locations are no longer in the list
            still_present = []
            for code in target_locations.keys():
                if code in remaining_codes:
                    still_present.append(code)
            
            if still_present:
                print(f"❌ Locations still present after deletion: {still_present}")
            else:
                print("✅ All target locations successfully removed from the system")
        
        # Step 6: Summary of deletion results
        print("\nStep 6: Deletion Summary:")
        successful_deletions = [code for code, success in deletion_results.items() if success]
        failed_deletions = [code for code, success in deletion_results.items() if not success]
        
        print(f"  Total target locations found: {len(target_locations)}")
        print(f"  Successfully deleted: {len(successful_deletions)} - {successful_deletions}")
        if failed_deletions:
            print(f"  Failed to delete: {len(failed_deletions)} - {failed_deletions}")
        if missing_codes:
            print(f"  Not found in system: {len(missing_codes)} - {missing_codes}")
        
        # Return True if all found locations were successfully deleted
        all_successful = len(failed_deletions) == 0
        if all_successful:
            print("\n🎉 Location deletion task completed successfully!")
        else:
            print("\n⚠️ Some location deletions failed")
        
        return all_successful

def main():
    print("🚀 LOCATION DELETION TEST")
    print("=" * 60)
    
    tester = LocationDeletionTester()
    
    # Login as Administrator
    if not tester.login_admin():
        print("\n❌ Failed to login as Administrator. Cannot proceed.")
        return 1
    
    # Run the location deletion test
    result = tester.test_delete_specific_test_locations()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if result:
        print("🎉 Location deletion task completed successfully!")
        return 0
    else:
        print("⚠️ Location deletion task had issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())