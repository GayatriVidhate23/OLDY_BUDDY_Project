import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import User, UserRole, ElderProfile
from app.auth import get_password_hash

async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Seed Elder
        res_elder = await db.execute(select(User).where(User.email == "elder@example.com"))
        if not res_elder.scalar_one_or_none():
            elder_user = User(
                email="elder@example.com",
                hashed_password=get_password_hash("password"),
                full_name="Grandpa Mary",
                role=UserRole.ELDER,
                is_active=True,
            )
            db.add(elder_user)
            await db.commit()
            await db.refresh(elder_user)
            
            profile = ElderProfile(
                user_id=elder_user.id,
                emergency_contact="+1 (555) 019-2834",
                preferences={"language": "English"},
                medical_info={"summary": "High blood pressure, daily morning medication"},
                routines={"breakfast": "8:00 AM"}
            )
            db.add(profile)
            await db.commit()
            print("Seeded elder@example.com")

        # Seed Caregiver
        res_cg = await db.execute(select(User).where(User.email == "caregiver@example.com"))
        if not res_cg.scalar_one_or_none():
            cg_user = User(
                email="caregiver@example.com",
                hashed_password=get_password_hash("password"),
                full_name="Caregiver Sarah",
                role=UserRole.CAREGIVER,
                is_active=True,
            )
            db.add(cg_user)
            await db.commit()
            print("Seeded caregiver@example.com")

if __name__ == "__main__":
    asyncio.run(seed())
