"""
Bot Catatan Keuangan AI - Transaction Handler
"""
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from database.db_service import db
from services.crypto_service import crypto
from services.ai_service import ai
from utils.constants import MESSAGES, CATEGORY_ICONS, Category, BUTTONS
from utils.helpers import format_currency, format_date, parse_amount
from bot.keyboards import get_category_keyboard


async def add_transaction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tambah command."""
    if not context.user_data.get("is_authenticated"):
        await update.message.reply_text("🔒 Silakan /start dulu.")
        return

    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text("📝 *Format:* `/tambah <nominal> <deskripsi>`", parse_mode="Markdown")
        return
    
    amount = parse_amount(args[0])
    if not amount:
        await update.message.reply_text("❌ Nominal tidak valid.")
        return
    
    description = " ".join(args[1:])
    parsed = await ai.parse_transaction(f"{description} {args[0]}")
    db_user = await db.get_user(update.effective_user.id)
    
    context.user_data["pending_transaction"] = {
        "amount": amount,
        "description": description,
        "category": parsed.get("category", "Lainnya"),
        "category_icon": parsed.get("category_icon", "📦"),
        "user_id": db_user["id"],
    }
    
    await show_wallet_selection(update.message, context)


async def handle_natural_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural language transaction input."""
    text = update.message.text.strip()
    if text.startswith("/") or text.isdigit(): return
    
    if not context.user_data.get("is_authenticated"):
        await update.message.reply_text("🔒 Silakan /start dulu.")
        return
    
    parsed = await ai.parse_transaction(text)
    amount = parsed.get("amount", 0)
    
    if not amount or parsed.get("confidence", 0) < 0.3:
        await update.message.reply_text(MESSAGES["error_parse"], parse_mode="Markdown")
        return
    
    db_user = await db.get_user(update.effective_user.id)
    context.user_data["pending_transaction"] = {
        "amount": amount,
        "description": parsed.get("description", text),
        "category": parsed.get("category", "Lainnya"),
        "category_icon": parsed.get("category_icon", "📦"),
        "user_id": db_user["id"],
    }
    
    await show_wallet_selection(update.message, context)


