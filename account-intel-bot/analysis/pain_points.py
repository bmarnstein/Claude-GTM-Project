import logging
import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from prompts.system_pain_points import SYSTEM_PAIN_POINTS_PROMPT
from prompts.oscilar_context import OSCILAR_CONTEXT

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def generate_pain_point_hypotheses(
    company_name: str,
    account_brief: str,
    formatted_research: str,
) -> str:
    """Stage 2: Generate evidence-based pain point hypotheses.

    This is the core intelligence of the system. Takes the account brief
    and raw research, reasons through signals, and produces grounded
    hypotheses mapped to Oscilar capabilities.

    Returns the hypotheses as a formatted string.
    """
    logger.info(f"Generating pain point hypotheses for: {company_name}")

    system_prompt = SYSTEM_PAIN_POINTS_PROMPT.format(
        company_name=company_name,
        oscilar_context=OSCILAR_CONTEXT,
    )

    user_message = f"""Analyze this account and generate pain point hypotheses:

ACCOUNT: {company_name}

ACCOUNT BRIEF:
{account_brief}

RAW SEARCH RESULTS:
{formatted_research}

Generate 3-5 evidence-based pain point hypotheses following your reasoning process and output format."""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=6000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    hypotheses = response.content[0].text
    logger.info(f"Pain point hypotheses generated ({len(hypotheses)} chars)")
    return hypotheses
