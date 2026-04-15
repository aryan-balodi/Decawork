"""
IT Agent Runner — CLI entry point for executing IT support tasks.

Usage:
    uv run python -m agent.run "reset password for bob@company.com"
    uv run python -m agent.run "create a new user john doe with email john@company.com in engineering"
    uv run python -m agent.run "check if john@company.com exists, if not create them, then assign Microsoft 365"
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

from browser_use import Agent
from browser_use.llm import ChatGoogle
from agent.orchestrator import build_agent_task

SYSTEM_PROMPT = """You are a highly capable IT Support Administrator.
Your task is to accurately navigate the admin panel to resolve employee issues (e.g., password resets, license assignments, user creation).
Always verify your actions. Return a final summary containing status, details, and success/failure.
Do NOT attempt to guess endpoints or use direct API calls; use the UI provided.
"""


def get_llm():
    """Initialize the LLM."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    llm = ChatGoogle(
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        temperature=0.0,
    )

    return llm


async def run_agent(task_description: str, headless: bool = False):
    """
    Run the IT agent to complete a task.

    Args:
        task_description: Natural language IT support request.
        headless: Whether to run the browser in headless mode.

    Returns:
        The agent's result/history.
    """
    llm = get_llm()
    task = build_agent_task(task_description)

    print(f"\n🤖 IT Agent Starting...")
    print(f"📋 Task: {task_description}")
    print(f"🌐 Admin Panel: {os.getenv('ADMIN_PANEL_URL', 'http://localhost:8000')}")
    print(f"{'🔇 Headless mode' if headless else '👁️  Browser visible'}")
    print("─" * 60)

    agent = Agent(
        task=task,
        llm=llm,
        extend_system_message=SYSTEM_PROMPT,
        max_actions_per_step=3,
        max_failures=5,
        use_vision=False,
    )

    try:
        result = await agent.run(max_steps=30)
        print("\n" + "─" * 60)
        print("✅ Agent completed task")

        # Extract final result
        if result and hasattr(result, 'final_result') and callable(result.final_result):
            print(f"📝 Result: {result.final_result()}")
        elif result:
            print(f"📝 Result: {result}")

        return result
    except Exception as e:
        print(f"\n❌ Agent failed: {str(e)}")
        raise


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run python -m agent.run '<IT support request>'")
        print("\nExamples:")
        print('  uv run python -m agent.run "reset password for bob@company.com"')
        print('  uv run python -m agent.run "create user John Doe john@company.com Engineering employee"')
        print('  uv run python -m agent.run "disable account for eve@company.com"')
        print('  uv run python -m agent.run "check if john@company.com exists, if not create, then assign Microsoft 365 license"')
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    headless = "--headless" in sys.argv
    if headless:
        task = task.replace("--headless", "").strip()

    asyncio.run(run_agent(task, headless=headless))


if __name__ == "__main__":
    main()
