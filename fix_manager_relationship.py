import requests
import json

class ManagerRelationshipFixer:
    def __init__(self, base_url="https://asset-flow-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None

    def login_admin(self):
        """Login as Administrator"""
        url = f"{self.api_url}/auth/login"
        data = {"email": "admin@company.com", "password": "password123"}
        
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            self.admin_token = result['session_token']
            print("✅ Administrator login successful")
            return True
        else:
            print(f"❌ Administrator login failed: {response.status_code}")
            return False

    def fix_sriram_manager_relationship(self):
        """Fix Sriram's reporting manager relationship"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        # Sriram's user ID from debug results
        sriram_id = "cf602201-1656-40e0-a9cf-beb85f96e0d4"
        # Kiran's user ID from debug results  
        kiran_id = "464f2383-d146-44ff-963d-e7bf492a6117"
        
        url = f"{self.api_url}/users/{sriram_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        update_data = {
            "reporting_manager_id": kiran_id
        }
        
        print(f"🔧 Setting Kiran as Sriram's reporting manager...")
        response = requests.put(url, json=update_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Successfully updated Sriram's reporting manager")
            print(f"   - Reporting Manager ID: {result.get('reporting_manager_id')}")
            print(f"   - Reporting Manager Name: {result.get('reporting_manager_name')}")
            return True
        else:
            print(f"❌ Failed to update Sriram's reporting manager: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text}")
            return False

    def set_sriram_password(self):
        """Set a password for Sriram so he can login"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        sriram_id = "cf602201-1656-40e0-a9cf-beb85f96e0d4"
        
        url = f"{self.api_url}/users/{sriram_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        update_data = {
            "password": "srirampass123"
        }
        
        print(f"🔧 Setting password for Sriram...")
        response = requests.put(url, json=update_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Successfully set password for Sriram")
            print("   - Password: srirampass123")
            return True
        else:
            print(f"❌ Failed to set password for Sriram: {response.status_code}")
            return False

    def run_fixes(self):
        """Run all fixes"""
        print("🚀 Starting Manager-Employee Relationship Fixes...")
        
        if not self.login_admin():
            return False
        
        # Fix 1: Set Sriram's reporting manager
        success1 = self.fix_sriram_manager_relationship()
        
        # Fix 2: Set Sriram's password so he can login
        success2 = self.set_sriram_password()
        
        if success1 and success2:
            print("\n✅ All fixes completed successfully!")
            print("🔍 Now Sriram should be able to:")
            print("   1. Login with email: sriram@company.com, password: srirampass123")
            print("   2. Create asset requisitions that will have Kiran as manager_id")
            print("   3. Kiran should be able to see and approve Sriram's requests")
            return True
        else:
            print("\n❌ Some fixes failed")
            return False

if __name__ == "__main__":
    fixer = ManagerRelationshipFixer()
    fixer.run_fixes()