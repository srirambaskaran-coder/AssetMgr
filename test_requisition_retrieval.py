import requests
import json

def test_requisition_retrieval():
    base_url = "https://inventoryhub-8.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as admin
    login_data = {"email": "admin@company.com", "password": "password123"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("Failed to login")
        return
    
    token = response.json()['session_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Get all requisitions
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
    print(f"Test requisition ID: {req_id}")
    print(f"Status: {repr(test_req['status'])}")
    
    # Try to get the specific requisition by ID (this would simulate what the backend does)
    # Since we don't have direct database access, let's try a different approach
    
    # Let's try the manager action with a non-existent requisition to see if we get a different error
    fake_req_id = "00000000-0000-0000-0000-000000000000"
    
    approve_data = {
        "action": "approve",
        "reason": "Test with fake ID"
    }
    
    print(f"\nTrying manager action on fake requisition...")
    response = requests.post(f"{api_url}/asset-requisitions/{fake_req_id}/manager-action", 
                           json=approve_data, headers=headers)
    
    print(f"Fake requisition response: {response.status_code}")
    if response.status_code != 200:
        try:
            error = response.json()
            print(f"Fake requisition error: {error}")
        except:
            print(f"Fake requisition text: {response.text}")
    
    # Now try with the real requisition
    print(f"\nTrying manager action on real requisition...")
    response = requests.post(f"{api_url}/asset-requisitions/{req_id}/manager-action", 
                           json=approve_data, headers=headers)
    
    print(f"Real requisition response: {response.status_code}")
    if response.status_code != 200:
        try:
            error = response.json()
            print(f"Real requisition error: {error}")
        except:
            print(f"Real requisition text: {response.text}")

if __name__ == "__main__":
    test_requisition_retrieval()