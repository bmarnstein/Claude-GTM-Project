import logging
from slack_sdk.web.async_client import AsyncWebClient

logger = logging.getLogger(__name__)

# Status messages for each pipeline stage
STATUS_MESSAGES = {
    "researching": "🔍 Researching {company}...",
    "gathering": "🔍 Gathering intelligence on {company}...",
    "analyzing": "📊 Analyzing pain points for {company}...",
    "triggers": "⚡ Identifying trigger events for {company}...",
    "outreach": "✍️ Drafting personalized outreach for {company}...",
    "notion": "📄 Creating Notion account plan for {company}...",
    "complete": "✅ Research complete for {company}!",
    "error": "❌ Error researching {company}: {error}",
}


async def post_status_message(
    client: AsyncWebClient,
    channel: str,
    company_name: str,
    status: str = "researching",
    error: str = "",
) -> dict:
    """Post or update the initial status message.

    Returns the Slack API response (contains 'ts' for threading).
    """
    text = STATUS_MESSAGES[status].format(company=company_name, error=error)
    response = await client.chat_postMessage(channel=channel, text=text)
    return response


async def update_status_message(
    client: AsyncWebClient,
    channel: str,
    ts: str,
    company_name: str,
    status: str,
    error: str = "",
):
    """Update the existing status message in-place."""
    text = STATUS_MESSAGES[status].format(company=company_name, error=error)
    await client.chat_update(channel=channel, ts=ts, text=text)


async def post_threaded_message(
    client: AsyncWebClient,
    channel: str,
    thread_ts: str,
    text: str,
    title: str = "",
) -> dict:
    """Post a message as a threaded reply under the status message.

    If the text is too long for a single Slack message (>3000 chars),
    it will be split into multiple messages.
    """
    MAX_LENGTH = 3000

    if title:
        text = f"*{title}*\n\n{text}"

    if len(text) <= MAX_LENGTH:
        response = await client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=text,
            unfurl_links=False,
            unfurl_media=False,
        )
        return response

    # Split long messages at paragraph boundaries
    chunks = _split_message(text, MAX_LENGTH)
    response = None
    for chunk in chunks:
        response = await client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=chunk,
            unfurl_links=False,
            unfurl_media=False,
        )
    return response


def _split_message(text: str, max_length: int) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


async def post_account_brief(
    client: AsyncWebClient,
    channel: str,
    thread_ts: str,
    brief: str,
) -> dict:
    """Post MESSAGE 1: Account Brief."""
    return await post_threaded_message(
        client, channel, thread_ts, brief, title="📋 Account Brief"
    )


async def post_pain_points(
    client: AsyncWebClient,
    channel: str,
    thread_ts: str,
    hypotheses: str,
) -> dict:
    """Post MESSAGE 2: Pain Point Hypotheses."""
    return await post_threaded_message(
        client, channel, thread_ts, hypotheses, title="🎯 Pain Point Hypotheses"
    )


async def post_trigger_events(
    client: AsyncWebClient,
    channel: str,
    thread_ts: str,
    triggers: str,
) -> dict:
    """Post MESSAGE 3: Trigger Events."""
    return await post_threaded_message(
        client, channel, thread_ts, triggers, title=""  # Title is in the content
    )


async def post_outreach(
    client: AsyncWebClient,
    channel: str,
    thread_ts: str,
    outreach: str,
) -> dict:
    """Post MESSAGE 4: Outreach Drafts."""
    return await post_threaded_message(
        client, channel, thread_ts, outreach, title="✉️ Outreach Drafts"
    )


async def post_notion_link(
    client: AsyncWebClient,
    channel: str,
    thread_ts: str,
    company_name: str,
    notion_url: str,
) -> dict:
    """Post MESSAGE 5: Notion page link."""
    text = f"📄 Full account plan created → <{notion_url}|{company_name} - Account Plan>"
    return await post_threaded_message(client, channel, thread_ts, text)


async def send_outreach_dm(
    client: AsyncWebClient,
    user_id: str,
    company_name: str,
    outreach_text: str,
):
    """DM a user a clean copy-paste version of outreach content."""
    # Open a DM channel with the user
    dm = await client.conversations_open(users=[user_id])
    dm_channel = dm["channel"]["id"]

    text = (
        f"*Copy-paste outreach for {company_name}*\n\n"
        f"```\n{outreach_text}\n```"
    )

    await client.chat_postMessage(channel=dm_channel, text=text)
