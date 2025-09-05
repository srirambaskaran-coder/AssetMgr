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
# Email imports
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import asyncio

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
    ON_HOLD = "On Hold"
    ASSIGNED_FOR_ALLOCATION = "Assigned for Allocation"
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
    location_id: Optional[str] = None
    location_name: Optional[str] = None
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
    allocation_date: Optional[datetime] = None  # When asset was allocated
    acknowledged: bool = False  # Whether employee has acknowledged receipt
    acknowledgment_date: Optional[datetime] = None  # When acknowledgment was made
    acknowledgment_notes: Optional[str] = None  # Employee notes during acknowledgment
    assigned_asset_manager_id: Optional[str] = None  # Asset Manager assigned to this asset
    assigned_asset_manager_name: Optional[str] = None  # Asset Manager name for display
    location_id: Optional[str] = None  # Location where asset is deployed
    location_name: Optional[str] = None  # Location name for display
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
    assigned_asset_manager_id: Optional[str] = None
    location_id: Optional[str] = None

class AssetDefinitionUpdate(BaseModel):
    asset_type_id: Optional[str] = None
    asset_code: Optional[str] = None
    asset_description: Optional[str] = None
    asset_details: Optional[str] = None
    asset_value: Optional[float] = None
    asset_depreciation_value_per_year: Optional[float] = None
    status: Optional[AssetStatus] = None
    assigned_asset_manager_id: Optional[str] = None
    location_id: Optional[str] = None
    allocated_to: Optional[str] = None
    allocated_to_name: Optional[str] = None

class AssetAcknowledgmentRequest(BaseModel):
    acknowledgment_notes: Optional[str] = None

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
    
    # Manager approval fields
    manager_approval_date: Optional[datetime] = None
    manager_approval_reason: Optional[str] = None
    manager_rejection_reason: Optional[str] = None
    manager_hold_reason: Optional[str] = None
    manager_action_by: Optional[str] = None  # Manager user ID who took action
    manager_action_by_name: Optional[str] = None  # Manager name who took action
    
    # HR approval fields  
    hr_approval_date: Optional[datetime] = None
    hr_approval_reason: Optional[str] = None
    hr_rejection_reason: Optional[str] = None
    hr_hold_reason: Optional[str] = None
    hr_action_by: Optional[str] = None  # HR Manager user ID who took action
    hr_action_by_name: Optional[str] = None  # HR Manager name who took action
    
    # Asset allocation fields
    allocated_asset_id: Optional[str] = None
    allocated_asset_code: Optional[str] = None
    comments: Optional[str] = None
    
    # Enhanced Asset Allocation Routing fields
    assigned_to: Optional[str] = None  # Asset Manager/Administrator ID assigned for allocation
    assigned_to_name: Optional[str] = None  # Asset Manager/Administrator name assigned for allocation
    assigned_date: Optional[datetime] = None  # When the routing assignment was made
    routing_reason: Optional[str] = None  # Reason for the routing decision
    
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

class ManagerActionRequest(BaseModel):
    action: str  # "approve", "reject", "hold"
    reason: str  # Reason for the action
    
class HRActionRequest(BaseModel):
    action: str  # "approve", "reject", "hold"
    reason: str  # Reason for the action

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
    location_id: Optional[str] = None
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    roles: Optional[List[UserRole]] = None
    designation: Optional[str] = None
    date_of_joining: Optional[datetime] = None
    reporting_manager_id: Optional[str] = None
    location_id: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

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

