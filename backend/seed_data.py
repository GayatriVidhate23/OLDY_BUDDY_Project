import asyncio
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models import Base, User, UserRole, ElderProfile, UserRelationship, RelationshipType, Activity
from app.auth import get_password_hash

DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Create Elder
        elder = User(email="sunita@oldybuddy.com", hashed_password=get_password_hash("elder"), full_name="Sunita Sharma", role=UserRole.ELDER)
        db.add(elder)
        await db.commit()
        await db.refresh(elder)

        # Create Profile
        profile_data = {
            "age": 72,
            "location": "Nagpur, Maharashtra",
            "language": "Hindi",
            "routine": {
                "Morning wake-up": "7:00 AM",
                "Breakfast": "8:00 AM",
                "Lunch": "1:00 PM",
                "Dinner": "8:00 PM",
                "Sleep": "10:00 PM"
            },
            "medications": [
                "Morning medicine — 8:30 AM",
                "Afternoon medicine — 1:30 PM",
                "Night medicine — 8:30 PM"
            ],
            "appointment": "Tomorrow, 11:00 AM - Doctor",
            "demo_vitals": {
                "Heart Rate": "76 BPM",
                "Blood Pressure": "124/78 mmHg",
                "SpO2": "97%",
                "Temperature": "36.6°C",
                "Steps": "3,842",
                "Sleep": "7h 20m",
                "Water": "5 / 8 glasses"
            }
        }
        
        profile = ElderProfile(user_id=elder.id, preferences=profile_data, emergency_contact="Anjali Sharma (Daughter)")
        db.add(profile)

        # Create Caregiver
        caregiver = User(email="anjali@example.com", hashed_password=get_password_hash("pass"), full_name="Anjali Sharma", role=UserRole.CAREGIVER)
        db.add(caregiver)
        await db.commit()
        await db.refresh(caregiver)

        # Create Relationship
        rel = UserRelationship(elder_id=elder.id, caregiver_id=caregiver.id, type=RelationshipType.CAREGIVER)
        db.add(rel)

        # Add Activities for Timeline
        now = datetime.datetime.now(datetime.timezone.utc)
        
        timeline = [
            ("ACTIVITY", "Night medication acknowledged", "COMPLETED", now - datetime.timedelta(hours=20)),
            ("ACTIVITY", "Morning conversation", "COMPLETED", now - datetime.timedelta(hours=4)),
            ("REMINDER", "Breakfast reminder completed", "COMPLETED", now - datetime.timedelta(hours=3, minutes=15)),
            ("REMINDER", "Morning medication acknowledged", "COMPLETED", now - datetime.timedelta(hours=2, minutes=45)),
            ("CHECK_IN", "Voice check-in completed", "COMPLETED", now - datetime.timedelta(hours=2)),
            ("CHECK_IN", "Afternoon check-in pending", "PENDING", now)
        ]

        for act_type, desc, status, ts in timeline:
            act = Activity(elder_id=elder.id, activity_type=act_type, description=desc, status=status)
            act.timestamp = ts # Override for realistic timeline
            db.add(act)

        await db.commit()
        print("Database seeded with realistic demo data for Sunita and Anjali.")

if __name__ == "__main__":
    asyncio.run(seed())
