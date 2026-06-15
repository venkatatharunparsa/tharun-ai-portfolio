"""
Contact Agent — returns contact info with executable actions.
When visitor asks about LinkedIn/GitHub/email — return action commands
that the frontend will execute (open link, open email client).
"""
from agents import AgentState
from core.contact_actions import CONTACT_DATA, detect_action

CONTACT_RESPONSE = """Here's how you can reach me:

📧 Email: parsavenkatatharun@gmail.com
💼 LinkedIn: linkedin.com/in/venkata-tharun-parsa-98850632a
💻 GitHub: github.com/venkatatharunparsa
📱 Phone: +91 9573528179

I'm open to internships, full-time roles, freelance, startup collaborations, and hackathons. Remote preferred but flexible. Just reach out — I respond fast."""

LINKEDIN_RESPONSE = "Taking you to my LinkedIn profile now! Feel free to connect — I'm always open to new connections."
GITHUB_RESPONSE = "Taking you to my GitHub now — you can see all my open source work there."
EMAIL_RESPONSE = "Opening your email client now — send me a message anytime. I check it regularly."


def contact_agent(state: AgentState) -> AgentState:
    """Returns contact info with optional action command for frontend."""
    query = state.get("user_query", "")
    action = detect_action(query)

    if action:
        if action["type"] == "open_email":
            response_text = EMAIL_RESPONSE
        elif CONTACT_DATA["linkedin"] in action.get("url", ""):
            response_text = LINKEDIN_RESPONSE
        elif CONTACT_DATA["github"] in action.get("url", ""):
            response_text = GITHUB_RESPONSE
        else:
            response_text = CONTACT_RESPONSE
    else:
        action = None
        response_text = CONTACT_RESPONSE

    return {
        **state,
        "final_response": response_text,
        "response_source": "contact_redirect",
        "rag_grounded": False,
        "cache_hit": False,
        "action": action,
    }
