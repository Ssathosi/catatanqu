"""
Bot Catatan Keuangan AI - Main Entry Point
Supports both Polling (local) and Webhook (production)
"""
import os
import logging
from telegram.ext import ApplicationBuilder

from config import config
from bot.handlers import (
    get_start_handler,
    get_transaction_handlers,
    get_report_handlers,
    get_help_handlers,
    get_wallet_handler,
    get_wallet_menu_handlers,
    get_savings_handler,
    get_progress_handler,
    get_receipt_handlers,
    get_settings_handlers,
    get_insight_handlers,
    get_sheets_handlers
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def setup_handlers(application):
    """Register all handlers."""
    application.add_handler(get_start_handler())
    application.add_handler(get_wallet_handler())
    for h in get_wallet_menu_handlers(): application.add_handler(h)
    
    application.add_handler(get_savings_handler())
    application.add_handler(get_progress_handler())
    
    for h in get_report_handlers(): application.add_handler(h)
    for h in get_settings_handlers(): application.add_handler(h)
    for h in get_insight_handlers(): application.add_handler(h)
    for h in get_receipt_handlers(): application.add_handler(h)
    for h in get_sheets_handlers(): application.add_handler(h)
    for h in get_help_handlers(): application.add_handler(h)
    for h in get_transaction_handlers(): application.add_handler(h)


def main():
    """Start the bot."""
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    setup_handlers(application)
    
    # Check if running in production (Koyeb, Render, etc)
    PORT = int(os.environ.get("PORT", 8000))
    WEBHOOK_URL = os.environ.get("KOYEB_PUBLIC_DOMAIN") or os.environ.get("RENDER_EXTERNAL_URL")
    
    if WEBHOOK_URL:
        # Production: Use webhook
        logger.info(f"Starting webhook on port {PORT}...")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=config.TELEGRAM_BOT_TOKEN,
            webhook_url=f"https://{WEBHOOK_URL}/{config.TELEGRAM_BOT_TOKEN}"
        )
    else:
        # Local development: Use polling
        logger.info("Bot is starting (polling mode)...")
        application.run_polling()


if __name__ == '__main__':
    main()
