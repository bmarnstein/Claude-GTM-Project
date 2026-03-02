import asyncio
import logging
import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from prompts.system_outreach import SYSTEM_OUTREACH_PROMPT
from analysis.persona_analysis import PERSONAS, extract_persona_section

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def _generate_single_persona_outreach(
    company_name: str,
    persona_title: str,
    persona_analysis: str,
    account_brief: str,
    pain_points: str,
    trigger_events: str,
) -> str:
    """Generate outreach for a single persona. Called 3x in parallel."""
    logger.info(f"Generating outreach for {persona_title} at {company_name}")

    system_prompt = SYSTEM_OUTREACH_PROMPT.format(
        company_name=company_name,
        persona_title=persona_title,
        persona_analysis=persona_analysis,
        brief_summary=account_brief[:2000],  # Truncate to keep context focused
        primary_hypothesis="(see persona analysis above)",
        strongest_trigger="(see persona analysis above)",
    )

    user_message = f"""Write outreach for {persona_title} at {company_name}.

PERSONA BRIEF:
{persona_analysis}

FULL RESEARCH CONTEXT:
Account Brief:
{account_brief}

Pain Point Hypotheses:
{pain_points}

Trigger Events:
{trigger_events}

Write the email and LinkedIn connection request. Focus entirely on this one persona's priorities and concerns."""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    outreach = response.content[0].text
    logger.info(f"Outreach for {persona_title} generated ({len(outreach)} chars)")
    return outreach


async def generate_all_outreach(
    company_name: str,
    full_persona_analysis: str,
    account_brief: str,
    pain_points: str,
    trigger_events: str,
) -> dict[str, str]:
    """Stage 5: Generate outreach for all 3 personas in parallel.

    Returns a dict mapping persona title to their outreach text.
    """
    logger.info(f"Generating outreach for all personas at: {company_name}")

    # Extract each persona's section from the full analysis
    persona_keywords = ["Fraud", "CISO", "Risk Officer"]

    tasks = []
    for persona_title, keyword in zip(PERSONAS, persona_keywords):
        persona_section = extract_persona_section(full_persona_analysis, keyword)
        tasks.append(
            _generate_single_persona_outreach(
                company_name=company_name,
                persona_title=persona_title,
                persona_analysis=persona_section,
                account_brief=account_brief,
                pain_points=pain_points,
                trigger_events=trigger_events,
            )
        )

    # Run all 3 persona outreach calls in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    outreach_by_persona = {}
    for persona_title, result in zip(PERSONAS, results):
        if isinstance(result, Exception):
            logger.error(f"Outreach generation failed for {persona_title}: {result}")
            outreach_by_persona[persona_title] = (
                f"*Error generating outreach for {persona_title}. "
                f"Please retry or draft manually based on the hypotheses above.*"
            )
        else:
            outreach_by_persona[persona_title] = result

    return outreach_by_persona


def assemble_outreach_message(outreach_by_persona: dict[str, str]) -> str:
    """Combine all persona outreach into a single formatted message."""
    sections = []
    for persona_title, outreach_text in outreach_by_persona.items():
        sections.append(f"### 👤 {persona_title}\n\n{outreach_text}")
    return "\n\n---\n\n".join(sections)
