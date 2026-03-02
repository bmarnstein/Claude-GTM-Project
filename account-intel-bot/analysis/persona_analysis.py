import logging
import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from prompts.system_persona import SYSTEM_PERSONA_PROMPT

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

PERSONAS = [
    "Head of Fraud / VP Fraud Operations",
    "CISO / Head of Information Security",
    "Chief Risk Officer / Head of Enterprise Risk",
]


async def generate_persona_analysis(
    company_name: str,
    account_brief: str,
    pain_points: str,
    trigger_events: str,
) -> str:
    """Stage 4: Map pain point hypotheses to specific buyer personas.

    Determines which hypothesis is most relevant to each persona,
    their preferred language, and the best opening hook.

    Returns the persona analysis as a formatted string.
    """
    logger.info(f"Generating persona analysis for: {company_name}")

    system_prompt = SYSTEM_PERSONA_PROMPT.format(company_name=company_name)

    user_message = f"""Map our research to personas for outreach planning:

ACCOUNT: {company_name}

ACCOUNT BRIEF:
{account_brief}

PAIN POINT HYPOTHESES:
{pain_points}

TRIGGER EVENTS:
{trigger_events}"""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    analysis = response.content[0].text
    logger.info(f"Persona analysis generated ({len(analysis)} chars)")
    return analysis


def extract_persona_section(full_analysis: str, persona_keyword: str) -> str:
    """Extract a single persona's section from the full persona analysis output.

    Looks for the persona heading (e.g., "Head of Fraud") and captures
    everything until the next persona heading or end of text.
    """
    lines = full_analysis.split("\n")
    capturing = False
    section_lines = []

    for line in lines:
        # Check if this line starts a persona section
        is_persona_heading = line.strip().startswith("### ") and "👤" in line

        if is_persona_heading and persona_keyword.lower() in line.lower():
            capturing = True
            section_lines.append(line)
        elif is_persona_heading and capturing:
            # Hit the next persona section — stop capturing
            break
        elif capturing:
            section_lines.append(line)

    if section_lines:
        return "\n".join(section_lines)

    # Fallback: return the full analysis if we can't parse sections
    return full_analysis
