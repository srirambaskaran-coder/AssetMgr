from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import os
import logging
import uuid
import hashlib
import requests
import pandas as pd
import io
import csv
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Asset Inventory Management System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    ADMINISTRATOR = "Administrator"
    HR_MANAGER = "HR Manager"
    EMPLOYEE = "Employee"
    MANAGER = "Manager"
    ASSET_MANAGER = "Asset Manager"

class AssetStatus(str, Enum):
    AVAILABLE = "Available"
    DAMAGED = "Damaged"
    LOST = "Lost"
    ALLOCATED = "Allocated"
    UNDER_REPAIR = "Under Repair"
    ON_HOLD = "On Hold"

class RequisitionStatus(str, Enum):
    PENDING = "Pending"
    MANAGER_APPROVED = "Manager Approved"
    HR_APPROVED = "HR Approved"
    REJECTED = "Rejected"
    ALLOCATED = "Allocated"

class ActiveStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class RequestType(str, Enum):
    NEW_ALLOCATION = "New Allocation"
    REPLACEMENT = "Replacement"
    RETURN = "Return"

class RequestFor(str, Enum):
    SELF = "Self"
    TEAM_MEMBER = "Team Member"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    roles: List[UserRole] = Field(default=[UserRole.EMPLOYEE])
    designation: Optional[str] = None
    date_of_joining: Optional[datetime] = None
    reporting_manager_id: Optional[str] = None
    reporting_manager_name: Optional[str] = None
    picture: Optional[str] = None
    session_token: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class UserLogin(BaseModel):
    email: str
    password: str

class AssetType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    depreciation_applicable: bool = True
    asset_life: Optional[int] = None  # in years, required if depreciation_applicable is True
    to_be_recovered_on_separation: bool = True
    status: ActiveStatus = ActiveStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class AssetTypeCreate(BaseModel):
    code: str
    name: str
    depreciation_applicable: bool = True
    asset_life: Optional[int] = None
    to_be_recovered_on_separation: bool = True
    status: ActiveStatus = ActiveStatus.ACTIVE

class AssetTypeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    depreciation_applicable: Optional[bool] = None
    asset_life: Optional[int] = None
    to_be_recovered_on_separation: Optional[bool] = None
    status: Optional[ActiveStatus] = None

class AssetDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_type_id: str
    asset_type_name: Optional[str] = None  # For display purposes
    asset_code: str
    asset_description: str
    asset_details: str
    asset_value: float
    asset_depreciation_value_per_year: Optional[float] = None
    status: AssetStatus = AssetStatus.AVAILABLE
    current_depreciation_value: Optional[float] = None
    allocated_to: Optional[str] = None  # User ID
    allocated_to_name: Optional[str] = None  # User name for display
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class AssetDefinitionCreate(BaseModel):
    asset_type_id: str
    asset_code: str
    asset_description: str
    asset_details: str
    asset_value: float
    asset_depreciation_value_per_year: Optional[float] = None
    status: AssetStatus = AssetStatus.AVAILABLE

class AssetDefinitionUpdate(BaseModel):
    asset_type_id: Optional[str] = None
    asset_code: Optional[str] = None
    asset_description: Optional[str] = None
    asset_details: Optional[str] = None
    asset_value: Optional[float] = None
    asset_depreciation_value_per_year: Optional[float] = None
    status: Optional[AssetStatus] = None

class AssetRequisition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_type_id: str
    asset_type_name: Optional[str] = None
    request_type: RequestType = RequestType.NEW_ALLOCATION
    reason_for_return_replacement: Optional[str] = None
    asset_details: Optional[str] = None
    request_for: RequestFor = RequestFor.SELF
    team_member_employee_id: Optional[str] = None
    team_member_name: Optional[str] = None
    requested_by: str  # User ID
    requested_by_name: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    hr_manager_id: Optional[str] = None
    hr_manager_name: Optional[str] = None
    justification: str  # This serves as general remarks
    required_by_date: Optional[datetime] = None
    status: RequisitionStatus = RequisitionStatus.PENDING
    manager_approval_date: Optional[datetime] = None
    hr_approval_date: Optional[datetime] = None
    allocated_asset_id: Optional[str] = None
    allocated_asset_code: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AssetRequisitionCreate(BaseModel):
    asset_type_id: str
    request_type: RequestType = RequestType.NEW_ALLOCATION
    reason_for_return_replacement: Optional[str] = None
    asset_details: Optional[str] = None
    request_for: RequestFor = RequestFor.SELF
    team_member_employee_id: Optional[str] = None
    justification: str
    required_by_date: Optional[datetime] = None

class AssetAllocationStatus(str, Enum):
    ALLOCATED_TO_EMPLOYEE = "Allocated to Employee"
    RECEIVED_FROM_EMPLOYEE = "Received from Employee"
    NOT_RECEIVED_FROM_EMPLOYEE = "Not Received from Employee"
    DAMAGED = "Damaged"
    LOST = "Lost"

class AssetCondition(str, Enum):
    GOOD_CONDITION = "Good Condition"
    DAMAGED = "Damaged"

