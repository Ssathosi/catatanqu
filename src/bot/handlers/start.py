"""
Bot Catatan Keuangan AI - Start Handler
Handles /start command, onboarding flow, and login.
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

from config import config
from database.db_service import db
from services.crypto_service import crypto
from utils.constants import MESSAGES


# Conversation states
WAITING_PIN = 1
CONFIRM_PIN = 2
VERIFY_LOGIN = 3


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command."""
    user = update.effective_user
    telegram_id = user.id
    
    # Check if user already exists
    existing_user = await db.get_user(telegram_id)
    
    if existing_user:
        # User exists, ask for PIN to login
        display_name = user.username or user.first_name or "Pengguna"
        await update.message.reply_text(
            f"👋 Selamat datang kembali, *@{display_name}*!\n\n"
            "Silakan masukkan PIN kamu untuk masuk ke aplikasi:",
            parse_mode="Markdown"
        )
        return VERIFY_LOGIN
    
    # New user - start onboarding
    welcome_msg = MESSAGES["welcome"].format(bot_name=config.BOT_NAME)
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    
    return WAITING_PIN


async def receive_pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle PIN input during onboarding."""
    pin = update.message.text.strip()
    
    # Delete for security
    try: await update.message.delete()
    except: pass
    
    from utils.helpers import validate_pin
    is_valid, error_msg = validate_pin(pin, config.PIN_MIN_LENGTH, config.PIN_MAX_LENGTH)
    
    if not is_valid:
        await update.message.reply_text(f"❌ {error_msg}\n\nMasukkan PIN lagi:")
        return WAITING_PIN
    
    context.user_data["temp_pin"] = pin
    await update.message.reply_text("✅ PIN diterima! Ketik ulang PIN untuk konfirmasi:")
    return CONFIRM_PIN


async def confirm_pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle PIN confirmation during onboarding."""
    confirm_pin = update.message.text.strip()
    temp_pin = context.user_data.pop("temp_pin", "")
    
    try: await update.message.delete()
    except: pass
    
    if confirm_pin != temp_pin:
        await update.message.reply_text("❌ PIN tidak cocok! Silakan ketik /start lagi.")
        return ConversationHandler.END
    
    user = update.effective_user
    pin_hash = crypto.hash_pin(confirm_pin)
    
    try:
        await db.create_user(
            telegram_id=user.id,
            pin_hash=pin_hash,
            username=user.username,
            first_name=user.first_name
        )
        
        # New: Direct to wallet creation
        await update.message.reply_text(
            "🎉 *Akun Berhasil Dibuat!*\n\n"
            "Sekarang, mari kita buat *Dompet* (Saldo Awal) kamu.\n"
            "Ketik: `/dompet` untuk membuat dompet pertamamu.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text("❌ Gagal membuat akun. Coba /start lagi.")
        print(f"Error: {e}")
    
    return ConversationHandler.END


async def verify_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle login for existing users."""
    pin = update.message.text.strip()
    user = update.effective_user
    
    try: await update.message.delete()
    except: pass
    
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text("❌ Kamu belum terdaftar. Ketik /start")
        return ConversationHandler.END
    
    if crypto.verify_pin(pin, db_user["pin_hash"]):
        # Login success
        context.user_data["is_authenticated"] = True
        context.user_data["user_id"] = db_user["id"]
        
        await update.message.reply_text(
            "✅ *Login Berhasil!*\n\n"
            "Sekarang kamu bisa menggunakan semua fitur bot.\n"
            "Gunakan /bantuan untuk melihat menu.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    else:
        # Login failed
        await update.message.reply_text("❌ *PIN Salah!*\n\nSilakan masukkan PIN yang benar:")
        return VERIFY_LOGIN


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("❌ Aksi dibatalkan.")
    return ConversationHandler.END


def get_start_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            WAITING_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pin)],
            CONFIRM_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_pin)],
            VERIFY_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_login)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )
