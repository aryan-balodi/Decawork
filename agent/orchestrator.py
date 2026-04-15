"""
IT Agent Orchestrator — Maps natural language IT requests to browser-use agent tasks.

This module takes a natural language IT support request and constructs a detailed
task prompt for the browser-use agent, along with the admin panel URL context.
"""

import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://localhost:8000")

# System prompt that gives the agent context about the admin panel
SYSTEM_PROMPT = f"""You are an IT support agent that completes IT administration tasks by navigating a web-based admin panel.

The admin panel is located at {ADMIN_PANEL_URL} and has the following pages:

1. **Dashboard** ({ADMIN_PANEL_URL}/) — Overview with stats and recent activity
2. **User Management** ({ADMIN_PANEL_URL}/users) — List, search, create, edit, and manage users
   - Search bar to find users by name or email
   - "+ Create User" button to add new users
   - "View" button on each row to see user details
   - User detail page has: Reset Password, Disable/Enable Account, Delete User buttons
   - User detail page also shows assigned licenses
3. **License Management** ({ADMIN_PANEL_URL}/licenses) — Manage software license assignments
   - Shows all available software licenses (Microsoft 365, Slack Pro, Jira, GitHub Enterprise, Figma)
   - Each license shows seat usage and assigned users
   - Dropdown + "Assign" button to assign a license to a user
   - Shows available seats count

Key navigation tips:
- Use the sidebar links to navigate between pages
- Use the search bar on the Users page to find specific users
- After completing an action, verify it worked by checking the result

Always complete the task step by step, verifying each action succeeded before proceeding to the next."""


def build_agent_task(user_request: str) -> str:
    """
    Build a detailed task prompt for the browser-use agent from a natural language request.
    
    Args:
        user_request: The natural language IT support request from the user.
    
    Returns:
        A detailed task prompt string for the browser-use agent.
    """
    task = f"""Complete the following IT support request by navigating the admin panel at {ADMIN_PANEL_URL}:

REQUEST: {user_request}

Instructions:
1. Start by navigating to {ADMIN_PANEL_URL}
2. Determine which pages and actions are needed to fulfill this request
3. Navigate to the appropriate pages and complete each step
4. After each action, verify it was successful
5. Once the task is fully complete, provide a summary of what was done

If the request involves finding a user, use the search bar on the User Management page.
If you need to check if a user exists before creating them, search for them first.
If you need to assign a license, go to the License Management page.
Complete all steps of the request before finishing."""

    return task
