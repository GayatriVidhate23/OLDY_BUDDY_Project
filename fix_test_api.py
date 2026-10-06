import re

with open('backend/app/api.py', 'r', encoding='utf-8') as f:
    api = f.read()

if 'def create_elder_by_caregiver' not in api:
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
    with open('backend/app/api.py', 'w', encoding='utf-8') as f:
        f.write(api)

with open('backend/tests/test_api.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(
    r'prof_in = \{(.*?)\}\n\s*prof = await client\.post\(\"/api/elders\", headers=headers, json=prof_in\)',
    'prof_in = {\\1}\\n        prof = await client.post(f"/api/elders/{elder_id}/profile", headers=headers, json=prof_in)',
    c
)

with open('backend/tests/test_api.py', 'w', encoding='utf-8') as f:
    f.write(c)
