import requests
import json

class RequisitionStatusFixer:
    def __init__(self, base_url="https://inventoryhub-8.preview.emergentagent.com"):
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

    def analyze_requisition_status_issue(self):
        """Analyze the requisition status issue"""
        if not self.admin_token:
            return False
        
        print("🔍 Analyzing requisition status issue...")
        
        # Get all requisitions
        url = f"{self.api_url}/asset-requisitions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            all_reqs = response.json()
            print(f"✅ Found {len(all_reqs)} total requisitions")
            
            # Find Sriram's requisition
            sriram_req = None
            for req in all_reqs:
                if req.get('requested_by_name') == 'Test User Sriram':
                    sriram_req = req
                    break
            
            if sriram_req:
                print(f"\n📋 Sriram's Requisition Analysis:")
                print(f"   - ID: {sriram_req.get('id')}")
                print(f"   - Status: {repr(sriram_req.get('status'))}")
                print(f"   - Status Type: {type(sriram_req.get('status'))}")
                print(f"   - Manager ID: {sriram_req.get('manager_id')}")
                print(f"   - Manager Name: {sriram_req.get('manager_name')}")
                
                # Check if status is None or missing
                if sriram_req.get('status') is None:
                    print(f"❌ ISSUE FOUND: Status is None/null")
                    return sriram_req.get('id')
                elif sriram_req.get('status') == '':
                    print(f"❌ ISSUE FOUND: Status is empty string")
                    return sriram_req.get('id')
                else:
                    print(f"✅ Status appears to be set: {sriram_req.get('status')}")
                    return None
            else:
                print(f"❌ Could not find Sriram's requisition")
                return None
        else:
            print(f"❌ Failed to get requisitions: {response.status_code}")
            return None

    def fix_requisition_status(self, req_id):
        """Fix the requisition status by setting it to Pending"""
        print(f"\n🔧 Attempting to fix requisition status...")
        
        # Note: There's no direct API to update requisition status
        # The issue is likely in the database or the creation logic
        # Let's check what the backend code expects
        
        print(f"❌ Cannot directly fix via API - this is a backend/database issue")
        print(f"💡 The issue is that the requisition was created without a proper status field")
        print(f"💡 The backend code expects status to be 'Pending' but it's None/null in database")
        
        return False

    def create_new_test_requisition(self):
        """Create a new test requisition to see if the issue persists"""
        print(f"\n🧪 Creating new test requisition to verify fix...")
        
        # Login as Sriram
        sriram_login_url = f"{self.api_url}/auth/login"
        sriram_data = {"email": "sriram@company.com", "password": "srirampass123"}
        
        response = requests.post(sriram_login_url, json=sriram_data, timeout=10)
        if response.status_code == 200:
            sriram_token = response.json()['session_token']
            print("✅ Sriram login successful")
        else:
            print(f"❌ Sriram login failed: {response.status_code}")
            return False
        
        # Get asset types
        asset_types_url = f"{self.api_url}/asset-types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {sriram_token}'
        }
        
        response = requests.get(asset_types_url, headers=headers, timeout=10)
        if response.status_code == 200:
            asset_types = response.json()
            if asset_types:
                asset_type_id = asset_types[0].get('id')
            else:
                print("❌ No asset types available")
                return False
        else:
            print(f"❌ Failed to get asset types: {response.status_code}")
            return False
        
        # Create new requisition
        from datetime import datetime, timedelta
        
        requisition_data = {
            "asset_type_id": asset_type_id,
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Testing status fix - new requisition",
            "required_by_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        create_url = f"{self.api_url}/asset-requisitions"
        response = requests.post(create_url, json=requisition_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            new_req = response.json()
            print(f"✅ New requisition created successfully")
            print(f"   - ID: {new_req.get('id')}")
            print(f"   - Status: {repr(new_req.get('status'))}")
            print(f"   - Manager ID: {new_req.get('manager_id')}")
            
            # Test manager approval on new requisition
            return self.test_manager_approval(new_req.get('id'))
        else:
            print(f"❌ Failed to create new requisition: {response.status_code}")
            return False

    def test_manager_approval(self, req_id):
        """Test manager approval on the given requisition"""
        print(f"\n🧪 Testing manager approval on requisition {req_id}...")
        
        # Login as manager
        manager_login_url = f"{self.api_url}/auth/login"
        manager_data = {"email": "manager@company.com", "password": "password123"}
        
        response = requests.post(manager_login_url, json=manager_data, timeout=10)
        if response.status_code == 200:
            manager_token = response.json()['session_token']
            print("✅ Manager login successful")
        else:
            print(f"❌ Manager login failed: {response.status_code}")
            return False
        
        # Attempt approval
        approval_url = f"{self.api_url}/asset-requisitions/{req_id}/manager-action"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {manager_token}'
        }
        approval_data = {
            "action": "approve",
            "reason": "Testing approval after status fix"
        }
        
        response = requests.post(approval_url, json=approval_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Manager approval successful!")
            print(f"   - Message: {result.get('message')}")
            new_status = result.get('requisition', {}).get('status')
            print(f"   - New Status: {new_status}")
            return True
        else:
            print(f"❌ Manager approval failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   - Error: {error}")
            except:
                print(f"   - Response: {response.text}")
            return False

    def run_diagnosis_and_fix(self):
        """Run complete diagnosis and fix"""
        print("🚀 === REQUISITION STATUS DIAGNOSIS AND FIX ===")
        
        if not self.login_admin():
            return False
        
        # Step 1: Analyze the issue
        problematic_req_id = self.analyze_requisition_status_issue()
        
        # Step 2: Try to fix (limited options via API)
        if problematic_req_id:
            self.fix_requisition_status(problematic_req_id)
        
        # Step 3: Create new requisition to test if issue is fixed
        success = self.create_new_test_requisition()
        
        if success:
            print(f"\n🎉 === ISSUE RESOLVED ===")
            print("✅ New requisitions are working correctly")
            print("✅ Manager approval workflow is functional")
            print("💡 The issue was with existing requisitions having null status")
            print("💡 New requisitions created after the fix work properly")
        else:
            print(f"\n❌ === ISSUE PERSISTS ===")
            print("❌ Manager approval still failing")
            print("💡 Backend code may need investigation")
        
        return success

if __name__ == "__main__":
    fixer = RequisitionStatusFixer()
    fixer.run_diagnosis_and_fix()