# Location Models
class Location(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    country: str
    status: str = "Active"  # Active, Inactive
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LocationCreate(BaseModel):
    code: str
    name: str
    country: str
    status: str = "Active"

class LocationUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None

# NDC (No Dues Certificate) Models for Employee Separation
class SeparationReason(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reason: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SeparationReasonCreate(BaseModel):
    reason: str

class NDCRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    employee_code: Optional[str] = None
    employee_designation: Optional[str] = None
    employee_date_of_joining: Optional[datetime] = None
    employee_location_name: Optional[str] = None
    employee_reporting_manager_name: Optional[str] = None
    
    # Separation details
    resigned_on: datetime
    notice_period: str  # Immediate, 7 days, 15 days, 30 days, 60 days, 90 days
    last_working_date: datetime
    separation_approved_by: str
    separation_approved_by_name: str
    separation_approved_on: datetime
    separation_reason: str
    
    # Request details
    created_by: str  # HR Manager ID
    created_by_name: str
    asset_manager_id: str  # Responsible Asset Manager
    asset_manager_name: str
    status: str = "Pending"  # Pending, Asset Manager Confirmation, Completed
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NDCRequestCreate(BaseModel):
    employee_id: str
    resigned_on: datetime
    notice_period: str
    last_working_date: datetime
    separation_approved_by: str
    separation_approved_on: datetime
    separation_reason: str

class NDCAssetRecovery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ndc_request_id: str
    asset_definition_id: str
    asset_code: str
    asset_type_name: str
    asset_value: float
    
    # Recovery details - filled by Asset Manager
    recovered: Optional[bool] = None  # Yes/No
    asset_condition: Optional[str] = None  # Good Condition / Damaged
    returned_on: Optional[datetime] = None
    recovery_value: Optional[float] = None  # If damaged
    remarks: Optional[str] = None
    status: str = "Pending"  # Pending, Recovered, Not Recovered
    
    updated_by: Optional[str] = None  # Asset Manager ID
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NDCAssetRecoveryUpdate(BaseModel):
    recovered: bool
    asset_condition: str
    returned_on: Optional[datetime] = None
    recovery_value: Optional[float] = None
    remarks: Optional[str] = None

class NDCRevokeRequest(BaseModel):
    reason: str

# Asset Manager Location Assignment Models
class AssetManagerLocation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_manager_id: str
    asset_manager_name: str
    location_id: str
    location_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AssetManagerLocationCreate(BaseModel):
    asset_manager_id: str
    location_id: str

# Email Configuration Models
class EmailConfiguration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str  # This should be encrypted in production
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str
    from_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmailConfigurationCreate(BaseModel):
    smtp_server: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    use_tls: bool = True
    use_ssl: bool = False
    from_email: EmailStr
    from_name: str

class EmailConfigurationUpdate(BaseModel):
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    is_active: Optional[bool] = None

class EmailTestRequest(BaseModel):
    test_email: EmailStr
    
class NotificationRequest(BaseModel):
    to_emails: List[EmailStr]
    cc_emails: Optional[List[EmailStr]] = []
    subject: str
    message: str
    notification_type: str

# Email Service
class EmailService:
    def __init__(self):
        self.email_config = None
    
    async def get_email_config(self):
        """Get active email configuration"""
        try:
            # Debug: Check all email configurations
            all_configs = await db.email_configurations.find().to_list(10)
            logging.info(f"DEBUG: Found {len(all_configs)} email configurations total")
            for i, config in enumerate(all_configs):
                logging.info(f"DEBUG: Config {i+1}: active={config.get('is_active')}, id={config.get('id')}")
            
            # Find active configuration
            config = await db.email_configurations.find_one({"is_active": True})
            logging.info(f"DEBUG: Active config query result: {config}")
            
            if config:
                self.email_config = EmailConfiguration(**config)
                logging.info(f"DEBUG: Successfully loaded email config for {config.get('smtp_username')}")
                return self.email_config
            else:
                logging.error("DEBUG: No active email configuration found in database")
                return None
        except Exception as e:
            logging.error(f"DEBUG: Error in get_email_config: {str(e)}")
            return None
    
    async def send_email(self, to_emails: List[str], cc_emails: List[str], subject: str, html_content: str, text_content: str = None):
        """Send email using SMTP configuration"""
        config = await self.get_email_config()
        if not config:
            raise HTTPException(status_code=500, detail="No active email configuration found")
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{config.from_name} <{config.from_email}>"
            message['To'] = ', '.join(to_emails)
            if cc_emails:
                message['CC'] = ', '.join(cc_emails)
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
            
            # Send email
            all_recipients = to_emails + (cc_emails or [])
            
            if config.use_ssl:
                await aiosmtplib.send(
                    message,
                    hostname=config.smtp_server,
                    port=config.smtp_port,
                    username=config.smtp_username,
                    password=config.smtp_password,
                    use_tls=False,
                    start_tls=False
                )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=config.smtp_server,
                    port=config.smtp_port,
                    username=config.smtp_username,
                    password=config.smtp_password,
                    use_tls=config.use_tls,
                    start_tls=config.use_tls
                )
            
            return True
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    
    async def send_notification(self, notification_type: str, to_emails: List[str], cc_emails: List[str], context: Dict[str, Any]):
        """Send notification email using templates"""
        subject = self.get_email_subject(notification_type, context)
        html_content = self.get_email_template(notification_type, context)
        text_content = self.get_text_template(notification_type, context)
        
        await self.send_email(to_emails, cc_emails, subject, html_content, text_content)
    
    def get_email_subject(self, notification_type: str, context: Dict[str, Any]) -> str:
        """Get email subject based on notification type"""
        subjects = {
            "asset_request": "New Asset Request - {{asset_type_name}} by {{employee_name}}",
            "request_approved": "Asset Request Approved - {{asset_type_name}}",
            "request_rejected": "Asset Request Rejected - {{asset_type_name}}",
            "asset_allocated": "Asset Allocated - {{asset_type_name}} ({{asset_code}})",
            "asset_acknowledged": "Asset Acknowledgment Received - {{asset_type_name}} ({{asset_code}})",
            "ndc_created": "NDC Request Created - {{employee_name}} Asset Recovery Required",
            "ndc_completed": "NDC Request Completed - {{employee_name}} Asset Recovery Finalized"
        }
        
        subject_template = subjects.get(notification_type, "Asset Management Notification")
        template = Template(subject_template)
        return template.render(**context)
    
    def get_email_template(self, notification_type: str, context: Dict[str, Any]) -> str:
        """Get HTML email template based on notification type"""
        templates = {
            "asset_request": """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">New Asset Request</h2>
                    <p>Dear {{manager_name}},</p>
                    <p>A new asset request has been submitted and requires your approval:</p>
                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Request Details:</strong><br>
                        Employee: {{employee_name}}<br>
                        Asset Type: {{asset_type_name}}<br>
                        Request Type: {{request_type}}<br>
                        Required By: {{required_by_date}}<br>
                        Reason: {{reason}}
                    </div>
                    <p>Please log in to the Asset Management System to review and approve this request.</p>
                    <p>Best regards,<br>Asset Management System</p>
                </div>
            </body>
            </html>
            """,
            "request_approved": """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #16a34a;">Asset Request Approved</h2>
                    <p>Dear {{employee_name}},</p>
                    <p>Good news! Your asset request has been approved:</p>
                    <div style="background-color: #f0fdf4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Request Details:</strong><br>
                        Asset Type: {{asset_type_name}}<br>
                        Request Type: {{request_type}}<br>
                        Approved By: {{manager_name}}<br>
                        Approval Reason: {{approval_reason}}
                    </div>
                    <p>The Asset Manager will now process your request and allocate the asset soon.</p>
                    <p>Best regards,<br>Asset Management System</p>
                </div>
            </body>
            </html>
            """,
            "request_rejected": """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc2626;">Asset Request Rejected</h2>
                    <p>Dear {{employee_name}},</p>
                    <p>We regret to inform you that your asset request has been rejected:</p>
                    <div style="background-color: #fef2f2; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Request Details:</strong><br>
                        Asset Type: {{asset_type_name}}<br>
                        Request Type: {{request_type}}<br>
                        Rejected By: {{manager_name}}<br>
                        Rejection Reason: {{rejection_reason}}
                    </div>
                    <p>If you have any questions, please contact your manager or HR department.</p>
                    <p>Best regards,<br>Asset Management System</p>
                </div>
            </body>
            </html>
            """,
            "asset_allocated": """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Asset Allocated</h2>
                    <p>Dear {{employee_name}},</p>
                    <p>Your asset has been allocated and is ready for collection:</p>
                    <div style="background-color: #eff6ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Asset Details:</strong><br>
                        Asset Type: {{asset_type_name}}<br>
                        Asset Code: {{asset_code}}<br>
                        Asset Value: ₹{{asset_value}}<br>
                        Allocated By: {{asset_manager_name}}<br>
                        Allocation Date: {{allocation_date}}
                    </div>
                    <p>Please log in to the system to acknowledge receipt of this asset.</p>
                    <p>Best regards,<br>Asset Management System</p>
                </div>
            </body>
            </html>
            """,
            "asset_acknowledged": """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #16a34a;">Asset Acknowledgment Received</h2>
                    <p>Dear {{asset_manager_name}},</p>
                    <p>The employee has acknowledged receipt of the allocated asset:</p>
                    <div style="background-color: #f0fdf4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Asset Details:</strong><br>
                        Employee: {{employee_name}}<br>
                        Asset Type: {{asset_type_name}}<br>
                        Asset Code: {{asset_code}}<br>
                        Acknowledgment Date: {{acknowledgment_date}}<br>
                        Notes: {{acknowledgment_notes}}
                    </div>
                    <p>The asset allocation process has been completed successfully.</p>
                    <p>Best regards,<br>Asset Management System</p>
                </div>
            </body>
            </html>
            """,
            "ndc_created": """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc2626;">NDC Request Created - Asset Recovery Required</h2>
                    <p>Dear {{asset_manager_name}},</p>
                    <p>A No Dues Certificate (NDC) request has been created for an employee separation. Your action is required for asset recovery:</p>
                    <div style="background-color: #fef2f2; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Employee Details:</strong><br>
                        Name: {{employee_name}}<br>
                        Designation: {{employee_designation}}<br>
                        Last Working Date: {{last_working_date}}<br>
                        Separation Reason: {{separation_reason}}<br>
                        Assets to Recover: {{asset_count}} items
                    </div>
                    <p>Please log in to the Asset Management System to review and process the asset recovery for this employee.</p>
                    <p>Best regards,<br>Asset Management System</p>
                </div>
            </body>
            </html>
            """,
            "ndc_completed": """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #16a34a;">NDC Request Completed</h2>
                    <p>Dear {{employee_name}},</p>
                    <p>Your No Dues Certificate (NDC) request has been completed. All asset recovery processes have been finalized:</p>
                    <div style="background-color: #f0fdf4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Recovery Summary:</strong><br>
                        Total Assets: {{total_assets}}<br>
                        Assets Recovered: {{recovered_assets}}<br>
                        Processed By: {{asset_manager_name}}<br>
                        HR Manager: {{hr_manager_name}}
                    </div>
                    <p>Your separation process regarding asset recovery has been completed successfully.</p>
                    <p>Best regards,<br>Asset Management System</p>
                </div>
            </body>
            </html>
            """,
            "request_routed": """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Asset Request Routed</h2>
                    <p>Dear {{assigned_person_name}},</p>
                    <p>An approved asset request has been assigned to you for processing:</p>
                    <div style="background-color: #eff6ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Request Details:</strong><br>
                        Employee: {{employee_name}}<br>
                        Asset Type: {{asset_type_name}}<br>
                        Request Type: {{request_type}}<br>
                        Location: {{location_name}}<br>
                        Requisition ID: {{requisition_id}}<br>
                        Routing Reason: {{routing_reason}}
                    </div>
                    <p>Please log in to the Asset Management System to process this asset allocation request.</p>
                    <p>Best regards,<br>Asset Management System</p>
                </div>
            </body>
            </html>
            """
        }
        
        template_html = templates.get(notification_type, "<p>{{message}}</p>")
        template = Template(template_html)
        return template.render(**context)
    
    def get_text_template(self, notification_type: str, context: Dict[str, Any]) -> str:
        """Get plain text email template based on notification type"""
        templates = {
            "asset_request": """
New Asset Request

Dear {{manager_name}},

A new asset request has been submitted and requires your approval:

Request Details:
Employee: {{employee_name}}
Asset Type: {{asset_type_name}}
Request Type: {{request_type}}
Required By: {{required_by_date}}
Reason: {{reason}}

Please log in to the Asset Management System to review and approve this request.

Best regards,
Asset Management System
            """,
            "request_approved": """
Asset Request Approved

Dear {{employee_name}},

Good news! Your asset request has been approved:

Request Details:
Asset Type: {{asset_type_name}}
Request Type: {{request_type}}
Approved By: {{manager_name}}
Approval Reason: {{approval_reason}}

The Asset Manager will now process your request and allocate the asset soon.

Best regards,
Asset Management System
            """,
            "request_rejected": """
Asset Request Rejected

Dear {{employee_name}},

We regret to inform you that your asset request has been rejected:

Request Details:
Asset Type: {{asset_type_name}}
Request Type: {{request_type}}
Rejected By: {{manager_name}}
Rejection Reason: {{rejection_reason}}

If you have any questions, please contact your manager or HR department.

Best regards,
Asset Management System
            """,
            "asset_allocated": """
Asset Allocated

Dear {{employee_name}},

Your asset has been allocated and is ready for collection:

Asset Details:
Asset Type: {{asset_type_name}}
Asset Code: {{asset_code}}
Asset Value: ₹{{asset_value}}
Allocated By: {{asset_manager_name}}
Allocation Date: {{allocation_date}}

Please log in to the system to acknowledge receipt of this asset.

Best regards,
Asset Management System
            """,
            "asset_acknowledged": """
Asset Acknowledgment Received

Dear {{asset_manager_name}},

The employee has acknowledged receipt of the allocated asset:

Asset Details:
Employee: {{employee_name}}
Asset Type: {{asset_type_name}}
Asset Code: {{asset_code}}
Acknowledgment Date: {{acknowledgment_date}}
Notes: {{acknowledgment_notes}}

The asset allocation process has been completed successfully.

Best regards,
Asset Management System
            """,
            "ndc_created": """
NDC Request Created - Asset Recovery Required

Dear {{asset_manager_name}},

A No Dues Certificate (NDC) request has been created for an employee separation. Your action is required for asset recovery:

Employee Details:
Name: {{employee_name}}
Designation: {{employee_designation}}
Last Working Date: {{last_working_date}}
Separation Reason: {{separation_reason}}
Assets to Recover: {{asset_count}} items

Please log in to the Asset Management System to review and process the asset recovery for this employee.

Best regards,
Asset Management System
            """,
            "ndc_completed": """
NDC Request Completed

Dear {{employee_name}},

Your No Dues Certificate (NDC) request has been completed. All asset recovery processes have been finalized:

Recovery Summary:
Total Assets: {{total_assets}}
Assets Recovered: {{recovered_assets}}
Processed By: {{asset_manager_name}}
HR Manager: {{hr_manager_name}}

Your separation process regarding asset recovery has been completed successfully.

Best regards,
Asset Management System
            """,
            "request_routed": """
Asset Request Routed

Dear {{assigned_person_name}},

An approved asset request has been assigned to you for processing:

Request Details:
Employee: {{employee_name}}
Asset Type: {{asset_type_name}}
Request Type: {{request_type}}
Location: {{location_name}}
Requisition ID: {{requisition_id}}
Routing Reason: {{routing_reason}}

Please log in to the Asset Management System to process this asset allocation request.

Best regards,
Asset Management System
            """
        }
        
        template_text = templates.get(notification_type, "{{message}}")
        template = Template(template_text)
        return template.render(**context)

# Initialize email service
email_service = EmailService()

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
    
    # If not a demo user, check for regular users in database
    existing_user = await db.users.find_one({"email": user_data.email, "is_active": True})
    if existing_user and existing_user.get("password_hash"):
        # Hash the provided password and compare
        password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
        if password_hash == existing_user["password_hash"]:
            # Generate session token and update user
            session_token = str(uuid.uuid4())
            await db.users.update_one(
                {"email": user_data.email},
                {"$set": {"session_token": session_token}}
            )
            existing_user["session_token"] = session_token
            existing_user.pop("password_hash", None)  # Don't return password hash
            user = User(**existing_user)
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
    
    # Asset Types no longer have Asset Manager assignments (moved to Asset Definitions)
    # This is part of the restructuring where Asset Manager assignment moved from Asset Type to Asset Definition level
    
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
    
    # Asset Types no longer have Asset Manager assignments (moved to Asset Definitions)
    # Remove any Asset Manager fields from update data if they were sent
    update_data.pop("assigned_asset_manager_id", None)
    update_data.pop("assigned_asset_manager_name", None)
    
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
    
    # Populate Asset Manager name if ID is provided
    if asset_def.assigned_asset_manager_id:
        asset_manager = await db.users.find_one({
            "id": asset_def.assigned_asset_manager_id,
            "roles": {"$in": [UserRole.ASSET_MANAGER]},
            "is_active": True
        })
        if not asset_manager:
            raise HTTPException(status_code=400, detail="Asset Manager not found or inactive")
        asset_def_dict["assigned_asset_manager_name"] = asset_manager["name"]
    
    # Populate Location name if ID is provided
    if asset_def.location_id:
        location = await db.locations.find_one({
            "id": asset_def.location_id,
            "status": ActiveStatus.ACTIVE
        })
        if not location:
            raise HTTPException(status_code=400, detail="Location not found or inactive")
        asset_def_dict["location_name"] = location["name"]
    
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
    
    # If Asset Manager is being changed, validate and update name
    if "assigned_asset_manager_id" in update_data:
        if update_data["assigned_asset_manager_id"]:
            asset_manager = await db.users.find_one({
                "id": update_data["assigned_asset_manager_id"],
                "roles": {"$in": [UserRole.ASSET_MANAGER]},
                "is_active": True
            })
            if not asset_manager:
                raise HTTPException(status_code=400, detail="Asset Manager not found or inactive")
            update_data["assigned_asset_manager_name"] = asset_manager["name"]
        else:
            # Clear Asset Manager if set to None
            update_data["assigned_asset_manager_name"] = None
    
    # If Location is being changed, validate and update name
    if "location_id" in update_data:
        if update_data["location_id"]:
            location = await db.locations.find_one({
                "id": update_data["location_id"],
                "status": ActiveStatus.ACTIVE
            })
            if not location:
                raise HTTPException(status_code=400, detail="Location not found or inactive")
            update_data["location_name"] = location["name"]
        else:
            # Clear Location if set to None
            update_data["location_name"] = None
    
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

@api_router.post("/asset-definitions/{asset_def_id}/acknowledge")
async def acknowledge_asset_allocation(
    asset_def_id: str,
    acknowledgment: AssetAcknowledgmentRequest,
    current_user: User = Depends(get_current_user)
):
    """Employee acknowledges receipt of allocated asset"""
    # Get the asset definition
    asset = await db.asset_definitions.find_one({"id": asset_def_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check if asset is allocated to the current user
    if asset.get("allocated_to") != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You can only acknowledge assets allocated to you"
        )
    
    # Check if asset is already acknowledged
    if asset.get("acknowledged", False):
        raise HTTPException(
            status_code=400, 
            detail="Asset has already been acknowledged"
        )
    
    # Update asset with acknowledgment details
    update_data = {
        "acknowledged": True,
        "acknowledgment_date": datetime.now(timezone.utc),
        "acknowledgment_notes": acknowledgment.acknowledgment_notes
    }
    
    await db.asset_definitions.update_one(
        {"id": asset_def_id}, 
        {"$set": update_data}
    )
    
    # Get updated asset to return
    updated_asset = await db.asset_definitions.find_one({"id": asset_def_id})
    
    # Send email notification for asset acknowledgment
    try:
        # Trigger 5: When employee acknowledges the allocation
        # To: Asset Manager, CC: Employee, Manager, HR Manager
        
        # Get asset type details
        asset_type = await db.asset_types.find_one({"id": asset["asset_type_id"]})
        
        # Get Asset Manager (either assigned to asset type or the one who allocated)
        asset_manager = None
        if asset_type and asset_type.get("assigned_asset_manager_id"):
            asset_manager = await db.users.find_one({"id": asset_type["assigned_asset_manager_id"]})
        
        # If no specific asset manager assigned, find asset managers from allocations
        if not asset_manager:
            allocation = await db.asset_allocations.find_one({"asset_definition_id": asset_def_id})
            if allocation and allocation.get("allocated_by"):
                asset_manager = await db.users.find_one({"id": allocation["allocated_by"]})
        
        # Get manager details
        manager = None
        if current_user.reporting_manager_id:
            manager = await db.users.find_one({"id": current_user.reporting_manager_id})
        
        # Get HR managers
        hr_managers = await db.users.find({"roles": UserRole.HR_MANAGER, "is_active": True}).to_list(100)
        
        if asset_manager:
            to_emails = [asset_manager["email"]]
            cc_emails = [current_user.email]  # Employee
            
            # Add manager to CC if exists
            if manager:
                cc_emails.append(manager["email"])
            
            # Add HR managers to CC
            cc_emails.extend([hr["email"] for hr in hr_managers])
            
            # Context for email template
            context = {
                "asset_manager_name": asset_manager["name"],
                "employee_name": current_user.name,
                "asset_type_name": asset_type["name"] if asset_type else "Unknown",
                "asset_code": asset["asset_code"],
                "acknowledgment_date": update_data["acknowledgment_date"].strftime("%Y-%m-%d %H:%M:%S"),
                "acknowledgment_notes": acknowledgment.acknowledgment_notes or "No additional notes"
            }
            
            await email_service.send_notification(
                notification_type="asset_acknowledged",
                to_emails=to_emails,
                cc_emails=cc_emails,
                context=context
            )
    except Exception as e:
        # Log error but don't fail the acknowledgment
        logging.error(f"Failed to send asset acknowledgment notification: {str(e)}")
    
    return {
        "message": "Asset allocation acknowledged successfully",
        "asset": AssetDefinition(**updated_asset).dict(),
        "acknowledged_at": update_data["acknowledgment_date"]
    }

@api_router.get("/my-allocated-assets", response_model=List[AssetDefinition])
async def get_my_allocated_assets(
    current_user: User = Depends(get_current_user)
):
    """Get assets allocated to the current user"""
    assets = await db.asset_definitions.find({
        "allocated_to": current_user.id,
        "status": AssetStatus.ALLOCATED
    }).to_list(1000)
    
    return [AssetDefinition(**asset) for asset in assets]

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
    
    # Set manager ID and name from the requesting user's reporting manager
    if current_user.reporting_manager_id:
        requisition_dict["manager_id"] = current_user.reporting_manager_id
        requisition_dict["manager_name"] = current_user.reporting_manager_name
    
    # Convert required_by_date to datetime if provided as string
    if requisition_dict.get("required_by_date") and isinstance(requisition_dict["required_by_date"], str):
        requisition_dict["required_by_date"] = datetime.fromisoformat(requisition_dict["required_by_date"])
    
    await db.asset_requisitions.insert_one(requisition_dict)
    
    # Send email notification for asset request
    try:
        if current_user.reporting_manager_id:
            # Trigger 1: When employee requests for an asset
            # To: Manager, CC: Employee, HR Manager
            
            # Get manager details
            manager = await db.users.find_one({"id": current_user.reporting_manager_id})
            # Get HR managers
            hr_managers = await db.users.find({"roles": UserRole.HR_MANAGER, "is_active": True}).to_list(100)
            
            to_emails = [manager["email"]] if manager else []
            cc_emails = [current_user.email] + [hr["email"] for hr in hr_managers]
            
            # Prepare email context
            context = {
                "manager_name": manager["name"] if manager else "Manager",
                "employee_name": current_user.name,
                "asset_type_name": asset_type["name"],
                "request_type": requisition.request_type.value,
                "required_by_date": requisition_dict.get("required_by_date", "Not specified"),
                "reason": requisition.justification
            }
            
            await email_service.send_notification(
                notification_type="asset_request",
                to_emails=to_emails,
                cc_emails=cc_emails,
                context=context
            )
    except Exception as e:
        # Log error but don't fail the request
        logging.error(f"Failed to send asset request notification: {str(e)}")
    
    return AssetRequisition(**requisition_dict)

@api_router.get("/asset-requisitions", response_model=List[AssetRequisition])
async def get_asset_requisitions(current_user: User = Depends(get_current_user)):
    """Get asset requisitions based on user role"""
    if UserRole.EMPLOYEE in current_user.roles and len(current_user.roles) == 1:
        # Pure employees can only see their own requisitions
        requisitions = await db.asset_requisitions.find({"requested_by": current_user.id}).to_list(1000)
    elif UserRole.MANAGER in current_user.roles:
        # Managers can see requisitions from their direct reports
        requisitions = await db.asset_requisitions.find({
            "manager_id": current_user.id
        }).to_list(1000)
    else:
        # HR Managers and Administrators can see all requisitions
        requisitions = await db.asset_requisitions.find().to_list(1000)
    
    return [AssetRequisition(**req) for req in requisitions]

@api_router.delete("/asset-requisitions/{requisition_id}")
async def delete_asset_requisition(
    requisition_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete/withdraw an asset requisition (employees can only delete their own pending requests)"""
    # Get the requisition to check ownership and status
    requisition = await db.asset_requisitions.find_one({"id": requisition_id})
    if not requisition:
        raise HTTPException(status_code=404, detail="Asset requisition not found")
    
    # Check if current user can delete this requisition
    user_roles = current_user.roles if hasattr(current_user, 'roles') else [current_user.role] if hasattr(current_user, 'role') else []
    
    # Only the requester can withdraw their own pending requests, or admins/HR can delete any
    if requisition["requested_by"] != current_user.id:
        if not any(role in user_roles for role in ["Administrator", "HR Manager"]):
            raise HTTPException(
                status_code=403, 
                detail="You can only withdraw your own asset requests"
            )
    
    # Only allow deletion of pending requests (not approved/allocated ones)
    requisition_status = requisition.get("status", "Pending")  # Default to Pending if status is missing
    if requisition_status not in ["Pending"]:
        raise HTTPException(
            status_code=400, 
            detail="You can only withdraw pending requests. This request has already been processed."
        )
    
    # Delete the requisition
    result = await db.asset_requisitions.delete_one({"id": requisition_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Asset requisition not found")
    
    return {"message": "Asset requisition withdrawn successfully"}

@api_router.post("/asset-requisitions/{requisition_id}/manager-action")
async def manager_action_on_requisition(
    requisition_id: str,
    action_request: ManagerActionRequest,
    current_user: User = Depends(require_role([UserRole.MANAGER, UserRole.ADMINISTRATOR]))
):
    """Manager action on asset requisition (approve/reject/hold)"""
    # Get the requisition
    requisition = await db.asset_requisitions.find_one({"id": requisition_id})
    if not requisition:
        raise HTTPException(status_code=404, detail="Asset requisition not found")
    
    # Check if requisition is in pending status
    req_status = requisition.get("status", "Pending")  # Default to Pending if status is missing
    pending_status = RequisitionStatus.PENDING.value  # Use the string value for comparison
    
    if req_status != pending_status:
        raise HTTPException(
            status_code=400, 
            detail="Only pending requisitions can be acted upon by managers"
        )
    
    # Get the requester to verify manager relationship (for non-admin users)
    user_roles = current_user.roles if hasattr(current_user, 'roles') else [current_user.role] if hasattr(current_user, 'role') else []
    if UserRole.ADMINISTRATOR not in user_roles:
        # For managers, verify they are the reporting manager of the requester
        requester = await db.users.find_one({"id": requisition["requested_by"]})
        if not requester or requester.get("reporting_manager_id") != current_user.id:
            raise HTTPException(
                status_code=403, 
                detail="You can only act on requisitions from your direct reports"
            )
    
    # Prepare update data based on action
    update_data = {
        "manager_action_by": current_user.id,
        "manager_action_by_name": current_user.name,
        "manager_approval_date": datetime.now(timezone.utc)
    }
    
    if action_request.action.lower() == "approve":
        update_data["status"] = RequisitionStatus.MANAGER_APPROVED
        update_data["manager_approval_reason"] = action_request.reason
    elif action_request.action.lower() == "reject":
        update_data["status"] = RequisitionStatus.REJECTED
        update_data["manager_rejection_reason"] = action_request.reason
    elif action_request.action.lower() == "hold":
        update_data["status"] = RequisitionStatus.ON_HOLD
        update_data["manager_hold_reason"] = action_request.reason
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve', 'reject', or 'hold'")
    
    # Update the requisition
    await db.asset_requisitions.update_one({"id": requisition_id}, {"$set": update_data})
    
    # Enhanced Asset Allocation Logic - Route approved requests immediately
    if action_request.action.lower() == "approve":
        await perform_asset_allocation_routing(requisition_id, requisition)
    
    # Get updated requisition to return
    updated_requisition = await db.asset_requisitions.find_one({"id": requisition_id})
    
    # Send email notifications for manager action
    try:
        # Get employee details
        requester = await db.users.find_one({"id": requisition["requested_by"]})
        # Get HR managers
        hr_managers = await db.users.find({"roles": UserRole.HR_MANAGER, "is_active": True}).to_list(100)
        # Get asset manager if assigned to asset type
        asset_managers = []
        if requisition.get("asset_type_id"):
            asset_type = await db.asset_types.find_one({"id": requisition["asset_type_id"]})
            if asset_type and asset_type.get("assigned_asset_manager_id"):
                asset_manager = await db.users.find_one({"id": asset_type["assigned_asset_manager_id"]})
                if asset_manager:
                    asset_managers.append(asset_manager)
        
        if requester:
            to_emails = [requester["email"]]
            cc_emails = [current_user.email] + [hr["email"] for hr in hr_managers]
            
            # Add asset manager to CC if action is approve and asset manager is assigned
            if action_request.action.lower() == "approve" and asset_managers:
                cc_emails.extend([am["email"] for am in asset_managers])
            
            # Context for email template
            context = {
                "employee_name": requester["name"],
                "asset_type_name": requisition.get("asset_type_name", "Unknown"),
                "request_type": requisition.get("request_type", "Unknown"),
                "manager_name": current_user.name
            }
            
            if action_request.action.lower() == "approve":
                # Trigger 2: When Manager approves the asset request from employee
                # To: Employee, CC: Manager, Asset Manager responsible for that Asset, HR Manager
                context["approval_reason"] = action_request.reason
                await email_service.send_notification(
                    notification_type="request_approved",
                    to_emails=to_emails,
                    cc_emails=cc_emails,
                    context=context
                )
            elif action_request.action.lower() == "reject":
                # Trigger 3: When Manager rejects the asset request from employee
                # To: Employee, CC: Manager, HR Manager
                context["rejection_reason"] = action_request.reason
                await email_service.send_notification(
                    notification_type="request_rejected",
                    to_emails=to_emails,
                    cc_emails=cc_emails,
                    context=context
                )
    except Exception as e:
        # Log error but don't fail the request
        logging.error(f"Failed to send manager action notification: {str(e)}")
    
    return {
        "message": f"Requisition {action_request.action.lower()}ed successfully",
        "requisition": AssetRequisition(**updated_requisition).dict()
    }

async def perform_asset_allocation_routing(requisition_id: str, requisition: dict):
    """Enhanced Asset Allocation Logic - Route approved requests based on available Asset Definitions with Asset Manager and Location"""
    try:
        # Get employee details (requester)
        requested_user = await db.users.find_one({"id": requisition["requested_by"]})
        if not requested_user:
            logging.error(f"Employee not found for requisition {requisition_id}")
            return
        
        employee_location_id = requested_user.get("location_id")
        
        # Get available asset definitions of the requested type
        available_assets = await db.asset_definitions.find({
            "asset_type_id": requisition["asset_type_id"],
            "status": AssetStatus.AVAILABLE
        }).to_list(100)
        
        if not available_assets:
            logging.warning(f"No available assets found for requisition {requisition_id}")
            # Still continue with routing even if no assets available - assignment needed for procurement
        
        assigned_person = None
        routing_reason = "No routing performed"
        
        # Step 1: Find Asset Manager from available assets in employee's location (if employee has location)
        if employee_location_id and available_assets:
            for asset in available_assets:
                if (asset.get("assigned_asset_manager_id") and 
                    asset.get("location_id") == employee_location_id):
                    
                    # Verify the Asset Manager still exists and is active
                    asset_manager = await db.users.find_one({
                        "id": asset["assigned_asset_manager_id"],
                        "is_active": True,
                        "roles": {"$in": [UserRole.ASSET_MANAGER]}
                    })
                    
                    if asset_manager:
                        assigned_person = asset_manager
                        routing_reason = f"Routed to Asset Manager '{asset_manager['name']}' (manages assets in employee location '{asset.get('location_name', 'Unknown')}')"
                        break
        
        # Step 2: Find Asset Manager from any available assets (location-agnostic)
        if not assigned_person and available_assets:
            for asset in available_assets:
                if asset.get("assigned_asset_manager_id"):
                    # Verify the Asset Manager still exists and is active
                    asset_manager = await db.users.find_one({
                        "id": asset["assigned_asset_manager_id"],
                        "is_active": True,
                        "roles": {"$in": [UserRole.ASSET_MANAGER]}
                    })
                    
                    if asset_manager:
                        assigned_person = asset_manager
                        asset_location = asset.get("location_name", "Unknown Location")
                        routing_reason = f"Routed to Asset Manager '{asset_manager['name']}' (manages available assets at '{asset_location}')"
                        break
        
        # Step 3: Fallback to Administrator based on employee location
        if not assigned_person and employee_location_id:
            # Find Administrator assigned to the same location as the employee
            admin_location_assignments = await db.asset_manager_locations.find({
                "location_id": employee_location_id
            }).to_list(100)
            
            for assignment in admin_location_assignments:
                admin = await db.users.find_one({
                    "id": assignment["asset_manager_id"],
                    "is_active": True,
                    "roles": {"$in": [UserRole.ADMINISTRATOR]}
                })
                
                if admin:
                    assigned_person = admin
                    routing_reason = f"Routed to Administrator '{admin['name']}' (assigned to employee location)"
                    break
        
        # Step 4: Final fallback to any Administrator
        if not assigned_person:
            administrators = await db.users.find({
                "is_active": True,
                "roles": {"$in": [UserRole.ADMINISTRATOR]}
            }).to_list(1)
            
            if administrators:
                assigned_person = administrators[0]
                routing_reason = f"Routed to Administrator '{assigned_person['name']}' (general fallback - no location-specific assignment found)"
        
        # Step 5: Update requisition with assigned person
        if assigned_person:
            await db.asset_requisitions.update_one(
                {"id": requisition_id},
                {
                    "$set": {
                        "assigned_to": assigned_person["id"],
                        "assigned_to_name": assigned_person["name"],
                        "assigned_date": datetime.now(timezone.utc),
                        "routing_reason": routing_reason,
                        "status": RequisitionStatus.ASSIGNED_FOR_ALLOCATION
                    }
                }
            )
            
            # Step 6: Send notification emails about the routing
            try:
                # Get manager details
                manager = None
                if requested_user.get("reporting_manager_id"):
                    manager = await db.users.find_one({"id": requested_user["reporting_manager_id"]})
                
                # Get HR managers
                hr_managers = await db.users.find({"roles": UserRole.HR_MANAGER, "is_active": True}).to_list(100)
                
                # Get asset type for context
                asset_type = await db.asset_types.find_one({"id": requisition["asset_type_id"]})
                
                # Prepare email recipients
                to_emails = [assigned_person["email"]]  # Primary recipient: assigned Asset Manager/Administrator
                cc_emails = [requested_user["email"]]  # CC: Employee who requested
                
                # Add manager to CC if exists
                if manager:
                    cc_emails.append(manager["email"])
                
                # Add HR managers to CC
                cc_emails.extend([hr["email"] for hr in hr_managers])
                
                # Context for email template
                context = {
                    "employee_name": requested_user["name"],
                    "asset_type_name": asset_type["name"] if asset_type else "Unknown",
                    "request_type": requisition.get("request_type", "Asset Request"),
                    "assigned_person_name": assigned_person["name"],
                    "routing_reason": routing_reason,
                    "location_name": requested_user.get("location_name", "Unknown Location"),
                    "requisition_id": requisition_id,
                    "available_assets_count": len(available_assets)
                }
                
                await email_service.send_notification(
                    notification_type="request_routed",
                    to_emails=to_emails,
                    cc_emails=cc_emails,
                    context=context
                )
                
                logging.info(f"Successfully routed requisition {requisition_id}: {routing_reason}")
                
            except Exception as e:
                # Log error but don't fail the routing
                logging.error(f"Failed to send routing notification for requisition {requisition_id}: {str(e)}")
        else:
            logging.error(f"No Asset Manager or Administrator found to route requisition {requisition_id}")
        
    except Exception as e:
        logging.error(f"Failed to perform enhanced asset allocation routing for requisition {requisition_id}: {str(e)}")

@api_router.post("/asset-requisitions/{requisition_id}/hr-action")
async def hr_action_on_requisition(
    requisition_id: str,
    action_request: HRActionRequest,
    current_user: User = Depends(require_role([UserRole.HR_MANAGER, UserRole.ADMINISTRATOR]))
):
    """HR Manager action on asset requisition (approve/reject/hold)"""
    # Get the requisition
    requisition = await db.asset_requisitions.find_one({"id": requisition_id})
    if not requisition:
        raise HTTPException(status_code=404, detail="Asset requisition not found")
    
    # Check if requisition is in manager approved or on hold status
    valid_statuses = [RequisitionStatus.MANAGER_APPROVED, RequisitionStatus.ON_HOLD]
    if requisition.get("status") not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail="HR can only act on manager-approved or on-hold requisitions"
        )
    
    # Prepare update data based on action
    update_data = {
        "hr_action_by": current_user.id,
        "hr_action_by_name": current_user.name,
        "hr_approval_date": datetime.now(timezone.utc)
    }
    
    if action_request.action.lower() == "approve":
        update_data["status"] = RequisitionStatus.HR_APPROVED
        update_data["hr_approval_reason"] = action_request.reason
    elif action_request.action.lower() == "reject":
        update_data["status"] = RequisitionStatus.REJECTED
        update_data["hr_rejection_reason"] = action_request.reason
    elif action_request.action.lower() == "hold":
        update_data["status"] = RequisitionStatus.ON_HOLD
        update_data["hr_hold_reason"] = action_request.reason
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve', 'reject', or 'hold'")
    
    # Update the requisition
    await db.asset_requisitions.update_one({"id": requisition_id}, {"$set": update_data})
    
    # Enhanced Asset Allocation Logic - Route approved requests immediately
    if action_request.action.lower() == "approve":
        await perform_asset_allocation_routing(requisition_id, requisition)
    
    # Get updated requisition to return
    updated_requisition = await db.asset_requisitions.find_one({"id": requisition_id})
    
    return {
        "message": f"Requisition {action_request.action.lower()}ed successfully",
        "requisition": AssetRequisition(**updated_requisition).dict()
    }

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
        # Manager-specific statistics: requests from their direct reports
        # Get all requisitions from the manager's direct reports
        total_requisitions = await db.asset_requisitions.count_documents({
            "manager_id": current_user.id
        })
        
        approved_requests = await db.asset_requisitions.count_documents({
            "manager_id": current_user.id,
            "status": RequisitionStatus.MANAGER_APPROVED
        })
        
        rejected_requests = await db.asset_requisitions.count_documents({
            "manager_id": current_user.id, 
            "status": RequisitionStatus.REJECTED,
            "manager_rejection_reason": {"$exists": True}
        })
        
        held_requests = await db.asset_requisitions.count_documents({
            "manager_id": current_user.id,
            "status": RequisitionStatus.ON_HOLD
        })
        
        stats.update({
            "total_requisitions": total_requisitions,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "held_requests": held_requests
        })
    
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
    
    # Validate location if provided
    location_name = None
    if user_data.location_id:
        location = await db.locations.find_one({"id": user_data.location_id})
        if not location:
            raise HTTPException(status_code=400, detail="Location not found")
        location_name = location["name"]
    
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
        "location_id": user_data.location_id,
        "location_name": location_name,
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

@api_router.get("/users/asset-managers", response_model=List[User])
async def get_asset_managers(
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.HR_MANAGER]))
):
    """Get all users with Asset Manager role"""
    asset_managers = await db.users.find({"roles": UserRole.ASSET_MANAGER, "is_active": True}, {"password_hash": 0}).to_list(1000)
    return [User(**asset_manager) for asset_manager in asset_managers]

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
    
    # Validate email uniqueness if provided
    if "email" in update_data and update_data["email"]:
        # Check if email already exists (excluding current user)
        existing_email_user = await db.users.find_one({
            "email": update_data["email"],
            "id": {"$ne": user_id}  # Exclude current user from check
        })
        if existing_email_user:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Handle password update if provided
    if "password" in update_data and update_data["password"]:
        # Hash the new password
        password_hash = hashlib.sha256(update_data["password"].encode()).hexdigest()
        update_data["password_hash"] = password_hash
        # Remove the plain password from update data
        del update_data["password"]
    
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
    
    # Validate and update location if provided
    if "location_id" in update_data:
        if update_data["location_id"]:
            location = await db.locations.find_one({"id": update_data["location_id"]})
            if not location:
                raise HTTPException(status_code=400, detail="Location not found")
            update_data["location_name"] = location["name"]
        else:
            # Clear location
            update_data["location_name"] = None
    
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
    
    if requisition["status"] not in [RequisitionStatus.MANAGER_APPROVED, RequisitionStatus.HR_APPROVED, RequisitionStatus.ASSIGNED_FOR_ALLOCATION]:
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
                "allocated_to_name": requested_user["name"] if requested_user else None,
                "allocation_date": datetime.now(timezone.utc)
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
    
    # Send email notification for asset allocation
    try:
        # Trigger 4: When Asset Manager allocates the asset to employee
        # To: Employee, CC: Asset Manager, Manager, HR Manager
        
        # Get manager details
        manager = None
        if requested_user and requested_user.get("reporting_manager_id"):
            manager = await db.users.find_one({"id": requested_user["reporting_manager_id"]})
        
        # Get HR managers
        hr_managers = await db.users.find({"roles": UserRole.HR_MANAGER, "is_active": True}).to_list(100)
        
        if requested_user:
            to_emails = [requested_user["email"]]
            cc_emails = [current_user.email]  # Asset Manager
            
            # Add manager to CC if exists
            if manager:
                cc_emails.append(manager["email"])
            
            # Add HR managers to CC
            cc_emails.extend([hr["email"] for hr in hr_managers])
            
            # Context for email template
            context = {
                "employee_name": requested_user["name"],
                "asset_type_name": asset_type["name"] if asset_type else "Unknown",
                "asset_code": asset_def["asset_code"],
                "asset_value": asset_def.get("asset_value", 0),
                "asset_manager_name": current_user.name,
                "allocation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            await email_service.send_notification(
                notification_type="asset_allocated",
                to_emails=to_emails,
                cc_emails=cc_emails,
                context=context
            )
    except Exception as e:
        # Log error but don't fail the allocation
        logging.error(f"Failed to send asset allocation notification: {str(e)}")
    
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

# Email Configuration Routes
@api_router.post("/email-config", response_model=EmailConfiguration)
async def create_email_configuration(
    email_config: EmailConfigurationCreate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Create or update email configuration"""
    try:
        logging.info(f"DEBUG: Creating email config for user {current_user.email}")
        logging.info(f"DEBUG: Email config data: {email_config.dict()}")
        logging.info(f"DEBUG: Database name: {db.name}")
        
        # Check existing configurations before deactivating
        existing_configs = await db.email_configurations.find().to_list(100)
        logging.info(f"DEBUG: Found {len(existing_configs)} existing configurations before deactivate")
        
        # Deactivate any existing configurations
        update_result = await db.email_configurations.update_many({}, {"$set": {"is_active": False}})
        logging.info(f"DEBUG: Deactivated {update_result.modified_count} existing configurations")
        
        email_config_dict = email_config.dict()
        email_config_dict["id"] = str(uuid.uuid4())
        email_config_dict["is_active"] = True  # Explicitly set active - this is the critical fix!
        email_config_dict["created_at"] = datetime.now(timezone.utc)
        email_config_dict["updated_at"] = datetime.now(timezone.utc)
        logging.info(f"DEBUG: Prepared config dict with ID: {email_config_dict['id']}")
        logging.info(f"DEBUG: Config dict keys: {list(email_config_dict.keys())}")
        
        # Insert new configuration
        insert_result = await db.email_configurations.insert_one(email_config_dict)
        logging.info(f"DEBUG: Inserted config, MongoDB _id: {insert_result.inserted_id}")
        
        # Verify insertion with multiple queries
        verification1 = await db.email_configurations.find_one({"id": email_config_dict["id"]})
        logging.info(f"DEBUG: Verification by ID: {verification1 is not None}")
        
        verification2 = await db.email_configurations.find_one({"is_active": True})
        logging.info(f"DEBUG: Verification by is_active=True: {verification2 is not None}")
        
        all_configs_after = await db.email_configurations.find().to_list(100)
        logging.info(f"DEBUG: Total configs after insert: {len(all_configs_after)}")
        
        for i, config in enumerate(all_configs_after):
            logging.info(f"DEBUG: Config {i+1} after insert: id={config.get('id')[:8]}..., is_active={config.get('is_active')}")
        
        # Reset email service config cache
        email_service.email_config = None
        logging.info("DEBUG: Reset email service cache")
        
        return EmailConfiguration(**email_config_dict)
    except Exception as e:
        logging.error(f"DEBUG: Error creating email configuration: {str(e)}")
        import traceback
        logging.error(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create email configuration: {str(e)}")

@api_router.get("/email-config", response_model=EmailConfiguration)
async def get_email_configuration(
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Get active email configuration"""
    config = await db.email_configurations.find_one({"is_active": True})
    if not config:
        raise HTTPException(status_code=404, detail="No email configuration found")
    
    # Don't return password in response
    config_response = config.copy()
    config_response["smtp_password"] = "***masked***"
    return EmailConfiguration(**config_response)

@api_router.put("/email-config/{config_id}", response_model=EmailConfiguration)
async def update_email_configuration(
    config_id: str,
    email_config_update: EmailConfigurationUpdate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Update email configuration"""
    existing = await db.email_configurations.find_one({"id": config_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Email configuration not found")
    
    update_data = email_config_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.email_configurations.update_one({"id": config_id}, {"$set": update_data})
    
    # Reset email service config cache
    email_service.email_config = None
    
    updated = await db.email_configurations.find_one({"id": config_id})
    # Don't return password in response
    updated["smtp_password"] = "***masked***"
    return EmailConfiguration(**updated)

@api_router.post("/email-config/test")
async def test_email_configuration(
    test_request: EmailTestRequest,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Test email configuration by sending a test email"""
    try:
        logging.info("DEBUG: Starting email test...")
        
        # Check all email configurations in database
        all_configs = await db.email_configurations.find().to_list(100)
        logging.info(f"DEBUG: Found {len(all_configs)} total email configurations")
        
        for i, config in enumerate(all_configs):
            logging.info(f"DEBUG: Config {i+1}: id={config.get('id')}, is_active={config.get('is_active')}, smtp_username={config.get('smtp_username')}")
        
        # Try to find active configuration
        config = await db.email_configurations.find_one({"is_active": True})
        logging.info(f"DEBUG: Active config query result: {config}")
        
        # If no active config found, try to find any config
        if not config:
            config = await db.email_configurations.find_one({})
            logging.info(f"DEBUG: Any config query result: {config}")
        
        if not config:
            # Let's also check the database and collection names
            logging.info(f"DEBUG: Database name: {db.name}")
            collections = await db.list_collection_names()
            logging.info(f"DEBUG: Available collections: {collections}")
            
            raise HTTPException(status_code=500, detail=f"No email configuration found in database. Found {len(all_configs)} configs total. Please save configuration first.")
        
        # Force use the first available config if no active one
        if not config.get('is_active'):
            logging.info("DEBUG: Using first available config since no active config found")
        
        # Create email service instance with fresh config
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import aiosmtplib
        
        subject = "Asset Management System - Email Test"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Email Configuration Test</h2>
                <p>Dear Administrator,</p>
                <p>This is a test email to verify your SMTP configuration is working correctly.</p>
                <p>If you received this email, your email configuration is set up properly!</p>
                <p>Best regards,<br>Asset Management System</p>
            </div>
        </body>
        </html>
        """
        text_content = """
Asset Management System - Email Configuration Test

Dear Administrator,

This is a test email to verify your SMTP configuration is working correctly.

If you received this email, your email configuration is set up properly!

Best regards,
Asset Management System
        """
        
        logging.info(f"DEBUG: Using config with SMTP server: {config.get('smtp_server')}, username: {config.get('smtp_username')}")
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = f"{config['from_name']} <{config['from_email']}>"
        message['To'] = test_request.test_email
        
        # Add text content
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        message.attach(text_part)
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)
        
        # Send email directly with correct TLS configuration
        logging.info(f"DEBUG: Sending email with config: server={config['smtp_server']}, port={config['smtp_port']}, use_tls={config.get('use_tls')}, use_ssl={config.get('use_ssl')}")
        
        if config.get('use_ssl'):
            # SSL connection (usually port 465)
            await aiosmtplib.send(
                message,
                hostname=config['smtp_server'],
                port=config['smtp_port'],
                username=config['smtp_username'],
                password=config['smtp_password'],
                use_tls=True,
                start_tls=False
            )
        elif config.get('use_tls'):
            # STARTTLS connection (usually port 587)
            await aiosmtplib.send(
                message,
                hostname=config['smtp_server'],
                port=config['smtp_port'],
                username=config['smtp_username'],
                password=config['smtp_password'],
                use_tls=False,
                start_tls=True
            )
        else:
            # Plain connection (not recommended)
            await aiosmtplib.send(
                message,
                hostname=config['smtp_server'],
                port=config['smtp_port'],
                username=config['smtp_username'],
                password=config['smtp_password'],
                use_tls=False,
                start_tls=False
            )
        
        logging.info("DEBUG: Email sent successfully")
        return {"message": "Test email sent successfully", "sent_to": test_request.test_email}
    except Exception as e:
        logging.error(f"DEBUG: Failed to send test email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

# Location Management Routes
@api_router.get("/locations", response_model=List[Location])
async def get_locations(
    current_user: User = Depends(get_current_user)
):
    """Get all locations"""
    locations = await db.locations.find().to_list(1000)
    return [Location(**location) for location in locations]

@api_router.post("/locations", response_model=Location)
async def create_location(
    location: LocationCreate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Create new location"""
    # Check if location code already exists
    existing = await db.locations.find_one({"code": location.code})
    if existing:
        raise HTTPException(status_code=400, detail="Location code already exists")
    
    location_dict = location.dict()
    location_dict["id"] = str(uuid.uuid4())
    location_dict["created_at"] = datetime.now(timezone.utc)
    location_dict["updated_at"] = datetime.now(timezone.utc)
    
    await db.locations.insert_one(location_dict)
    return Location(**location_dict)

@api_router.put("/locations/{location_id}", response_model=Location)
async def update_location(
    location_id: str,
    location_update: LocationUpdate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Update location"""
    existing = await db.locations.find_one({"id": location_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if new code conflicts with existing locations
    update_data = location_update.dict(exclude_unset=True)
    if "code" in update_data:
        code_conflict = await db.locations.find_one({
            "code": update_data["code"], 
            "id": {"$ne": location_id}
        })
        if code_conflict:
            raise HTTPException(status_code=400, detail="Location code already exists")
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.locations.update_one({"id": location_id}, {"$set": update_data})
    
    updated = await db.locations.find_one({"id": location_id})
    return Location(**updated)

@api_router.delete("/locations/{location_id}")
async def delete_location(
    location_id: str,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Delete location"""
    existing = await db.locations.find_one({"id": location_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if location is assigned to any users
    users_with_location = await db.users.find_one({"location_id": location_id})
    if users_with_location:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete location that is assigned to users"
        )
    
    # Check if location is assigned to any asset managers
    asset_managers_with_location = await db.asset_manager_locations.find_one({"location_id": location_id})
    if asset_managers_with_location:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete location that is assigned to asset managers"
        )
    
    await db.locations.delete_one({"id": location_id})
    return {"message": "Location deleted successfully"}

# Asset Manager Location Assignment Routes
@api_router.get("/asset-manager-locations", response_model=List[AssetManagerLocation])
async def get_asset_manager_locations(
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Get all asset manager location assignments"""
    assignments = await db.asset_manager_locations.find().to_list(1000)
    return [AssetManagerLocation(**assignment) for assignment in assignments]

@api_router.post("/asset-manager-locations", response_model=AssetManagerLocation)
async def assign_asset_manager_location(
    assignment: AssetManagerLocationCreate,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Assign asset manager to location"""
    # Validate asset manager exists and has Asset Manager role
    asset_manager = await db.users.find_one({"id": assignment.asset_manager_id})
    if not asset_manager:
        raise HTTPException(status_code=404, detail="Asset manager not found")
    
    if UserRole.ASSET_MANAGER not in asset_manager.get("roles", []):
        raise HTTPException(status_code=400, detail="User is not an Asset Manager")
    
    # Validate location exists
    location = await db.locations.find_one({"id": assignment.location_id})
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if assignment already exists
    existing = await db.asset_manager_locations.find_one({
        "asset_manager_id": assignment.asset_manager_id,
        "location_id": assignment.location_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Asset manager already assigned to this location")
    
    assignment_dict = {
        "id": str(uuid.uuid4()),
        "asset_manager_id": assignment.asset_manager_id,
        "asset_manager_name": asset_manager["name"],
        "location_id": assignment.location_id,
        "location_name": location["name"],
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.asset_manager_locations.insert_one(assignment_dict)
    return AssetManagerLocation(**assignment_dict)

@api_router.delete("/asset-manager-locations/{assignment_id}")
async def remove_asset_manager_location(
    assignment_id: str,
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Remove asset manager location assignment"""
    existing = await db.asset_manager_locations.find_one({"id": assignment_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    await db.asset_manager_locations.delete_one({"id": assignment_id})
    return {"message": "Asset manager location assignment removed successfully"}

# Data Migration Endpoint - Set Default Location for Existing Users
@api_router.post("/migrate/set-default-location")
async def set_default_location_for_users(
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """Set default location for existing users without location assignment"""
    # First, create a default location if it doesn't exist
    default_location = await db.locations.find_one({"code": "DEFAULT"})
    if not default_location:
        default_location_dict = {
            "id": str(uuid.uuid4()),
            "code": "DEFAULT",
            "name": "Default Location",
            "country": "N/A",
            "status": "Active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.locations.insert_one(default_location_dict)
        default_location_id = default_location_dict["id"]
        default_location_name = default_location_dict["name"]
    else:
        default_location_id = default_location["id"]
        default_location_name = default_location["name"]
    
    # Update users without location assignment
    result = await db.users.update_many(
        {"location_id": {"$exists": False}},  # Users without location_id field
        {"$set": {
            "location_id": default_location_id,
            "location_name": default_location_name
        }}
    )
    
    # Also update users with null location_id
    result2 = await db.users.update_many(
        {"location_id": None},  # Users with null location_id
        {"$set": {
            "location_id": default_location_id,
            "location_name": default_location_name
        }}
    )
    
    total_updated = result.modified_count + result2.modified_count
    
    return {
        "message": f"Default location set for {total_updated} existing users",
        "default_location": default_location_name,
        "updated_count": total_updated
    }

# NDC (No Dues Certificate) Management Routes

# Separation Reasons Management
@api_router.get("/separation-reasons", response_model=List[SeparationReason])
async def get_separation_reasons(
    current_user: User = Depends(require_role([UserRole.HR_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Get all separation reasons"""
    reasons = await db.separation_reasons.find().to_list(100)
    return [SeparationReason(**reason) for reason in reasons]

@api_router.post("/separation-reasons", response_model=SeparationReason)
async def create_separation_reason(
    reason_data: SeparationReasonCreate,
    current_user: User = Depends(require_role([UserRole.HR_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Create new separation reason"""
    # Check if reason already exists
    existing = await db.separation_reasons.find_one({"reason": reason_data.reason})
    if existing:
        raise HTTPException(status_code=400, detail="Separation reason already exists")
    
    reason_dict = {
        "id": str(uuid.uuid4()),
        "reason": reason_data.reason,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.separation_reasons.insert_one(reason_dict)
    return SeparationReason(**reason_dict)

# NDC Request Management
@api_router.get("/ndc-requests", response_model=List[NDCRequest])
async def get_ndc_requests(
    current_user: User = Depends(get_current_user)
):
    """Get NDC requests based on user role"""
    if UserRole.HR_MANAGER in current_user.roles:
        # HR Managers see all NDC requests
        requests = await db.ndc_requests.find().to_list(1000)
    elif UserRole.ASSET_MANAGER in current_user.roles:
        # Asset Managers see only their assigned requests
        requests = await db.ndc_requests.find({"asset_manager_id": current_user.id}).to_list(1000)
    elif UserRole.ADMINISTRATOR in current_user.roles:
        # Administrators see all
        requests = await db.ndc_requests.find().to_list(1000)
    else:
        # Employee or other roles - access denied
        raise HTTPException(status_code=403, detail="Access denied. Insufficient permissions to view NDC requests.")
    
    return [NDCRequest(**request) for request in requests]

@api_router.post("/ndc-requests", response_model=dict)
async def create_ndc_request(
    ndc_data: NDCRequestCreate,
    current_user: User = Depends(require_role([UserRole.HR_MANAGER]))
):
    """Create NDC request for employee separation"""
    # Get employee details
    employee = await db.users.find_one({"id": ndc_data.employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get separation approver details
    approver = await db.users.find_one({"id": ndc_data.separation_approved_by})
    if not approver:
        raise HTTPException(status_code=404, detail="Separation approver not found")
    
    # Get all assets assigned to the employee
    assigned_assets = await db.asset_definitions.find({
        "allocated_to": ndc_data.employee_id,
        "status": "Allocated"
    }).to_list(1000)
    
    if not assigned_assets:
        raise HTTPException(status_code=400, detail="Employee has no allocated assets")
    
    # Group assets by Asset Manager (based on location and asset type)
    asset_manager_groups = {}
    
    for asset in assigned_assets:
        # Get asset type details
        asset_type = await db.asset_types.find_one({"id": asset["asset_type_id"]})
        
        # Find Asset Manager for this asset (by location + asset type)
        asset_manager = None
        if asset_type and asset_type.get("assigned_asset_manager_id"):
            # Check if Asset Manager is assigned to the employee's location
            am_location = await db.asset_manager_locations.find_one({
                "asset_manager_id": asset_type["assigned_asset_manager_id"],
                "location_id": employee.get("location_id")
            })
            if am_location:
                asset_manager = await db.users.find_one({"id": asset_type["assigned_asset_manager_id"]})
        
        # Fallback to Administrator if no Asset Manager found
        if not asset_manager:
            # Find an Administrator
            admin = await db.users.find_one({"roles": {"$in": [UserRole.ADMINISTRATOR]}})
            if admin:
                asset_manager = admin
        
        if asset_manager:
            am_id = asset_manager["id"]
            if am_id not in asset_manager_groups:
                asset_manager_groups[am_id] = {
                    "asset_manager": asset_manager,
                    "assets": []
                }
            asset_manager_groups[am_id]["assets"].append(asset)
    
    # Create NDC requests for each Asset Manager
    created_requests = []
    
    for am_id, group_data in asset_manager_groups.items():
        asset_manager = group_data["asset_manager"]
        assets = group_data["assets"]
        
        # Create NDC request
        ndc_request_dict = {
            "id": str(uuid.uuid4()),
            "employee_id": ndc_data.employee_id,
            "employee_name": employee["name"],
            "employee_code": employee.get("employee_code", "N/A"),
            "employee_designation": employee.get("designation"),
            "employee_date_of_joining": employee.get("date_of_joining"),
            "employee_location_name": employee.get("location_name"),
            "employee_reporting_manager_name": employee.get("reporting_manager_name"),
            
            "resigned_on": ndc_data.resigned_on,
            "notice_period": ndc_data.notice_period,
            "last_working_date": ndc_data.last_working_date,
            "separation_approved_by": ndc_data.separation_approved_by,
            "separation_approved_by_name": approver["name"],
            "separation_approved_on": ndc_data.separation_approved_on,
            "separation_reason": ndc_data.separation_reason,
            
            "created_by": current_user.id,
            "created_by_name": current_user.name,
            "asset_manager_id": asset_manager["id"],
            "asset_manager_name": asset_manager["name"],
            "status": "Pending",
            
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.ndc_requests.insert_one(ndc_request_dict)
        
        # Create asset recovery records
        for asset in assets:
            asset_type = await db.asset_types.find_one({"id": asset["asset_type_id"]})
            
            recovery_dict = {
                "id": str(uuid.uuid4()),
                "ndc_request_id": ndc_request_dict["id"],
                "asset_definition_id": asset["id"],
                "asset_code": asset["asset_code"],
                "asset_type_name": asset_type["name"] if asset_type else "Unknown",
                "asset_value": asset.get("asset_value", 0),
                "status": "Pending",
                "updated_at": datetime.now(timezone.utc)
            }
            
            await db.ndc_asset_recovery.insert_one(recovery_dict)
        
        created_requests.append({
            "ndc_request_id": ndc_request_dict["id"],
            "asset_manager_name": asset_manager["name"],
            "asset_count": len(assets)
        })
        
        # Send email notification to Asset Manager
        try:
            # Get HR managers for CC
            hr_managers = await db.users.find({"roles": UserRole.HR_MANAGER, "is_active": True}).to_list(100)
            reporting_manager = await db.users.find_one({"id": employee.get("reporting_manager_id")}) if employee.get("reporting_manager_id") else None
            
            to_emails = [asset_manager["email"]]
            cc_emails = [current_user.email]  # HR Manager
            
            if reporting_manager:
                cc_emails.append(reporting_manager["email"])
            
            context = {
                "asset_manager_name": asset_manager["name"],
                "employee_name": employee["name"],
                "employee_designation": employee.get("designation", "N/A"),
                "last_working_date": ndc_data.last_working_date.strftime("%Y-%m-%d"),
                "asset_count": len(assets),
                "separation_reason": ndc_data.separation_reason
            }
            
            await email_service.send_notification(
                notification_type="ndc_created",
                to_emails=to_emails,
                cc_emails=cc_emails,  
                context=context
            )
        except Exception as e:
            logging.error(f"Failed to send NDC creation notification: {str(e)}")
    
    return {
        "message": f"NDC requests created successfully for {len(created_requests)} Asset Manager(s)",
        "requests": created_requests
    }

@api_router.get("/ndc-requests/{ndc_id}/assets", response_model=List[NDCAssetRecovery])
async def get_ndc_assets(
    ndc_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get assets for NDC request"""
    # Verify access
    ndc_request = await db.ndc_requests.find_one({"id": ndc_id})
    if not ndc_request:
        raise HTTPException(status_code=404, detail="NDC request not found")
    
    # Check if user has access
    if (UserRole.ASSET_MANAGER in current_user.roles and ndc_request["asset_manager_id"] != current_user.id and
        UserRole.HR_MANAGER not in current_user.roles and UserRole.ADMINISTRATOR not in current_user.roles):
        raise HTTPException(status_code=403, detail="Access denied")
    
    assets = await db.ndc_asset_recovery.find({"ndc_request_id": ndc_id}).to_list(1000)
    return [NDCAssetRecovery(**asset) for asset in assets]

@api_router.put("/ndc-asset-recovery/{recovery_id}", response_model=NDCAssetRecovery)
async def update_asset_recovery(
    recovery_id: str,
    recovery_data: NDCAssetRecoveryUpdate,
    current_user: User = Depends(require_role([UserRole.ASSET_MANAGER, UserRole.ADMINISTRATOR]))
):
    """Update asset recovery details by Asset Manager"""
    recovery = await db.ndc_asset_recovery.find_one({"id": recovery_id})
    if not recovery:
        raise HTTPException(status_code=404, detail="Asset recovery record not found")
    
    # Get NDC request to verify access
    ndc_request = await db.ndc_requests.find_one({"id": recovery["ndc_request_id"]})
    if (UserRole.ASSET_MANAGER in current_user.roles and 
        ndc_request and ndc_request["asset_manager_id"] != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = recovery_data.dict()
    update_data["status"] = "Recovered" if recovery_data.recovered else "Not Recovered"
    update_data["updated_by"] = current_user.id
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.ndc_asset_recovery.update_one({"id": recovery_id}, {"$set": update_data})
    
    # Check if all assets are processed for this NDC request
    if ndc_request:
        all_assets = await db.ndc_asset_recovery.find({"ndc_request_id": ndc_request["id"]}).to_list(1000)
        processed_assets = [asset for asset in all_assets if asset.get("recovered") is not None]
        
        if len(processed_assets) == len(all_assets):
            # All assets processed, update NDC request status
            await db.ndc_requests.update_one(
                {"id": ndc_request["id"]},
                {"$set": {"status": "Completed", "updated_at": datetime.now(timezone.utc)}}
            )
            
            # Send completion notification
            try:
                employee = await db.users.find_one({"id": ndc_request["employee_id"]})
                hr_manager = await db.users.find_one({"id": ndc_request["created_by"]})
                reporting_manager = await db.users.find_one({"id": employee.get("reporting_manager_id")}) if employee and employee.get("reporting_manager_id") else None
                
                if employee and hr_manager:
                    to_emails = [employee["email"], hr_manager["email"]]
                    cc_emails = []
                    if reporting_manager:
                        cc_emails.append(reporting_manager["email"])
                    
                    context = {
                        "employee_name": employee["name"],
                        "hr_manager_name": hr_manager["name"],
                        "asset_manager_name": current_user.name,
                        "total_assets": len(all_assets),
                        "recovered_assets": len([a for a in all_assets if a.get("recovered") == True])
                    }
                    
                    await email_service.send_notification(
                        notification_type="ndc_completed",
                        to_emails=to_emails,
                        cc_emails=cc_emails,
                        context=context
                    )
            except Exception as e:
                logging.error(f"Failed to send NDC completion notification: {str(e)}")
    
    updated = await db.ndc_asset_recovery.find_one({"id": recovery_id})
    return NDCAssetRecovery(**updated)

@api_router.post("/ndc-requests/{ndc_id}/revoke")
async def revoke_ndc_request(
    ndc_id: str,
    revoke_data: NDCRevokeRequest,
    current_user: User = Depends(require_role([UserRole.HR_MANAGER]))
):
    """Revoke NDC request"""
    ndc_request = await db.ndc_requests.find_one({"id": ndc_id})
    if not ndc_request:
        raise HTTPException(status_code=404, detail="NDC request not found")
    
    if ndc_request["status"] == "Completed":
        raise HTTPException(status_code=400, detail="Cannot revoke completed NDC request")
    
    # Update NDC request status
    await db.ndc_requests.update_one(
        {"id": ndc_id},
        {"$set": {
            "status": "Revoked",
            "revoke_reason": revoke_data.reason,
            "revoked_by": current_user.id,
            "revoked_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    # Update all associated asset recovery records
    await db.ndc_asset_recovery.update_many(
        {"ndc_request_id": ndc_id},
        {"$set": {"status": "Revoked", "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "NDC request revoked successfully"}

@api_router.post("/admin/reset-asset-system")
async def reset_asset_system(
    current_user: User = Depends(require_role([UserRole.ADMINISTRATOR]))
):
    """
    Complete asset management system reset - deletes all asset types, definitions, and related transactions
    WARNING: This is a destructive operation that cannot be undone
    """
    try:
        deletion_summary = {
            "ndc_requests": 0,
            "ndc_asset_recovery": 0,
            "asset_retrievals": 0,
            "asset_allocations": 0,
            "asset_requisitions": 0,
            "asset_definitions": 0,
            "asset_types": 0,
            "user_asset_assignments_cleared": 0
        }
        
        # Delete in order to avoid referential integrity issues
        
        # 1. Delete NDC requests and related asset recovery records
        ndc_recovery_result = await db.ndc_asset_recovery.delete_many({})
        deletion_summary["ndc_asset_recovery"] = ndc_recovery_result.deleted_count
        
        ndc_requests_result = await db.ndc_requests.delete_many({})
        deletion_summary["ndc_requests"] = ndc_requests_result.deleted_count
        
        # 2. Delete asset retrievals
        asset_retrievals_result = await db.asset_retrievals.delete_many({})
        deletion_summary["asset_retrievals"] = asset_retrievals_result.deleted_count
        
        # 3. Delete asset allocations
        asset_allocations_result = await db.asset_allocations.delete_many({})
        deletion_summary["asset_allocations"] = asset_allocations_result.deleted_count
        
        # 4. Delete asset requisitions
        asset_requisitions_result = await db.asset_requisitions.delete_many({})
        deletion_summary["asset_requisitions"] = asset_requisitions_result.deleted_count
        
        # 5. Delete asset definitions
        asset_definitions_result = await db.asset_definitions.delete_many({})
        deletion_summary["asset_definitions"] = asset_definitions_result.deleted_count
        
        # 6. Delete asset types
        asset_types_result = await db.asset_types.delete_many({})
        deletion_summary["asset_types"] = asset_types_result.deleted_count
        
        # 7. Clear user asset assignments and related fields
        user_update_result = await db.users.update_many(
            {},
            {"$unset": {
                "allocated_to": "",
                "allocated_to_name": "",
                "allocation_date": "",
                "acknowledged": "",
                "acknowledgment_date": "",
                "acknowledgment_notes": ""
            }}
        )
        deletion_summary["user_asset_assignments_cleared"] = user_update_result.modified_count
        
        # Log the deletion for audit trail
        logging.info(f"Asset system reset performed by user {current_user.id} ({current_user.name})")
        logging.info(f"Deletion summary: {deletion_summary}")
        
        return {
            "message": "Asset management system has been completely reset",
            "deleted_by": {
                "user_id": current_user.id,
                "user_name": current_user.name
            },
            "deletion_summary": deletion_summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error during asset system reset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset asset system: {str(e)}")

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