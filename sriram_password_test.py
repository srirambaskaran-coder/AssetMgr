#!/usr/bin/env python3
"""
Focused test script for sriram@company.com password update and login issues
"""

import requests
import json
import hashlib
from datetime import datetime

class SriramPasswordTester:
    def __init__(self, base_url="https://resource-manager-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.sriram_user_id = None
        
    def login_admin(self):
        """Login as administrator to get admin token"""
        print("🔐 Logging in as Administrator...")
        
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
            data = response.json()
            self.admin_token = data.get('session_token')
            print(f"✅ Administrator login successful")
            print(f"   Token: {self.admin_token[:20]}...")
            return True
        else:
            print(f"❌ Administrator login failed: {response.status_code}")
            try:
                print(f"   Error: {response.json()}")
            except:
                print(f"   Response: {response.text}")
            return False
    
    def get_admin_headers(self):
        """Get headers with admin authorization"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
    
    def check_user_exists(self, email):
        """Check if user exists in database"""
        print(f"\n📋 Checking if user {email} exists...")
        
        response = requests.get(
            f"{self.api_url}/users",
            headers=self.get_admin_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get('email') == email:
                    print(f"✅ User {email} found in database")
                    print(f"   User ID: {user.get('id')}")
                    print(f"   Name: {user.get('name')}")
                    print(f"   Roles: {user.get('roles', [])}")
                    print(f"   Is Active: {user.get('is_active', False)}")
                    return user
            
            print(f"❌ User {email} NOT found in database")
            return None
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            return None
    
    def create_user(self, email, name, password):
        """Create a new user"""
        print(f"\n👤 Creating user {email}...")
        
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
            print(f"✅ User {email} created successfully")
            print(f"   User ID: {user.get('id')}")
            return user
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            try:
                print(f"   Error: {response.json()}")
            except:
                print(f"   Response: {response.text}")
            return None
    
    def test_login(self, email, password, should_succeed=True):
        """Test login with given credentials"""
        print(f"\n🔑 Testing login for {email} with password '{password}'...")
        
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
        
        if should_succeed:
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful")
                print(f"   Session token: {data.get('session_token', '')[:20]}...")
                user_data = data.get('user', {})
                print(f"   User name: {user_data.get('name', 'Unknown')}")
                print(f"   User roles: {user_data.get('roles', [])}")
                return True, data
            else:
                print(f"❌ Login failed (expected success): {response.status_code}")
                try:
                    print(f"   Error: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, None
        else:
            if response.status_code == 401:
                print(f"✅ Login correctly rejected (as expected)")
                return True, None
            else:
                print(f"❌ Login should have failed but got: {response.status_code}")
                return False, None
    
    def update_user_password(self, user_id, new_password):
        """Update user password via PUT /api/users/{user_id}"""
        print(f"\n🔄 Updating password for user {user_id}...")
        
        update_data = {
            "password": new_password
        }
        
        response = requests.put(
            f"{self.api_url}/users/{user_id}",
            json=update_data,
            headers=self.get_admin_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Password update successful")
            print(f"   Updated user: {user.get('name', 'Unknown')}")
            print(f"   User email: {user.get('email', 'Unknown')}")
            return True
        else:
            print(f"❌ Password update failed: {response.status_code}")
            try:
                print(f"   Error: {response.json()}")
            except:
                print(f"   Response: {response.text}")
            return False
    
    def test_password_hashing_consistency(self, email, user_id):
        """Test password hashing consistency across multiple updates"""
        print(f"\n🔐 Testing password hashing consistency for {email}...")
        
        test_passwords = ["hash_test_1", "hash_test_2", "hash_test_3"]
        
        for i, password in enumerate(test_passwords):
            print(f"\n   Test {i+1}: Password '{password}'")
            
            # Calculate expected hash
            expected_hash = hashlib.sha256(password.encode()).hexdigest()
            print(f"   Expected SHA256: {expected_hash[:20]}...")
            
            # Update password
            if self.update_user_password(user_id, password):
                # Test login
                success, _ = self.test_login(email, password, should_succeed=True)
                if success:
                    print(f"   ✅ Password {password} - Update and login successful")
                else:
                    print(f"   ❌ Password {password} - Login failed after update")
            else:
                print(f"   ❌ Password {password} - Update failed")
    
    def run_comprehensive_test(self):
        """Run comprehensive password update and login test"""
        print("🚀 Starting Comprehensive Password Update and Login Test for sriram@company.com")
        print("=" * 80)
        
        # Step 1: Login as administrator
        if not self.login_admin():
            print("❌ Cannot proceed without admin access")
            return False
        
        # Step 2: Check if sriram@company.com exists
        sriram_user = self.check_user_exists("sriram@company.com")
        
        if not sriram_user:
            # Create the user
            sriram_user = self.create_user("sriram@company.com", "Sriram Test User", "password123")
            if not sriram_user:
                print("❌ Cannot proceed without creating sriram user")
                return False
        
        self.sriram_user_id = sriram_user['id']
        
        # Step 3: Test initial login with password123
        print("\n" + "="*50)
        print("STEP 3: Initial Login Test")
        print("="*50)
        
        success, _ = self.test_login("sriram@company.com", "password123", should_succeed=True)
        if not success:
            print("❌ Initial login test failed")
            return False
        
        # Step 4: Update password
        print("\n" + "="*50)
        print("STEP 4: Password Update Test")
        print("="*50)
        
        new_password = "newpassword456"
        if not self.update_user_password(self.sriram_user_id, new_password):
            print("❌ Password update failed")
            return False
        
        # Step 5: Test old password fails
        print("\n" + "="*50)
        print("STEP 5: Old Password Rejection Test")
        print("="*50)
        
        success, _ = self.test_login("sriram@company.com", "password123", should_succeed=False)
        if not success:
            print("❌ Old password should have been rejected")
            return False
        
        # Step 6: Test new password works
        print("\n" + "="*50)
        print("STEP 6: New Password Login Test")
        print("="*50)
        
        success, _ = self.test_login("sriram@company.com", new_password, should_succeed=True)
        if not success:
            print("❌ New password login failed")
            return False
        
        # Step 7: Test password hashing consistency
        print("\n" + "="*50)
        print("STEP 7: Password Hashing Consistency Test")
        print("="*50)
        
        self.test_password_hashing_consistency("sriram@company.com", self.sriram_user_id)
        
        # Step 8: End-to-end flow test with new user
        print("\n" + "="*50)
        print("STEP 8: End-to-End Flow Test")
        print("="*50)
        
        # Create a new test user
        e2e_email = f"e2e_test_{datetime.now().strftime('%H%M%S')}@company.com"
        e2e_user = self.create_user(e2e_email, "E2E Test User", "initial123")
        
        if e2e_user:
            e2e_user_id = e2e_user['id']
            
            # Test initial login
            success, _ = self.test_login(e2e_email, "initial123", should_succeed=True)
            if success:
                # Update password
                if self.update_user_password(e2e_user_id, "updated456"):
                    # Test old password fails
                    success, _ = self.test_login(e2e_email, "initial123", should_succeed=False)
                    if success:
                        # Test new password works
                        success, _ = self.test_login(e2e_email, "updated456", should_succeed=True)
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
        
        print("\n" + "="*80)
        print("🎉 COMPREHENSIVE PASSWORD TEST COMPLETED")
        print("="*80)
        
        return True

def main():
    tester = SriramPasswordTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()