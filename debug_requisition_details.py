import requests
import json

def debug_requisition_details():
    base_url = "https://asset-flow-app.preview.emergentagent.com"
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
    
    # Find a test requisition and show all its fields
    for req in requisitions:
        if "Test Employee for Approval" in req.get('requested_by_name', ''):
            print(f"Test requisition {req['id'][:8]}... full details:")
            for key, value in req.items():
                print(f"  {key}: {repr(value)}")
            print()
            
            # Try to manually check the status comparison
            status = req.get('status')
            print(f"Status comparison tests:")
            print(f"  status: {repr(status)}")
            print(f"  status == 'Pending': {status == 'Pending'}")
            print(f"  status != 'Pending': {status != 'Pending'}")
            print(f"  type(status): {type(status)}")
            
            # Check if there are any hidden characters
            if status:
                print(f"  status bytes: {status.encode('utf-8')}")
                print(f"  status length: {len(status)}")
            
            break

if __name__ == "__main__":
    debug_requisition_details()