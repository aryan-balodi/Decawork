"""
Decawork IT Agent — Main entry point.

Usage:
    # Start admin panel:
    uv run uvicorn admin_panel.app:app --reload --port 8000

    # Run agent (in separate terminal):
    uv run python -m agent.run "reset password for bob@company.com"

    # Start Slack bot:
    uv run python -m slack_bot.bot
"""


def main():
    print("🤖 Decawork IT Agent")
    print("=" * 40)
    print()
    print("Commands:")
    print("  1. Start admin panel:")
    print("     uv run uvicorn admin_panel.app:app --reload --port 8000")
    print()
    print("  2. Run agent (in separate terminal):")
    print('     uv run python -m agent.run "reset password for bob@company.com"')
    print()
    print("  3. Start Slack bot:")
    print("     uv run python -m slack_bot.bot")


if __name__ == "__main__":
    main()
