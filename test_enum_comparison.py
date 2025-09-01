from enum import Enum

class RequisitionStatus(str, Enum):
    PENDING = "Pending"
    MANAGER_APPROVED = "Manager Approved"
    HR_APPROVED = "HR Approved"
    REJECTED = "Rejected"
    ALLOCATED = "Allocated"

# Test the enum comparison
status_from_db = "Pending"
enum_value = RequisitionStatus.PENDING

print(f"Status from DB: {repr(status_from_db)}")
print(f"Enum value: {repr(enum_value)}")
print(f"Enum value string: {repr(str(enum_value))}")
print(f"Direct comparison: {status_from_db == enum_value}")
print(f"String comparison: {status_from_db == str(enum_value)}")
print(f"Enum comparison: {status_from_db == RequisitionStatus.PENDING}")

# Test the condition that's failing
requisition = {"status": "Pending"}
print(f"\nTesting backend condition:")
print(f"requisition.get('status'): {repr(requisition.get('status'))}")
print(f"RequisitionStatus.PENDING: {repr(RequisitionStatus.PENDING)}")
print(f"Condition result: {requisition.get('status') != RequisitionStatus.PENDING}")

# Test if there's any issue with the comparison
if requisition.get("status") != RequisitionStatus.PENDING:
    print("❌ Condition would FAIL (raise exception)")
else:
    print("✅ Condition would PASS")