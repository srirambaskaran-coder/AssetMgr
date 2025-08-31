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

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: UserRole
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
    requested_by: str  # User ID
    requested_by_name: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    hr_manager_id: Optional[str] = None
    hr_manager_name: Optional[str] = None
    justification: str
    status: RequisitionStatus = RequisitionStatus.PENDING
    manager_approval_date: Optional[datetime] = None
    hr_approval_date: Optional[datetime] = None
    allocated_asset_id: Optional[str] = None
    allocated_asset_code: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AssetRequisitionCreate(BaseModel):
    asset_type_id: str
    justification: str

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
    role: UserRole
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
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
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        return current_user
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
                "role": UserRole.EMPLOYEE,  # Default role
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
        {"email": "admin@company.com", "name": "System Administrator", "role": UserRole.ADMINISTRATOR},
        {"email": "hr@company.com", "name": "HR Manager", "role": UserRole.HR_MANAGER},
        {"email": "manager@company.com", "name": "Department Manager", "role": UserRole.MANAGER},
        {"email": "employee@company.com", "name": "Employee", "role": UserRole.EMPLOYEE},
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
                "role": demo_user["role"],
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
    
    requisition_dict = requisition.dict()
    requisition_dict["id"] = str(uuid.uuid4())
    requisition_dict["asset_type_name"] = asset_type["name"]
    requisition_dict["requested_by"] = current_user.id
    requisition_dict["requested_by_name"] = current_user.name
    requisition_dict["created_at"] = datetime.now(timezone.utc)
    
    await db.asset_requisitions.insert_one(requisition_dict)
    return AssetRequisition(**requisition_dict)

@api_router.get("/asset-requisitions", response_model=List[AssetRequisition])
async def get_asset_requisitions(current_user: User = Depends(get_current_user)):
    """Get asset requisitions based on user role"""
    if current_user.role == UserRole.EMPLOYEE:
        # Employees can only see their own requisitions
        requisitions = await db.asset_requisitions.find({"requested_by": current_user.id}).to_list(1000)
    elif current_user.role == UserRole.MANAGER:
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
    
    if current_user.role in [UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]:
        pending_requisitions = await db.asset_requisitions.count_documents({"status": RequisitionStatus.PENDING})
        stats["pending_requisitions"] = pending_requisitions
    
    if current_user.role == UserRole.MANAGER:
        pending_approvals = await db.asset_requisitions.count_documents({
            "status": RequisitionStatus.PENDING
        })
        stats["pending_approvals"] = pending_approvals
    
    if current_user.role == UserRole.EMPLOYEE:
        my_requisitions = await db.asset_requisitions.count_documents({"requested_by": current_user.id})
        my_allocated_assets = await db.asset_definitions.count_documents({"allocated_to": current_user.id})
        stats.update({
            "my_requisitions": my_requisitions,
            "my_allocated_assets": my_allocated_assets
        })
    
    return stats

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