async def show_wallet_selection(message, context):
    """Show wallet selection for transaction."""
    pending = context.user_data.get("pending_transaction")
    wallets = await db.get_user_wallets(pending["user_id"])
    
    preview = MESSAGES["transaction_preview"].format(
        amount=pending["amount"],
        description=pending["description"],
        category=pending["category"],
        category_icon=pending["category_icon"],
        date=format_date(datetime.now(), "short")
    )
    
    keyboard = []
    if wallets:
        preview += "\n\n💳 *Pilih sumber dana:*"
        for w in wallets:
            bal = crypto.decrypt_amount(w["balance_encrypted"])
            keyboard.append([InlineKeyboardButton(f"{w.get('icon', '💰')} {w['name']} ({format_currency(bal)})", callback_data=f"txwallet_{w['id']}")])
        keyboard.append([InlineKeyboardButton("⏭️ Lewati (tanpa akun)", callback_data="txwallet_skip")])
    else:
        keyboard.append([
            InlineKeyboardButton(BUTTONS["confirm"], callback_data="confirm_tx"),
            InlineKeyboardButton(BUTTONS["cancel"], callback_data="cancel_tx")
        ])
    
    await message.reply_text(preview, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def wallet_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet selection."""
    query = update.callback_query
    await query.answer()
    
    pending = context.user_data.get("pending_transaction")
    if not pending:
        await query.edit_message_text("❌ Transaksi kadaluarsa.")
        return

    if query.data == "txwallet_skip":
        pending["wallet_id"] = None
    else:
        wallet_id = int(query.data.replace("txwallet_", ""))
        wallet = await db.get_wallet(wallet_id)
        balance = crypto.decrypt_amount(wallet["balance_encrypted"])
        
        if balance < pending["amount"]:
            await query.edit_message_text(f"❌ Saldo {wallet['name']} tidak cukup.\nSaldo: {format_currency(balance)}")
            return
        
        pending["wallet_id"] = wallet_id
        pending["wallet_name"] = wallet["name"]
        pending["wallet_balance"] = balance
    
    context.user_data["pending_transaction"] = pending
    
    # Show final confirm
    keyboard = [[
        InlineKeyboardButton("✅ Simpan", callback_data="confirm_tx"),
        InlineKeyboardButton("❌ Batal", callback_data="cancel_tx")
    ]]
    await query.edit_message_text(
        f"📝 *Konfirmasi Final*\n\n"
        f"💰 {format_currency(pending['amount'])}\n"
        f"📍 {pending['description']}\n"
        f"🏷️ {pending['category']}\n"
        f"💳 {pending.get('wallet_name', 'Tanpa Dompet')}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def confirm_tx_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save transaction."""
    query = update.callback_query
    pending = context.user_data.pop("pending_transaction", None)
    if not pending:
        await query.answer("Kadaluarsa")
        return
    
    tx = await db.create_transaction(
        user_id=pending["user_id"],
        amount_encrypted=crypto.encrypt_amount(pending["amount"]),
        description=pending["description"],
        category=pending["category"],
        wallet_id=pending.get("wallet_id")
    )
    
    # Deduct wallet if selected
    if pending.get("wallet_id"):
        new_bal = pending["wallet_balance"] - pending["amount"]
        await db.update_wallet_balance(
            pending["wallet_id"],
            crypto.encrypt_amount(new_bal),
            amount_encrypted=crypto.encrypt_amount(pending["amount"]),
            log_type="expense",
            transaction_id=tx["id"]
        )
    
    await query.answer("Tersimpan!")
    await query.edit_message_text("✅ *Transaksi berhasil dicatat!*", parse_mode="Markdown")


async def cancel_tx_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data.pop("pending_transaction", None)
    await query.answer()
    await query.delete_message()


# ==================== LIST / HAPUS / EDIT ====================

async def list_transactions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transactions as a numbered list."""
    if not context.user_data.get("is_authenticated"):
        await update.message.reply_text("🔒 Silakan /start dulu.")
        return

    db_user = await db.get_user(update.effective_user.id)
    transactions = await db.get_user_transactions(user_id=db_user["id"], start_date=date.today())
    
    if not transactions:
        await update.message.reply_text("📭 Belum ada transaksi hari ini.")
        return

    context.user_data["last_tx_list"] = [tx["id"] for tx in transactions]
    
    msg = f"📋 *Transaksi Hari Ini*\n💡 _Gunakan /hapus <no> atau /edit <no>_\n\n"
    for i, tx in enumerate(transactions, 1):
        amount = crypto.decrypt_amount(tx["amount_encrypted"])
        msg += f"{i}. *{tx['description']}*\n   💰 {format_currency(amount)} | {tx['category']}\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /hapus <number> command."""
    if not context.args:
        await update.message.reply_text("💡 Contoh: `/hapus 1`", parse_mode="Markdown")
        return

    try:
        index = int(context.args[0]) - 1
        tx_ids = context.user_data.get("last_tx_list", [])
        
        if index < 0 or index >= len(tx_ids):
            await update.message.reply_text("❌ Nomor tidak valid. Ketik /list dulu.")
            return
        
        tx_id = tx_ids[index]
        tx_data = await db.get_transaction(tx_id)
        
        keyboard = [[
            InlineKeyboardButton("✅ Ya, Hapus", callback_data=f"confirm_del_{tx_id}"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel_del")
        ]]
        
        amount = crypto.decrypt_amount(tx_data["amount_encrypted"])
        await update.message.reply_text(
            f"❓ *Konfirmasi Hapus*\n\n📍 {tx_data['description']}\n💰 {format_currency(amount)}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except ValueError:
        await update.message.reply_text("❌ Masukkan angka.")


async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /edit <number> command."""
    if not context.args:
        await update.message.reply_text("💡 Contoh: `/edit 1`", parse_mode="Markdown")
        return

    try:
        index = int(context.args[0]) - 1
        tx_ids = context.user_data.get("last_tx_list", [])
        
        if index < 0 or index >= len(tx_ids):
            await update.message.reply_text("❌ Nomor tidak valid.")
            return
        
        context.user_data["editing_tx_id"] = tx_ids[index]
        await update.message.reply_text("📝 *Pilih kategori baru:*", parse_mode="Markdown", reply_markup=get_category_keyboard())
    except ValueError:
        await update.message.reply_text("❌ Masukkan angka.")


async def confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tx_id = int(query.data.replace("confirm_del_", ""))
    await db.delete_transaction(tx_id)
    await query.answer("Terhapus!")
    await query.edit_message_text("✅ *Transaksi dihapus.*", parse_mode="Markdown")


async def category_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    new_cat = query.data.replace("category_", "")
    tx_id = context.user_data.pop("editing_tx_id", None)
    
    if tx_id:
        await db.update_transaction_category(tx_id, new_cat)
        await query.answer(f"Diubah ke {new_cat}")
        await query.edit_message_text(f"✅ Kategori diubah menjadi *{new_cat}*", parse_mode="Markdown")
    else:
        await query.answer()
        await query.delete_message()


async def cancel_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data.pop("editing_tx_id", None)
    await query.answer()
    await query.delete_message()


def get_transaction_handlers():
    return [
        CommandHandler("tambah", add_transaction_command),
        CommandHandler("list", list_transactions_command),
        CommandHandler("hapus", delete_command),
        CommandHandler("edit", edit_command),
        CallbackQueryHandler(wallet_select_callback, pattern=r"^txwallet_"),
        CallbackQueryHandler(confirm_tx_callback, pattern="^confirm_tx$"),
        CallbackQueryHandler(cancel_tx_callback, pattern="^cancel_tx$"),
        CallbackQueryHandler(confirm_delete_callback, pattern="^confirm_del_"),
        CallbackQueryHandler(cancel_tx_callback, pattern="^cancel_del$"),
        CallbackQueryHandler(category_select_callback, pattern="^category_"),
        CallbackQueryHandler(cancel_category_callback, pattern="^cancel_category$"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_natural_input),
    ]
