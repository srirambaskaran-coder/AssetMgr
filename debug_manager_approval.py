import requests
import json

class ManagerApprovalDebugger:
    def __init__(self, base_url="https://inventoryhub-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}

    def login(self, email, password, role_name):
        """Login and store token"""
        url = f"{self.api_url}/auth/login"
        data = {"email": email, "password": password}
        
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            self.tokens[role_name] = result['session_token']
            print(f"✅ {role_name} login successful")
            return True
        else:
            print(f"❌ {role_name} login failed: {response.status_code}")
            return False

    def debug_manager_approval_issue(self):
        """Debug why manager approval is failing"""
        print("🔍 === DEBUGGING MANAGER APPROVAL ISSUE ===")
        
        # Login as admin and manager
        if not self.login("admin@company.com", "password123", "Administrator"):
            return
        if not self.login("manager@company.com", "password123", "Manager"):
            return
        
        # Get all requisitions as admin to find Sriram's
        print("\n1️⃣ Getting all requisitions to find Sriram's...")
        url = f"{self.api_url}/asset-requisitions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.tokens["Administrator"]}'
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
                print(f"✅ Found Sriram's requisition:")
                print(f"   - ID: {sriram_req.get('id')}")
                print(f"   - Status: {sriram_req.get('status')}")
                print(f"   - Manager ID: {sriram_req.get('manager_id')}")
                print(f"   - Manager Name: {sriram_req.get('manager_name')}")
                print(f"   - Requested By: {sriram_req.get('requested_by_name')}")
                
                # Test manager approval
                print(f"\n2️⃣ Testing manager approval...")
                req_id = sriram_req.get('id')
                
                approval_url = f"{self.api_url}/asset-requisitions/{req_id}/manager-action"
                approval_headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.tokens["Manager"]}'
                }
                approval_data = {
                    "action": "approve",
                    "reason": "Approved for development work"
                }
                
                print(f"   - Approval URL: {approval_url}")
                print(f"   - Approval Data: {approval_data}")
                
                approval_response = requests.post(approval_url, json=approval_data, headers=approval_headers, timeout=10)
                
                print(f"   - Response Status: {approval_response.status_code}")
                
                if approval_response.status_code == 200:
                    result = approval_response.json()
                    print(f"✅ Approval successful!")
                    print(f"   - Message: {result.get('message')}")
                    new_status = result.get('requisition', {}).get('status')
                    print(f"   - New Status: {new_status}")
                else:
                    print(f"❌ Approval failed!")
                    try:
                        error = approval_response.json()
                        print(f"   - Error: {error}")
                    except:
                        print(f"   - Response Text: {approval_response.text}")
                    
                    # Debug the specific error
                    if approval_response.status_code == 400:
                        print(f"\n🔍 Debugging 400 error...")
                        print(f"   - Checking requisition status...")
                        print(f"   - Current status: {sriram_req.get('status')}")
                        print(f"   - Expected status for manager action: 'Pending'")
                        
                        if sriram_req.get('status') != 'Pending':
                            print(f"   ❌ Issue: Requisition status is not 'Pending'")
                        else:
                            print(f"   ✅ Requisition status is correct")
                    
                    elif approval_response.status_code == 403:
                        print(f"\n🔍 Debugging 403 error...")
                        print(f"   - Checking manager relationship...")
                        manager_id = "464f2383-d146-44ff-963d-e7bf492a6117"  # Kiran's ID
                        req_manager_id = sriram_req.get('manager_id')
                        
                        if req_manager_id != manager_id:
                            print(f"   ❌ Issue: Requisition manager_id ({req_manager_id}) doesn't match current manager ({manager_id})")
                        else:
                            print(f"   ✅ Manager relationship is correct")
                            
                            # Check if manager has correct role
                            print(f"   - Checking manager role...")
                            # Get manager user data
                            manager_url = f"{self.api_url}/users/{manager_id}"
                            manager_response = requests.get(manager_url, headers=headers, timeout=10)
                            if manager_response.status_code == 200:
                                manager_data = manager_response.json()
                                manager_roles = manager_data.get('roles', [])
                                print(f"   - Manager roles: {manager_roles}")
                                if 'Manager' in manager_roles:
                                    print(f"   ✅ Manager has correct role")
                                else:
                                    print(f"   ❌ Manager missing Manager role")
                            else:
                                print(f"   ❌ Could not get manager data")
            else:
                print(f"❌ Could not find Sriram's requisition")
        else:
            print(f"❌ Failed to get requisitions: {response.status_code}")

if __name__ == "__main__":
    debugger = ManagerApprovalDebugger()
    debugger.debug_manager_approval_issue()