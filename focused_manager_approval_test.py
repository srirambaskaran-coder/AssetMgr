import requests
import json
from datetime import datetime, timedelta

def focused_manager_approval_test():
    base_url = "https://asset-flow-app.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🎯 FOCUSED MANAGER APPROVAL WORKFLOW TESTING")
    print("=" * 60)
    
    # Login as admin to get all requisitions and test manager actions
    login_data = {"email": "admin@company.com", "password": "password123"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Failed to login as admin")
        return False
    
    admin_token = response.json()['session_token']
    admin_headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
    
    # Get all requisitions
    response = requests.get(f"{api_url}/asset-requisitions", headers=admin_headers)
    if response.status_code != 200:
        print("❌ Failed to get requisitions")
        return False
    
    requisitions = response.json()
    print(f"📋 Found {len(requisitions)} total requisitions")
    
    # Find a pending requisition from test employee
    test_requisition = None
    for req in requisitions:
        if (req.get('requested_by_name') == 'Test Employee for Approval' and 
            req.get('status') == 'Pending'):
            test_requisition = req
            break
    
    if not test_requisition:
        print("❌ No pending test requisition found")
        return False
    
    req_id = test_requisition['id']
    print(f"✅ Found test requisition: {req_id[:8]}...")
    print(f"   Status: {test_requisition['status']}")
    print(f"   Requested by: {test_requisition['requested_by_name']}")
    print(f"   Requested by ID: {test_requisition['requested_by']}")
    
    # Test 1: Manager Action Endpoint - Approve
    print(f"\n🎯 Test 1: Manager Approve Action (as Administrator)")
    approve_data = {
        "action": "approve",
        "reason": "Approved for testing manager approval workflow"
    }
    
    response = requests.post(f"{api_url}/asset-requisitions/{req_id}/manager-action", 
                           json=approve_data, headers=admin_headers)
    
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS: {result.get('message', 'No message')}")
        
        requisition = result.get('requisition', {})
        print(f"   New Status: {requisition.get('status', 'Unknown')}")
        print(f"   Manager Action By: {requisition.get('manager_action_by_name', 'Unknown')}")
        print(f"   Approval Reason: {requisition.get('manager_approval_reason', 'Unknown')}")
        print(f"   Approval Date: {requisition.get('manager_approval_date', 'Unknown')}")
        
        # Test 2: HR Action Endpoint - Approve the manager-approved request
        print(f"\n🏥 Test 2: HR Approve Action")
        hr_approve_data = {
            "action": "approve",
            "reason": "HR approved for testing workflow"
        }
        
        response = requests.post(f"{api_url}/asset-requisitions/{req_id}/hr-action", 
                               json=hr_approve_data, headers=admin_headers)
        
        print(f"Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'No message')}")
            
            requisition = result.get('requisition', {})
            print(f"   Final Status: {requisition.get('status', 'Unknown')}")
            print(f"   HR Action By: {requisition.get('hr_action_by_name', 'Unknown')}")
            print(f"   HR Approval Reason: {requisition.get('hr_approval_reason', 'Unknown')}")
            print(f"   HR Approval Date: {requisition.get('hr_approval_date', 'Unknown')}")
        else:
            try:
                error = response.json()
                print(f"❌ FAILED: {error}")
            except:
                print(f"❌ FAILED: {response.text}")
    else:
        try:
            error = response.json()
            print(f"❌ FAILED: {error}")
        except:
            print(f"❌ FAILED: {response.text}")
    
    # Test 3: Find another pending requisition for rejection test
    print(f"\n🎯 Test 3: Manager Reject Action")
    reject_requisition = None
    for req in requisitions:
        if (req.get('requested_by_name') == 'Test Employee for Approval' and 
            req.get('status') == 'Pending' and req['id'] != req_id):
            reject_requisition = req
            break
    
    if reject_requisition:
        reject_req_id = reject_requisition['id']
        print(f"Found requisition for rejection test: {reject_req_id[:8]}...")
        
        reject_data = {
            "action": "reject",
            "reason": "Rejected for testing manager rejection workflow"
        }
        
        response = requests.post(f"{api_url}/asset-requisitions/{reject_req_id}/manager-action", 
                               json=reject_data, headers=admin_headers)
        
        print(f"Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'No message')}")
            
            requisition = result.get('requisition', {})
            print(f"   Status: {requisition.get('status', 'Unknown')}")
            print(f"   Rejection Reason: {requisition.get('manager_rejection_reason', 'Unknown')}")
        else:
            try:
                error = response.json()
                print(f"❌ FAILED: {error}")
            except:
                print(f"❌ FAILED: {response.text}")
    
    # Test 4: Find another pending requisition for hold test
    print(f"\n🎯 Test 4: Manager Hold Action")
    hold_requisition = None
    for req in requisitions:
        if (req.get('requested_by_name') == 'Test Employee for Approval' and 
            req.get('status') == 'Pending' and 
            req['id'] != req_id and 
            req['id'] != (reject_requisition['id'] if reject_requisition else '')):
            hold_requisition = req
            break
    
    if hold_requisition:
        hold_req_id = hold_requisition['id']
        print(f"Found requisition for hold test: {hold_req_id[:8]}...")
        
        hold_data = {
            "action": "hold",
            "reason": "On hold for testing manager hold workflow"
        }
        
        response = requests.post(f"{api_url}/asset-requisitions/{hold_req_id}/manager-action", 
                               json=hold_data, headers=admin_headers)
        
        print(f"Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'No message')}")
            
            requisition = result.get('requisition', {})
            print(f"   Status: {requisition.get('status', 'Unknown')}")
            print(f"   Hold Reason: {requisition.get('manager_hold_reason', 'Unknown')}")
        else:
            try:
                error = response.json()
                print(f"❌ FAILED: {error}")
            except:
                print(f"❌ FAILED: {response.text}")
    
    # Test 5: Role-based access control
    print(f"\n🔒 Test 5: Role-Based Access Control")
    
    # Login as employee and try manager action (should fail)
    employee_login = {"email": "employee@company.com", "password": "password123"}
    response = requests.post(f"{api_url}/auth/login", json=employee_login)
    
    if response.status_code == 200:
        employee_token = response.json()['session_token']
        employee_headers = {'Authorization': f'Bearer {employee_token}', 'Content-Type': 'application/json'}
        
        # Find any pending requisition
        pending_req = None
        for req in requisitions:
            if req.get('status') == 'Pending':
                pending_req = req
                break
        
        if pending_req:
            unauthorized_data = {
                "action": "approve",
                "reason": "This should fail"
            }
            
            response = requests.post(f"{api_url}/asset-requisitions/{pending_req['id']}/manager-action", 
                                   json=unauthorized_data, headers=employee_headers)
            
            print(f"Employee manager-action response: {response.status_code}")
            if response.status_code == 403:
                print(f"✅ Employee correctly denied access to manager-action")
            else:
                print(f"❌ Employee access control failed")
    
    # Test 6: Error handling - Invalid action
    print(f"\n⚠️ Test 6: Error Handling - Invalid Action")
    
    # Find any pending requisition
    pending_req = None
    for req in requisitions:
        if req.get('status') == 'Pending':
            pending_req = req
            break
    
    if pending_req:
        invalid_data = {
            "action": "invalid_action",
            "reason": "This should fail"
        }
        
        response = requests.post(f"{api_url}/asset-requisitions/{pending_req['id']}/manager-action", 
                               json=invalid_data, headers=admin_headers)
        
        print(f"Invalid action response: {response.status_code}")
        if response.status_code == 400:
            print(f"✅ Invalid action correctly rejected")
        else:
            print(f"❌ Invalid action validation failed")
    
    print(f"\n🎉 FOCUSED MANAGER APPROVAL WORKFLOW TESTING COMPLETED")
    return True

if __name__ == "__main__":
    focused_manager_approval_test()