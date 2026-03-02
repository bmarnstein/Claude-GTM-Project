import logging
from datetime import datetime, timezone

import httpx

from config import NOTION_TOKEN, NOTION_DATABASE_ID

logger = logging.getLogger(__name__)

NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_API_VERSION,
}


async def _request(method: str, path: str, json: dict | None = None) -> dict:
    """Make a Notion API request with retry on rate limits."""
    url = f"{NOTION_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(3):
            response = await client.request(method, url, headers=HEADERS, json=json)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "2"))
                logger.warning(f"Notion rate limited, retrying in {retry_after}s")
                import asyncio
                await asyncio.sleep(retry_after)
                continue
            response.raise_for_status()
            return response.json()
    raise Exception("Notion API rate limit exceeded after retries")


async def find_existing_account(account_name: str) -> dict | None:
    """Query the Notion database for an existing account page.

    Searches by account name (title property). Returns the page dict if found, None otherwise.
    """
    body = {
        "filter": {
            "property": "Account Name",
            "title": {
                "contains": account_name,
            },
        },
        "page_size": 1,
    }

    result = await _request("POST", f"/databases/{NOTION_DATABASE_ID}/query", json=body)
    results = result.get("results", [])

    if results:
        logger.info(f"Found existing account page for: {account_name}")
        return results[0]

    return None


async def create_account_page(
    account_name: str,
    domain: str,
    owner_name: str,
    slack_thread_url: str,
    account_brief: str,
    pain_points: str,
    trigger_events: str,
    persona_analysis: str,
    outreach: str,
    top_pain_point: str = "",
) -> str:
    """Create a new Notion page in the account database.

    Returns the URL of the created page.
    """
    logger.info(f"Creating Notion page for: {account_name}")

    properties = _build_properties(
        account_name=account_name,
        domain=domain,
        owner_name=owner_name,
        slack_thread_url=slack_thread_url,
        top_pain_point=top_pain_point,
    )

    children = _build_page_content(
        account_brief=account_brief,
        pain_points=pain_points,
        trigger_events=trigger_events,
        persona_analysis=persona_analysis,
        outreach=outreach,
    )

    body = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
        "children": children,
    }

    result = await _request("POST", "/pages", json=body)
    page_url = result.get("url", "")
    logger.info(f"Notion page created: {page_url}")
    return page_url


async def update_account_page(
    page_id: str,
    account_name: str,
    domain: str,
    owner_name: str,
    slack_thread_url: str,
    account_brief: str,
    pain_points: str,
    trigger_events: str,
    persona_analysis: str,
    outreach: str,
    top_pain_point: str = "",
) -> str:
    """Update an existing Notion page with fresh research.

    Preserves the Notes section by reading existing content first.
    Returns the page URL.
    """
    logger.info(f"Updating Notion page {page_id} for: {account_name}")

    # Update properties
    properties = _build_properties(
        account_name=account_name,
        domain=domain,
        owner_name=owner_name,
        slack_thread_url=slack_thread_url,
        top_pain_point=top_pain_point,
    )

    await _request("PATCH", f"/pages/{page_id}", json={"properties": properties})

    # Read existing content to preserve Notes section
    existing_notes = await _read_notes_section(page_id)

    # Delete existing blocks (Notion requires this for full page updates)
    existing_blocks = await _request("GET", f"/blocks/{page_id}/children")
    for block in existing_blocks.get("results", []):
        try:
            await _request("DELETE", f"/blocks/{block['id']}")
        except Exception as e:
            logger.warning(f"Failed to delete block {block['id']}: {e}")

    # Rebuild content with preserved notes
    children = _build_page_content(
        account_brief=account_brief,
        pain_points=pain_points,
        trigger_events=trigger_events,
        persona_analysis=persona_analysis,
        outreach=outreach,
        existing_notes=existing_notes,
        is_update=True,
    )

    await _request("PATCH", f"/blocks/{page_id}/children", json={"children": children})

    # Get the page URL
    page = await _request("GET", f"/pages/{page_id}")
    return page.get("url", "")


async def _read_notes_section(page_id: str) -> str:
    """Read the Notes section from an existing page to preserve it during updates."""
    blocks = await _request("GET", f"/blocks/{page_id}/children")
    in_notes = False
    notes_text = []

    for block in blocks.get("results", []):
        block_type = block.get("type", "")

        if block_type == "heading_2":
            text = _extract_text_from_block(block)
            if "Notes" in text:
                in_notes = True
                continue
            elif in_notes:
                break  # Hit next section

        if in_notes:
            text = _extract_text_from_block(block)
            if text:
                notes_text.append(text)

    return "\n".join(notes_text)


def _extract_text_from_block(block: dict) -> str:
    """Extract plain text from a Notion block."""
    block_type = block.get("type", "")
    block_data = block.get(block_type, {})
    rich_text = block_data.get("rich_text", [])
    return "".join(t.get("plain_text", "") for t in rich_text)


def _build_properties(
    account_name: str,
    domain: str,
    owner_name: str,
    slack_thread_url: str,
    top_pain_point: str = "",
) -> dict:
    """Build the Notion database properties for a page."""
    properties = {
        "Account Name": {"title": [{"text": {"content": account_name}}]},
        "Status": {"select": {"name": "Researched"}},
        "Last Researched": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        "Owner": {"rich_text": [{"text": {"content": owner_name}}]},
    }

    if domain:
        properties["Domain"] = {"url": domain if domain.startswith("http") else f"https://{domain}"}

    if slack_thread_url:
        properties["Slack Thread Link"] = {"url": slack_thread_url}

    if top_pain_point:
        properties["Top Pain Point"] = {"select": {"name": top_pain_point}}

    return properties


def _build_page_content(
    account_brief: str,
    pain_points: str,
    trigger_events: str,
    persona_analysis: str,
    outreach: str,
    existing_notes: str = "",
    is_update: bool = False,
) -> list[dict]:
    """Build the Notion page body as a list of block objects."""
    blocks = []

    # Update marker
    if is_update:
        blocks.append(_callout_block(
            f"🔄 Research Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        ))
        blocks.append(_divider())

    # Company Overview
    blocks.append(_heading2("Company Overview"))
    blocks.extend(_markdown_to_blocks(account_brief))
    blocks.append(_divider())

    # Pain Point Hypotheses
    blocks.append(_heading2("Pain Point Hypotheses"))
    blocks.extend(_markdown_to_blocks(pain_points))
    blocks.append(_divider())

    # Trigger Events
    blocks.append(_heading2("Trigger Events"))
    blocks.extend(_markdown_to_blocks(trigger_events))
    blocks.append(_divider())

    # Key Personas
    blocks.append(_heading2("Key Personas"))
    blocks.extend(_markdown_to_blocks(persona_analysis))
    blocks.append(_divider())

    # Outreach Drafts
    blocks.append(_heading2("Outreach Drafts"))
    blocks.extend(_markdown_to_blocks(outreach))
    blocks.append(_divider())

    # Research Sources are embedded in the brief/hypotheses sections

    # Notes section — preserved from existing content or empty
    blocks.append(_heading2("Notes"))
    if existing_notes:
        blocks.append(_paragraph(existing_notes))
    else:
        blocks.append(_paragraph("Add your notes from meetings, calls, and follow-ups here."))

    # Notion API limits children to 100 blocks per request
    return blocks[:100]


def _heading2(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }


def _paragraph(text: str) -> dict:
    # Notion rich_text content max is 2000 chars
    content = text[:2000]
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": content}}],
        },
    }


def _callout_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "icon": {"type": "emoji", "emoji": "🔄"},
        },
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _bulleted_list_item(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
        },
    }


def _markdown_to_blocks(text: str) -> list[dict]:
    """Convert markdown-ish text into Notion blocks.

    Simple converter — handles paragraphs, bullet points, and bold text.
    Not a full markdown parser, but good enough for our structured output.
    """
    blocks = []
    lines = text.split("\n")
    current_paragraph = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Empty line — flush current paragraph
            if current_paragraph:
                blocks.append(_paragraph("\n".join(current_paragraph)))
                current_paragraph = []
            continue

        if stripped.startswith("### "):
            # Sub-heading — use heading_3
            if current_paragraph:
                blocks.append(_paragraph("\n".join(current_paragraph)))
                current_paragraph = []
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[4:]}}],
                },
            })
        elif stripped.startswith("## "):
            if current_paragraph:
                blocks.append(_paragraph("\n".join(current_paragraph)))
                current_paragraph = []
            blocks.append(_heading2(stripped[3:]))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if current_paragraph:
                blocks.append(_paragraph("\n".join(current_paragraph)))
                current_paragraph = []
            blocks.append(_bulleted_list_item(stripped[2:]))
        elif stripped.startswith("1. ") or stripped.startswith("2. ") or stripped.startswith("3. "):
            if current_paragraph:
                blocks.append(_paragraph("\n".join(current_paragraph)))
                current_paragraph = []
            # Numbered list as bulleted (Notion numbered lists are separate blocks)
            blocks.append(_bulleted_list_item(stripped))
        else:
            current_paragraph.append(stripped)

    if current_paragraph:
        blocks.append(_paragraph("\n".join(current_paragraph)))

    return blocks
