import requests
import json

def debug_requisition_status():
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
    print(f"Found {len(requisitions)} requisitions")
    
    # Show recent requisitions and their status
    for req in requisitions[-10:]:  # Last 10 requisitions
        print(f"ID: {req['id'][:8]}... Status: '{req.get('status', 'NO STATUS')}' Created: {req.get('created_at', 'Unknown')}")
        print(f"  Requested by: {req.get('requested_by_name', 'Unknown')}")
        print(f"  Asset type: {req.get('asset_type_name', 'Unknown')}")
        print()

if __name__ == "__main__":
    debug_requisition_status()