"""
Bot Catatan Keuangan AI - Settings Handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, 
    CallbackQueryHandler, MessageHandler, filters
)

from database.db_service import db
from services.crypto_service import crypto
from utils.helpers import validate_pin


# States
SETTINGS_MENU = 0
WAITING_OLD_PIN = 1
WAITING_NEW_PIN = 2


def get_settings_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Google Sheets (Coming Soon)", callback_data="set_sheets")],
        [InlineKeyboardButton("🔑 Ganti PIN", callback_data="set_pin")],
        [InlineKeyboardButton("🔙 Tutup", callback_data="set_close")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pengaturan command."""
    # Check authentication first
    if not context.user_data.get("is_authenticated"):
        await update.message.reply_text("🔒 Silakan /start dulu untuk login.")
        return ConversationHandler.END
    
    db_user = await db.get_user(update.effective_user.id)
    if not db_user:
        await update.message.reply_text("❌ Silakan /start dulu.")
        return ConversationHandler.END

    await update.message.reply_text(
        "⚙️ *Pengaturan Bot*\n\nPilih menu:",
        parse_mode="Markdown",
        reply_markup=get_settings_keyboard()
    )
    return SETTINGS_MENU



async def settings_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu button clicks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "set_sheets":
        await query.edit_message_text(
            "📊 *Google Sheets Sync*\n\n"
            "🚧 _Fitur ini Coming Soon._",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="set_back")]])
        )
        return SETTINGS_MENU

    elif query.data == "set_pin":
        await query.edit_message_text(
            "🔑 *Ganti PIN*\n\nMasukkan PIN lama kamu:",
            parse_mode="Markdown"
        )
        return WAITING_OLD_PIN

    elif query.data == "set_back":
        await query.edit_message_text(
            "⚙️ *Pengaturan Bot*",
            parse_mode="Markdown",
            reply_markup=get_settings_keyboard()
        )
        return SETTINGS_MENU
    
    elif query.data == "set_close":
        await query.delete_message()
        return ConversationHandler.END
    
    return SETTINGS_MENU


async def verify_old_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify old PIN."""
    pin = update.message.text.strip()
    try: await update.message.delete()
    except: pass
    
    db_user = await db.get_user(update.effective_user.id)
    
    if not crypto.verify_pin(pin, db_user["pin_hash"]):
        await update.message.reply_text("❌ PIN lama salah. Coba lagi:")
        return WAITING_OLD_PIN
    
    await update.message.reply_text("✅ PIN benar!\n\nMasukkan PIN baru (4-6 digit):")
    return WAITING_NEW_PIN


async def set_new_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set new PIN."""
    pin = update.message.text.strip()
    try: await update.message.delete()
    except: pass
    
    is_valid, error = validate_pin(pin)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}\n\nMasukkan PIN baru:")
        return WAITING_NEW_PIN
    
    new_hash = crypto.hash_pin(pin)
    await db.update_user(update.effective_user.id, {"pin_hash": new_hash})
    
    await update.message.reply_text("✅ *PIN berhasil diubah!*", parse_mode="Markdown")
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan")
    return ConversationHandler.END


def get_settings_handlers():
    return [
        ConversationHandler(
            entry_points=[
                CommandHandler("pengaturan", settings_command),
            ],
            states={
                SETTINGS_MENU: [
                    CallbackQueryHandler(settings_menu_callback, pattern=r"^set_"),
                ],
                WAITING_OLD_PIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, verify_old_pin),
                ],
                WAITING_NEW_PIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_pin),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command),
            ],
            per_user=True,
            per_chat=True,
        )
    ]
