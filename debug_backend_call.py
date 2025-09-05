import requests
import json

def debug_backend_call():
    base_url = "https://resource-manager-6.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as admin
    login_data = {"email": "admin@company.com", "password": "password123"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("Failed to login")
        return
    
    token = response.json()['session_token']
    user_info = response.json()['user']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print(f"Logged in as: {user_info['name']}")
    print(f"User roles: {user_info.get('roles', [])}")
    print(f"User ID: {user_info['id']}")
    
    # Get a specific test requisition
    response = requests.get(f"{api_url}/asset-requisitions", headers=headers)
    
    if response.status_code != 200:
        print("Failed to get requisitions")
        return
    
    requisitions = response.json()
    
    # Find a test requisition
    test_req = None
    for req in requisitions:
        if "Test Employee for Approval" in req.get('requested_by_name', ''):
            test_req = req
            break
    
    if not test_req:
        print("No test requisition found")
        return
    
    req_id = test_req['id']
    print(f"\nFound test requisition: {req_id}")
    print(f"Status: {repr(test_req['status'])}")
    print(f"Requested by: {test_req['requested_by_name']} (ID: {test_req['requested_by']})")
    
    # Get the requester details
    response = requests.get(f"{api_url}/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        requester = None
        for user in users:
            if user['id'] == test_req['requested_by']:
                requester = user
                break
        
        if requester:
            print(f"Requester details:")
            print(f"  Name: {requester['name']}")
            print(f"  ID: {requester['id']}")
            print(f"  Reporting Manager ID: {requester.get('reporting_manager_id', 'None')}")
            print(f"  Reporting Manager Name: {requester.get('reporting_manager_name', 'None')}")
    
    # Now try the manager action
    approve_data = {
        "action": "approve",
        "reason": "Debug test approval"
    }
    
    print(f"\nTrying manager action on requisition {req_id[:8]}...")
    response = requests.post(f"{api_url}/asset-requisitions/{req_id}/manager-action", 
                           json=approve_data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code != 200:
        print(f"Response text: {response.text}")
        try:
            error = response.json()
            print(f"Error JSON: {error}")
        except:
            pass
    else:
        try:
            result = response.json()
            print(f"Success JSON: {result}")
        except:
            print(f"Success text: {response.text}")

if __name__ == "__main__":
    debug_backend_call()