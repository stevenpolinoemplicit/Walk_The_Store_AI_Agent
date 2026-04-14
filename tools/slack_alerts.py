# slack_alerts.py — Slack notification client.
# Sends formatted messages to a Slack channel and optionally DMs the account manager.
# Token comes from config/settings.py. Channel and user IDs come from AccountConfig.

import logging
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import settings

logger = logging.getLogger(__name__)

# #note: Instantiate one shared WebClient per process using the bot token from .env
_client = WebClient(token=settings.SLACK_BOT_TOKEN)


# #note: Posts a formatted message to a Slack channel; drive_url is attached as context if provided
def post_to_channel(
    channel_id: str,
    text: str,
    blocks: Optional[list] = None,
    drive_url: Optional[str] = None,
) -> None:
    try:
        kwargs: dict = {"channel": channel_id, "text": text}
        if blocks:
            kwargs["blocks"] = blocks
        _client.chat_postMessage(**kwargs)
        logger.info(f"Slack message posted to channel {channel_id}")
    except SlackApiError as e:
        logger.error(f"Slack post_to_channel failed: {e.response['error']}")
        raise


# #note: DMs a Slack user directly; used only for critical severity alerts to account managers
def send_dm(user_id: str, text: str) -> None:
    try:
        dm_response = _client.conversations_open(users=user_id)
        dm_channel = dm_response["channel"]["id"]
        _client.chat_postMessage(channel=dm_channel, text=text)
        logger.info(f"Slack DM sent to user {user_id}")
    except SlackApiError as e:
        logger.error(f"Slack send_dm failed: {e.response['error']}")
        raise


# #note: Posts the cross-brand daily summary to the ops channel defined in .env
def post_ops_summary(text: str, blocks: Optional[list] = None) -> None:
    post_to_channel(settings.SLACK_OPS_CHANNEL, text, blocks)


# #note: Posts a formatted error alert to the ops channel — never raises so it cannot crash the agent
def notify_error(source: str, message: str) -> None:
    text = f":warning: *Walk the Store — Agent Error*\n*Source:* {source}\n{message}"
    try:
        post_to_channel(settings.SLACK_OPS_CHANNEL, text)
        logger.info(f"Error notification sent to ops channel — source: {source}")
    except Exception as e:
        logger.error(f"Failed to send error notification to Slack: {e}")
