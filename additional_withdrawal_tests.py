#!/usr/bin/env python3
"""
Additional Edge Case Tests for Asset Requisition Withdrawal
"""

import requests
import json
import sys
from datetime import datetime, timedelta

class AdditionalWithdrawalTester:
    def __init__(self):
        self.base_url = "https://asset-track-2.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tokens = {}
        self.users = {}
        self.test_data = {}

    def setup_auth(self):
        """Quick authentication setup"""
        test_users = [
            ("admin@company.com", "password123", "Administrator"),
            ("hr@company.com", "password123", "HR Manager"),
            ("employee@company.com", "password123", "Employee"),
        ]
        
        for email, password, role in test_users:
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json={"email": email, "password": password})
            if response.status_code == 200:
                data = response.json()
                self.tokens[role] = data['session_token']
                self.users[role] = data['user']
                print(f"✅ {role} authenticated")
            else:
                print(f"❌ {role} authentication failed")
                return False
        return True

    def get_asset_type(self):
        """Get asset type for testing"""
        headers = {'Authorization': f'Bearer {self.tokens["Administrator"]}'}
        response = requests.get(f"{self.api_url}/asset-types", headers=headers)
        if response.status_code == 200:
            asset_types = response.json()
            if asset_types:
                self.test_data['asset_type_id'] = asset_types[0]['id']
                return True
        return False

    def create_requisition(self, user_role):
        """Create a test requisition"""
        headers = {'Authorization': f'Bearer {self.tokens[user_role]}'}
        data = {
            "asset_type_id": self.test_data['asset_type_id'],
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": f"Test requisition by {user_role}",
            "required_by_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        response = requests.post(f"{self.api_url}/asset-requisitions", 
                               json=data, headers=headers)
        if response.status_code == 200:
            return response.json()['id']
        return None

    def test_backward_compatibility(self):
        """Test that the endpoint works with both old and new user structures"""
        print("\n🔄 Testing Backward Compatibility")
        
        # Test with current multi-role users
        for role in ["Employee", "Administrator", "HR Manager"]:
            if role in self.tokens:
                headers = {'Authorization': f'Bearer {self.tokens[role]}'}
                response = requests.get(f"{self.api_url}/auth/me", headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    roles_field = user_data.get('roles', [])
                    
                    if isinstance(roles_field, list):
                        print(f"   ✅ {role}: Multi-role structure - {roles_field}")
                    else:
                        print(f"   ⚠️ {role}: Legacy structure detected")
                else:
                    print(f"   ❌ {role}: Failed to get user info")

    def test_role_hierarchy_withdrawal(self):
        """Test role hierarchy in withdrawal permissions"""
        print("\n🏗️ Testing Role Hierarchy in Withdrawal")
        
        # Create requisition as Employee
        req_id = self.create_requisition("Employee")
        if not req_id:
            print("   ❌ Failed to create test requisition")
            return
        
        print(f"   Created requisition: {req_id[:8]}...")
        
        # Test Administrator can delete (role hierarchy)
        headers = {'Authorization': f'Bearer {self.tokens["Administrator"]}'}
        response = requests.delete(f"{self.api_url}/asset-requisitions/{req_id}", 
                                 headers=headers)
        
        if response.status_code == 200:
            print("   ✅ Administrator can delete employee's request (role hierarchy working)")
        else:
            print(f"   ❌ Administrator deletion failed: {response.status_code}")

    def test_concurrent_withdrawal_attempts(self):
        """Test what happens when multiple users try to withdraw the same request"""
        print("\n🔀 Testing Concurrent Withdrawal Scenarios")
        
        # Create requisition as Employee
        req_id = self.create_requisition("Employee")
        if not req_id:
            print("   ❌ Failed to create test requisition")
            return
        
        print(f"   Created requisition: {req_id[:8]}...")
        
        # First withdrawal by Employee (should succeed)
        headers = {'Authorization': f'Bearer {self.tokens["Employee"]}'}
        response1 = requests.delete(f"{self.api_url}/asset-requisitions/{req_id}", 
                                  headers=headers)
        
        # Second withdrawal attempt by Administrator (should fail - already deleted)
        headers = {'Authorization': f'Bearer {self.tokens["Administrator"]}'}
        response2 = requests.delete(f"{self.api_url}/asset-requisitions/{req_id}", 
                                  headers=headers)
        
        if response1.status_code == 200 and response2.status_code == 404:
            print("   ✅ Concurrent withdrawal handled correctly")
            print(f"      First attempt: {response1.status_code} (success)")
            print(f"      Second attempt: {response2.status_code} (not found)")
        else:
            print(f"   ⚠️ Unexpected behavior: {response1.status_code}, {response2.status_code}")

    def test_withdrawal_with_special_characters(self):
        """Test withdrawal with requisition IDs containing special scenarios"""
        print("\n🔤 Testing Special Character Handling")
        
        # Test with malformed ID
        headers = {'Authorization': f'Bearer {self.tokens["Employee"]}'}
        
        test_cases = [
            ("empty-string", ""),
            ("sql-injection", "'; DROP TABLE asset_requisitions; --"),
            ("very-long-id", "a" * 1000),
            ("unicode-chars", "测试-αβγ-🚀"),
        ]
        
        for test_name, test_id in test_cases:
            response = requests.delete(f"{self.api_url}/asset-requisitions/{test_id}", 
                                     headers=headers)
            
            # Should return 404 for all these cases
            if response.status_code == 404:
                print(f"   ✅ {test_name}: Handled correctly (404)")
            else:
                print(f"   ⚠️ {test_name}: Unexpected status {response.status_code}")

    def run_additional_tests(self):
        """Run all additional tests"""
        print("🧪 Additional Asset Requisition Withdrawal Tests")
        print("=" * 55)
        
        if not self.setup_auth():
            print("❌ Authentication failed")
            return False
        
        if not self.get_asset_type():
            print("❌ Could not get asset type")
            return False
        
        self.test_backward_compatibility()
        self.test_role_hierarchy_withdrawal()
        self.test_concurrent_withdrawal_attempts()
        self.test_withdrawal_with_special_characters()
        
        print("\n✅ Additional tests completed")
        return True

def main():
    tester = AdditionalWithdrawalTester()
    success = tester.run_additional_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())