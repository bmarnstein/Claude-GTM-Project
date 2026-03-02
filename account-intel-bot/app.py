import asyncio
import logging
import time
from collections import defaultdict

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, INTEL_COOLDOWN_SECONDS
from research.aggregator import gather_research
from analysis.account_brief import generate_account_brief
from analysis.pain_points import generate_pain_point_hypotheses
from analysis.trigger_events import generate_trigger_events
from analysis.persona_analysis import generate_persona_analysis
from analysis.outreach import generate_all_outreach, assemble_outreach_message
from integrations.slack_messages import (
    post_status_message,
    update_status_message,
    post_account_brief,
    post_pain_points,
    post_trigger_events,
    post_outreach,
    post_notion_link,
    send_outreach_dm,
)
from integrations.notion_client import (
    find_existing_account,
    create_account_page,
    update_account_page,
)
from utils.formatting import (
    extract_top_pain_point,
    extract_domain_from_brief,
    clean_outreach_for_dm,
    get_slack_thread_permalink,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("account-intel-bot")

# Initialize Slack app
app = AsyncApp(token=SLACK_BOT_TOKEN)

# Simple in-memory rate limiting: user_id -> last request timestamp
_last_request: dict[str, float] = defaultdict(float)


@app.command("/intel")
async def handle_intel_command(ack, command, client, respond):
    """Handle the /intel slash command.

    Flow: ack → status message → background pipeline → threaded messages → Notion page.
    """
    await ack()

    user_id = command["user_id"]
    user_name = command.get("user_name", "unknown")
    channel_id = command["channel_id"]
    company_name = command.get("text", "").strip()

    # Validate input
    if not company_name:
        await respond(
            "Usage: `/intel <company name>`\n"
            "Example: `/intel JPMorgan Chase`"
        )
        return

    # Rate limiting
    now = time.time()
    if now - _last_request[user_id] < INTEL_COOLDOWN_SECONDS:
        remaining = int(INTEL_COOLDOWN_SECONDS - (now - _last_request[user_id]))
        await respond(
            f"Please wait {remaining} seconds before running another `/intel` command."
        )
        return
    _last_request[user_id] = now

    logger.info(f"Intel request from {user_name} for: {company_name}")

    # Post initial status message
    status = await post_status_message(client, channel_id, company_name)
    status_ts = status["ts"]

    # Run the full pipeline in the background
    asyncio.create_task(
        _run_intel_pipeline(
            client=client,
            channel_id=channel_id,
            status_ts=status_ts,
            company_name=company_name,
            user_id=user_id,
            user_name=user_name,
        )
    )


async def _run_intel_pipeline(
    client,
    channel_id: str,
    status_ts: str,
    company_name: str,
    user_id: str,
    user_name: str,
):
    """Execute the full research → analysis → Slack → Notion pipeline."""
    start_time = time.time()

    try:
        # STAGE 0: Web research
        await update_status_message(client, channel_id, status_ts, company_name, "gathering")
        raw_results, formatted_research = await gather_research(company_name)
        logger.info(f"Research gathered in {time.time() - start_time:.1f}s")

        # STAGE 1: Account brief
        await update_status_message(client, channel_id, status_ts, company_name, "analyzing")
        brief = await generate_account_brief(company_name, formatted_research)
        brief_response = await post_account_brief(client, channel_id, status_ts, brief)
        logger.info(f"Account brief posted in {time.time() - start_time:.1f}s")

        # STAGE 2: Pain point hypotheses
        hypotheses = await generate_pain_point_hypotheses(
            company_name, brief, formatted_research
        )
        await post_pain_points(client, channel_id, status_ts, hypotheses)
        logger.info(f"Pain points posted in {time.time() - start_time:.1f}s")

        # STAGE 3: Trigger events
        await update_status_message(client, channel_id, status_ts, company_name, "triggers")
        triggers = await generate_trigger_events(
            company_name, brief, hypotheses, formatted_research
        )
        await post_trigger_events(client, channel_id, status_ts, triggers)
        logger.info(f"Trigger events posted in {time.time() - start_time:.1f}s")

        # STAGE 4: Persona analysis
        await update_status_message(client, channel_id, status_ts, company_name, "outreach")
        persona_analysis = await generate_persona_analysis(
            company_name, brief, hypotheses, triggers
        )

        # STAGE 5: Per-persona outreach (3 parallel calls)
        outreach_by_persona = await generate_all_outreach(
            company_name=company_name,
            full_persona_analysis=persona_analysis,
            account_brief=brief,
            pain_points=hypotheses,
            trigger_events=triggers,
        )
        assembled_outreach = assemble_outreach_message(outreach_by_persona)
        await post_outreach(client, channel_id, status_ts, assembled_outreach)
        logger.info(f"Outreach posted in {time.time() - start_time:.1f}s")

        # STAGE 7: Notion page
        await update_status_message(client, channel_id, status_ts, company_name, "notion")

        domain = extract_domain_from_brief(brief)
        top_pain_point = extract_top_pain_point(hypotheses)
        slack_thread_url = get_slack_thread_permalink(channel_id, status_ts)

        existing = await find_existing_account(company_name)
        if existing:
            page_url = await update_account_page(
                page_id=existing["id"],
                account_name=company_name,
                domain=domain,
                owner_name=user_name,
                slack_thread_url=slack_thread_url,
                account_brief=brief,
                pain_points=hypotheses,
                trigger_events=triggers,
                persona_analysis=persona_analysis,
                outreach=assembled_outreach,
                top_pain_point=top_pain_point,
            )
        else:
            page_url = await create_account_page(
                account_name=company_name,
                domain=domain,
                owner_name=user_name,
                slack_thread_url=slack_thread_url,
                account_brief=brief,
                pain_points=hypotheses,
                trigger_events=triggers,
                persona_analysis=persona_analysis,
                outreach=assembled_outreach,
                top_pain_point=top_pain_point,
            )

        await post_notion_link(client, channel_id, status_ts, company_name, page_url)

        # Done!
        elapsed = time.time() - start_time
        await update_status_message(client, channel_id, status_ts, company_name, "complete")
        logger.info(f"Full pipeline complete for {company_name} in {elapsed:.1f}s")

    except Exception as e:
        logger.exception(f"Pipeline failed for {company_name}: {e}")
        await update_status_message(
            client, channel_id, status_ts, company_name, "error", error=str(e)[:200]
        )


@app.event("reaction_added")
async def handle_reaction(event, client):
    """Handle emoji reactions — 🎯 on outreach messages triggers a DM with clean copy-paste text."""
    if event.get("reaction") != "dart":
        return

    user_id = event["user"]
    channel = event["item"]["channel"]
    message_ts = event["item"]["ts"]

    try:
        # Fetch the message that was reacted to
        result = await client.conversations_replies(
            channel=channel,
            ts=message_ts,
            limit=1,
            inclusive=True,
        )

        messages = result.get("messages", [])
        if not messages:
            return

        message_text = messages[0].get("text", "")

        # Only process if this looks like an outreach message
        if "Outreach" not in message_text and "📧" not in message_text:
            return

        clean_text = clean_outreach_for_dm(message_text)
        await send_outreach_dm(client, user_id, "Account", clean_text)

    except Exception as e:
        logger.error(f"Failed to handle reaction: {e}")


async def main():
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    logger.info("Account Intel Bot starting...")
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
