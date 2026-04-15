An AI-powered IT support agent that takes natural language requests and completes them by navigating a web-based admin panel — using real browser automation, not API shortcuts.

**Live Demo:** [https://it-admin-agent.balodi.me](https://it-admin-agent.balodi.me)


## Architecture

```
┌─────────────────────────────────────────────────┐
│                 ENTRY POINTS                     │
│  ┌────────┐   ┌────────┐   ┌───────────────┐   │
│  │ Slack  │   │  CLI   │   │  REST API     │   │
│  │  Bot   │   │ Input  │   │  (future)     │   │
│  └───┬────┘   └───┬────┘   └───────┬───────┘   │
│      └────────────┼────────────────┘            │
│                   ▼                              │
│       ┌───────────────────────┐                  │
│       │  Task Orchestrator    │                  │
│       │  (NL → Agent Task)   │                  │
│       └───────────┬───────────┘                  │
│                   ▼                              │
│       ┌───────────────────────┐                  │
│       │  browser-use Agent    │                  │
│       │  (Gemini + Playwright)│                  │
│       └───────────┬───────────┘                  │
│                   ▼                              │
│       ┌───────────────────────┐                  │
│       │  Mock IT Admin Panel  │                  │
│       │  (FastAPI + aiosqlite)│                  │
│       └───────────┬───────────┘                  │
└─────────────────────────────────────────────────┘
```

## Tech Stack

| Admin Panel | FastAPI + Jinja2 + aiosqlite |
| Browser Automation | [browser-use](https://github.com/browser-use/browser-use) |
| LLM | Gemini 2.5 Flash-Lite |
| Chat Trigger | Slack Bot (slack-bolt, Socket Mode) |
| Package Manager | uv |


## Quick Start

### 1. Install dependencies

```bash
uv sync
uv run python -m playwright install chromium
```

### 2. Set up API key

Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) and add it to `.env`:

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Start the admin panel

```bash
uv run uvicorn admin_panel.app:app --reload --port 8000
```

Visit http://localhost:8000 to see the admin panel.

### 4. Run the agent

In a separate terminal:

```bash
# Simple tasks
uv run python -m agent.run "reset password for bob@company.com"
uv run python -m agent.run "create a new user John Doe with email john@company.com in Engineering as an employee"
uv run python -m agent.run "disable account for eve@company.com"

# Multi-step conditional task (Bonus)
uv run python -m agent.run "check if john@company.com exists, if not create them as an employee in Engineering, then assign them a Microsoft 365 license"

# Headless mode (no browser window)
uv run python -m agent.run "reset password for bob@company.com" --headless
```

## Bonus Features

### ✅ Multi-step Conditional Logic

The agent handles complex workflows with branching:
- "Check if user exists → create if not → assign license"
- "Onboard new employee (create + assign multiple licenses)"

### ✅ Slack Bot Trigger

Trigger IT tasks directly from Slack:

1. Create a Slack app at https://api.slack.com/apps
2. Enable Socket Mode, add `chat:write` and `app_mentions:read` scopes
3. Subscribe to `app_mention` events
4. Add tokens to `.env`
5. Run: `uv run python -m slack_bot.bot`
6. Mention: `@ITBot reset password for bob@company.com`

## Admin Panel Pages

| Page | URL | Features |
|---|---|---|
| Dashboard | `/` | Stats, activity log |
| User Management | `/users` | List, search, create, edit, reset password, disable/enable, delete |
| License Management | `/licenses` | View seats, assign/revoke licenses |

## Project Structure

```
Decawork/
├── admin_panel/          # FastAPI admin panel
│   ├── app.py           # Routes and handlers
│   ├── database.py      # SQLite setup + seed data
│   ├── templates/       # Jinja2 HTML templates
│   └── static/          # CSS styles
├── agent/               # Browser-use AI agent
│   ├── orchestrator.py  # NL → task prompt mapping
│   └── run.py          # CLI entry point
├── slack_bot/           # Slack bot integration
│   └── bot.py          # Socket Mode listener
├── .env.example         # Environment template
├── pyproject.toml       # Dependencies (uv)
└── README.md
```

## Key Design Decisions

1. **browser-use over Anthropic Computer Use** — Faster to implement, more reliable for web-only tasks, model-agnostic. The LLM decides what to click/type based on page content, not hardcoded selectors.

2. **Gemini 2.0 Flash** — Free tier, strong vision + reasoning, fast inference. Perfect for budget-conscious development.

3. **FastAPI over Flask** — Async-native (matches browser-use's async nature), Pydantic models, auto Swagger docs at `/docs`.

4. **aiosqlite** — Async-native SQLite driver that prevents blocking the FastAPI event loop during database operations. File-based, zero-config, and perfect for persistent storage in Docker volumes.

5. **Socket Mode for Slack** — No public URL needed, works locally behind a firewall.

6. **AWS EC2 + Docker + Caddy** — Fully containerized deployment on a `t3.small` instance. Uses `ipc: host` for performant headless browser execution and Caddy for automatic Let's Encrypt SSL.

