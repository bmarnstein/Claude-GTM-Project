# Account Intel Bot

Slack bot that lets sales reps trigger prospect research and personalized outreach generation with a single slash command. Automatically creates structured account plan pages in Notion.

## What it does

Type `/intel US Bank` in Slack and get:

1. **Account Brief** — Company overview, risk/fraud stack, recent news, job posting signals
2. **Pain Point Hypotheses** — 3-5 evidence-based hypotheses mapped to Oscilar capabilities with confidence levels, discovery questions, and talk tracks
3. **Trigger Events** — Ranked "why now" reasons to reach out
4. **Outreach Drafts** — Personalized email + LinkedIn for Head of Fraud, CISO, and CRO (each persona gets its own dedicated AI call for maximum quality)
5. **Notion Link** — Full account plan page auto-created in your Notion database

React with 🎯 on any outreach message to get a clean copy-paste version DM'd to you.

## Architecture

```
/intel command → 8-10 Tavily searches → Claude analysis pipeline (8 calls) → Slack thread + Notion page
```

- **Stage 0**: Research aggregation (8-10 parallel Tavily searches)
- **Stage 1**: Account brief synthesis (Claude)
- **Stage 2**: Pain point hypothesis engine (Claude — core intelligence)
- **Stage 3**: Trigger event identification (Claude)
- **Stage 4**: Persona-to-hypothesis mapping (Claude)
- **Stage 5a/5b/5c**: Per-persona outreach generation (3 parallel Claude calls)
- **Stage 6**: Notion page creation/update

## Setup

### 1. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App
2. Enable **Socket Mode** (Settings → Socket Mode → Enable)
3. Generate an **App-Level Token** with `connections:write` scope
4. Add **Slash Command**: `/intel` with description "Research an account"
5. Add **Bot Token Scopes** (OAuth & Permissions):
   - `commands`
   - `chat:write`
   - `reactions:read`
   - `im:write`
   - `users:read`
6. Subscribe to **Bot Events** (Event Subscriptions):
   - `reaction_added`
7. Install app to your workspace
8. Copy the **Bot User OAuth Token** (`xoxb-...`)

### 2. Create Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create an **Internal Integration**
3. Copy the integration token (`secret_...`)
4. Create a database in Notion with these properties:
   - Account Name (title)
   - Domain (URL)
   - Status (select: Researched, In Pursuit, Engaged, Opportunity)
   - Tier (select: Tier 1, Tier 2, Tier 3)
   - Primary Personas (multi-select)
   - Top Pain Point (select: Legacy Vendor Lock-in, Fragmented Stack, Slow Model Iteration, High False Positives, Rising Fraud Losses, Regulatory Pressure, Digital Transformation Gaps, TCO)
   - Trigger Events (rich text)
   - Last Researched (date)
   - Owner (rich text)
   - Slack Thread Link (URL)
5. **Share the database** with your integration (click ··· on the database → Connections → Add your integration)
6. Copy the **Database ID** from the database URL

### 3. Get API Keys

- **Anthropic**: [console.anthropic.com](https://console.anthropic.com)
- **Tavily**: [tavily.com](https://tavily.com) (free tier: 1000 searches/month)

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual keys
```

### 5. Install & Run

```bash
pip install -r requirements.txt
python app.py
```

## Deploy to fly.io

```bash
# Install flyctl: https://fly.io/docs/flyctl/install/
fly launch
fly secrets set SLACK_BOT_TOKEN=xoxb-... SLACK_APP_TOKEN=xapp-... ...
fly deploy
```

Or to Railway:

```bash
# Connect GitHub repo at railway.app
# Set env vars in Railway dashboard
# Deploy automatically on push
```

## Cost Estimate

| Component | Per Run |
|-----------|---------|
| Tavily (8-10 searches) | ~$0.08-0.10 |
| Claude Sonnet (8 calls) | ~$0.25-0.40 |
| **Total** | **~$0.35-0.50** |

At 20 accounts/week: ~$28-40/month in API costs.

## Customizing

### Edit prompts
All prompts live in `prompts/`. Edit these files to change the bot's analysis style:
- `oscilar_context.py` — Update when product messaging changes
- `system_pain_points.py` — The core hypothesis engine prompt
- `system_outreach.py` — Email tone, style, and rules

### Change target personas
Edit `analysis/persona_analysis.py` → `PERSONAS` list and the system prompt in `prompts/system_persona.py`.

### Adjust research depth
Edit `research/web_search.py` → `search_company()` to add/remove search queries.
