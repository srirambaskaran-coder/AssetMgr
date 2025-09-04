import requests
import json

def debug_enum_values():
    base_url = "https://asset-track-2.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login as admin
    login_data = {"email": "admin@company.com", "password": "password123"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("Failed to login")
        return
    
    token = response.json()['session_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Get all requisitions and check their exact status values
    response = requests.get(f"{api_url}/asset-requisitions", headers=headers)
    
    if response.status_code != 200:
        print("Failed to get requisitions")
        return
    
    requisitions = response.json()
    
    # Check status values
    status_values = set()
    for req in requisitions:
        status = req.get('status')
        status_values.add(status)
        if "Test Employee for Approval" in req.get('requested_by_name', ''):
            print(f"Test requisition {req['id'][:8]}...")
            print(f"  Status: '{status}' (type: {type(status)})")
            print(f"  Status repr: {repr(status)}")
            print(f"  Status == 'Pending': {status == 'Pending'}")
            print()
    
    print(f"All status values found: {status_values}")
    
    # Also check the enum values from the backend
    print("\nEnum comparison:")
    print(f"'Pending' == 'Pending': {'Pending' == 'Pending'}")

if __name__ == "__main__":
    debug_enum_values()