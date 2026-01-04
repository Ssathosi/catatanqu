"""
Bot Catatan Keuangan AI - Help Handler
Handles /bantuan and general help commands.
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from utils.constants import MESSAGES


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bantuan command."""
    await update.message.reply_text(MESSAGES["help"], parse_mode="Markdown")


async def bantuan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bantuan command (Indonesian alias)."""
    await help_command(update, context)


# Export handlers
def get_help_handlers():
    """Get all help-related handlers."""
    return [
        CommandHandler("help", help_command),
        CommandHandler("bantuan", bantuan_command),
    ]