class AssetAllocation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requisition_id: str
    request_type: str = "Asset Request"
    asset_type_id: str
    asset_type_name: Optional[str] = None
    asset_definition_id: str
    asset_definition_code: Optional[str] = None
    requested_for: str  # Employee ID
    requested_for_name: Optional[str] = None
    approved_by: str  # Manager ID / HR Manager ID
    approved_by_name: Optional[str] = None
    allocated_by: str  # Asset Manager ID
    allocated_by_name: Optional[str] = None
    allocated_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    remarks: Optional[str] = None
    reference_id: Optional[str] = None
    document_id: Optional[str] = None
    dispatch_details: Optional[str] = None
    status: AssetAllocationStatus = AssetAllocationStatus.ALLOCATED_TO_EMPLOYEE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AssetAllocationCreate(BaseModel):
    requisition_id: str
    asset_definition_id: str
    remarks: Optional[str] = None
    reference_id: Optional[str] = None
    document_id: Optional[str] = None
    dispatch_details: Optional[str] = None

class AssetRetrieval(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: Optional[str] = None
    asset_definition_id: str
    asset_definition_code: Optional[str] = None
    asset_type_name: Optional[str] = None
    allocation_id: Optional[str] = None  # Link to original allocation
    recovered: bool = False
    asset_condition: Optional[AssetCondition] = None
    returned_on: Optional[datetime] = None
    recovery_value: Optional[float] = None  # If asset condition is damaged
    remarks: Optional[str] = None
    status: str = "Pending Recovery"
    processed_by: Optional[str] = None  # Asset Manager ID
    processed_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AssetRetrievalCreate(BaseModel):
    employee_id: str
    asset_definition_id: str
    remarks: Optional[str] = None

class AssetRetrievalUpdate(BaseModel):
    recovered: Optional[bool] = None
    asset_condition: Optional[AssetCondition] = None
    returned_on: Optional[datetime] = None
    recovery_value: Optional[float] = None
    remarks: Optional[str] = None
    status: Optional[str] = None

class SessionData(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    session_token: str

class CompanyProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_website: Optional[str] = None
    company_logo: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyProfileCreate(BaseModel):
    company_name: str
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_website: Optional[str] = None
    company_logo: Optional[str] = None

class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_website: Optional[str] = None
    company_logo: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    name: str
    roles: List[UserRole] = Field(default=[UserRole.EMPLOYEE])
    designation: Optional[str] = None
    date_of_joining: Optional[datetime] = None
    reporting_manager_id: Optional[str] = None
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    roles: Optional[List[UserRole]] = None
    designation: Optional[str] = None
    date_of_joining: Optional[datetime] = None
    reporting_manager_id: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class BulkImportResult(BaseModel):
    success: bool
    message: str
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, str]] = []

# Authentication helpers
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        token = credentials.credentials
        user = await db.users.find_one({"session_token": token, "is_active": True})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return User(**user)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def require_role(required_roles: List[UserRole]):
    async def role_checker(current_user: User = Depends(get_current_user)):
        # Role hierarchy logic - Administrator has access to everything
        if UserRole.ADMINISTRATOR in current_user.roles:
            return current_user
        
        # Check if user has any of the required roles
        user_roles_set = set(current_user.roles)
        required_roles_set = set(required_roles)
        
        # Role hierarchy: HR Manager can access Employee functions
        if UserRole.HR_MANAGER in user_roles_set and UserRole.EMPLOYEE in required_roles_set:
            return current_user
            
        # Role hierarchy: Manager can access Employee functions  
        if UserRole.MANAGER in user_roles_set and UserRole.EMPLOYEE in required_roles_set:
            return current_user
            
        # Role hierarchy: Asset Manager can access Employee functions
        if UserRole.ASSET_MANAGER in user_roles_set and UserRole.EMPLOYEE in required_roles_set:
            return current_user
        
        # Check direct role match
        if user_roles_set.intersection(required_roles_set):
            return current_user
            
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied. Required roles: {', '.join(required_roles)}"
        )
    return role_checker

