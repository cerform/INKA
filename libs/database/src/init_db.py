from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from packages.core.models.role import Role, Permission
from packages.core.models.user import User
from packages.core.config import settings

async def init_db(db: AsyncSession) -> None:
    # 1. Create Permissions
    permissions_data = [
        {"name": "booking.create", "description": "Create new bookings"},
        {"name": "booking.view", "description": "View bookings"},
        {"name": "booking.manage", "description": "Manage any booking"},
        {"name": "staff.manage", "description": "Manage masters and salon settings"},
    ]
    
    db_permissions = []
    for p_data in permissions_data:
        result = await db.execute(select(Permission).where(Permission.name == p_data["name"]))
        p = result.scalars().first()
        if not p:
            p = Permission(**p_data)
            db.add(p)
        db_permissions.append(p)
    await db.commit()

    # 2. Create Roles
    roles_data = [
        {"name": "admin", "description": "Salon Administrator", "perms": ["booking.create", "booking.view", "booking.manage", "staff.manage"]},
        {"name": "master", "description": "Tattoo Master", "perms": ["booking.view"]},
    ]

    for r_data in roles_data:
        result = await db.execute(select(Role).where(Role.name == r_data["name"]))
        role = result.scalars().first()
        if not role:
            role = Role(name=r_data["name"], description=r_data["description"])
            # Assign permissions
            role.permissions = [p for p in db_permissions if p.name in r_data["perms"]]
            db.add(role)
    await db.commit()

    # 3. Create Superuser (if not exists)
    # This would require more logic for telegram_id, etc.
    print("Database initialization complete.")
