"""Contact link detection and executable actions for the frontend."""

CONTACT_DATA = {
    "email": "parsavenkatatharun@gmail.com",
    "linkedin": "https://www.linkedin.com/in/venkata-tharun-parsa-98850632a/",
    "github": "https://github.com/venkatatharunparsa",
    "phone": "+91 9573528179",
}

LINKEDIN_TRIGGERS = ["linkedin", "linked in", "linkedin profile", "connect on linkedin"]
GITHUB_TRIGGERS = ["github", "git hub", "github profile", "repos", "repositories", "your code"]
EMAIL_TRIGGERS = [
    "email", "mail", "reach me", "reach you", "contact", "write to you",
    "message you", "get in touch", "how can i contact", "how do i contact",
]
PHONE_TRIGGERS = ["phone", "phone number", "call you", "whatsapp"]


def detect_action(query: str) -> dict | None:
    """Detect if query implies a direct navigation action."""
    q = query.lower()

    if any(t in q for t in LINKEDIN_TRIGGERS):
        return {
            "type": "open_url",
            "url": CONTACT_DATA["linkedin"],
            "label": "Opening LinkedIn profile...",
        }

    if any(t in q for t in GITHUB_TRIGGERS):
        return {
            "type": "open_url",
            "url": CONTACT_DATA["github"],
            "label": "Opening GitHub profile...",
        }

    if any(t in q for t in EMAIL_TRIGGERS):
        return {
            "type": "open_email",
            "url": f"mailto:{CONTACT_DATA['email']}",
            "label": "Opening email...",
        }

    return None
