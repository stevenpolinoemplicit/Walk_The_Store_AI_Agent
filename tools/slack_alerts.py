# slack_alerts.py — Slack notification client.
# Sends formatted messages to a Slack channel and optionally DMs the account manager.
# Token comes from config/settings.py. Channel and user IDs come from AccountConfig.

import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import settings

logger = logging.getLogger(__name__)

# #note: Instantiate one shared WebClient per process using the bot token from .env
_client = WebClient(token=settings.SLACK_BOT_TOKEN)


# #note: Posts a formatted message to a Slack channel; used for brand-level alerts and daily summary
def post_to_channel(channel_id: str, text: str, blocks: list = None) -> None:
    try:
        kwargs = {"channel": channel_id, "text": text}
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
        # Open a direct message channel, then post to it
        dm_response = _client.conversations_open(users=user_id)
        dm_channel = dm_response["channel"]["id"]
        _client.chat_postMessage(channel=dm_channel, text=text)
        logger.info(f"Slack DM sent to user {user_id}")
    except SlackApiError as e:
        logger.error(f"Slack send_dm failed: {e.response['error']}")
        raise


# #note: Posts the cross-brand daily summary to the ops channel defined in .env
def post_ops_summary(text: str, blocks: list = None) -> None:
    post_to_channel(settings.SLACK_OPS_CHANNEL, text, blocks)
