"""
Slack Bot — Triggers IT Agent from Slack messages.

Setup:
1. Create a Slack app at https://api.slack.com/apps
2. Enable Socket Mode
3. Add Bot Token Scopes: chat:write, app_mentions:read
4. Subscribe to Events: app_mention
5. Install to workspace
6. Set SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env

Usage:
    uv run python -m slack_bot.bot

Then mention the bot in Slack:
    @ITBot reset password for bob@company.com
"""

import asyncio
import os
import sys
import threading

from dotenv import load_dotenv

load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


def create_slack_app():
    """Create and configure the Slack bot."""
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    app_token = os.getenv("SLACK_APP_TOKEN")

    if not bot_token or not app_token:
        print("❌ Error: SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set in .env")
        print("   See: https://api.slack.com/apps to create a Slack app")
        sys.exit(1)

    app = App(token=bot_token)

    @app.event("app_mention")
    def handle_mention(event, say, logger):
        """Handle @ITBot mentions in Slack."""
        user_input = event.get("text", "")
        user_id = event.get("user", "")
        
        # Remove the bot mention from the text
        # The mention looks like <@U1234567> at the start
        import re
        task_text = re.sub(r"<@\w+>\s*", "", user_input).strip()

        if not task_text:
            say(
                "👋 Hi! I'm the IT Support Bot. Tell me what you need!\n\n"
                "Examples:\n"
                "• `@ITBot reset password for bob@company.com`\n"
                "• `@ITBot create a new user John Doe john@company.com Engineering`\n"
                "• `@ITBot check if john@company.com exists, if not create them and assign Microsoft 365`"
            )
            return

        # Acknowledge the request
        say(
            f"🤖 Got it, <@{user_id}>! Working on your request:\n"
            f"> _{task_text}_\n\n"
            f"⏳ The agent is navigating the admin panel now. I'll update you when done..."
        )

        # Run the agent in a separate thread to not block Slack
        def run_agent_task():
            try:
                from agent.run import run_agent

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(run_agent(task_text, headless=True))
                loop.close()

                # Extract result summary
                result_text = "Task completed successfully."
                if result and hasattr(result, 'final_result') and result.final_result:
                    result_text = result.final_result()

                say(
                    f"✅ Done, <@{user_id}>!\n\n"
                    f"*Request:* {task_text}\n"
                    f"*Result:* {result_text}"
                )

            except Exception as e:
                say(
                    f"❌ Sorry <@{user_id}>, the task failed:\n"
                    f"```{str(e)}```\n"
                    f"Please try again or contact IT support directly."
                )

        thread = threading.Thread(target=run_agent_task)
        thread.start()

    @app.event("message")
    def handle_message(event, logger):
        """Handle direct messages (ignore, we only respond to mentions)."""
        pass

    return app


def main():
    """Start the Slack bot."""
    app = create_slack_app()
    app_token = os.getenv("SLACK_APP_TOKEN")

    print("🤖 IT Support Bot is running!")
    print("   Mention @ITBot in Slack to trigger IT tasks")
    print("   Press Ctrl+C to stop")

    handler = SocketModeHandler(app, app_token)
    handler.start()


if __name__ == "__main__":
    main()
