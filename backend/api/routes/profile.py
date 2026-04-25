import io
import zipfile
import csv

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.crud import get_linkedin_profile_data, save_linkedin_profile_data
from backend.db.database import get_db
from backend.db.models import User
from backend.linkedin.client import LinkedInClient
from backend.rag.vector_store import USER_PROFILE_COLLECTION, add_documents

router = APIRouter(prefix="/profile", tags=["profile"])

ALGORITHM = "HS256"


def get_current_user(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def ingest_profile_to_pinecone(user_id: str, headline: str, about: str, experience: str, skills: str):
    """Embed each profile section into Pinecone so the agent can retrieve them."""
    sections = [
        {"text": f"Headline: {headline}", "section": "headline"},
        {"text": f"About: {about}", "section": "about"},
        {"text": f"Experience: {experience}", "section": "experience"},
        {"text": f"Skills: {skills}", "section": "skills"},
    ]
    documents = [s["text"] for s in sections if s["text"].strip()]
    metadatas = [{"user_id": user_id, "section": s["section"]} for s in sections if s["text"].strip()]
    ids = [f"{user_id}-{s['section']}" for s in sections if s["text"].strip()]

    if documents:
        add_documents(USER_PROFILE_COLLECTION, documents, metadatas, ids)


@router.get("/me")
async def get_my_profile(token: str, db: Session = Depends(get_db)):
    """Return the authenticated user's LinkedIn profile (basic info from LinkedIn API)."""
    user = get_current_user(token, db)
    client = LinkedInClient(user.access_token)
    profile = await client.get_profile()
    return profile


@router.get("/data")
def get_profile_data(token: str, db: Session = Depends(get_db)):
    """Get the user's stored LinkedIn profile sections."""
    user = get_current_user(token, db)
    profile = get_linkedin_profile_data(db, user.id)
    if not profile:
        return {"headline": "", "about": "", "experience": "", "skills": ""}
    return {
        "headline": profile.headline or "",
        "about": profile.about or "",
        "experience": profile.experience or "",
        "skills": profile.skills or "",
        "updated_at": str(profile.updated_at) if profile.updated_at else None,
    }


class ProfileDataRequest(BaseModel):
    token: str
    headline: str
    about: str
    experience: str
    skills: str


@router.post("/data")
def save_profile_data(request: ProfileDataRequest, db: Session = Depends(get_db)):
    """Save the user's LinkedIn profile sections and embed into Pinecone."""
    user = get_current_user(request.token, db)
    save_linkedin_profile_data(
        db,
        user_id=user.id,
        headline=request.headline,
        about=request.about,
        experience=request.experience,
        skills=request.skills,
    )
    ingest_profile_to_pinecone(
        str(user.id),
        request.headline,
        request.about,
        request.experience,
        request.skills,
    )
    return {"message": "Profile saved and indexed."}


@router.post("/import")
async def import_linkedin_export(token: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Parse a LinkedIn data export ZIP and auto-populate the profile.
    Download your export from LinkedIn Settings → Privacy → Get a copy of your data.
    """
    user = get_current_user(token, db)

    contents = await file.read()
    headline, about, experience_lines, skills_list = "", "", [], []

    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as z:
            names = z.namelist()

            # Profile.csv — headline and summary
            profile_file = next((n for n in names if "Profile.csv" in n or "profile.csv" in n), None)
            if profile_file:
                with z.open(profile_file) as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                    for row in reader:
                        headline = row.get("Headline", "")
                        about = row.get("Summary", "")
                        break

            # Positions.csv — experience
            positions_file = next((n for n in names if "Positions.csv" in n or "positions.csv" in n), None)
            if positions_file:
                with z.open(positions_file) as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                    for row in reader:
                        title = row.get("Title", "")
                        company = row.get("Company Name", "")
                        started = row.get("Started On", "")
                        finished = row.get("Finished On", "Present")
                        description = row.get("Description", "")
                        entry = f"{title} at {company} ({started} – {finished})"
                        if description:
                            entry += f"\n{description}"
                        experience_lines.append(entry)

            # Skills.csv
            skills_file = next((n for n in names if "Skills.csv" in n or "skills.csv" in n), None)
            if skills_file:
                with z.open(skills_file) as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                    for row in reader:
                        skill = row.get("Name", "")
                        if skill:
                            skills_list.append(skill)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse LinkedIn export: {str(e)}")

    experience = "\n\n".join(experience_lines)
    skills = ", ".join(skills_list)

    save_linkedin_profile_data(db, user.id, headline, about, experience, skills)
    ingest_profile_to_pinecone(str(user.id), headline, about, experience, skills)

    return {
        "message": "Profile imported successfully.",
        "headline": headline,
        "positions_imported": len(experience_lines),
        "skills_imported": len(skills_list),
    }
