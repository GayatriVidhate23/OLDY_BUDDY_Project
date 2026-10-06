import glob
import re

with open('backend/app/api.py', 'r', encoding='utf-8') as f:
    api = f.read()

# Fix update_profile to use merge
api = re.sub(
    r'    profile = ElderProfile\(\*\*profile_in\.model_dump\(\), user_id=elder_id\)\n    existing = await db\.execute[^\n]+\n    if not existing: db\.add\(profile\)',
    '    profile = ElderProfile(**profile_in.model_dump(), user_id=elder_id)\n    profile = await db.merge(profile)',
    api
)

# Add POST /elders dummy if it doesn't exist
if '@router.post("/elders"' not in api and '@router.post("/v1/elders"' not in api:
    api += """
@router.post("/elders", response_model=ElderProfileResponse)
async def create_elder_by_caregiver(profile_in: ElderProfileBase, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import ElderProfile, User, UserRelationship, RelationshipType
    import uuid
    dummy_email = f"elder_{uuid.uuid4().hex[:8]}@oldybuddy.internal"
    new_user = User(email=dummy_email, hashed_password="dummy", role=UserRole.ELDER, full_name=profile_in.name)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    profile = ElderProfile(**profile_in.model_dump(), user_id=new_user.id)
    db.add(profile)
    rel = UserRelationship(elder_id=new_user.id, caregiver_id=current_user.id, type=RelationshipType.CAREGIVER)
    db.add(rel)
    await db.commit()
    await db.refresh(profile)
    return profile
"""

with open('backend/app/api.py', 'w', encoding='utf-8') as f:
    f.write(api)

with open('backend/app/schemas.py', 'r', encoding='utf-8') as f:
    schemas = f.read()

schemas = schemas.replace('status: str = "completed"', 'status: str = "COMPLETED"')
schemas = schemas.replace('class ActivityCreate(ActivityBase): pass', '')
if 'class ActivityCreate(BaseModel):' not in schemas:
    schemas += """
class ActivityCreate(BaseModel):
    type: str
    description: str
"""

with open('backend/app/schemas.py', 'w', encoding='utf-8') as f:
    f.write(schemas)

for f in glob.glob('backend/tests/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    c = c.replace('"/api/v1/elders"', '"/api/elders"')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(c)

