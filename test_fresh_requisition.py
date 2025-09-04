import requests
import json
from datetime import datetime, timedelta

def test_fresh_requisition():
    base_url = "https://asset-track-2.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as admin
    login_data = {"email": "admin@company.com", "password": "password123"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("Failed to login as admin")
        return
    
    admin_token = response.json()['session_token']
    admin_headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
    
    # Login as test employee
    employee_login = {"email": "testemp_172755@company.com", "password": "TestPassword123!"}
    response = requests.post(f"{api_url}/auth/login", json=employee_login)
    
    if response.status_code != 200:
        print("Failed to login as test employee")
        return
    
    employee_token = response.json()['session_token']
    employee_headers = {'Authorization': f'Bearer {employee_token}', 'Content-Type': 'application/json'}
    
    # Get asset types to find one for testing
    response = requests.get(f"{api_url}/asset-types", headers=admin_headers)
    if response.status_code != 200:
        print("Failed to get asset types")
        return
    
    asset_types = response.json()
    if not asset_types:
        print("No asset types found")
        return
    
    asset_type_id = asset_types[0]['id']
    print(f"Using asset type: {asset_types[0]['name']} (ID: {asset_type_id})")
    
    # Create a fresh requisition
    required_by_date = (datetime.now() + timedelta(days=7)).isoformat()
    
    requisition_data = {
        "asset_type_id": asset_type_id,
        "request_type": "New Allocation",
        "request_for": "Self",
        "justification": "Fresh requisition for immediate testing",
        "required_by_date": required_by_date
    }
    
    print(f"\nCreating fresh requisition...")
    response = requests.post(f"{api_url}/asset-requisitions", 
                           json=requisition_data, headers=employee_headers)
    
    if response.status_code != 200:
        print(f"Failed to create requisition: {response.status_code}")
        try:
            error = response.json()
            print(f"Error: {error}")
        except:
            print(f"Error text: {response.text}")
        return
    
    new_req = response.json()
    req_id = new_req['id']
    
    print(f"✅ Created fresh requisition: {req_id[:8]}...")
    print(f"   Status: {repr(new_req['status'])}")
    print(f"   Requested by: {new_req['requested_by_name']}")
    
    # Immediately try manager action on the fresh requisition
    approve_data = {
        "action": "approve",
        "reason": "Immediate test approval on fresh requisition"
    }
    
    print(f"\nTrying manager action on fresh requisition...")
    response = requests.post(f"{api_url}/asset-requisitions/{req_id}/manager-action", 
                           json=approve_data, headers=admin_headers)
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS: {result.get('message', 'No message')}")
        
        requisition = result.get('requisition', {})
        print(f"   New Status: {requisition.get('status', 'Unknown')}")
        print(f"   Manager Action By: {requisition.get('manager_action_by_name', 'Unknown')}")
        print(f"   Approval Reason: {requisition.get('manager_approval_reason', 'Unknown')}")
    else:
        try:
            error = response.json()
            print(f"❌ FAILED: {error}")
        except:
            print(f"❌ FAILED: {response.text}")

if __name__ == "__main__":
    test_fresh_requisition()