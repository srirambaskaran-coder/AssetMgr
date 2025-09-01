import requests
import json

def simple_manager_test():
    base_url = "https://inventoryhub-8.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as test manager
    login_data = {"email": "testmanager_172755@company.com", "password": "TestPassword123!"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("Failed to login as test manager")
        return
    
    token = response.json()['session_token']
    user_info = response.json()['user']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print(f"Logged in as: {user_info['name']} (ID: {user_info['id']})")
    
    # Test /auth/me to verify current user
    response = requests.get(f"{api_url}/auth/me", headers=headers)
    if response.status_code == 200:
        current_user = response.json()
        print(f"Current user from /auth/me: {current_user['name']} (ID: {current_user['id']})")
    
    # Try manager action on a test requisition
    requisition_id = "06f6ea82-b8b8-4b8b-8b8b-8b8b8b8b8b8b"  # One of our test requisitions
    
    # First get the correct requisition ID
    response = requests.get(f"{api_url}/asset-requisitions", headers=headers)
    if response.status_code == 200:
        requisitions = response.json()
        print(f"Manager can see {len(requisitions)} requisitions")
        for req in requisitions[-5:]:  # Show last 5
            print(f"  ID: {req['id'][:8]}... Status: {req.get('status')} Requested by: {req.get('requested_by_name')}")
        
        for req in requisitions:
            if req.get('requested_by_name') == 'Test Employee for Approval' and req.get('status') == 'Pending':
                requisition_id = req['id']
                print(f"Found test requisition: {requisition_id[:8]}...")
                break
    else:
        print(f"Failed to get requisitions: {response.status_code}")
        return
    
    approve_data = {
        "action": "approve",
        "reason": "Simple test approval"
    }
    
    print(f"\nTrying manager action on requisition: {requisition_id[:8]}...")
    response = requests.post(f"{api_url}/asset-requisitions/{requisition_id}/manager-action", 
                           json=approve_data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        try:
            error = response.json()
            print(f"Error: {error}")
        except:
            print(f"Error text: {response.text}")
    else:
        result = response.json()
        print(f"Success: {result.get('message', 'No message')}")

if __name__ == "__main__":
    simple_manager_test()