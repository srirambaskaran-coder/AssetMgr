#!/usr/bin/env python3
"""
Final comprehensive test for sriram@company.com password update and login issues
"""

import requests
import json
import hashlib
from datetime import datetime

class FinalPasswordTest:
    def __init__(self, base_url="https://resource-manager-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
    def get_fresh_admin_token(self):
        """Get a fresh admin token"""
        login_data = {
            "email": "admin@company.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{self.api_url}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get('session_token')
        return None
    
    def get_admin_headers(self):
        """Get headers with fresh admin token"""
        token = self.get_fresh_admin_token()
        if token:
            return {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        return {'Content-Type': 'application/json'}
    
    def test_login(self, email, password, expected_success=True):
        """Test login with given credentials"""
        print(f"🔑 Testing login: {email} with password '{password}'")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        response = requests.post(
            f"{self.api_url}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if expected_success:
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Login successful")
                print(f"   Session token: {data.get('session_token', '')[:20]}...")
                user = data.get('user', {})
                print(f"   User: {user.get('name', 'Unknown')} ({user.get('email', 'Unknown')})")
                print(f"   Roles: {user.get('roles', [])}")
                return True, data
            else:
                print(f"   ❌ Login failed (expected success): {response.status_code}")
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Response: {response.text}")
                return False, None
        else:
            if response.status_code == 401:
                print(f"   ✅ Login correctly rejected (as expected)")
                return True, None
            else:
                print(f"   ❌ Login should have failed but got: {response.status_code}")
                return False, None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        print(f"📋 Looking up user: {email}")
        
        response = requests.get(
            f"{self.api_url}/users",
            headers=self.get_admin_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get('email') == email:
                    print(f"   ✅ Found user: {user.get('name')} (ID: {user.get('id')})")
                    return user
            print(f"   ❌ User {email} not found")
            return None
        else:
            print(f"   ❌ Failed to get users: {response.status_code}")
            return None
    
    def create_user(self, email, name, password):
        """Create a new user"""
        print(f"👤 Creating user: {email}")
        
        user_data = {
            "email": email,
            "name": name,
            "roles": ["Employee"],
            "designation": "Software Developer",
            "password": password
        }
        
        response = requests.post(
            f"{self.api_url}/users",
            json=user_data,
            headers=self.get_admin_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ User created: {user.get('name')} (ID: {user.get('id')})")
            return user
        else:
            print(f"   ❌ Failed to create user: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text}")
            return None
    
    def update_user_password(self, user_id, new_password):
        """Update user password"""
        print(f"🔄 Updating password for user ID: {user_id}")
        
        update_data = {"password": new_password}
        
        response = requests.put(
            f"{self.api_url}/users/{user_id}",
            json=update_data,
            headers=self.get_admin_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ Password updated for: {user.get('name')} ({user.get('email')})")
            return True
        else:
            print(f"   ❌ Password update failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text}")
            return False
    
    def run_sriram_password_test(self):
        """Run comprehensive test for sriram@company.com"""
        print("🚀 COMPREHENSIVE PASSWORD TEST FOR SRIRAM@COMPANY.COM")
        print("=" * 60)
        
        # Test 1: Check if sriram user exists
        print("\n📋 STEP 1: USER DATABASE STATE VERIFICATION")
        print("-" * 40)
        
        sriram_user = self.get_user_by_email("sriram@company.com")
        
        if not sriram_user:
            print("Creating sriram@company.com user...")
            sriram_user = self.create_user("sriram@company.com", "Sriram Test User", "password123")
            if not sriram_user:
                print("❌ Cannot proceed without sriram user")
                return False
        
        sriram_user_id = sriram_user['id']
        print(f"User details:")
        print(f"   ID: {sriram_user.get('id')}")
        print(f"   Name: {sriram_user.get('name')}")
        print(f"   Email: {sriram_user.get('email')}")
        print(f"   Roles: {sriram_user.get('roles', [])}")
        print(f"   Active: {sriram_user.get('is_active', False)}")
        
        # Test 2: Set a known password and test login
        print("\n🔄 STEP 2: PASSWORD UPDATE AND INITIAL LOGIN")
        print("-" * 45)
        
        initial_password = "password123"
        if self.update_user_password(sriram_user_id, initial_password):
            success, _ = self.test_login("sriram@company.com", initial_password, expected_success=True)
            if not success:
                print("❌ Initial login test failed")
                return False
        else:
            print("❌ Failed to set initial password")
            return False
        
        # Test 3: Update to new password
        print("\n🔐 STEP 3: PASSWORD UPDATE VERIFICATION")
        print("-" * 35)
        
        new_password = "newpassword456"
        if not self.update_user_password(sriram_user_id, new_password):
            print("❌ Password update failed")
            return False
        
        # Test 4: Verify old password fails
        print("\n❌ STEP 4: OLD PASSWORD REJECTION TEST")
        print("-" * 35)
        
        success, _ = self.test_login("sriram@company.com", initial_password, expected_success=False)
        if not success:
            print("❌ Old password should have been rejected")
            return False
        
        # Test 5: Verify new password works
        print("\n✅ STEP 5: NEW PASSWORD LOGIN TEST")
        print("-" * 30)
        
        success, _ = self.test_login("sriram@company.com", new_password, expected_success=True)
        if not success:
            print("❌ New password login failed")
            return False
        
        # Test 6: Password hashing consistency
        print("\n🔐 STEP 6: PASSWORD HASHING CONSISTENCY")
        print("-" * 35)
        
        test_passwords = ["hash1", "hash2", "hash3"]
        for i, password in enumerate(test_passwords):
            print(f"\nTest {i+1}: Password '{password}'")
            
            # Calculate expected SHA256 hash
            expected_hash = hashlib.sha256(password.encode()).hexdigest()
            print(f"   Expected SHA256: {expected_hash[:20]}...")
            
            # Update password
            if self.update_user_password(sriram_user_id, password):
                # Test login
                success, _ = self.test_login("sriram@company.com", password, expected_success=True)
                if success:
                    print(f"   ✅ Password '{password}' - Update and login successful")
                else:
                    print(f"   ❌ Password '{password}' - Login failed after update")
            else:
                print(f"   ❌ Password '{password}' - Update failed")
        
        # Test 7: End-to-end flow with fresh user
        print("\n🔄 STEP 7: END-TO-END FLOW TEST")
        print("-" * 25)
        
        e2e_email = f"e2e_test_{datetime.now().strftime('%H%M%S')}@company.com"
        e2e_user = self.create_user(e2e_email, "E2E Test User", "initial123")
        
        if e2e_user:
            e2e_user_id = e2e_user['id']
            
            # Test initial login
            success, _ = self.test_login(e2e_email, "initial123", expected_success=True)
            if success:
                # Update password
                if self.update_user_password(e2e_user_id, "updated456"):
                    # Test old password fails
                    success, _ = self.test_login(e2e_email, "initial123", expected_success=False)
                    if success:
                        # Test new password works
                        success, _ = self.test_login(e2e_email, "updated456", expected_success=True)
                        if success:
                            print("✅ End-to-end flow test successful")
                        else:
                            print("❌ E2E: New password login failed")
                    else:
                        print("❌ E2E: Old password was not rejected")
                else:
                    print("❌ E2E: Password update failed")
            else:
                print("❌ E2E: Initial login failed")
        
        print("\n" + "=" * 60)
        print("🎉 SRIRAM PASSWORD TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return True

def main():
    tester = FinalPasswordTest()
    tester.run_sriram_password_test()

if __name__ == "__main__":
    main()