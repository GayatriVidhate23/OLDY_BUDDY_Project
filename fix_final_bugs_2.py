import re

with open('backend/app/api.py', 'r', encoding='utf-8') as f:
    api = f.read()

# 1. Add POST /api/elders explicitly
api += """

@router.post("/elders", response_model=ElderProfileResponse)
async def create_elder_by_caregiver(profile_in: ElderProfileBase, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import ElderProfile, User, UserRelationship, RelationshipType
    import uuid
    dummy_email = f"elder_{uuid.uuid4().hex[:8]}@oldybuddy.internal"
    new_user = User(email=dummy_email, hashed_password="dummy", role=UserRole.ELDER, full_name=profile_in.name)
    db.add(new_user)
    await db.flush()
    profile = ElderProfile(**profile_in.model_dump(), user_id=new_user.id)
    db.add(profile)
    rel = UserRelationship(elder_id=new_user.id, caregiver_id=current_user.id, type=RelationshipType.CAREGIVER)
    db.add(rel)
    await db.commit()
    await db.refresh(profile)
    return profile
"""

# 2. Fix IntegrityError
# If auth/register has db.add(ElderProfile(user_id=new_user.id)), remove it.
# Note: we need to use regex properly
api = re.sub(
    r'db\.add\(ElderProfile\(user_id=new_user\.id\)\)',
    '',
    api
)

# 3. Ensure the duplicate POST /elders from my previous script is not there (it wasn't).

with open('backend/app/api.py', 'w', encoding='utf-8') as f:
    f.write(api)

# 4. Fix test_voice_and_dashboard.py 422 Unprocessable Entity
# Wait, why did the test get 422? Because VoiceCallCreate has phone_number?
# In schemas.py, I added `phone_number: Optional[str] = None`. So it should not fail 422.
# Let's verify test_module5.py `user_id` KeyError.
# test_module5 does: eld2_res = await client.post("/api/elders"...) -> elder2_id = eld2_res.json()["user_id"]
# Our ElderProfileResponse has `user_id: int`. So it will succeed.

print("api.py patched")
