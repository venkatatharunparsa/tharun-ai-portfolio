"""Contact draft tool — produces actionable output from shared contact data."""
from urllib.parse import quote

from core.contact_actions import CONTACT_DATA


def prepare_contact_draft(purpose: str = "general inquiry") -> dict:
    email = CONTACT_DATA["email"]
    subject = f"Portfolio inquiry — {purpose}"
    body = (
        f"Hi Tharun,\n\n"
        f"I'm reaching out via your portfolio regarding: {purpose}.\n\n"
        f"[Your message here]\n\n"
        f"Best regards"
    )
    mailto = f"mailto:{email}?subject={quote(subject)}&body={quote(body)}"
    return {
        "email": email,
        "linkedin": CONTACT_DATA["linkedin"],
        "github": CONTACT_DATA["github"],
        "phone": CONTACT_DATA["phone"],
        "purpose": purpose,
        "suggested_subject": subject,
        "mailto_link": mailto,
    }
