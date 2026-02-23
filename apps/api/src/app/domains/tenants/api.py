from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from packages.core.models.tenant import Tenant, TenantStatus
from packages.db.session import get_db
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class TenantThemeConfig(BaseModel):
    primary_color: str = "#000000"
    secondary_color: str = "#ffffff"
    logo_url: Optional[str] = None
    font_family: str = "Inter"

class TenantCreate(BaseModel):
    name: str
    slug: str
    domain: Optional[str] = None
    type: str = "beauty"
    timezone: str = "Asia/Jerusalem"
    theme_config: TenantThemeConfig = TenantThemeConfig()

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[TenantStatus] = None
    domain: Optional[str] = None
    theme_config: Optional[TenantThemeConfig] = None

class TenantDTO(BaseModel):
    id: int
    name: str
    slug: str
    domain: Optional[str]
    type: str
    status: TenantStatus
    theme_config: dict
    
    class Config:
        from_attributes = True

# --- Public endpoint (no auth required) ---

@router.get("/config/{slug}", response_model=TenantDTO)
async def get_tenant_config(slug: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint: fetch tenant branding/config by slug."""
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

# --- Admin endpoints ---

@router.get("/", response_model=List[TenantDTO])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant))
    return result.scalars().all()

@router.post("/", response_model=TenantDTO, status_code=status.HTTP_201_CREATED)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    # Check if slug exists
    exists = await db.execute(select(Tenant).where(Tenant.slug == payload.slug))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    tenant = Tenant(
        name=payload.name,
        slug=payload.slug,
        domain=payload.domain,
        type=payload.type,
        timezone=payload.timezone,
        theme_config=payload.theme_config.model_dump(),
        status=TenantStatus.ACTIVE
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant

@router.get("/{tenant_id}", response_model=TenantDTO)
async def get_tenant(tenant_id: int, db: AsyncSession = Depends(get_db)):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.patch("/{tenant_id}", response_model=TenantDTO)
async def update_tenant(tenant_id: int, payload: TenantUpdate, db: AsyncSession = Depends(get_db)):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    if "theme_config" in update_data and update_data["theme_config"] is not None:
        update_data["theme_config"] = payload.theme_config.model_dump()
        
    for key, value in update_data.items():
        setattr(tenant, key, value)
    
    await db.commit()
    await db.refresh(tenant)
    return tenant
