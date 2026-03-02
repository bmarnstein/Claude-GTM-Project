import logging
import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from prompts.system_research import SYSTEM_RESEARCH_PROMPT

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def generate_account_brief(company_name: str, formatted_research: str) -> str:
    """Stage 1: Synthesize raw research into a structured account brief.

    Returns the account brief as a formatted string.
    """
    logger.info(f"Generating account brief for: {company_name}")

    system_prompt = SYSTEM_RESEARCH_PROMPT.format(company_name=company_name)

    user_message = f"""Research the following account: {company_name}

Here are the web search results to synthesize:

{formatted_research}

Each result includes: title, URL, content snippet, and relevance score.
Synthesize these into a structured account brief following your output format."""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    brief = response.content[0].text
    logger.info(f"Account brief generated ({len(brief)} chars)")
    return brief
