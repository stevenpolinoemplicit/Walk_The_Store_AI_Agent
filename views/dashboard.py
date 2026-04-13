# dashboard.py — DEPRECATED. Gradio UI removed from scope.
# Manual triggers: run `python main.py --mode agent` from the terminal or a Cloud Run one-off job.
# Report viewing: Drive docs linked in Slack, or ask Claude Enterprise.
# This file is preserved per project no-delete policy but is not used.

import logging
from datetime import date

import gradio as gr

from controllers.orchestrator import run_agent
from tools.postgres import get_active_accounts

logger = logging.getLogger(__name__)


# #note: Triggers a full agent run and returns a status string for display in the Gradio UI
def trigger_run() -> str:
    try:
        logger.info("Manual agent run triggered via Gradio dashboard")
        run_agent()
        return f"✅ Run complete — {date.today()}. Check Slack for alerts and reports."
    except Exception as e:
        logger.error(f"Manual run failed: {e}")
        return f"❌ Run failed: {e}"


# #note: Fetches active account names from Postgres and returns them as a formatted string for display
def list_accounts() -> str:
    try:
        accounts = get_active_accounts()
        if not accounts:
            return "No active accounts found."
        return "\n".join(
            f"• {a.brand_name} ({a.marketplace}) — seller: {a.seller_id}"
            for a in accounts
        )
    except Exception as e:
        logger.error(f"Failed to fetch accounts for dashboard: {e}")
        return f"❌ Could not load accounts: {e}"


# #note: Builds and returns the Gradio Blocks UI object without launching it (caller decides launch)
def build_dashboard() -> gr.Blocks:
    with gr.Blocks(title="Walk the Store — Agent Dashboard") as demo:
        gr.Markdown("# 🛒 Walk the Store — Agent Dashboard")
        gr.Markdown("Manual trigger and account overview for the Amazon health agent.")

        with gr.Row():
            with gr.Column():
                gr.Markdown("## Run Agent")
                run_button = gr.Button("▶ Run Now", variant="primary")
                run_output = gr.Textbox(
                    label="Run Status", lines=2, interactive=False
                )
                run_button.click(fn=trigger_run, outputs=run_output)

            with gr.Column():
                gr.Markdown("## Active Accounts")
                refresh_button = gr.Button("🔄 Refresh")
                accounts_output = gr.Textbox(
                    label="Accounts", lines=15, interactive=False
                )
                refresh_button.click(fn=list_accounts, outputs=accounts_output)

    return demo


# #note: Entry point when dashboard.py is run directly — launches Gradio on default port 7860
if __name__ == "__main__":
    app = build_dashboard()
    app.launch()