# Authentication Routes
@api_router.post("/auth/emergent-callback")
async def emergent_auth_callback(session_id: str):
    """Handle Emergent Auth callback with session ID"""
    try:
        # Call Emergent auth API to get user data
        headers = {"X-Session-ID": session_id}
        response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
            
        session_data = SessionData(**response.json())
        
        # Check if user exists, if not create with default Employee role
        existing_user = await db.users.find_one({"email": session_data.email})
        if not existing_user:
            user_data = {
                "id": str(uuid.uuid4()),
                "email": session_data.email,
                "name": session_data.name,
                "roles": [UserRole.EMPLOYEE],  # Default roles
                "picture": session_data.picture,
                "session_token": session_data.session_token,
                "created_at": datetime.now(timezone.utc),
                "is_active": True
            }
            await db.users.insert_one(user_data)
            user = User(**user_data)
        else:
            # Update session token
            await db.users.update_one(
                {"email": session_data.email},
                {"$set": {"session_token": session_data.session_token}}
            )
            existing_user["session_token"] = session_data.session_token
            user = User(**existing_user)
        
        return {
            "success": True,
            "user": user.dict(),
            "session_token": session_data.session_token
        }
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Authentication service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    """Simple username/password login (for demo purposes)"""
    # Demo users configuration
    demo_users = [
        {"email": "admin@company.com", "name": "System Administrator", "roles": [UserRole.ADMINISTRATOR]},
        {"email": "hr@company.com", "name": "HR Manager", "roles": [UserRole.HR_MANAGER]},
        {"email": "manager@company.com", "name": "Department Manager", "roles": [UserRole.MANAGER]},
        {"email": "employee@company.com", "name": "Employee", "roles": [UserRole.EMPLOYEE]},
        {"email": "assetmanager@company.com", "name": "Asset Manager Demo", "roles": [UserRole.ASSET_MANAGER]},
    ]
    
    # Check if this is a demo user with correct password
    demo_user = next((u for u in demo_users if u["email"] == user_data.email), None)
    if demo_user and user_data.password == "password123":
        # Check if user already exists in database
        existing_user = await db.users.find_one({"email": user_data.email})
        
        if existing_user:
            # Update session token for existing user
            session_token = str(uuid.uuid4())
            await db.users.update_one(
                {"email": user_data.email},
                {"$set": {"session_token": session_token, "is_active": True}}
            )
            existing_user["session_token"] = session_token
            user = User(**existing_user)
        else:
            # Create new demo user
            session_token = str(uuid.uuid4())
            user_data_dict = {
                "id": str(uuid.uuid4()),
                "email": demo_user["email"],
                "name": demo_user["name"],
                "roles": demo_user["roles"],
                "session_token": session_token,
                "created_at": datetime.now(timezone.utc),
                "is_active": True
            }
            await db.users.insert_one(user_data_dict)
            user = User(**user_data_dict)
        
        return {"success": True, "user": user.dict(), "session_token": session_token}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# Asset Type Routes
