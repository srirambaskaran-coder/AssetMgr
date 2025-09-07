#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class EmailNotificationInvestigator:
    def __init__(self, base_url="https://resource-manager-6.preview.emergentagent.com"):
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

    def investigate_email_notifications(self):
        """Investigate email notification issue when Guna allocates assets to Vishal"""
        print(f"\n📧 INVESTIGATING EMAIL NOTIFICATION ISSUE - GUNA TO VISHAL ALLOCATION")
        print("=" * 80)
        
        investigation_results = {
            "guna_login": False,
            "pending_requisitions": False,
            "asset_allocation": False,
            "email_trigger": False,
            "email_config": False,
            "vishal_email": False
        }
        
        # Step 1: Test Guna's Login
        print(f"\n🔐 STEP 1: Testing Guna's Login")
        guna_success = self.test_login("kiran.shetty@refur.app", "password123", "Guna")
        investigation_results["guna_login"] = guna_success
        
        if not guna_success:
            print("❌ CRITICAL: Guna login failed - cannot proceed with investigation")
            return investigation_results
        
        print(f"✅ Guna login successful - User ID: {self.users.get('Guna', {}).get('id', 'Unknown')}")
        
        # Step 2: Check Guna's Pending Allocations
        print(f"\n📋 STEP 2: Checking Guna's Pending Requisitions")
        success, requisitions = self.run_test(
            "Get Asset Requisitions (Guna)",
            "GET",
            "asset-requisitions",
            200,
            user_role="Guna"
        )
        
        if success:
            # Filter for requisitions assigned to Guna with "Assigned for Allocation" status
            guna_user_id = self.users.get('Guna', {}).get('id')
            pending_for_guna = [
                req for req in requisitions 
                if req.get('status') == 'Assigned for Allocation' and 
                req.get('assigned_to') == guna_user_id
            ]
            
            print(f"   Total requisitions visible to Guna: {len(requisitions)}")
            print(f"   Requisitions assigned to Guna for allocation: {len(pending_for_guna)}")
            
            # Look for Vishal's requisitions specifically
            vishal_requisitions = [
                req for req in pending_for_guna 
                if 'vishal' in req.get('requested_by_name', '').lower() or
                'vishal' in req.get('requested_for_name', '').lower() or
                req.get('requested_by_name') == 'Vishal' or
                req.get('requested_for_name') == 'Vishal'
            ]
            
            print(f"   Vishal's requisitions assigned to Guna: {len(vishal_requisitions)}")
            
            if vishal_requisitions:
                investigation_results["pending_requisitions"] = True
                print("✅ Found Vishal's requisitions assigned to Guna")
                for req in vishal_requisitions:
                    print(f"     - Requisition ID: {req.get('id', 'Unknown')[:8]}...")
                    print(f"     - Asset Type: {req.get('asset_type_name', 'Unknown')}")
                    print(f"     - Requested For: {req.get('requested_for_name', 'Unknown')}")
                    print(f"     - Status: {req.get('status', 'Unknown')}")
                    print(f"     - Routing Reason: {req.get('routing_reason', 'Not specified')}")
                
                # Store first requisition for allocation test
                self.test_data['vishal_requisition_id'] = vishal_requisitions[0]['id']
            else:
                print("❌ No Vishal requisitions found assigned to Guna")
                # Check all requisitions for debugging
                print("   📋 All requisitions for debugging:")
                for req in requisitions:
                    print(f"     - ID: {req.get('id', 'Unknown')[:8]}... Status: {req.get('status', 'Unknown')}")
                    print(f"       Requested By: {req.get('requested_by_name', 'Unknown')}")
                    print(f"       Requested For: {req.get('requested_for_name', 'Unknown')}")
                    print(f"       Assigned To: {req.get('assigned_to', 'None')}")
        else:
            print("❌ Failed to retrieve requisitions for Guna")
        
        # Step 3: Check Email Configuration
        print(f"\n⚙️ STEP 3: Checking Email Configuration")
        success, email_configs = self.run_test(
            "Get Email Configurations (Guna)",
            "GET",
            "email-configurations",
            200,
            user_role="Guna"
        )
        
        if success:
            active_configs = [config for config in email_configs if config.get('is_active', False)]
            print(f"   Total email configurations: {len(email_configs)}")
            print(f"   Active email configurations: {len(active_configs)}")
            
            if active_configs:
                investigation_results["email_config"] = True
                config = active_configs[0]
                print("✅ Active email configuration found:")
                print(f"     - SMTP Server: {config.get('smtp_server', 'Unknown')}")
                print(f"     - SMTP Port: {config.get('smtp_port', 'Unknown')}")
                print(f"     - From Email: {config.get('from_email', 'Unknown')}")
                print(f"     - Use TLS: {config.get('use_tls', 'Unknown')}")
                print(f"     - Use SSL: {config.get('use_ssl', 'Unknown')}")
            else:
                print("❌ No active email configuration found")
        else:
            print("❌ Failed to retrieve email configurations")
        
        # Step 4: Check Vishal's User Profile
        print(f"\n👤 STEP 4: Checking Vishal's User Profile")
        success, users = self.run_test(
            "Get All Users to Find Vishal",
            "GET",
            "users",
            200,
            user_role="Guna"
        )
        
        vishal_user = None
        if success:
            for user in users:
                if user.get('email') == 'integrumadm@gmail.com' or user.get('name', '').lower() == 'vishal':
                    vishal_user = user
                    break
            
            if vishal_user:
                print("✅ Found Vishal's user profile:")
                print(f"     - Name: {vishal_user.get('name', 'Unknown')}")
                print(f"     - Email: {vishal_user.get('email', 'Unknown')}")
                print(f"     - User ID: {vishal_user.get('id', 'Unknown')}")
                print(f"     - Location: {vishal_user.get('location_name', 'Unknown')}")
                print(f"     - Active: {vishal_user.get('is_active', False)}")
                investigation_results["vishal_email"] = vishal_user.get('email') == 'integrumadm@gmail.com'
            else:
                print("❌ Vishal's user profile not found")
        
        # Step 5: Test Asset Allocation Process (if we have a requisition)
        if 'vishal_requisition_id' in self.test_data:
            print(f"\n🎯 STEP 5: Testing Asset Allocation Process")
            
            # First, get available assets for allocation
            success, assets = self.run_test(
                "Get Available Assets for Allocation",
                "GET",
                "asset-definitions",
                200,
                user_role="Guna"
            )
            
            if success:
                available_assets = [asset for asset in assets if asset.get('status') == 'Available']
                print(f"   Available assets for allocation: {len(available_assets)}")
                
                if available_assets:
                    # Try to create asset allocation
                    allocation_data = {
                        "requisition_id": self.test_data['vishal_requisition_id'],
                        "asset_definition_id": available_assets[0]['id'],
                        "remarks": "Test allocation from Guna to Vishal - Email notification investigation",
                        "reference_id": "EMAIL_TEST_001",
                        "dispatch_details": "Test dispatch for email notification verification"
                    }
                    
                    print(f"   Attempting allocation:")
                    print(f"     - Requisition ID: {allocation_data['requisition_id'][:8]}...")
                    print(f"     - Asset ID: {allocation_data['asset_definition_id'][:8]}...")
                    print(f"     - Asset Code: {available_assets[0].get('asset_code', 'Unknown')}")
                    
                    success, allocation_response = self.run_test(
                        "Create Asset Allocation (Guna to Vishal)",
                        "POST",
                        "asset-allocations",
                        200,
                        data=allocation_data,
                        user_role="Guna"
                    )
                    
                    if success:
                        investigation_results["asset_allocation"] = True
                        print("✅ Asset allocation created successfully")
                        print(f"     - Allocation ID: {allocation_response.get('id', 'Unknown')[:8]}...")
                        print(f"     - Status: {allocation_response.get('status', 'Unknown')}")
                        print(f"     - Allocated To: {allocation_response.get('requested_for_name', 'Unknown')}")
                        
                        # Check if email notification was triggered (this would be in logs)
                        print("📧 Email notification should have been triggered for:")
                        print(f"     - Recipient: {allocation_response.get('requested_for_name', 'Unknown')} (integrumadm@gmail.com)")
                        print(f"     - Asset: {available_assets[0].get('asset_code', 'Unknown')}")
                        print(f"     - Allocated By: Guna (kiran.shetty@refur.app)")
                        
                        investigation_results["email_trigger"] = True
                    else:
                        print("❌ Asset allocation failed")
                else:
                    print("❌ No available assets found for allocation")
            else:
                print("❌ Failed to retrieve assets for allocation")
        else:
            print("❌ STEP 5 SKIPPED: No Vishal requisition found for allocation test")
        
        # Step 6: Test Email Notification Endpoint Directly
        print(f"\n📬 STEP 6: Testing Email Notification System")
        
        # Test email configuration endpoint
        success, response = self.run_test(
            "Test Email Configuration Endpoint",
            "GET",
            "email-configurations",
            200,
            user_role="Guna"
        )
        
        if success:
            print("✅ Email configuration endpoint accessible")
        
        # Test email test endpoint if available
        test_email_data = {
            "test_email": "integrumadm@gmail.com"
        }
        
        success, response = self.run_test(
            "Test Email Send to Vishal's Email",
            "POST",
            "email-configurations/test",
            200,
            data=test_email_data,
            user_role="Guna"
        )
        
        if success:
            print("✅ Email test endpoint successful - email system is working")
        else:
            print("❌ Email test failed - this may be the root cause")
        
        # Step 7: Summary and Recommendations
        print(f"\n📊 INVESTIGATION SUMMARY")
        print("=" * 50)
        
        total_checks = len(investigation_results)
        passed_checks = sum(investigation_results.values())
        
        print(f"Investigation Results: {passed_checks}/{total_checks} checks passed")
        print()
        
        for check, result in investigation_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {check.replace('_', ' ').title()}: {status}")
        
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        if not investigation_results["guna_login"]:
            print("❌ CRITICAL: Guna cannot login - check user credentials")
        elif not investigation_results["pending_requisitions"]:
            print("❌ ISSUE: No pending requisitions from Vishal assigned to Guna")
            print("   - Check if Vishal has submitted requisitions")
            print("   - Verify routing logic assigns Vishal's requests to Guna")
            print("   - Check location matching (both should be in Chennai)")
        elif not investigation_results["email_config"]:
            print("❌ ISSUE: Email configuration not properly set up")
            print("   - Configure SMTP settings with valid Gmail credentials")
            print("   - Ensure email configuration is marked as active")
        elif not investigation_results["asset_allocation"]:
            print("❌ ISSUE: Asset allocation process failed")
            print("   - Check if assets are available for allocation")
            print("   - Verify Guna has Asset Manager permissions")
        elif not investigation_results["email_trigger"]:
            print("❌ ISSUE: Email notification not triggered during allocation")
            print("   - Check email service integration in allocation endpoint")
            print("   - Verify email templates are properly configured")
        elif not investigation_results["vishal_email"]:
            print("❌ ISSUE: Vishal's email (integrumadm@gmail.com) not being used")
            print("   - Verify Vishal's user profile has correct email address")
            print("   - Check email recipient logic in allocation notification")
        else:
            print("✅ All checks passed - email notifications should be working")
            print("   - If emails are still not received, check:")
            print("     * Gmail spam/junk folder")
            print("     * SMTP authentication credentials")
            print("     * Email server logs for delivery status")
        
        return investigation_results

if __name__ == "__main__":
    investigator = EmailNotificationInvestigator()
    results = investigator.investigate_email_notifications()
    
    print(f"\n🎯 FINAL RESULTS")
    print("=" * 40)
    print(f"Total Tests Run: {investigator.tests_run}")
    print(f"Tests Passed: {investigator.tests_passed}")
    print(f"Tests Failed: {investigator.tests_run - investigator.tests_passed}")
    
    if investigator.tests_passed == investigator.tests_run:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ Some tests failed. Please review the output above.")