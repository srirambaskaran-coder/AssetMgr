import requests
import json

def debug_user_relationships():
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
    
    # Get all users
    response = requests.get(f"{api_url}/users", headers=headers)
    
    if response.status_code != 200:
        print("Failed to get users")
        return
    
    users = response.json()
    print(f"Found {len(users)} users")
    
    # Find test users
    test_manager = None
    test_employee = None
    
    for user in users:
        if "Test Manager for Approval" in user.get('name', ''):
            test_manager = user
            print(f"Found Test Manager: {user['name']} (ID: {user['id']})")
        elif "Test Employee for Approval" in user.get('name', ''):
            test_employee = user
            print(f"Found Test Employee: {user['name']} (ID: {user['id']})")
            print(f"  Reporting Manager ID: {user.get('reporting_manager_id', 'None')}")
            print(f"  Reporting Manager Name: {user.get('reporting_manager_name', 'None')}")
    
    if test_manager and test_employee:
        print(f"\nRelationship Check:")
        print(f"Test Manager ID: {test_manager['id']}")
        print(f"Test Employee Reporting Manager ID: {test_employee.get('reporting_manager_id', 'None')}")
        print(f"Match: {test_manager['id'] == test_employee.get('reporting_manager_id')}")
    
    # Get recent requisitions to check requester details
    response = requests.get(f"{api_url}/asset-requisitions", headers=headers)
    if response.status_code == 200:
        requisitions = response.json()
        print(f"\nRecent Test Requisitions:")
        for req in requisitions[-5:]:
            if "Test Employee for Approval" in req.get('requested_by_name', ''):
                print(f"Requisition ID: {req['id'][:8]}...")
                print(f"  Requested by ID: {req.get('requested_by', 'Unknown')}")
                print(f"  Requested by Name: {req.get('requested_by_name', 'Unknown')}")
                print(f"  Status: {req.get('status', 'Unknown')}")

if __name__ == "__main__":
    debug_user_relationships()