@api_router.post("/asset-types", response_model=AssetType)
async def create_asset_type(
    asset_type: AssetTypeCreate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Create a new asset type"""
    # Validate that asset_life is provided if depreciation is applicable
    if asset_type.depreciation_applicable and not asset_type.asset_life:
        raise HTTPException(status_code=400, detail="Asset life is required when depreciation is applicable")
    
    # Check if code already exists
    existing = await db.asset_types.find_one({"code": asset_type.code})
    if existing:
        raise HTTPException(status_code=400, detail="Asset type code already exists")
    
    asset_type_dict = asset_type.dict()
    asset_type_dict["id"] = str(uuid.uuid4())
    asset_type_dict["created_at"] = datetime.now(timezone.utc)
    asset_type_dict["created_by"] = current_user.id
    
    await db.asset_types.insert_one(asset_type_dict)
    return AssetType(**asset_type_dict)

@api_router.get("/asset-types", response_model=List[AssetType])
async def get_asset_types(current_user: User = Depends(get_current_user)):
    """Get all asset types"""
    asset_types = await db.asset_types.find().to_list(1000)
    return [AssetType(**asset_type) for asset_type in asset_types]

@api_router.get("/asset-types/{asset_type_id}", response_model=AssetType)
async def get_asset_type(asset_type_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific asset type"""
    asset_type = await db.asset_types.find_one({"id": asset_type_id})
    if not asset_type:
        raise HTTPException(status_code=404, detail="Asset type not found")
    return AssetType(**asset_type)

@api_router.put("/asset-types/{asset_type_id}", response_model=AssetType)
async def update_asset_type(
    asset_type_id: str,
    asset_type_update: AssetTypeUpdate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Update an asset type"""
    existing = await db.asset_types.find_one({"id": asset_type_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Asset type not found")
    
    # Validate depreciation logic
    update_data = asset_type_update.dict(exclude_unset=True)
    if "depreciation_applicable" in update_data:
        if update_data["depreciation_applicable"] and not update_data.get("asset_life") and not existing.get("asset_life"):
            raise HTTPException(status_code=400, detail="Asset life is required when depreciation is applicable")
    
    if update_data:
        await db.asset_types.update_one({"id": asset_type_id}, {"$set": update_data})
        updated = await db.asset_types.find_one({"id": asset_type_id})
        return AssetType(**updated)
    
    return AssetType(**existing)

@api_router.delete("/asset-types/{asset_type_id}")
async def delete_asset_type(
    asset_type_id: str,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Delete an asset type"""
    # Check if any asset definitions use this type
    asset_definitions = await db.asset_definitions.find_one({"asset_type_id": asset_type_id})
    if asset_definitions:
        raise HTTPException(status_code=400, detail="Cannot delete asset type that has associated asset definitions")
    
    result = await db.asset_types.delete_one({"id": asset_type_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Asset type not found")
    
    return {"message": "Asset type deleted successfully"}

# Asset Definition Routes
@api_router.get("/asset-definitions/template")
async def download_asset_definitions_template(
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Download CSV template for bulk asset definitions import"""
    template_data = {
        'asset_type_code': ['LAPTOP', 'MOBILE'],
        'asset_code': ['LAP001', 'MOB001'],
        'asset_description': ['Dell Laptop', 'iPhone 14'],
        'asset_details': ['Dell Inspiron 15 3000 Series', 'iPhone 14 Pro 128GB'],
        'asset_value': [50000.00, 80000.00],
        'asset_depreciation_value_per_year': [16666.67, 26666.67],
        'status': ['Available', 'Available']
    }
    
    df = pd.DataFrame(template_data)
    
    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    # Create response
    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=asset_definitions_template.csv"}
    )
    
    return response

@api_router.post("/asset-definitions", response_model=AssetDefinition)
async def create_asset_definition(
    asset_def: AssetDefinitionCreate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Create a new asset definition"""
    # Verify asset type exists
    asset_type = await db.asset_types.find_one({"id": asset_def.asset_type_id})
    if not asset_type:
        raise HTTPException(status_code=400, detail="Asset type not found")
    
    # Check if asset code already exists
    existing = await db.asset_definitions.find_one({"asset_code": asset_def.asset_code})
    if existing:
        raise HTTPException(status_code=400, detail="Asset code already exists")
    
    asset_def_dict = asset_def.dict()
    asset_def_dict["id"] = str(uuid.uuid4())
    asset_def_dict["asset_type_name"] = asset_type["name"]
    asset_def_dict["created_at"] = datetime.now(timezone.utc)
    asset_def_dict["created_by"] = current_user.id
    
    # Calculate current depreciation value
    if asset_type.get("depreciation_applicable") and asset_def.asset_depreciation_value_per_year:
        years_since_creation = 0  # New asset
        asset_def_dict["current_depreciation_value"] = asset_def.asset_value - (asset_def.asset_depreciation_value_per_year * years_since_creation)
    else:
        asset_def_dict["current_depreciation_value"] = asset_def.asset_value
    
    await db.asset_definitions.insert_one(asset_def_dict)
    return AssetDefinition(**asset_def_dict)

@api_router.get("/asset-definitions", response_model=List[AssetDefinition])
async def get_asset_definitions(current_user: User = Depends(get_current_user)):
    """Get all asset definitions"""
    asset_definitions = await db.asset_definitions.find().to_list(1000)
    return [AssetDefinition(**asset_def) for asset_def in asset_definitions]

@api_router.get("/asset-definitions/{asset_def_id}", response_model=AssetDefinition)
async def get_asset_definition(asset_def_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific asset definition"""
    asset_def = await db.asset_definitions.find_one({"id": asset_def_id})
    if not asset_def:
        raise HTTPException(status_code=404, detail="Asset definition not found")
    return AssetDefinition(**asset_def)

@api_router.put("/asset-definitions/{asset_def_id}", response_model=AssetDefinition)
async def update_asset_definition(
    asset_def_id: str,
    asset_def_update: AssetDefinitionUpdate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Update an asset definition"""
    existing = await db.asset_definitions.find_one({"id": asset_def_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Asset definition not found")
    
    update_data = asset_def_update.dict(exclude_unset=True)
    
    # If asset type is being changed, validate and update asset type name
    if "asset_type_id" in update_data:
        asset_type = await db.asset_types.find_one({"id": update_data["asset_type_id"]})
        if not asset_type:
            raise HTTPException(status_code=400, detail="Asset type not found")
        update_data["asset_type_name"] = asset_type["name"]
    
    if update_data:
        await db.asset_definitions.update_one({"id": asset_def_id}, {"$set": update_data})
        updated = await db.asset_definitions.find_one({"id": asset_def_id})
        return AssetDefinition(**updated)
    
    return AssetDefinition(**existing)

@api_router.delete("/asset-definitions/{asset_def_id}")
async def delete_asset_definition(
    asset_def_id: str,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Delete an asset definition"""
    result = await db.asset_definitions.delete_one({"id": asset_def_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Asset definition not found")
    
    return {"message": "Asset definition deleted successfully"}

# Asset Requisition Routes
@api_router.post("/asset-requisitions", response_model=AssetRequisition)
async def create_asset_requisition(
    requisition: AssetRequisitionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new asset requisition"""
    # Verify asset type exists
    asset_type = await db.asset_types.find_one({"id": requisition.asset_type_id})
    if not asset_type:
        raise HTTPException(status_code=400, detail="Asset type not found")
    
    # Validate conditional fields based on request type
    if requisition.request_type in [RequestType.REPLACEMENT, RequestType.RETURN]:
        if not requisition.reason_for_return_replacement:
            raise HTTPException(
                status_code=422, 
                detail=f"Reason for {requisition.request_type.lower()} is required"
            )
        if not requisition.asset_details:
            raise HTTPException(
                status_code=422, 
                detail="Asset details are required for replacement/return requests"
            )
    
    # If request is for team member, verify the team member exists and employee ID is provided
    team_member_name = None
    if requisition.request_for == RequestFor.TEAM_MEMBER:
        if not requisition.team_member_employee_id:
            raise HTTPException(
                status_code=400, 
                detail="Team member employee ID is required when requesting for team member"
            )
        
        team_member = await db.users.find_one({"id": requisition.team_member_employee_id})
        if not team_member:
            raise HTTPException(status_code=400, detail="Team member not found")
        team_member_name = team_member["name"]
    
    requisition_dict = requisition.dict()
    requisition_dict["id"] = str(uuid.uuid4())
    requisition_dict["asset_type_name"] = asset_type["name"]
    requisition_dict["requested_by"] = current_user.id
    requisition_dict["requested_by_name"] = current_user.name
    requisition_dict["team_member_name"] = team_member_name
    requisition_dict["created_at"] = datetime.now(timezone.utc)
    
    # Convert required_by_date to datetime if provided as string
    if requisition_dict.get("required_by_date") and isinstance(requisition_dict["required_by_date"], str):
        requisition_dict["required_by_date"] = datetime.fromisoformat(requisition_dict["required_by_date"])
    
    await db.asset_requisitions.insert_one(requisition_dict)
    return AssetRequisition(**requisition_dict)

@api_router.get("/asset-requisitions", response_model=List[AssetRequisition])
async def get_asset_requisitions(current_user: User = Depends(get_current_user)):
    """Get asset requisitions based on user role"""
    if UserRole.EMPLOYEE in current_user.roles and len(current_user.roles) == 1:
        # Pure employees can only see their own requisitions
        requisitions = await db.asset_requisitions.find({"requested_by": current_user.id}).to_list(1000)
    elif UserRole.MANAGER in current_user.roles:
        # Managers can see requisitions pending their approval
        requisitions = await db.asset_requisitions.find({
            "$or": [
                {"status": RequisitionStatus.PENDING},
                {"manager_id": current_user.id}
            ]
        }).to_list(1000)
    else:
        # HR Managers and Administrators can see all requisitions
        requisitions = await db.asset_requisitions.find().to_list(1000)
    
    return [AssetRequisition(**req) for req in requisitions]

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics based on user role"""
    stats = {}
    
    # Common stats
    total_asset_types = await db.asset_types.count_documents({"status": ActiveStatus.ACTIVE})
    total_assets = await db.asset_definitions.count_documents({})
    available_assets = await db.asset_definitions.count_documents({"status": AssetStatus.AVAILABLE})
    allocated_assets = await db.asset_definitions.count_documents({"status": AssetStatus.ALLOCATED})
    
    stats.update({
        "total_asset_types": total_asset_types,
        "total_assets": total_assets,
        "available_assets": available_assets,
        "allocated_assets": allocated_assets,
    })
    
    if UserRole.ADMINISTRATOR in current_user.roles or UserRole.HR_MANAGER in current_user.roles:
        pending_requisitions = await db.asset_requisitions.count_documents({"status": RequisitionStatus.PENDING})
        stats["pending_requisitions"] = pending_requisitions
    
    if UserRole.MANAGER in current_user.roles:
        pending_approvals = await db.asset_requisitions.count_documents({
            "status": RequisitionStatus.PENDING
        })
        stats["pending_approvals"] = pending_approvals
    
    if UserRole.EMPLOYEE in current_user.roles:
        my_requisitions = await db.asset_requisitions.count_documents({"requested_by": current_user.id})
        my_allocated_assets = await db.asset_definitions.count_documents({"allocated_to": current_user.id})
        stats.update({
            "my_requisitions": my_requisitions,
            "my_allocated_assets": my_allocated_assets
        })
    
    return stats

# User Management Routes (Administrator only)
@api_router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Create a new user"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Validate reporting manager if provided
    reporting_manager_name = None
    if user_data.reporting_manager_id:
        reporting_manager = await db.users.find_one({"id": user_data.reporting_manager_id})
        if not reporting_manager:
            raise HTTPException(status_code=400, detail="Reporting manager not found")
        
        # Check if the reporting manager has Manager role
        manager_roles = reporting_manager.get("roles", [])
        if UserRole.MANAGER not in manager_roles:
            raise HTTPException(status_code=400, detail="Selected reporting manager must have Manager role")
        reporting_manager_name = reporting_manager["name"]
    
    # Hash password (simple hash for demo)
    password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    user_dict = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "name": user_data.name,
        "roles": user_data.roles,
        "designation": user_data.designation,
        "date_of_joining": user_data.date_of_joining,
        "reporting_manager_id": user_data.reporting_manager_id,
        "reporting_manager_name": reporting_manager_name,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    await db.users.insert_one(user_dict)
    user_dict.pop("password_hash", None)  # Don't return password hash
    return User(**user_dict)

@api_router.get("/users", response_model=List[User])
async def get_users(
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Get all users"""
    users = await db.users.find({}, {"password_hash": 0}).to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/users/managers", response_model=List[User])
async def get_managers(
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Get all users with Manager role"""
    managers = await db.users.find({"roles": UserRole.MANAGER, "is_active": True}, {"password_hash": 0}).to_list(1000)
    return [User(**manager) for manager in managers]

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Get a specific user"""
    user = await db.users.find_one({"id": user_id}, {"password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Update a user"""
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Validate and update reporting manager if provided
    if "reporting_manager_id" in update_data:
        if update_data["reporting_manager_id"]:
            reporting_manager = await db.users.find_one({"id": update_data["reporting_manager_id"]})
            if not reporting_manager:
                raise HTTPException(status_code=400, detail="Reporting manager not found")
            
            # Check if the reporting manager has Manager role
            manager_roles = reporting_manager.get("roles", [])
            if UserRole.MANAGER not in manager_roles:
                raise HTTPException(status_code=400, detail="Selected reporting manager must have Manager role")
            update_data["reporting_manager_name"] = reporting_manager["name"]
        else:
            # Clear reporting manager
            update_data["reporting_manager_name"] = None
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        updated_user = await db.users.find_one({"id": user_id}, {"password_hash": 0})
        return User(**updated_user)
    
    existing_user.pop("password_hash", None)
    return User(**existing_user)

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Delete a user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# Company Profile Routes
@api_router.post("/company-profile", response_model=CompanyProfile)
async def create_company_profile(
    profile_data: CompanyProfileCreate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Create or update company profile"""
    # Check if profile already exists
    existing_profile = await db.company_profile.find_one({})
    
    if existing_profile:
        # Update existing profile
        update_data = profile_data.dict()
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.company_profile.update_one({}, {"$set": update_data})
        updated_profile = await db.company_profile.find_one({})
        return CompanyProfile(**updated_profile)
    else:
        # Create new profile
        profile_dict = profile_data.dict()
        profile_dict["id"] = str(uuid.uuid4())
        profile_dict["created_at"] = datetime.now(timezone.utc)
        profile_dict["updated_at"] = datetime.now(timezone.utc)
        await db.company_profile.insert_one(profile_dict)
        return CompanyProfile(**profile_dict)

@api_router.get("/company-profile", response_model=CompanyProfile)
async def get_company_profile():
    """Get company profile (public endpoint)"""
    profile = await db.company_profile.find_one({})
    if not profile:
        # Return default profile
        default_profile = {
            "id": str(uuid.uuid4()),
            "company_name": "Your Company Name",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        return CompanyProfile(**default_profile)
    return CompanyProfile(**profile)

@api_router.put("/company-profile", response_model=CompanyProfile)
async def update_company_profile(
    profile_update: CompanyProfileUpdate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Update company profile"""
    update_data = profile_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # Check if profile exists
    existing_profile = await db.company_profile.find_one({})
    if not existing_profile:
        # Create new profile with provided data
        profile_dict = update_data
        profile_dict["id"] = str(uuid.uuid4())
        profile_dict["company_name"] = profile_dict.get("company_name", "Your Company Name")
        profile_dict["created_at"] = datetime.now(timezone.utc)
        await db.company_profile.insert_one(profile_dict)
        return CompanyProfile(**profile_dict)
    else:
        await db.company_profile.update_one({}, {"$set": update_data})
        updated_profile = await db.company_profile.find_one({})
        return CompanyProfile(**updated_profile)

# Password Change Route
@api_router.post("/auth/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    user = await db.users.find_one({"id": current_user.id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # For demo users, check if current password is correct
    current_hash = hashlib.sha256(password_data.current_password.encode()).hexdigest()
    stored_hash = user.get("password_hash")
    
    # If no stored hash (demo users), allow password123
    if not stored_hash and password_data.current_password != "password123":
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    elif stored_hash and stored_hash != current_hash:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password
    new_hash = hashlib.sha256(password_data.new_password.encode()).hexdigest()
    
    # Update password
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"password_hash": new_hash}}
    )
    
    return {"message": "Password changed successfully"}


@api_router.post("/asset-definitions/bulk-import", response_model=BulkImportResult)
async def bulk_import_asset_definitions(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Bulk import asset definitions from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        required_columns = ['asset_type_code', 'asset_code', 'asset_description', 'asset_details', 'asset_value']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        total_rows = len(df)
        successful_imports = 0
        failed_imports = 0
        errors = []
        
        # Get all asset types for lookup
        asset_types = await db.asset_types.find().to_list(1000)
        asset_type_lookup = {at['code']: at for at in asset_types}
        
        for index, row in df.iterrows():
            try:
                # Validate asset type exists
                asset_type_code = row['asset_type_code']
                if asset_type_code not in asset_type_lookup:
                    errors.append({
                        'row': index + 2,  # +2 because pandas is 0-indexed and CSV has header
                        'error': f'Asset type code "{asset_type_code}" not found'
                    })
                    failed_imports += 1
                    continue
                
                asset_type = asset_type_lookup[asset_type_code]
                
                # Check if asset code already exists
                existing_asset = await db.asset_definitions.find_one({"asset_code": row['asset_code']})
                if existing_asset:
                    errors.append({
                        'row': index + 2,
                        'error': f'Asset code "{row["asset_code"]}" already exists'
                    })
                    failed_imports += 1
                    continue
                
                # Create asset definition
                asset_def_dict = {
                    "id": str(uuid.uuid4()),
                    "asset_type_id": asset_type['id'],
                    "asset_type_name": asset_type['name'],
                    "asset_code": row['asset_code'],
                    "asset_description": row['asset_description'],
                    "asset_details": row['asset_details'],
                    "asset_value": float(row['asset_value']),
                    "asset_depreciation_value_per_year": float(row.get('asset_depreciation_value_per_year', 0)) if pd.notna(row.get('asset_depreciation_value_per_year')) else None,
                    "status": row.get('status', 'Available'),
                    "current_depreciation_value": float(row['asset_value']),  # Initial value
                    "created_at": datetime.now(timezone.utc),
                    "created_by": current_user.id
                }
                
                await db.asset_definitions.insert_one(asset_def_dict)
                successful_imports += 1
                
            except Exception as e:
                errors.append({
                    'row': index + 2,
                    'error': str(e)
                })
                failed_imports += 1
        
        return BulkImportResult(
            success=successful_imports > 0,
            message=f"Import completed. {successful_imports} successful, {failed_imports} failed.",
            total_rows=total_rows,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Asset Allocation Routes (Asset Manager)
@api_router.get("/asset-allocations", response_model=List[AssetAllocation])
async def get_asset_allocations(
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Get all asset allocations"""
    allocations = await db.asset_allocations.find().to_list(1000)
    return [AssetAllocation(**allocation) for allocation in allocations]

@api_router.post("/asset-allocations", response_model=AssetAllocation)
async def create_asset_allocation(
    allocation_data: AssetAllocationCreate,
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Allocate an asset to an employee based on approved requisition"""
    # Get requisition details
    requisition = await db.asset_requisitions.find_one({"id": allocation_data.requisition_id})
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    
    if requisition["status"] not in [RequisitionStatus.MANAGER_APPROVED, RequisitionStatus.HR_APPROVED]:
        raise HTTPException(status_code=400, detail="Requisition must be approved before allocation")
    
    # Get asset definition details
    asset_def = await db.asset_definitions.find_one({"id": allocation_data.asset_definition_id})
    if not asset_def:
        raise HTTPException(status_code=404, detail="Asset definition not found")
    
    if asset_def["status"] != AssetStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Asset is not available for allocation")
    
    # Get asset type and user details
    asset_type = await db.asset_types.find_one({"id": asset_def["asset_type_id"]})
    requested_user = await db.users.find_one({"id": requisition["requested_by"]})
    approved_by_user = await db.users.find_one({"id": requisition.get("manager_id") or requisition.get("hr_manager_id")})
    
    # Create allocation record
    allocation_dict = {
        "id": str(uuid.uuid4()),
        "requisition_id": allocation_data.requisition_id,
        "request_type": "Asset Request",
        "asset_type_id": asset_def["asset_type_id"],
        "asset_type_name": asset_type["name"] if asset_type else None,
        "asset_definition_id": allocation_data.asset_definition_id,
        "asset_definition_code": asset_def["asset_code"],
        "requested_for": requisition["requested_by"],
        "requested_for_name": requested_user["name"] if requested_user else None,
        "approved_by": requisition.get("manager_id") or requisition.get("hr_manager_id"),
        "approved_by_name": approved_by_user["name"] if approved_by_user else None,
        "allocated_by": current_user.id,
        "allocated_by_name": current_user.name,
        "allocated_date": datetime.now(timezone.utc),
        "remarks": allocation_data.remarks,
        "reference_id": allocation_data.reference_id,
        "document_id": allocation_data.document_id,
        "dispatch_details": allocation_data.dispatch_details,
        "status": AssetAllocationStatus.ALLOCATED_TO_EMPLOYEE,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.asset_allocations.insert_one(allocation_dict)
    
    # Update asset definition status and allocated to
    await db.asset_definitions.update_one(
        {"id": allocation_data.asset_definition_id},
        {
            "$set": {
                "status": AssetStatus.ALLOCATED,
                "allocated_to": requisition["requested_by"],
                "allocated_to_name": requested_user["name"] if requested_user else None
            }
        }
    )
    
    # Update requisition status
    await db.asset_requisitions.update_one(
        {"id": allocation_data.requisition_id},
        {
            "$set": {
                "status": RequisitionStatus.ALLOCATED,
                "allocated_asset_id": allocation_data.asset_definition_id,
                "allocated_asset_code": asset_def["asset_code"]
            }
        }
    )
    
    return AssetAllocation(**allocation_dict)

@api_router.get("/pending-allocations")
async def get_pending_allocations(
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Get approved requisitions pending allocation"""
    pending_requisitions = await db.asset_requisitions.find({
        "status": {"$in": [RequisitionStatus.MANAGER_APPROVED, RequisitionStatus.HR_APPROVED]}
    }).to_list(1000)
    
    return [AssetRequisition(**req) for req in pending_requisitions]

# Asset Retrieval Routes (Asset Manager)
@api_router.get("/asset-retrievals", response_model=List[AssetRetrieval])
async def get_asset_retrievals(
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Get all asset retrievals"""
    retrievals = await db.asset_retrievals.find().to_list(1000)
    return [AssetRetrieval(**retrieval) for retrieval in retrievals]

@api_router.post("/asset-retrievals", response_model=AssetRetrieval)
async def create_asset_retrieval(
    retrieval_data: AssetRetrievalCreate,
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Create asset retrieval record for employee separation"""
    # Get employee and asset details
    employee = await db.users.find_one({"id": retrieval_data.employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    asset_def = await db.asset_definitions.find_one({"id": retrieval_data.asset_definition_id})
    if not asset_def:
        raise HTTPException(status_code=404, detail="Asset definition not found")
    
    # Check if asset is allocated to this employee
    if asset_def.get("allocated_to") != retrieval_data.employee_id:
        raise HTTPException(status_code=400, detail="Asset is not allocated to this employee")
    
    # Get asset type details
    asset_type = await db.asset_types.find_one({"id": asset_def["asset_type_id"]})
    
    # Find original allocation
    allocation = await db.asset_allocations.find_one({
        "asset_definition_id": retrieval_data.asset_definition_id,
        "requested_for": retrieval_data.employee_id
    })
    
    retrieval_dict = {
        "id": str(uuid.uuid4()),
        "employee_id": retrieval_data.employee_id,
        "employee_name": employee["name"],
        "asset_definition_id": retrieval_data.asset_definition_id,
        "asset_definition_code": asset_def["asset_code"],
        "asset_type_name": asset_type["name"] if asset_type else None,
        "allocation_id": allocation["id"] if allocation else None,
        "recovered": False,
        "remarks": retrieval_data.remarks,
        "status": "Pending Recovery",
        "processed_by": current_user.id,
        "processed_by_name": current_user.name,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.asset_retrievals.insert_one(retrieval_dict)
    return AssetRetrieval(**retrieval_dict)

@api_router.put("/asset-retrievals/{retrieval_id}", response_model=AssetRetrieval)
async def update_asset_retrieval(
    retrieval_id: str,
    retrieval_update: AssetRetrievalUpdate,
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Update asset retrieval record"""
    existing_retrieval = await db.asset_retrievals.find_one({"id": retrieval_id})
    if not existing_retrieval:
        raise HTTPException(status_code=404, detail="Asset retrieval record not found")
    
    update_data = retrieval_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # If marking as recovered, update asset status
    if update_data.get("recovered") == True and not existing_retrieval.get("recovered"):
        asset_def = await db.asset_definitions.find_one({"id": existing_retrieval["asset_definition_id"]})
        if asset_def:
            new_status = AssetStatus.AVAILABLE
            if update_data.get("asset_condition") == AssetCondition.DAMAGED:
                new_status = AssetStatus.DAMAGED
            
            await db.asset_definitions.update_one(
                {"id": existing_retrieval["asset_definition_id"]},
                {
                    "$set": {
                        "status": new_status,
                        "allocated_to": None,
                        "allocated_to_name": None
                    }
                }
            )
        
        # Update allocation status
        if existing_retrieval.get("allocation_id"):
            await db.asset_allocations.update_one(
                {"id": existing_retrieval["allocation_id"]},
                {"$set": {"status": AssetAllocationStatus.RECEIVED_FROM_EMPLOYEE}}
            )
        
        update_data["status"] = "Recovered"
        if not update_data.get("returned_on"):
            update_data["returned_on"] = datetime.now(timezone.utc)
    
    await db.asset_retrievals.update_one({"id": retrieval_id}, {"$set": update_data})
    updated_retrieval = await db.asset_retrievals.find_one({"id": retrieval_id})
    return AssetRetrieval(**updated_retrieval)

@api_router.get("/allocated-assets")
async def get_allocated_assets(
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Get all currently allocated assets"""
    allocated_assets = await db.asset_definitions.find({"status": AssetStatus.ALLOCATED}).to_list(1000)
    return allocated_assets

# Asset Manager Dashboard Stats
@api_router.get("/dashboard/asset-manager-stats")
async def get_asset_manager_stats(
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Get comprehensive asset statistics for Asset Manager dashboard"""
    
    # Basic asset counts
    total_assets = await db.asset_definitions.count_documents({})
    available_assets = await db.asset_definitions.count_documents({"status": AssetStatus.AVAILABLE})
    allocated_assets = await db.asset_definitions.count_documents({"status": AssetStatus.ALLOCATED})
    damaged_assets = await db.asset_definitions.count_documents({"status": AssetStatus.DAMAGED})
    lost_assets = await db.asset_definitions.count_documents({"status": AssetStatus.LOST})
    under_repair = await db.asset_definitions.count_documents({"status": AssetStatus.UNDER_REPAIR})
    
    # Requisition stats
    pending_allocations = await db.asset_requisitions.count_documents({
        "status": {"$in": [RequisitionStatus.MANAGER_APPROVED, RequisitionStatus.HR_APPROVED]}
    })
    total_allocations = await db.asset_allocations.count_documents({})
    
    # Retrieval stats
    pending_retrievals = await db.asset_retrievals.count_documents({"recovered": False})
    completed_retrievals = await db.asset_retrievals.count_documents({"recovered": True})
    
    # Asset type breakdown
    asset_type_pipeline = [
        {"$lookup": {
            "from": "asset_types",
            "localField": "asset_type_id",
            "foreignField": "id",
            "as": "asset_type"
        }},
        {"$unwind": "$asset_type"},
        {"$group": {
            "_id": "$asset_type.name",
            "total": {"$sum": 1},
            "available": {"$sum": {"$cond": [{"$eq": ["$status", "Available"]}, 1, 0]}},
            "allocated": {"$sum": {"$cond": [{"$eq": ["$status", "Allocated"]}, 1, 0]}}
        }}
    ]
    
    asset_type_stats = await db.asset_definitions.aggregate(asset_type_pipeline).to_list(100)
    
    return {
        "total_assets": total_assets,
        "available_assets": available_assets,
        "allocated_assets": allocated_assets,
        "damaged_assets": damaged_assets,
        "lost_assets": lost_assets,
        "under_repair": under_repair,
        "pending_allocations": pending_allocations,
        "total_allocations": total_allocations,
        "pending_retrievals": pending_retrievals,
        "completed_retrievals": completed_retrievals,
        "asset_type_breakdown": asset_type_stats,
        "allocation_rate": round((allocated_assets / total_assets * 100) if total_assets > 0 else 0, 1),
        "availability_rate": round((available_assets / total_assets * 100) if total_assets > 0 else 0, 1)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()