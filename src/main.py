"""
Bot Catatan Keuangan AI - Main Entry Point
"""
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


def main():
    """Start the bot."""
    # Create application
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(get_start_handler())
    application.add_handler(get_wallet_handler())
    for h in get_wallet_menu_handlers(): application.add_handler(h)
    
    application.add_handler(get_savings_handler())
    application.add_handler(get_progress_handler())
    
    # Reports
    for h in get_report_handlers(): application.add_handler(h)
    
    # AI & Settings
    for h in get_settings_handlers(): application.add_handler(h)
    for h in get_insight_handlers(): application.add_handler(h)
    for h in get_receipt_handlers(): application.add_handler(h)
    for h in get_sheets_handlers(): application.add_handler(h)
    
    # Help handlers
    for h in get_help_handlers(): application.add_handler(h)
    
    # Transaction handlers (Natural Language should be near the end)
    for h in get_transaction_handlers(): application.add_handler(h)
    
    # Start bot
    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == '__main__':
    main()
