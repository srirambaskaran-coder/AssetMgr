import requests
import sys
from datetime import datetime, timedelta
import json

class EnhancedAssetRequisitionTester:
    def __init__(self, base_url="https://asset-flow-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.asset_type_id = None
        self.team_member_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)

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

    def test_login(self, email, password):
        """Test login and get token"""
        success, response = self.run_test(
            "Employee Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'session_token' in response:
            self.token = response['session_token']
            print(f"   Logged in as: {response['user']['name']} ({response['user']['role']})")
            return True
        return False

    def setup_test_data(self):
        """Setup required test data"""
        print("\n📋 Setting up test data...")
        
        # Get asset types
        success, response = self.run_test(
            "Get Asset Types",
            "GET",
            "asset-types",
            200
        )
        if success and response:
            self.asset_type_id = response[0]['id']
            print(f"   Using asset type: {response[0]['name']} (ID: {self.asset_type_id})")
        
        # Login as admin to get users for team member testing
        admin_success, admin_response = self.run_test(
            "Admin Login for User Lookup",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@company.com", "password": "password123"}
        )
        
        if admin_success:
            admin_token = admin_response['session_token']
            # Temporarily use admin token to get users
            original_token = self.token
            self.token = admin_token
            
            success, response = self.run_test(
                "Get Users",
                "GET",
                "users",
                200
            )
            
            # Restore employee token
            self.token = original_token
            
            if success and response:
                # Find a different user to use as team member
                for user in response:
                    if user['role'] in ['Employee', 'Manager'] and user['email'] != 'employee@company.com':
                        self.team_member_id = user['id']
                        print(f"   Using team member: {user['name']} (ID: {self.team_member_id})")
                        break

    def test_new_allocation_request(self):
        """Test creating a new allocation request"""
        if not self.asset_type_id:
            print("❌ Cannot test - No asset type available")
            return False
            
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        data = {
            "asset_type_id": self.asset_type_id,
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Need laptop for development work",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create New Allocation Request",
            "POST",
            "asset-requisitions",
            200,
            data=data
        )
        
        if success:
            print(f"   Created requisition ID: {response['id'][:8]}...")
            print(f"   Request type: {response['request_type']}")
            print(f"   Request for: {response['request_for']}")
            print(f"   Required by: {response.get('required_by_date', 'Not set')}")
            
            # Verify all enhanced fields are present
            enhanced_fields = ['request_type', 'request_for', 'required_by_date', 'reason_for_return_replacement', 'asset_details', 'team_member_employee_id', 'team_member_name']
            present_fields = [field for field in enhanced_fields if field in response]
            print(f"   Enhanced fields present: {present_fields}")
            
            return response['id']
        return None

    def test_replacement_request(self):
        """Test creating a replacement request with conditional fields"""
        if not self.asset_type_id:
            print("❌ Cannot test - No asset type available")
            return False
            
        required_by_date = (datetime.now() + timedelta(days=5)).isoformat()
        
        data = {
            "asset_type_id": self.asset_type_id,
            "request_type": "Replacement",
            "reason_for_return_replacement": "Current laptop screen is damaged and affecting productivity",
            "asset_details": "Dell Inspiron 15, Serial: DL123456, purchased 2022, screen has cracks",
            "request_for": "Self",
            "justification": "Need replacement laptop due to hardware failure",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Replacement Request",
            "POST",
            "asset-requisitions",
            200,
            data=data
        )
        
        if success:
            print(f"   Created requisition ID: {response['id'][:8]}...")
            print(f"   Request type: {response['request_type']}")
            print(f"   Reason: {response['reason_for_return_replacement'][:50]}...")
            print(f"   Asset details: {response['asset_details'][:50]}...")
            return response['id']
        return None

    def test_return_request(self):
        """Test creating a return request with conditional fields"""
        if not self.asset_type_id:
            print("❌ Cannot test - No asset type available")
            return False
            
        data = {
            "asset_type_id": self.asset_type_id,
            "request_type": "Return",
            "reason_for_return_replacement": "Project completed, no longer need this equipment",
            "asset_details": "MacBook Pro 16, Serial: MP789012, good condition, all accessories included",
            "request_for": "Self",
            "justification": "Returning equipment after project completion"
        }
        
        success, response = self.run_test(
            "Create Return Request",
            "POST",
            "asset-requisitions",
            200,
            data=data
        )
        
        if success:
            print(f"   Created requisition ID: {response['id'][:8]}...")
            print(f"   Request type: {response['request_type']}")
            print(f"   Reason: {response['reason_for_return_replacement'][:50]}...")
            return response['id']
        return None

    def test_team_member_request(self):
        """Test creating a request for team member"""
        if not self.asset_type_id or not self.team_member_id:
            print("❌ Cannot test - Missing asset type or team member")
            return False
            
        required_by_date = (datetime.now() + timedelta(days=10)).isoformat()
        
        data = {
            "asset_type_id": self.asset_type_id,
            "request_type": "New Allocation",
            "request_for": "Team Member",
            "team_member_employee_id": self.team_member_id,
            "justification": "New team member needs laptop for onboarding",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Team Member Request",
            "POST",
            "asset-requisitions",
            200,
            data=data
        )
        
        if success:
            print(f"   Created requisition ID: {response['id'][:8]}...")
            print(f"   Request for: {response['request_for']}")
            print(f"   Team member: {response.get('team_member_name', 'Unknown')}")
            return response['id']
        return None

    def test_validation_errors(self):
        """Test validation for conditional fields"""
        print("\n🔍 Testing validation errors...")
        
        # Test replacement without required fields
        data = {
            "asset_type_id": self.asset_type_id,
            "request_type": "Replacement",
            "request_for": "Self",
            "justification": "Need replacement"
            # Missing reason_for_return_replacement and asset_details
        }
        
        success, response = self.run_test(
            "Replacement without conditional fields",
            "POST",
            "asset-requisitions",
            422,  # Expecting validation error
            data=data
        )
        
        if not success:
            # Try with 400 status code instead
            success, response = self.run_test(
                "Replacement without conditional fields (400)",
                "POST",
                "asset-requisitions",
                400,
                data=data
            )
        
        if success:
            print("   ✅ Validation correctly rejected replacement without conditional fields")
        
        # Test team member request without team member ID
        data = {
            "asset_type_id": self.asset_type_id,
            "request_type": "New Allocation",
            "request_for": "Team Member",
            "justification": "Need for team member"
            # Missing team_member_employee_id
        }
        
        success, response = self.run_test(
            "Team Member request without member ID",
            "POST",
            "asset-requisitions",
            400,  # Expecting validation error
            data=data
        )
        
        if success:
            print("   ✅ Validation correctly rejected team member request without member ID")

    def test_get_requisitions(self):
        """Test getting requisitions with enhanced fields"""
        success, response = self.run_test(
            "Get Asset Requisitions",
            "GET",
            "asset-requisitions",
            200
        )
        
        if success and response:
            print(f"   Found {len(response)} requisitions")
            for req in response[:3]:  # Show first 3
                print(f"   - ID: {req['id'][:8]}... Type: {req.get('request_type', 'N/A')} For: {req.get('request_for', 'N/A')}")
                
                # Check enhanced fields
                enhanced_fields = ['request_type', 'request_for', 'required_by_date', 'reason_for_return_replacement', 'asset_details']
                present_fields = [field for field in enhanced_fields if field in req and req[field] is not None]
                if present_fields:
                    print(f"     Enhanced fields: {present_fields}")
            return True
        return False

    def test_past_date_validation(self):
        """Test that past dates are handled properly"""
        if not self.asset_type_id:
            return False
            
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        
        data = {
            "asset_type_id": self.asset_type_id,
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Test past date",
            "required_by_date": past_date
        }
        
        # This should still work on backend (frontend prevents it)
        success, response = self.run_test(
            "Request with past date",
            "POST",
            "asset-requisitions",
            200,
            data=data
        )
        
        if success:
            print(f"   Backend accepts past date (frontend should prevent)")
            return True
        return False

def main():
    print("🚀 Starting Enhanced Asset Requisition API Tests")
    print("=" * 60)
    
    tester = EnhancedAssetRequisitionTester()
    
    # Test employee login
    if not tester.test_login("employee@company.com", "password123"):
        print("❌ Login failed, stopping tests")
        return 1
    
    # Setup test data
    tester.setup_test_data()
    
    if not tester.asset_type_id:
        print("❌ No asset type available, cannot proceed with tests")
        return 1
    
    # Test different request types
    print("\n📝 Testing Enhanced Request Types")
    print("-" * 40)
    
    new_allocation_id = tester.test_new_allocation_request()
    replacement_id = tester.test_replacement_request()
    return_id = tester.test_return_request()
    team_member_id = tester.test_team_member_request()
    
    # Test validation
    print("\n🔍 Testing Validation Logic")
    print("-" * 30)
    tester.test_validation_errors()
    
    # Test getting requisitions
    print("\n📋 Testing Enhanced Requisition Retrieval")
    print("-" * 40)
    tester.test_get_requisitions()
    
    # Test edge cases
    print("\n🧪 Testing Edge Cases")
    print("-" * 20)
    tester.test_past_date_validation()
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All enhanced asset requisition tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())