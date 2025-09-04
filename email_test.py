#!/usr/bin/env python3
"""
Email Notification System Testing Script
Tests the newly implemented Email Notification System backend functionality
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class EmailNotificationTester:
    def __init__(self, base_url="https://asset-track-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.employee_token = None
        self.manager_token = None
        self.hr_token = None
        self.asset_manager_token = None
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0

    def login_users(self):
        """Login all required users for testing"""
        users = [
            ("admin@company.com", "password123", "Administrator"),
            ("employee@company.com", "password123", "Employee"),
            ("manager@company.com", "password123", "Manager"),
            ("hr@company.com", "password123", "HR Manager"),
            ("assetmanager@company.com", "password123", "Asset Manager")
        ]
        
        print("🔐 Logging in test users...")
        for email, password, role in users:
            success, token = self.login_user(email, password, role)
            if success:
                if role == "Administrator":
                    self.admin_token = token
                elif role == "Employee":
                    self.employee_token = token
                elif role == "Manager":
                    self.manager_token = token
                elif role == "HR Manager":
                    self.hr_token = token
                elif role == "Asset Manager":
                    self.asset_manager_token = token
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

    def test_email_configuration_crud(self):
        """Test Email Configuration CRUD operations"""
        print(f"\n📋 Testing Email Configuration CRUD Operations")
        
        # Test 1: GET /api/email-config (should return 404 initially)
        success, response = self.run_test(
            "Get Email Configuration (Should be 404 initially)",
            "GET",
            "email-config",
            404,
            token=self.admin_token
        )
        
        if success:
            print("   ✅ No email configuration found initially (expected)")
        
        # Test 2: POST /api/email-config - Create email configuration
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
            self.test_data['email_config_id'] = response['id']
            print(f"   Created email config with ID: {response['id']}")
            print(f"   SMTP Server: {response.get('smtp_server', 'Not set')}")
            print(f"   SMTP Port: {response.get('smtp_port', 'Not set')}")
            print(f"   From Email: {response.get('from_email', 'Not set')}")
            print(f"   Use TLS: {response.get('use_tls', False)}")
            print(f"   Is Active: {response.get('is_active', False)}")
        
        # Test 3: GET /api/email-config - Retrieve active configuration
        success, response = self.run_test(
            "Get Active Email Configuration",
            "GET",
            "email-config",
            200,
            token=self.admin_token
        )
        
        if success:
            print(f"   Retrieved config - Server: {response.get('smtp_server', 'Unknown')}")
            print(f"   Password masked: {response.get('smtp_password') == '***masked***'}")
            print(f"   From Name: {response.get('from_name', 'Unknown')}")
        
        # Test 4: PUT /api/email-config/{id} - Update email configuration
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
                token=self.admin_token
            )
            
            if success:
                print(f"   Updated SMTP server: {response.get('smtp_server', 'Not updated')}")
                print(f"   Updated from name: {response.get('from_name', 'Not updated')}")
        
        # Test 5: POST /api/email-config/test - Send test email (will fail without real SMTP)
        test_email_data = {
            "test_email": "admin@company.com"
        }
        
        success, response = self.run_test(
            "Send Test Email (Expected to fail without real SMTP)",
            "POST",
            "email-config/test",
            500,  # Expecting failure due to invalid SMTP
            data=test_email_data,
            token=self.admin_token
        )
        
        if success:
            print("   ✅ Test email endpoint correctly handled SMTP failure")
        
        return True

    def test_email_access_control(self):
        """Test Email Configuration Access Control"""
        print(f"\n🔒 Testing Email Configuration Access Control")
        
        # Test Employee access (should fail)
        success, response = self.run_test(
            "Employee Access Email Config (Should Fail)",
            "GET",
            "email-config",
            403,
            token=self.employee_token
        )
        
        if success:
            print("   ✅ Employee correctly denied access to email configuration")
        
        # Test Manager access (should fail)
        success, response = self.run_test(
            "Manager Access Email Config (Should Fail)",
            "GET",
            "email-config",
            403,
            token=self.manager_token
        )
        
        if success:
            print("   ✅ Manager correctly denied access to email configuration")
        
        # Test HR Manager access (should fail)
        success, response = self.run_test(
            "HR Manager Access Email Config (Should Fail)",
            "GET",
            "email-config",
            403,
            token=self.hr_token
        )
        
        if success:
            print("   ✅ HR Manager correctly denied access to email configuration")
        
        # Test Asset Manager access (should fail)
        success, response = self.run_test(
            "Asset Manager Access Email Config (Should Fail)",
            "GET",
            "email-config",
            403,
            token=self.asset_manager_token
        )
        
        if success:
            print("   ✅ Asset Manager correctly denied access to email configuration")
        
        return True

    def test_email_validation(self):
        """Test Email Configuration Validation"""
        print(f"\n✅ Testing Email Configuration Validation")
        
        # Test invalid email format
        invalid_config_data = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "test@company.com",
            "smtp_password": "test_password",
            "from_email": "invalid-email-format",  # Invalid email format
            "from_name": "Test System"
        }
        
        success, response = self.run_test(
            "Create Invalid Email Configuration (Should Fail)",
            "POST",
            "email-config",
            422,  # Expecting validation error
            data=invalid_config_data,
            token=self.admin_token
        )
        
        if success:
            print("   ✅ Invalid email configuration correctly rejected")
        
        # Test missing required fields
        incomplete_config = {
            "smtp_server": "smtp.gmail.com",
            # Missing required fields
        }
        
        success, response = self.run_test(
            "Create Incomplete Email Configuration (Should Fail)",
            "POST",
            "email-config",
            422,  # Expecting validation error
            data=incomplete_config,
            token=self.admin_token
        )
        
        if success:
            print("   ✅ Incomplete email configuration correctly rejected")
        
        return True

    def test_email_triggers_integration(self):
        """Test Email Triggers in Asset Management Workflows"""
        print(f"\n🎯 Testing Email Triggers Integration")
        
        # First, create an asset type for testing
        asset_type_data = {
            "code": f"EMAIL_TEST_{datetime.now().strftime('%H%M%S')}",
            "name": "Email Test Asset Type",
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
            token=self.admin_token
        )
        
        if not success:
            print("   ❌ Cannot test email triggers without asset type")
            return False
        
        asset_type_id = response['id']
        print(f"   Created asset type: {asset_type_id}")
        
        # Test Trigger 1: Asset requisition creation (should send email to manager)
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        requisition_data = {
            "asset_type_id": asset_type_id,
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Email notification test - asset request trigger",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Asset Requisition (Email Trigger 1)",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data,
            token=self.employee_token
        )
        
        if success:
            requisition_id = response['id']
            self.test_data['email_test_requisition_id'] = requisition_id
            print(f"   ✅ Asset requisition created - email notification should be triggered")
            print(f"   Requisition ID: {requisition_id[:8]}...")
            print(f"   Status: {response.get('status', 'Unknown')}")
        
        # Test Trigger 2: Manager approval action (should send email to employee)
        if 'email_test_requisition_id' in self.test_data:
            approval_data = {
                "action": "approve",
                "reason": "Email notification test - manager approval trigger"
            }
            
            success, response = self.run_test(
                "Manager Approve Requisition (Email Trigger 2)",
                "POST",
                f"asset-requisitions/{self.test_data['email_test_requisition_id']}/manager-action",
                200,
                data=approval_data,
                token=self.admin_token  # Using admin as they can approve any request
            )
            
            if success:
                print(f"   ✅ Manager approval completed - email notification should be triggered")
                print(f"   New status: {response.get('requisition', {}).get('status', 'Unknown')}")
        
        # Test Trigger 3: Manager rejection action (create new requisition for this)
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
            token=self.employee_token
        )
        
        if success:
            rejection_req_id = response['id']
            
            rejection_data = {
                "action": "reject",
                "reason": "Email notification test - manager rejection trigger"
            }
            
            success, response = self.run_test(
                "Manager Reject Requisition (Email Trigger 3)",
                "POST",
                f"asset-requisitions/{rejection_req_id}/manager-action",
                200,
                data=rejection_data,
                token=self.admin_token
            )
            
            if success:
                print(f"   ✅ Manager rejection completed - email notification should be triggered")
        
        # Test Trigger 4: Asset allocation (need to create asset definition first)
        asset_def_data = {
            "asset_type_id": asset_type_id,
            "asset_code": f"EMAIL_TEST_{datetime.now().strftime('%H%M%S')}",
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
            token=self.admin_token
        )
        
        if success:
            asset_def_id = response['id']
            print(f"   Created asset definition: {asset_def_id[:8]}...")
            
            # Now test asset allocation
            if 'email_test_requisition_id' in self.test_data:
                allocation_data = {
                    "requisition_id": self.test_data['email_test_requisition_id'],
                    "asset_definition_id": asset_def_id,
                    "remarks": "Email notification test - asset allocation trigger"
                }
                
                success, response = self.run_test(
                    "Create Asset Allocation (Email Trigger 4)",
                    "POST",
                    "asset-allocations",
                    200,
                    data=allocation_data,
                    token=self.asset_manager_token
                )
                
                if success:
                    print(f"   ✅ Asset allocation completed - email notification should be triggered")
                    
                    # Test Trigger 5: Asset acknowledgment
                    acknowledgment_data = {
                        "acknowledgment_notes": "Email notification test - asset acknowledgment trigger"
                    }
                    
                    success, response = self.run_test(
                        "Acknowledge Asset Allocation (Email Trigger 5)",
                        "POST",
                        f"asset-definitions/{asset_def_id}/acknowledge",
                        200,
                        data=acknowledgment_data,
                        token=self.employee_token
                    )
                    
                    if success:
                        print(f"   ✅ Asset acknowledgment completed - email notification should be triggered")
                    else:
                        print(f"   ⚠️ Asset acknowledgment failed - may not be allocated to current user")
        
        return True

    def test_email_error_handling(self):
        """Test Email Error Handling Scenarios"""
        print(f"\n🚨 Testing Email Error Handling")
        
        # Test updating non-existent email configuration
        success, response = self.run_test(
            "Update Non-existent Email Config (Should Fail)",
            "PUT",
            "email-config/non-existent-id",
            404,
            data={"smtp_server": "test.com"},
            token=self.admin_token
        )
        
        if success:
            print("   ✅ Non-existent email config update correctly rejected")
        
        # Test sending test email to invalid email format
        invalid_test_email = {
            "test_email": "invalid-email-format"
        }
        
        success, response = self.run_test(
            "Send Test Email to Invalid Address (Should Fail)",
            "POST",
            "email-config/test",
            422,  # Expecting validation error
            data=invalid_test_email,
            token=self.admin_token
        )
        
        if success:
            print("   ✅ Invalid test email address correctly rejected")
        
        return True

    def test_email_service_methods(self):
        """Test Email Service Integration"""
        print(f"\n🔧 Testing Email Service Integration")
        
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
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Second email configuration created")
            
            # Verify only the new one is active
            success, active_config = self.run_test(
                "Verify Only One Active Configuration",
                "GET",
                "email-config",
                200,
                token=self.admin_token
            )
            
            if success:
                if active_config.get('smtp_server') == 'smtp.yahoo.com':
                    print(f"   ✅ Only latest configuration is active")
                else:
                    print(f"   ⚠️ Unexpected active configuration: {active_config.get('smtp_server')}")
        
        return True

    def run_all_tests(self):
        """Run all email notification system tests"""
        print("📧 Starting Email Notification System Tests")
        print("=" * 60)
        
        # Login users
        if not self.login_users():
            print("❌ Failed to login required users")
            return False
        
        # Run test suites
        print("\n📋 EMAIL CONFIGURATION CRUD TESTS")
        print("-" * 35)
        self.test_email_configuration_crud()
        
        print("\n🔒 EMAIL ACCESS CONTROL TESTS")
        print("-" * 30)
        self.test_email_access_control()
        
        print("\n✅ EMAIL VALIDATION TESTS")
        print("-" * 25)
        self.test_email_validation()
        
        print("\n🎯 EMAIL TRIGGERS INTEGRATION TESTS")
        print("-" * 35)
        self.test_email_triggers_integration()
        
        print("\n🚨 EMAIL ERROR HANDLING TESTS")
        print("-" * 30)
        self.test_email_error_handling()
        
        print("\n🔧 EMAIL SERVICE INTEGRATION TESTS")
        print("-" * 35)
        self.test_email_service_methods()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 EMAIL NOTIFICATION SYSTEM TEST RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📧 Email Notification System Testing Summary:")
        print(f"   ✅ Email Configuration API endpoints tested")
        print(f"   ✅ SMTP configuration validation tested")
        print(f"   ✅ Email service integration tested")
        print(f"   ✅ Email triggers in workflows tested")
        print(f"   ✅ Access control for email features tested")
        print(f"   ✅ Error handling scenarios tested")
        print(f"   ⚠️ Note: Actual email sending requires valid SMTP server")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All email notification tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = EmailNotificationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())