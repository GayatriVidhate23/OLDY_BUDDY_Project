import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.elder_profile import ElderProfile
from app.models.relationship import UserRelationship, RelationshipType
from app.core.config import settings
from app.db.database import Base
import sys
import os

# Ensure backend is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy import select
        res = await session.execute(select(User).where(User.email == "admin@oldybuddy.com"))
        if res.scalar_one_or_none():
            print("Database already seeded.")
            return

        # Create Admin
        admin = User(email="admin@oldybuddy.com", hashed_password=get_password_hash("admin"), role=UserRole.ADMIN, full_name="Admin")
        session.add(admin)
        
        # Create Elder
        elder = User(email="elder@oldybuddy.com", hashed_password=get_password_hash("elder"), role=UserRole.ELDER, full_name="John Doe")
        session.add(elder)
        
        # Create Caregiver
        caregiver = User(email="caregiver@oldybuddy.com", hashed_password=get_password_hash("caregiver"), role=UserRole.CAREGIVER, full_name="Jane Doe")
        session.add(caregiver)
        
        await session.commit()
        await session.refresh(elder)
        await session.refresh(caregiver)
        
        # Create Profile
        profile = ElderProfile(user_id=elder.id, preferences={"theme": "dark"}, emergency_contact="911")
        session.add(profile)
        
        # Create Relationship
        rel = UserRelationship(elder_id=elder.id, caregiver_id=caregiver.id, type=RelationshipType.CAREGIVER)
        session.add(rel)
        
        await session.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
