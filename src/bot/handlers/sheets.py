"""
Bot Catatan Keuangan AI - Google Sheets Handler
Handles spreadsheet backup and sync commands.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from database.db_service import db
from services.crypto_service import crypto
from services.sheets_service import sheets


# Conversation states
SHEETS_EMAIL = 1


async def sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sheets command - setup Google Sheets connection."""
    user = update.effective_user
    
    # Check if user exists
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text(
            "❌ Kamu belum terdaftar. Ketik /start untuk memulai."
        )
        return ConversationHandler.END
    
    # Check if Sheets is configured
    if not sheets.is_configured():
        await update.message.reply_text(
            "⚠️ *Google Sheets Belum Dikonfigurasi*\n\n"
            "Admin perlu mengatur credentials di server.\n\n"
            "Hubungi admin untuk mengaktifkan fitur ini.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    context.user_data["db_user"] = db_user
    
    # Check if already connected
    if db_user.get("sheets_connected") and db_user.get("sheets_id"):
        keyboard = [
            [
                InlineKeyboardButton("📤 Backup Sekarang", callback_data="sheets_backup"),
                InlineKeyboardButton("🔗 Buka Spreadsheet", url=f"https://docs.google.com/spreadsheets/d/{db_user['sheets_id']}")
            ],
            [
                InlineKeyboardButton("🔄 Ganti Spreadsheet", callback_data="sheets_new"),
                InlineKeyboardButton("❌ Putus Koneksi", callback_data="sheets_disconnect"),
            ]
        ]
        
        await update.message.reply_text(
            "📊 *Google Sheets Terhubung!*\n\n"
            f"📄 Spreadsheet ID: `{db_user['sheets_id'][:20]}...`\n\n"
            "Pilih aksi:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    # Ask for email to share
    await update.message.reply_text(
        "📊 *Setup Google Sheets*\n\n"
        "Masukkan email Google kamu untuk berbagi spreadsheet:\n\n"
        "_Contoh: email@gmail.com_",
        parse_mode="Markdown"
    )
    return SHEETS_EMAIL


async def sheets_email_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle email input for Sheets setup."""
    email = update.message.text.strip()
    
    # Simple email validation
    if "@" not in email or "." not in email:
        await update.message.reply_text(
            "❌ Email tidak valid. Masukkan email yang benar."
        )
        return SHEETS_EMAIL
    
    db_user = context.user_data.get("db_user")
    if not db_user:
        await update.message.reply_text("❌ Session expired. Ketik /sheets lagi.")
        return ConversationHandler.END
    
    # Send creating message
    creating_msg = await update.message.reply_text(
        "⏳ *Membuat spreadsheet...*",
        parse_mode="Markdown"
    )
    
    # Create spreadsheet
    title = f"Catatan Keuangan - {db_user.get('first_name', 'User')}"
    result = await sheets.create_spreadsheet(title, share_email=email)
    
    if result.get("error"):
        await creating_msg.edit_text(
            f"❌ *Gagal membuat spreadsheet*\n\n{result['error']}",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Save to user
    try:
        await db.update_user(db_user["id"], {
            "sheets_connected": True,
            "sheets_id": result["id"]
        })
        
        await creating_msg.edit_text(
            "✅ *Spreadsheet Berhasil Dibuat!*\n\n"
            f"📄 Nama: {result['title']}\n"
            f"📧 Dibagikan ke: {email}\n\n"
            f"🔗 [Buka Spreadsheet]({result['url']})\n\n"
            "Gunakan /backup untuk backup data.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"Error saving sheets info: {e}")
        await creating_msg.edit_text(
            "❌ Gagal menyimpan konfigurasi. Coba lagi nanti.",
            parse_mode="Markdown"
        )
    
    return ConversationHandler.END


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /backup command - manual backup to Sheets."""
    user = update.effective_user
    
    # Check if user exists
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text(
            "❌ Kamu belum terdaftar. Ketik /start untuk memulai."
        )
        return
    
    # Check if Sheets is connected
    if not db_user.get("sheets_connected") or not db_user.get("sheets_id"):
        await update.message.reply_text(
            "⚠️ Google Sheets belum terhubung.\n\n"
            "Ketik /sheets untuk setup.",
            parse_mode="Markdown"
        )
        return
    
    # Send backing up message
    backup_msg = await update.message.reply_text(
        "⏳ *Membackup data...*",
        parse_mode="Markdown"
    )
    
    sheet_id = db_user["sheets_id"]
    
    # Backup transactions
    transactions = await db.get_user_transactions(db_user["id"], limit=1000)
    tx_result = await sheets.backup_transactions(
        sheet_id, 
        transactions,
        crypto.decrypt_amount
    )
    
    # Backup wallets
    wallets = await db.get_user_wallets(db_user["id"])
    wallet_result = await sheets.backup_wallets(
        sheet_id,
        wallets,
        crypto.decrypt_amount
    )
    
    # Build result message
    if tx_result.get("error") or wallet_result.get("error"):
        error = tx_result.get("error", "") or wallet_result.get("error", "")
        await backup_msg.edit_text(
            f"❌ *Gagal backup*\n\n{error}",
            parse_mode="Markdown"
        )
        return
    
    await backup_msg.edit_text(
        "✅ *Backup Selesai!*\n\n"
        f"📝 Transaksi: +{tx_result['count']} baru (total {tx_result['total']})\n"
        f"💰 Wallet: {wallet_result['count']} akun\n\n"
        f"🔗 [Buka Spreadsheet](https://docs.google.com/spreadsheets/d/{sheet_id})",
        parse_mode="Markdown"
    )


async def sheets_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle sheets callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    db_user = context.user_data.get("db_user")
    
    if not db_user:
        db_user = await db.get_user(update.effective_user.id)
        context.user_data["db_user"] = db_user
    
    if data == "sheets_backup":
        # Trigger backup
        await query.edit_message_text("⏳ *Membackup data...*", parse_mode="Markdown")
        
        sheet_id = db_user["sheets_id"]
        
        transactions = await db.get_user_transactions(db_user["id"], limit=1000)
        tx_result = await sheets.backup_transactions(
            sheet_id,
            transactions,
            crypto.decrypt_amount
        )
        
        wallets = await db.get_user_wallets(db_user["id"])
        wallet_result = await sheets.backup_wallets(
            sheet_id,
            wallets,
            crypto.decrypt_amount
        )
        
        await query.edit_message_text(
            "✅ *Backup Selesai!*\n\n"
            f"📝 Transaksi: +{tx_result.get('count', 0)} baru\n"
            f"💰 Wallet: {wallet_result.get('count', 0)} akun\n\n"
            f"🔗 [Buka Spreadsheet](https://docs.google.com/spreadsheets/d/{sheet_id})",
            parse_mode="Markdown"
        )
    
    elif data == "sheets_new":
        await query.edit_message_text(
            "📊 *Ganti Spreadsheet*\n\n"
            "Masukkan email Google baru:",
            parse_mode="Markdown"
        )
        return SHEETS_EMAIL
    
    elif data == "sheets_disconnect":
        try:
            await db.update_user(db_user["id"], {
                "sheets_connected": False,
                "sheets_id": None
            })
            await query.edit_message_text(
                "✅ Koneksi Google Sheets diputus.\n\n"
                "Ketik /sheets untuk menghubungkan kembali."
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Gagal: {e}")
    
    return ConversationHandler.END


async def sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sync command - alias for backup."""
    await backup_command(update, context)


async def cancel_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel sheets operation."""
    await update.message.reply_text("❌ Dibatalkan")
    return ConversationHandler.END


# ==================== Handlers ====================

async def sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 *Google Sheets Sync*\n\n"
        "🚧 _Fitur ini sedang dalam pengembangan (Coming Soon)._\n\n"
        "Nantinya kamu bisa backup data otomatis ke Spreadsheet kamu sendiri!",
        parse_mode="Markdown"
    )

def get_sheets_handlers():
    """Get all sheets-related handlers."""
    # Since sheets is coming soon, we use a simple command handler
    # that points to the notification in settings
    return [
        CommandHandler("sheets", sheets_command),
        CommandHandler("backup", sheets_command),
        CommandHandler("sync", sheets_command),
        CallbackQueryHandler(sheets_callback, pattern=r"^sheets_"),
    ]
