import os
from dotenv import load_dotenv

load_dotenv()

# Slack
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")

# Anthropic
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# Tavily
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

# Notion
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

# Rate limiting
INTEL_COOLDOWN_SECONDS = int(os.environ.get("INTEL_COOLDOWN_SECONDS", "120"))
