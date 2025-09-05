#!/usr/bin/env python3
"""
Email Acknowledgment Test - Test Trigger 5 specifically
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class EmailAcknowledgmentTester:
    def __init__(self, base_url="https://resource-manager-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.employee_token = None
        self.asset_manager_token = None
        self.test_data = {}

    def login_users(self):
        """Login required users"""
        users = [
            ("admin@company.com", "password123", "Administrator"),
            ("employee@company.com", "password123", "Employee"),
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

    def test_asset_acknowledgment_email_trigger(self):
        """Test the complete asset acknowledgment email trigger workflow"""
        print(f"\n🎯 Testing Asset Acknowledgment Email Trigger (Trigger 5)")
        
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
            "Create Email Configuration for Acknowledgment Test",
            "POST",
            "email-config",
            200,
            data=email_config_data,
            token=self.admin_token
        )
        
        if not success:
            print("   ❌ Cannot test acknowledgment without email config")
            return False
        
        # Step 2: Create asset type
        asset_type_data = {
            "code": f"ACK_TEST_{datetime.now().strftime('%H%M%S')}",
            "name": "Acknowledgment Test Asset Type",
            "depreciation_applicable": False,
            "to_be_recovered_on_separation": True,
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Create Asset Type for Acknowledgment Test",
            "POST",
            "asset-types",
            200,
            data=asset_type_data,
            token=self.admin_token
        )
        
        if not success:
            return False
        
        asset_type_id = response['id']
        print(f"   Created asset type: {asset_type_id}")
        
        # Step 3: Create asset definition
        asset_def_data = {
            "asset_type_id": asset_type_id,
            "asset_code": f"ACK_ASSET_{datetime.now().strftime('%H%M%S')}",
            "asset_description": "Acknowledgment Test Asset",
            "asset_details": "Asset for acknowledgment email testing",
            "asset_value": 30000.0,
            "status": "Available"
        }
        
        success, response = self.run_test(
            "Create Asset Definition for Acknowledgment Test",
            "POST",
            "asset-definitions",
            200,
            data=asset_def_data,
            token=self.admin_token
        )
        
        if not success:
            return False
        
        asset_def_id = response['id']
        print(f"   Created asset definition: {asset_def_id}")
        
        # Step 4: Create asset requisition
        required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        requisition_data = {
            "asset_type_id": asset_type_id,
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Acknowledgment test - need asset for testing email trigger",
            "required_by_date": required_by_date
        }
        
        success, response = self.run_test(
            "Create Asset Requisition for Acknowledgment Test",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data,
            token=self.employee_token
        )
        
        if not success:
            return False
        
        requisition_id = response['id']
        print(f"   Created requisition: {requisition_id}")
        
        # Step 5: Approve the requisition
        approval_data = {
            "action": "approve",
            "reason": "Acknowledgment test - approving for allocation"
        }
        
        success, response = self.run_test(
            "Approve Requisition for Acknowledgment Test",
            "POST",
            f"asset-requisitions/{requisition_id}/manager-action",
            200,
            data=approval_data,
            token=self.admin_token
        )
        
        if not success:
            return False
        
        print(f"   Requisition approved")
        
        # Step 6: Allocate the asset
        allocation_data = {
            "requisition_id": requisition_id,
            "asset_definition_id": asset_def_id,
            "remarks": "Acknowledgment test - allocating asset for email trigger test"
        }
        
        success, response = self.run_test(
            "Allocate Asset for Acknowledgment Test",
            "POST",
            "asset-allocations",
            200,
            data=allocation_data,
            token=self.asset_manager_token
        )
        
        if not success:
            print("   ❌ Asset allocation failed - checking asset status")
            # Check asset status
            success, asset_response = self.run_test(
                "Check Asset Status",
                "GET",
                f"asset-definitions/{asset_def_id}",
                200,
                token=self.admin_token
            )
            
            if success:
                print(f"   Asset status: {asset_response.get('status', 'Unknown')}")
                print(f"   Allocated to: {asset_response.get('allocated_to', 'None')}")
            return False
        
        print(f"   Asset allocated successfully")
        
        # Step 7: Verify asset is allocated to employee
        success, asset_response = self.run_test(
            "Verify Asset Allocation Status",
            "GET",
            f"asset-definitions/{asset_def_id}",
            200,
            token=self.admin_token
        )
        
        if success:
            print(f"   Asset status: {asset_response.get('status', 'Unknown')}")
            print(f"   Allocated to: {asset_response.get('allocated_to', 'None')}")
            print(f"   Allocation date: {asset_response.get('allocation_date', 'None')}")
            
            if asset_response.get('status') != 'Allocated':
                print("   ❌ Asset is not in Allocated status")
                return False
        
        # Step 8: Test asset acknowledgment (Email Trigger 5)
        acknowledgment_data = {
            "acknowledgment_notes": "Acknowledgment test - confirming receipt of asset for email trigger testing"
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
            print(f"   Acknowledgment date: {response.get('acknowledged_at', 'Unknown')}")
            
            # Verify acknowledgment was recorded
            asset_data = response.get('asset', {})
            print(f"   Acknowledged: {asset_data.get('acknowledged', False)}")
            print(f"   Acknowledgment notes: {asset_data.get('acknowledgment_notes', 'None')}")
            
            return True
        else:
            print(f"   ❌ Asset acknowledgment failed")
            return False

    def test_my_allocated_assets(self):
        """Test the my allocated assets endpoint"""
        print(f"\n📋 Testing My Allocated Assets Endpoint")
        
        success, response = self.run_test(
            "Get My Allocated Assets (Employee)",
            "GET",
            "my-allocated-assets",
            200,
            token=self.employee_token
        )
        
        if success:
            print(f"   Employee has {len(response)} allocated assets")
            for asset in response:
                print(f"     - {asset.get('asset_code', 'Unknown')} ({asset.get('asset_description', 'Unknown')})")
                print(f"       Status: {asset.get('status', 'Unknown')}")
                print(f"       Acknowledged: {asset.get('acknowledged', False)}")
        
        return success

    def run_all_tests(self):
        """Run all acknowledgment tests"""
        print("🎯 Starting Asset Acknowledgment Email Trigger Tests")
        print("=" * 60)
        
        # Login users
        if not self.login_users():
            print("❌ Failed to login required users")
            return False
        
        # Test my allocated assets first
        self.test_my_allocated_assets()
        
        # Test acknowledgment email trigger
        success = self.test_asset_acknowledgment_email_trigger()
        
        # Test my allocated assets after acknowledgment
        self.test_my_allocated_assets()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 Asset Acknowledgment Email Trigger Test Completed Successfully!")
            print("📧 Email notification should have been triggered to Asset Manager")
            print("📧 CC should include Employee, Manager, and HR Manager")
        else:
            print("❌ Asset Acknowledgment Email Trigger Test Failed")
        
        return success

def main():
    tester = EmailAcknowledgmentTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())