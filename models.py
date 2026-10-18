import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resumes_db.json")


def default_resume_structure() -> Dict[str, Any]:
    """Returns an empty resume structure with all customizable sections."""
    return {
        "photo": None,              # Path to uploaded photo or None
        "name": "",                 # Full Name
        "title": "",                # Headline / Target Job Title
        "email": "",                # Email Address
        "phone": "",                # Phone Number
        "location": "",             # City, State / Country
        "linkedin": "",             # LinkedIn URL or username
        "portfolio": "",            # Portfolio / GitHub URL
        "summary": "",              # Professional Background / Summary
        "skills": [],               # List of core skills / competencies
        "experience": [],           # List of dicts: [{title, company, duration, location, details}]
        "education": [],            # List of dicts: [{degree, institution, year, score}]
        "certifications": [],       # List of dicts: [{name, issuer, year}]
        "theme": "navy",            # Default theme
        "state": None,              # Current wizard state
        "edit_section": None,       # Track if currently editing a specific section
        "temp_item": {}             # Temporary storage while adding multi-entry item
    }


class ResumeStore:
    """Manages active user resume sessions and persists them to disk."""

    def __init__(self, file_path: str = DB_FILE):
        self.file_path = file_path
        self.users: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                logger.error(f"Error loading {self.file_path}: {e}")
        return {}

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving {self.file_path}: {e}")

    def get(self, user_id: int | str) -> Dict[str, Any]:
        uid = str(user_id)
        if uid not in self.users:
            self.users[uid] = default_resume_structure()
            self.save()
        return self.users[uid]

    def update(self, user_id: int | str, **kwargs):
        data = self.get(user_id)
        for k, v in kwargs.items():
            data[k] = v
        self.save()

    def reset(self, user_id: int | str):
        uid = str(user_id)
        self.users[uid] = default_resume_structure()
        self.save()

    def format_summary_text(self, user_id: int | str) -> str:
        """Generates a formatted overview of the user's resume for preview and editing."""
        data = self.get(user_id)

        name = data.get("name") or "<i>Not specified</i>"
        title = data.get("title") or "<i>Not specified</i>"
        email = data.get("email") or "<i>Not specified</i>"
        phone = data.get("phone") or "<i>Not specified</i>"
        location = data.get("location") or "<i>Not specified</i>"
        photo_status = "✅ Attached" if data.get("photo") else "❌ Skipped / None"

        summary = data.get("summary")
        summary_display = f"{summary[:150]}..." if summary and len(summary) > 150 else (summary or "<i>Skipped</i>")

        skills = data.get("skills", [])
        skills_display = ", ".join(skills) if skills else "<i>Skipped</i>"

        exp_count = len(data.get("experience", []))
        edu_count = len(data.get("education", []))
        cert_count = len(data.get("certifications", []))

        text = (
            "📋 <b>RESUME DETAILS OVERVIEW</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Name:</b> {name}\n"
            f"💼 <b>Target Role:</b> {title}\n"
            f"📸 <b>Photo:</b> {photo_status}\n"
            f"📧 <b>Email:</b> {email}\n"
            f"📱 <b>Phone:</b> {phone}\n"
            f"📍 <b>Location:</b> {location}\n\n"
            f"📝 <b>Summary:</b> {summary_display}\n\n"
            f"🛠️ <b>Core Skills ({len(skills)}):</b>\n{skills_display}\n\n"
            f"💼 <b>Experience Entries:</b> {exp_count}\n"
            f"🎓 <b>Education Entries:</b> {edu_count}\n"
            f"📜 <b>Certifications:</b> {cert_count}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <i>Neeche buttons se aap kisi bhi section ko edit kar sakte hain ya PDF bana sakte hain!</i>"
        )
        return text


resume_store = ResumeStore()

