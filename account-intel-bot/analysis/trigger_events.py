import logging
import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from prompts.system_trigger_events import SYSTEM_TRIGGER_EVENTS_PROMPT

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def generate_trigger_events(
    company_name: str,
    account_brief: str,
    pain_points: str,
    formatted_research: str,
) -> str:
    """Stage 3: Identify ranked trigger events for outreach timing.

    Returns trigger events as a formatted string.
    """
    logger.info(f"Generating trigger events for: {company_name}")

    system_prompt = SYSTEM_TRIGGER_EVENTS_PROMPT.format(company_name=company_name)

    user_message = f"""Identify trigger events for outreach timing:

ACCOUNT: {company_name}

ACCOUNT BRIEF:
{account_brief}

PAIN POINT HYPOTHESES:
{pain_points}

RAW SEARCH RESULTS:
{formatted_research}

Identify 1-3 trigger events ranked by urgency."""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=3000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    triggers = response.content[0].text
    logger.info(f"Trigger events generated ({len(triggers)} chars)")
    return triggers
