import requests
import json
from datetime import datetime, timedelta

class ManagerEmployeeWorkflowTester:
    def __init__(self, base_url="https://inventoryhub-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}
        self.users = {}
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        self.test_results.append(result)
        print(result)

    def run_test(self, name, method, endpoint, expected_status, data=None, user_role=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if user_role and user_role in self.tokens:
            headers['Authorization'] = f'Bearer {self.tokens[user_role]}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            try:
                return success, response.json()
            except:
                return success, {}

        except Exception as e:
            print(f"❌ Error in {name}: {str(e)}")
            return False, {}

    def test_login(self, email, password, role_name):
        """Test login and store token"""
        success, response = self.run_test(
            f"Login {role_name}",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'session_token' in response:
            self.tokens[role_name] = response['session_token']
            self.users[role_name] = response['user']
            self.log_result(f"{role_name} Login", True, f"User ID: {response['user'].get('id', 'Unknown')}")
            return True
        self.log_result(f"{role_name} Login", False, "Authentication failed")
        return False

    def test_user_relationship_verification(self):
        """Test 1: Verify user relationship is now fixed"""
        print(f"\n🔍 === TEST 1: USER RELATIONSHIP VERIFICATION ===")
        
        # Login as admin to get user data
        if not self.test_login("admin@company.com", "password123", "Administrator"):
            return False
        
        # Get Sriram's user data
        success, response = self.run_test(
            "Get Sriram User Data",
            "GET",
            "users/cf602201-1656-40e0-a9cf-beb85f96e0d4",
            200,
            user_role="Administrator"
        )
        
        if success:
            sriram_manager_id = response.get('reporting_manager_id')
            sriram_manager_name = response.get('reporting_manager_name')
            
            if sriram_manager_id == "464f2383-d146-44ff-963d-e7bf492a6117":
                self.log_result("Sriram-Kiran Relationship", True, f"Manager: {sriram_manager_name}")
                return True
            else:
                self.log_result("Sriram-Kiran Relationship", False, f"Wrong manager ID: {sriram_manager_id}")
                return False
        else:
            self.log_result("Get Sriram User Data", False, "Could not retrieve user data")
            return False

    def test_sriram_login_and_requisition_creation(self):
        """Test 2: Test Sriram login and asset requisition creation"""
        print(f"\n🔍 === TEST 2: SRIRAM LOGIN AND REQUISITION CREATION ===")
        
        # Test Sriram login with new password
        if not self.test_login("sriram@company.com", "srirampass123", "Sriram"):
            return False
        
        # Get asset types for requisition
        success, asset_types = self.run_test(
            "Get Asset Types",
            "GET",
            "asset-types",
            200,
            user_role="Sriram"
        )
        
        if not success or not asset_types:
            self.log_result("Get Asset Types", False, "No asset types available")
            return False
        
        asset_type_id = asset_types[0].get('id')
        
        # Create asset requisition as Sriram
        requisition_data = {
            "asset_type_id": asset_type_id,
            "request_type": "New Allocation",
            "request_for": "Self",
            "justification": "Need laptop for development work - testing manager relationship",
            "required_by_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        success, response = self.run_test(
            "Create Asset Requisition as Sriram",
            "POST",
            "asset-requisitions",
            200,
            data=requisition_data,
            user_role="Sriram"
        )
        
        if success:
            req_id = response.get('id')
            manager_id = response.get('manager_id')
            manager_name = response.get('manager_name')
            
            if manager_id == "464f2383-d146-44ff-963d-e7bf492a6117":
                self.log_result("Requisition Manager ID Population", True, f"Manager: {manager_name}")
                self.test_data = {'sriram_requisition_id': req_id}
                return True
            else:
                self.log_result("Requisition Manager ID Population", False, f"Wrong manager ID: {manager_id}")
                return False
        else:
            self.log_result("Create Asset Requisition as Sriram", False, "Requisition creation failed")
            return False

    def test_manager_filtering_and_visibility(self):
        """Test 3: Test manager filtering logic"""
        print(f"\n🔍 === TEST 3: MANAGER FILTERING AND VISIBILITY ===")
        
        # Login as Kiran (Manager)
        if not self.test_login("manager@company.com", "password123", "Manager"):
            return False
        
        # Get requisitions as Manager
        success, response = self.run_test(
            "Get Requisitions as Manager",
            "GET",
            "asset-requisitions",
            200,
            user_role="Manager"
        )
        
        if success:
            manager_requisitions = response
            sriram_req_found = False
            
            # Check if Sriram's requisition is visible to manager
            if hasattr(self, 'test_data') and 'sriram_requisition_id' in self.test_data:
                sriram_req_id = self.test_data['sriram_requisition_id']
                sriram_req_found = any(req.get('id') == sriram_req_id for req in manager_requisitions)
            
            # Count requisitions from direct reports
            kiran_id = "464f2383-d146-44ff-963d-e7bf492a6117"
            direct_report_reqs = [req for req in manager_requisitions if req.get('manager_id') == kiran_id]
            
            self.log_result("Manager Can See Requisitions", True, f"Total visible: {len(manager_requisitions)}")
            self.log_result("Direct Report Requisitions", True, f"Count: {len(direct_report_reqs)}")
            
            if sriram_req_found:
                self.log_result("Sriram Requisition Visible to Manager", True, "Manager can see Sriram's request")
                return True
            else:
                self.log_result("Sriram Requisition Visible to Manager", False, "Manager cannot see Sriram's request")
                return False
        else:
            self.log_result("Get Requisitions as Manager", False, "Failed to get requisitions")
            return False

    def test_manager_approval_workflow(self):
        """Test 4: Test manager approval workflow"""
        print(f"\n🔍 === TEST 4: MANAGER APPROVAL WORKFLOW ===")
        
        if not hasattr(self, 'test_data') or 'sriram_requisition_id' not in self.test_data:
            self.log_result("Manager Approval Test", False, "No Sriram requisition to approve")
            return False
        
        sriram_req_id = self.test_data['sriram_requisition_id']
        
        # Test manager approval
        approval_data = {
            "action": "approve",
            "reason": "Approved for development work - legitimate business need"
        }
        
        success, response = self.run_test(
            "Manager Approve Sriram's Requisition",
            "POST",
            f"asset-requisitions/{sriram_req_id}/manager-action",
            200,
            data=approval_data,
            user_role="Manager"
        )
        
        if success:
            new_status = response.get('requisition', {}).get('status')
            if new_status == "Manager Approved":
                self.log_result("Manager Approval Action", True, f"Status: {new_status}")
                return True
            else:
                self.log_result("Manager Approval Action", False, f"Unexpected status: {new_status}")
                return False
        else:
            self.log_result("Manager Approval Action", False, "Approval failed")
            return False

    def test_end_to_end_workflow(self):
        """Test 5: Complete end-to-end workflow verification"""
        print(f"\n🔍 === TEST 5: END-TO-END WORKFLOW VERIFICATION ===")
        
        # Verify the complete workflow worked
        if not hasattr(self, 'test_data') or 'sriram_requisition_id' not in self.test_data:
            self.log_result("End-to-End Workflow", False, "No requisition to verify")
            return False
        
        sriram_req_id = self.test_data['sriram_requisition_id']
        
        # Get the final state of the requisition as Administrator
        success, response = self.run_test(
            "Get Final Requisition State",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            # Find Sriram's requisition
            sriram_req = None
            for req in response:
                if req.get('id') == sriram_req_id:
                    sriram_req = req
                    break
            
            if sriram_req:
                status = sriram_req.get('status')
                manager_id = sriram_req.get('manager_id')
                manager_name = sriram_req.get('manager_name')
                requested_by_name = sriram_req.get('requested_by_name')
                
                workflow_success = (
                    status == "Manager Approved" and
                    manager_id == "464f2383-d146-44ff-963d-e7bf492a6117" and
                    requested_by_name == "Test User Sriram"
                )
                
                if workflow_success:
                    self.log_result("End-to-End Workflow", True, 
                        f"Employee: {requested_by_name} → Manager: {manager_name} → Status: {status}")
                    return True
                else:
                    self.log_result("End-to-End Workflow", False, 
                        f"Workflow incomplete - Status: {status}, Manager: {manager_name}")
                    return False
            else:
                self.log_result("End-to-End Workflow", False, "Requisition not found")
                return False
        else:
            self.log_result("Get Final Requisition State", False, "Could not verify final state")
            return False

    def test_data_integrity_verification(self):
        """Test 6: Verify data integrity and existing requisitions"""
        print(f"\n🔍 === TEST 6: DATA INTEGRITY VERIFICATION ===")
        
        # Get all requisitions and analyze manager_id population
        success, response = self.run_test(
            "Get All Requisitions for Analysis",
            "GET",
            "asset-requisitions",
            200,
            user_role="Administrator"
        )
        
        if success:
            total_reqs = len(response)
            reqs_with_manager_id = sum(1 for req in response if req.get('manager_id'))
            reqs_without_manager_id = total_reqs - reqs_with_manager_id
            
            self.log_result("Total Requisitions", True, f"Count: {total_reqs}")
            self.log_result("Requisitions with Manager ID", True, f"Count: {reqs_with_manager_id}")
            self.log_result("Requisitions without Manager ID", True, f"Count: {reqs_without_manager_id}")
            
            # Check if new requisitions are working correctly
            if reqs_with_manager_id > 0:
                self.log_result("Manager ID Population Fix", True, "New requisitions populate manager_id")
                return True
            else:
                self.log_result("Manager ID Population Fix", False, "No requisitions have manager_id")
                return False
        else:
            self.log_result("Get All Requisitions for Analysis", False, "Could not analyze data")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive test of manager-employee workflow"""
        print(f"\n🚀 === COMPREHENSIVE MANAGER-EMPLOYEE WORKFLOW TEST ===")
        
        self.test_data = {}
        
        # Run all tests
        test1_success = self.test_user_relationship_verification()
        test2_success = self.test_sriram_login_and_requisition_creation()
        test3_success = self.test_manager_filtering_and_visibility()
        test4_success = self.test_manager_approval_workflow()
        test5_success = self.test_end_to_end_workflow()
        test6_success = self.test_data_integrity_verification()
        
        # Summary
        print(f"\n📋 === TEST SUMMARY ===")
        for result in self.test_results:
            print(result)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if "✅ PASS" in result)
        
        print(f"\n📊 === OVERALL RESULTS ===")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Final assessment
        critical_tests = [test1_success, test2_success, test3_success, test5_success]
        if all(critical_tests):
            print(f"\n🎉 === MANAGER-EMPLOYEE RELATIONSHIP ISSUE RESOLVED ===")
            print("✅ Sriram can login and create requisitions")
            print("✅ Requisitions correctly populate manager_id with Kiran's ID")
            print("✅ Kiran can see and approve Sriram's requisitions")
            print("✅ End-to-end workflow is working correctly")
            return True
        else:
            print(f"\n❌ === MANAGER-EMPLOYEE RELATIONSHIP ISSUE PERSISTS ===")
            print("Some critical tests failed - issue not fully resolved")
            return False

if __name__ == "__main__":
    tester = ManagerEmployeeWorkflowTester()
    tester.run_comprehensive_test()