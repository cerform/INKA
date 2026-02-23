from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel, EmailStr, validator, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os
import subprocess
from pathlib import Path
from typing import Optional, List
import uuid
import secrets

from app.deps.auth import get_db
from packages.core.models import User
from packages.db.session import engine
from app.domains.setup.models import SalonSetup, SalonWorkSchedule

router = APIRouter(prefix="/api/v1/setup", tags=["Setup"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============ Salon Setup Schemas ============

class WorkScheduleCreate(BaseModel):
    day_of_week: str
    is_working: bool = True
    start_time: Optional[str] = "09:00"
    end_time: Optional[str] = "21:00"


class SalonSetupCreate(BaseModel):
    salon_name: str = Field(..., min_length=1, max_length=255)
    specialization: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    work_start_time: str = "09:00"
    work_end_time: str = "21:00"
    timezone: str = "UTC"
    work_schedule: Optional[List[WorkScheduleCreate]] = None


class SalonSetupUpdate(BaseModel):
    salon_name: Optional[str] = None
    specialization: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    timezone: Optional[str] = None
    is_completed: Optional[bool] = None


class WorkScheduleRead(WorkScheduleCreate):
    id: str
    setup_id: str


class SalonSetupRead(BaseModel):
    id: str
    admin_id: str
    salon_name: str
    specialization: Optional[str]
    api_key: str
    work_start_time: str
    work_end_time: str
    timezone: str
    is_completed: bool
    is_active: bool
    work_schedule: List[WorkScheduleRead] = []


class SetupResponse(BaseModel):
    status: str
    message: str
    data: Optional[SalonSetupRead] = None


# ============ Salon Setup Endpoints ============

def generate_api_key():
    """Generate a secure API key"""
    return f"sk_{secrets.token_urlsafe(32)}"


@router.post("/salon-init", response_model=SetupResponse, status_code=status.HTTP_201_CREATED)
async def initialize_salon_setup(
    payload: SalonSetupCreate,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """
    Initialize salon setup for new admin - Landing page endpoint
    """
    # Get user ID from token (simplified)
    admin_id = authorization.split()[-1] if authorization else str(uuid.uuid4())
    
    # Check if already has setup
    existing = db.query(SalonSetup).filter(SalonSetup.admin_id == admin_id).first()
    if existing and existing.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Salon setup already completed"
        )
    
    # Create setup record
    setup_id = str(uuid.uuid4())
    api_key = generate_api_key()
    
    salon_setup = SalonSetup(
        id=setup_id,
        admin_id=admin_id,
        salon_name=payload.salon_name,
        specialization=payload.specialization,
        telegram_bot_token=payload.telegram_bot_token,
        api_key=api_key,
        work_start_time=payload.work_start_time,
        work_end_time=payload.work_end_time,
        timezone=payload.timezone,
        is_completed=bool(payload.work_schedule)
    )
    
    db.add(salon_setup)
    db.flush()
    
    # Create work schedule if provided
    if payload.work_schedule:
        for schedule in payload.work_schedule:
            work_schedule = SalonWorkSchedule(
                id=str(uuid.uuid4()),
                setup_id=setup_id,
                day_of_week=schedule.day_of_week,
                is_working=schedule.is_working,
                start_time=schedule.start_time,
                end_time=schedule.end_time
            )
            db.add(work_schedule)
    
    db.commit()
    
    return SetupResponse(
        status="success",
        message="Salon setup initialized successfully",
        data=salon_setup
    )


@router.get("/salon-status", response_model=SetupResponse)
async def get_setup_status(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """Get current salon setup status"""
    admin_id = authorization.split()[-1] if authorization else None
    
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    setup = db.query(SalonSetup).filter(SalonSetup.admin_id == admin_id).first()
    
    if not setup:
        return SetupResponse(
            status="not_started",
            message="Setup not started yet"
        )
    
    return SetupResponse(
        status="in_progress" if not setup.is_completed else "completed",
        message="Setup status retrieved",
        data=setup
    )


@router.put("/salon-update", response_model=SetupResponse)
async def update_setup(
    payload: SalonSetupUpdate,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """Update salon setup"""
    admin_id = authorization.split()[-1] if authorization else None
    
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    setup = db.query(SalonSetup).filter(SalonSetup.admin_id == admin_id).first()
    
    if not setup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setup not found"
        )
    
    # Update fields
    if payload.salon_name:
        setup.salon_name = payload.salon_name
    if payload.specialization:
        setup.specialization = payload.specialization
    if payload.telegram_bot_token:
        setup.telegram_bot_token = payload.telegram_bot_token
    if payload.work_start_time:
        setup.work_start_time = payload.work_start_time
    if payload.work_end_time:
        setup.work_end_time = payload.work_end_time
    if payload.timezone:
        setup.timezone = payload.timezone
    if payload.is_completed is not None:
        setup.is_completed = payload.is_completed
    
    db.commit()
    
    return SetupResponse(
        status="success",
        message="Setup updated successfully",
        data=setup
    )


@router.get("/api-key", response_model=dict)
async def get_api_key(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """Get salon API key"""
    admin_id = authorization.split()[-1] if authorization else None
    
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    setup = db.query(SalonSetup).filter(SalonSetup.admin_id == admin_id).first()
    
    if not setup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setup not found"
        )
    
    return {"api_key": setup.api_key}


# ============ System Setup (Old Endpoints) ============

class SetupConfig(BaseModel):
    botToken: str
    apiSecretKey: str
    databaseUrl: str
    gcpProjectId: str = ""
    adminEmail: EmailStr
    adminPassword: str

    @validator('botToken')
    def validate_bot_token(cls, v):
        if ':' not in v or len(v) < 20:
            raise ValueError('Invalid Telegram Bot Token format')
        return v

    @validator('apiSecretKey')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('API Secret Key must be at least 32 characters')
        return v

    @validator('databaseUrl')
    def validate_database_url(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Database URL must start with postgresql://')
        return v

    @validator('adminPassword')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


def check_if_setup_completed():
    """Check if setup has already been completed"""
    env_file = Path('/app/.env')
    if env_file.exists():
        return True
    
    # Also check if admin user exists
    try:
        from packages.db.session import SessionLocal
        db = SessionLocal()
        admin_exists = db.query(User).filter(User.role == 'admin').first()
        db.close()
        return admin_exists is not None
    except:
        return False


@router.post("/setup")
async def setup_system(config: SetupConfig, db: Session = Depends(get_db)):
    """
    Initial system setup endpoint.
    Creates .env file, runs migrations, creates admin user.
    """
    
    # Check if setup already completed
    if check_if_setup_completed():
        raise HTTPException(
            status_code=400,
            detail="Setup has already been completed. Contact administrator to reconfigure."
        )
    
    try:
        # 1. Create .env file
        env_content = f"""# Generated by Setup Wizard
DATABASE_URL={config.databaseUrl}
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

REDIS_URL=redis://localhost:6379/0

BOT_TOKEN={config.botToken}
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
TELEGRAM_WEBHOOK_SECRET=auto-generated-secret

API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY={config.apiSecretKey}
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8000

GOOGLE_CLOUD_PROJECT={config.gcpProjectId}
GCS_BUCKET_NAME={config.gcpProjectId}-uploads

ENVIRONMENT=production
LOG_LEVEL=INFO
TZ=Asia/Jerusalem
"""
        
        env_path = Path('/app/.env')
        env_path.write_text(env_content)
        
        # 2. Test database connection
        try:
            from sqlalchemy import create_engine, text
            test_engine = create_engine(config.databaseUrl)
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            test_engine.dispose()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Database connection failed: {str(e)}"
            )
        
        # 3. Run database migrations
        try:
            alembic_ini = Path('/app/libs/database/alembic.ini')
            result = subprocess.run(
                ['alembic', '-c', str(alembic_ini), 'upgrade', 'head'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                raise Exception(f"Migration failed: {result.stderr}")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database migration failed: {str(e)}"
            )
        
        # 4. Create admin user
        hashed_password = pwd_context.hash(config.adminPassword)
        admin_user = User(
            email=config.adminEmail,
            hashed_password=hashed_password,
            full_name="System Administrator",
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # 5. Set setup completion flag
        setup_flag = Path('/app/.setup_completed')
        setup_flag.write_text('1')
        
        return {
            "success": True,
            "message": "System setup completed successfully",
            "admin_user_id": str(admin_user.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Setup failed: {str(e)}"
        )


@router.get("/setup/status")
async def get_setup_status():
    """Check if system setup is required"""
    return {
        "setup_required": not check_if_setup_completed()
    }
