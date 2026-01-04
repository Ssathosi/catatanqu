"""
Bot Catatan Keuangan AI - Receipt OCR Handler
Handles photo receipt scanning and auto-transaction creation.
"""
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, MessageHandler, CallbackQueryHandler, filters
)

from database.db_service import db
from services.crypto_service import crypto
from services.ai_service import ai
from utils.constants import MESSAGES, CATEGORY_ICONS, Category, BUTTONS
from utils.helpers import format_currency, format_date


async def handle_receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle receipt photo upload - TEMPORARILY DISABLED."""
    user = update.effective_user
    
    # Check if user exists and is authenticated
    db_user = await db.get_user(user.id)
    if not db_user or not context.user_data.get("is_authenticated"):
        await update.message.reply_text(
            "🔒 *Akses Terkunci*\n\nSilakan ketik /start dan masukkan PIN kamu.",
            parse_mode="Markdown"
        )
        return
    
    # OCR DISABLED - Show message
    await update.message.reply_text(
        "📸 *Fitur Scan Struk Dinonaktifkan*\n\n"
        "Fitur OCR sedang dalam maintenance.\n\n"
        "💡 *Gunakan input manual:*\n"
        "Ketik langsung seperti:\n"
        "• `beli kopi 20rb`\n"
        "• `makan siang 35k`\n"
        "• `bensin 50000`\n\n"
        "Bot akan otomatis mengenali transaksi kamu! ✨",
        parse_mode="Markdown"
    )
    return


def categorize_store(store_name: str) -> Category:
    """Categorize based on store name."""
    store_lower = store_name.lower()
    
    # Food/Beverage
    food_keywords = ["mcd", "kfc", "pizza", "burger", "cafe", "coffee", "resto", "warung", 
                     "bakso", "mie", "sate", "ayam", "starbucks", "chatime", "gofood"]
    if any(kw in store_lower for kw in food_keywords):
        return Category.MAKAN
    
    # Supermarket/Belanja
    shop_keywords = ["indomaret", "alfamart", "alfamidi", "carrefour", "hypermart", 
                     "giant", "superindo", "lottemart", "transmart", "tokopedia", "shopee"]
    if any(kw in store_lower for kw in shop_keywords):
        return Category.BELANJA
    
    # Transport
    transport_keywords = ["pertamina", "shell", "spbu", "benzin", "parkir", "toll", "tol"]
    if any(kw in store_lower for kw in transport_keywords):
        return Category.TRANSPORT
    
    # Pharmacy/Health
    health_keywords = ["apotek", "kimia farma", "century", "guardian", "watson"]
    if any(kw in store_lower for kw in health_keywords):
        return Category.KESEHATAN
    
    return Category.BELANJA  # Default to Belanja for receipts


async def receipt_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet selection for receipt transaction."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    pending = context.user_data.get("pending_receipt")
    
    if not pending:
        await query.edit_message_text("❌ Session expired. Kirim foto struk lagi.")
        return
    
    if data == "receipt_wallet_skip":
        pending["wallet_id"] = None
    else:
        wallet_id = int(data.replace("receipt_wallet_", ""))
        wallet = await db.get_wallet(wallet_id)
        
        if not wallet:
            await query.edit_message_text("❌ Akun tidak ditemukan")
            return
        
        balance = crypto.decrypt_amount(wallet["balance_encrypted"])
        if balance < pending["amount"]:
            await query.edit_message_text(
                MESSAGES["wallet_insufficient"].format(
                    name=wallet["name"],
                    balance=balance
                )
            )
            return
        
        pending["wallet_id"] = wallet_id
        pending["wallet_name"] = wallet["name"]
        pending["wallet_icon"] = wallet.get("icon", "💰")
        pending["wallet_balance"] = balance
        pending["wallet_balance_encrypted"] = wallet["balance_encrypted"]
    
    context.user_data["pending_receipt"] = pending
    
    # Show confirm buttons
    keyboard = [
        [
            InlineKeyboardButton(BUTTONS["confirm"], callback_data="receipt_confirm"),
            InlineKeyboardButton(BUTTONS["cancel"], callback_data="receipt_cancel"),
        ]
    ]
    
    # Update message with wallet info
    preview = f"📸 *Struk Terdeteksi!*\n\n"
    preview += f"🏪 *{pending['store_name']}*\n"
    preview += f"💰 Total: {format_currency(pending['amount'])}\n"
    preview += f"{pending['category_icon']} Kategori: {pending['category']}\n"
    
    if pending.get("wallet_id"):
        preview += f"{pending['wallet_icon']} Dari: {pending['wallet_name']}\n"
    
    preview += "\n✅ Konfirmasi untuk menyimpan"
    
    await query.edit_message_text(
        preview,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def receipt_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle receipt confirmation."""
    query = update.callback_query
    await query.answer()
    
    pending = context.user_data.get("pending_receipt")
    
    if not pending:
        await query.edit_message_text("❌ Session expired. Kirim foto struk lagi.")
        return
    
    try:
        encrypted_amount = crypto.encrypt_amount(pending["amount"])
        wallet_id = pending.get("wallet_id")
        
        # Parse receipt date if available
        receipt_date = None
        if pending.get("receipt_date"):
            try:
                receipt_date = date.fromisoformat(pending["receipt_date"])
            except:
                pass
        
        # Create transaction
        transaction = await db.create_transaction(
            user_id=pending["user_id"],
            amount_encrypted=encrypted_amount,
            description=pending["description"],
            category=pending["category"],
            source_type="receipt",
            store_name=pending.get("store_name"),
            items=pending.get("items"),
            receipt_date=receipt_date,
            wallet_id=wallet_id
        )
        
        # If wallet selected, deduct balance
        if wallet_id:
            old_balance = pending["wallet_balance"]
            new_balance = old_balance - pending["amount"]
            
            await db.update_wallet_balance(
                wallet_id=wallet_id,
                new_balance_encrypted=crypto.encrypt_amount(new_balance),
                old_balance_encrypted=pending["wallet_balance_encrypted"],
                amount_encrypted=encrypted_amount,
                log_type="expense",
                transaction_id=transaction["id"],
                note=f"Struk: {pending['store_name']}"
            )
            
            success_msg = (
                "✅ *Struk Tersimpan!*\n\n"
                f"🏪 {pending['store_name']}\n"
                f"💰 {format_currency(pending['amount'])}\n"
                f"{pending['category_icon']} {pending['category']}\n"
                f"{pending['wallet_icon']} {pending['wallet_name']}\n"
                f"💳 Sisa saldo: {format_currency(new_balance)}"
            )
        else:
            success_msg = (
                "✅ *Struk Tersimpan!*\n\n"
                f"🏪 {pending['store_name']}\n"
                f"💰 {format_currency(pending['amount'])}\n"
                f"{pending['category_icon']} {pending['category']}"
            )
        
        # Clear pending
        context.user_data.pop("pending_receipt", None)
        
        await query.edit_message_text(success_msg, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error saving receipt: {e}")
        await query.edit_message_text(MESSAGES["error_generic"])


async def receipt_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle receipt cancellation."""
    query = update.callback_query
    await query.answer()
    
    context.user_data.pop("pending_receipt", None)
    try:
        await query.delete_message()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Scan struk dibatalkan",
        )
    except:
        await query.edit_message_text("❌ Dibatalkan")


def get_receipt_handlers():
    """Get receipt OCR handlers."""
    return [
        MessageHandler(filters.PHOTO, handle_receipt_photo),
        CallbackQueryHandler(receipt_wallet_callback, pattern=r"^receipt_wallet_"),
        CallbackQueryHandler(receipt_confirm_callback, pattern=r"^receipt_confirm$"),
        CallbackQueryHandler(receipt_cancel_callback, pattern=r"^receipt_cancel$"),
    ]
