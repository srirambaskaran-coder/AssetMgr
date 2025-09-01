#!/usr/bin/env python3
"""
Diagnostic script to understand password issues for sriram@company.com
"""

import requests
import json
import hashlib
from datetime import datetime

class PasswordDiagnostic:
    def __init__(self, base_url="https://inventoryhub-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        
    def login_admin(self):
        """Login as administrator"""
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
            return True
        else:
            print(f"❌ Administrator login failed: {response.status_code}")
            return False
    
    def get_admin_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
    
    def diagnose_sriram_user(self):
        """Diagnose sriram@company.com user state"""
        print("\n🔍 DIAGNOSING SRIRAM@COMPANY.COM USER STATE")
        print("=" * 50)
        
        # Get all users and find sriram
        response = requests.get(
            f"{self.api_url}/users",
            headers=self.get_admin_headers(),
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get users: {response.status_code}")
            return
        
        users = response.json()
        sriram_user = None
        
        for user in users:
            if user.get('email') == 'sriram@company.com':
                sriram_user = user
                break
        
        if not sriram_user:
            print("❌ sriram@company.com not found in database")
            return
        
        print("✅ Found sriram@company.com user:")
        print(f"   ID: {sriram_user.get('id')}")
        print(f"   Name: {sriram_user.get('name')}")
        print(f"   Email: {sriram_user.get('email')}")
        print(f"   Roles: {sriram_user.get('roles', [])}")
        print(f"   Is Active: {sriram_user.get('is_active', False)}")
        print(f"   Created At: {sriram_user.get('created_at', 'Unknown')}")
        print(f"   Designation: {sriram_user.get('designation', 'None')}")
        
        # Check if password_hash field exists (it won't be returned in API response)
        print(f"   Password hash field: Not visible in API response (security)")
        
        return sriram_user
    
    def test_password_reset_flow(self, user_id):
        """Test password reset flow"""
        print(f"\n🔄 TESTING PASSWORD RESET FLOW")
        print("=" * 40)
        
        # Set a known password
        new_password = "testpassword123"
        print(f"Setting password to: {new_password}")
        
        update_data = {"password": new_password}
        response = requests.put(
            f"{self.api_url}/users/{user_id}",
            json=update_data,
            headers=self.get_admin_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Password update API call successful")
            
            # Test login with new password
            login_data = {
                "email": "sriram@company.com",
                "password": new_password
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Login successful with new password")
                data = response.json()
                print(f"   Session token: {data.get('session_token', '')[:20]}...")
                return True
            else:
                print(f"❌ Login failed with new password: {response.status_code}")
                try:
                    print(f"   Error: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False
        else:
            print(f"❌ Password update failed: {response.status_code}")
            try:
                print(f"   Error: {response.json()}")
            except:
                print(f"   Response: {response.text}")
            return False
    
    def test_demo_user_login(self):
        """Test demo user login to verify login endpoint works"""
        print(f"\n🧪 TESTING DEMO USER LOGIN")
        print("=" * 30)
        
        demo_users = [
            ("admin@company.com", "password123"),
            ("employee@company.com", "password123"),
            ("manager@company.com", "password123")
        ]
        
        for email, password in demo_users:
            print(f"\nTesting {email}...")
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
            
            if response.status_code == 200:
                print(f"✅ {email} login successful")
            else:
                print(f"❌ {email} login failed: {response.status_code}")
    
    def create_fresh_test_user(self):
        """Create a fresh test user to verify the flow"""
        print(f"\n👤 CREATING FRESH TEST USER")
        print("=" * 35)
        
        test_email = f"fresh_test_{datetime.now().strftime('%H%M%S')}@company.com"
        test_password = "freshpass123"
        
        user_data = {
            "email": test_email,
            "name": "Fresh Test User",
            "roles": ["Employee"],
            "password": test_password
        }
        
        response = requests.post(
            f"{self.api_url}/users",
            json=user_data,
            headers=self.get_admin_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Created fresh test user: {test_email}")
            print(f"   User ID: {user.get('id')}")
            
            # Test immediate login
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Fresh user can login immediately after creation")
                
                # Test password update
                new_password = "updatedpass456"
                update_data = {"password": new_password}
                
                response = requests.put(
                    f"{self.api_url}/users/{user['id']}",
                    json=update_data,
                    headers=self.get_admin_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    print("✅ Password update successful")
                    
                    # Test login with new password
                    login_data = {
                        "email": test_email,
                        "password": new_password
                    }
                    
                    response = requests.post(
                        f"{self.api_url}/auth/login",
                        json=login_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print("✅ Login successful with updated password")
                        print("✅ Complete flow working for fresh user")
                        return True
                    else:
                        print(f"❌ Login failed with updated password: {response.status_code}")
                else:
                    print(f"❌ Password update failed: {response.status_code}")
            else:
                print(f"❌ Fresh user cannot login: {response.status_code}")
        else:
            print(f"❌ Failed to create fresh user: {response.status_code}")
        
        return False
    
    def run_full_diagnostic(self):
        """Run full diagnostic"""
        print("🔍 STARTING PASSWORD DIAGNOSTIC FOR SRIRAM@COMPANY.COM")
        print("=" * 60)
        
        if not self.login_admin():
            return
        
        # Step 1: Diagnose sriram user
        sriram_user = self.diagnose_sriram_user()
        if not sriram_user:
            return
        
        # Step 2: Test demo users to verify login endpoint
        self.test_demo_user_login()
        
        # Step 3: Test password reset flow for sriram
        self.test_password_reset_flow(sriram_user['id'])
        
        # Step 4: Create fresh test user to verify complete flow
        self.create_fresh_test_user()
        
        print("\n" + "=" * 60)
        print("🎯 DIAGNOSTIC COMPLETE")
        print("=" * 60)

def main():
    diagnostic = PasswordDiagnostic()
    diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    main()