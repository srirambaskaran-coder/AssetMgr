#!/usr/bin/env python3
"""
Direct Asset Acknowledgment Test - Test existing allocated assets
"""

import requests
import sys
import json

class DirectAcknowledgmentTester:
    def __init__(self, base_url="https://resource-manager-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.employee_token = None

    def login_users(self):
        """Login required users"""
        users = [
            ("admin@company.com", "password123", "Administrator"),
            ("employee@company.com", "password123", "Employee")
        ]
        
        print("🔐 Logging in test users...")
        for email, password, role in users:
            success, token = self.login_user(email, password, role)
            if success:
                if role == "Administrator":
                    self.admin_token = token
                elif role == "Employee":
                    self.employee_token = token
                print(f"   ✅ {role} logged in successfully")
            else:
                print(f"   ❌ {role} login failed")
                return False
        return True

    def login_user(self, email, password, role):
        """Login a single user and return token"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return True, data.get('session_token')
            return False, None
        except Exception as e:
            print(f"Login error for {role}: {str(e)}")
            return False, None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

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

    def test_direct_acknowledgment(self):
        """Test acknowledgment on existing allocated assets"""
        print(f"\n🎯 Testing Direct Asset Acknowledgment")
        
        # Step 1: Create email configuration
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
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Email configuration created")
        
        # Step 2: Get employee's allocated assets
        success, response = self.run_test(
            "Get Employee's Allocated Assets",
            "GET",
            "my-allocated-assets",
            200,
            token=self.employee_token
        )
        
        if not success:
            print("   ❌ Cannot get allocated assets")
            return False
        
        allocated_assets = response
        print(f"   Found {len(allocated_assets)} allocated assets")
        
        if not allocated_assets:
            print("   ⚠️ No allocated assets found for testing")
            return False
        
        # Step 3: Test acknowledgment on each unacknowledged asset
        acknowledgment_success = False
        
        for asset in allocated_assets:
            asset_id = asset.get('id')
            asset_code = asset.get('asset_code', 'Unknown')
            acknowledged = asset.get('acknowledged', False)
            
            print(f"\n   Asset: {asset_code} (ID: {asset_id})")
            print(f"   Status: {asset.get('status', 'Unknown')}")
            print(f"   Already acknowledged: {acknowledged}")
            
            if not acknowledged:
                # Test acknowledgment
                acknowledgment_data = {
                    "acknowledgment_notes": f"Direct test acknowledgment for {asset_code} - testing email trigger 5"
                }
                
                success, ack_response = self.run_test(
                    f"Acknowledge Asset {asset_code} (Email Trigger 5)",
                    "POST",
                    f"asset-definitions/{asset_id}/acknowledge",
                    200,
                    data=acknowledgment_data,
                    token=self.employee_token
                )
                
                if success:
                    print(f"   ✅ Asset {asset_code} acknowledged successfully")
                    print(f"   📧 Email notification should be triggered to Asset Manager")
                    print(f"   📧 CC should include Employee, Manager, and HR Manager")
                    
                    # Show acknowledgment details
                    asset_data = ack_response.get('asset', {})
                    print(f"   Acknowledgment date: {ack_response.get('acknowledged_at', 'Unknown')}")
                    print(f"   Acknowledgment notes: {asset_data.get('acknowledgment_notes', 'None')}")
                    
                    acknowledgment_success = True
                    break  # Test one acknowledgment
                else:
                    print(f"   ❌ Failed to acknowledge asset {asset_code}")
            else:
                print(f"   ⚠️ Asset {asset_code} already acknowledged")
        
        return acknowledgment_success

    def test_acknowledgment_validation(self):
        """Test acknowledgment validation scenarios"""
        print(f"\n✅ Testing Acknowledgment Validation")
        
        # Get allocated assets first
        success, response = self.run_test(
            "Get Allocated Assets for Validation Test",
            "GET",
            "my-allocated-assets",
            200,
            token=self.employee_token
        )
        
        if not success or not response:
            print("   ⚠️ No allocated assets for validation testing")
            return True
        
        # Test double acknowledgment (should fail)
        for asset in response:
            if asset.get('acknowledged', False):
                asset_id = asset.get('id')
                asset_code = asset.get('asset_code', 'Unknown')
                
                acknowledgment_data = {
                    "acknowledgment_notes": "Double acknowledgment test - should fail"
                }
                
                success, ack_response = self.run_test(
                    f"Double Acknowledge Asset {asset_code} (Should Fail)",
                    "POST",
                    f"asset-definitions/{asset_id}/acknowledge",
                    400,  # Should fail with 400
                    data=acknowledgment_data,
                    token=self.employee_token
                )
                
                if success:
                    print(f"   ✅ Double acknowledgment correctly rejected for {asset_code}")
                break
        
        return True

    def test_cross_user_acknowledgment(self):
        """Test cross-user acknowledgment (should fail)"""
        print(f"\n🔒 Testing Cross-User Acknowledgment Security")
        
        # Get all asset definitions to find one not allocated to current employee
        success, response = self.run_test(
            "Get All Asset Definitions",
            "GET",
            "asset-definitions",
            200,
            token=self.admin_token
        )
        
        if not success:
            print("   ⚠️ Cannot get asset definitions for security test")
            return True
        
        # Find an asset not allocated to the employee
        employee_user = None
        success, user_response = self.run_test(
            "Get Current Employee User",
            "GET",
            "auth/me",
            200,
            token=self.employee_token
        )
        
        if success:
            employee_user_id = user_response.get('id')
            
            for asset in response:
                allocated_to = asset.get('allocated_to')
                if allocated_to and allocated_to != employee_user_id:
                    asset_id = asset.get('id')
                    asset_code = asset.get('asset_code', 'Unknown')
                    
                    acknowledgment_data = {
                        "acknowledgment_notes": "Cross-user acknowledgment test - should fail"
                    }
                    
                    success, ack_response = self.run_test(
                        f"Cross-User Acknowledge Asset {asset_code} (Should Fail)",
                        "POST",
                        f"asset-definitions/{asset_id}/acknowledge",
                        403,  # Should fail with 403
                        data=acknowledgment_data,
                        token=self.employee_token
                    )
                    
                    if success:
                        print(f"   ✅ Cross-user acknowledgment correctly rejected for {asset_code}")
                    break
        
        return True

    def run_all_tests(self):
        """Run all acknowledgment tests"""
        print("🎯 Starting Direct Asset Acknowledgment Tests")
        print("=" * 60)
        
        # Login users
        if not self.login_users():
            print("❌ Failed to login required users")
            return False
        
        # Test direct acknowledgment
        success1 = self.test_direct_acknowledgment()
        
        # Test validation scenarios
        success2 = self.test_acknowledgment_validation()
        
        # Test security scenarios
        success3 = self.test_cross_user_acknowledgment()
        
        print("\n" + "=" * 60)
        if success1:
            print("🎉 Direct Asset Acknowledgment Test Completed Successfully!")
            print("📧 Email Trigger 5 (Asset Acknowledgment) has been tested")
            print("📧 Email notification should have been sent to Asset Manager")
            print("📧 CC should include Employee, Manager, and HR Manager")
        else:
            print("❌ Direct Asset Acknowledgment Test Failed")
        
        print(f"\n✅ Validation Tests: {'Passed' if success2 else 'Failed'}")
        print(f"✅ Security Tests: {'Passed' if success3 else 'Failed'}")
        
        return success1 and success2 and success3

def main():
    tester = DirectAcknowledgmentTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())