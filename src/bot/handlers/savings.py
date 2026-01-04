"""
Bot Catatan Keuangan AI - Savings Target Handler
Handles savings goals with progress tracking.
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from database.db_service import db
from utils.helpers import format_currency, parse_amount


# Conversation states
TARGET_NAME = 1
TARGET_AMOUNT = 2
TARGET_DEADLINE = 3
NABUNG_SELECT = 4
NABUNG_AMOUNT = 5


async def target_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /target command - create new savings target."""
    # Check authentication
    if not context.user_data.get("is_authenticated"):
        await update.message.reply_text("🔒 Silakan /start dulu untuk login.")
        return ConversationHandler.END
    
    user = update.effective_user
    
    # Check if user exists
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text(
            "❌ Kamu belum terdaftar. Ketik /start untuk memulai."
        )
        return ConversationHandler.END

    
    context.user_data["db_user"] = db_user
    
    await update.message.reply_text(
        "🎯 *Buat Target Tabungan Baru*\n\n"
        "Apa nama target kamu?\n\n"
        "_Contoh: iPhone 16, Liburan Bali, Dana Darurat_",
        parse_mode="Markdown"
    )
    return TARGET_NAME


async def target_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target name input."""
    name = update.message.text.strip()
    
    if len(name) > 100:
        await update.message.reply_text(
            "❌ Nama terlalu panjang (max 100 karakter)"
        )
        return TARGET_NAME
    
    if len(name) < 2:
        await update.message.reply_text(
            "❌ Nama terlalu pendek (min 2 karakter)"
        )
        return TARGET_NAME
    
    context.user_data["target_name"] = name
    
    await update.message.reply_text(
        f"🎯 *Target:* {name}\n\n"
        "💰 Berapa nominal yang ingin ditabung?\n\n"
        "_Contoh: 5000000, 5jt, 5juta_",
        parse_mode="Markdown"
    )
    return TARGET_AMOUNT


async def target_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target amount input."""
    text = update.message.text.strip()
    amount = parse_amount(text)
    
    if not amount or amount <= 0:
        await update.message.reply_text(
            "❌ Nominal tidak valid\n\n"
            "Contoh: 5000000, 5jt, 5juta"
        )
        return TARGET_AMOUNT
    
    context.user_data["target_amount"] = amount
    
    name = context.user_data.get("target_name", "")
    
    await update.message.reply_text(
        f"🎯 *Target:* {name}\n"
        f"💰 *Nominal:* {format_currency(amount)}\n\n"
        "📅 Dalam berapa bulan ingin tercapai?\n\n"
        "_Ketik angka bulan, contoh: 6_",
        parse_mode="Markdown"
    )
    return TARGET_DEADLINE


async def target_deadline_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deadline input and create target."""
    text = update.message.text.strip()
    
    try:
        months = int(text)
        if months <= 0 or months > 120:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Masukkan angka bulan yang valid (1-120)"
        )
        return TARGET_DEADLINE
    
    # Get data
    db_user = context.user_data.get("db_user")
    name = context.user_data.get("target_name", "")
    amount = context.user_data.get("target_amount", 0)
    
    # Calculate monthly savings needed (rounded)
    monthly = int(amount / months)
    
    # Create target
    try:
        target = await db.create_savings_target(
            user_id=db_user["id"],
            name=name,
            target_amount=amount,
            deadline_months=months
        )
        
        # Clear temp data
        context.user_data.pop("target_name", None)
        context.user_data.pop("target_amount", None)
        
        await update.message.reply_text(
            "✅ *Target Tabungan Dibuat!*\n\n"
            f"🎯 {name}\n"
            f"💰 Target: {format_currency(amount)}\n"
            f"📅 Deadline: {months} bulan\n"
            f"📊 Nabung/bulan: {format_currency(monthly)}\n\n"
            "Gunakan /nabung untuk menambah tabungan.\n"
            "Gunakan /progress untuk melihat progress.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"Error creating target: {e}")
        await update.message.reply_text("❌ Gagal membuat target. Silakan coba lagi.")
    
    return ConversationHandler.END


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /progress command - show all savings targets."""
    user = update.effective_user
    
    # Check if user exists
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text(
            "❌ Kamu belum terdaftar. Ketik /start untuk memulai."
        )
        return
    
    # Get targets
    targets = await db.get_user_savings_targets(db_user["id"])
    
    if not targets:
        await update.message.reply_text(
            "📭 Belum ada target tabungan.\n\n"
            "Ketik /target untuk membuat target baru.",
            parse_mode="Markdown"
        )
        return
    
    msg = "🎯 *Progress Tabungan*\n\n"
    
    for target in targets:
        name = target["name"]
        target_amount = target["target_amount"]
        current = target.get("current_amount", 0) or 0
        months = target["deadline_months"]
        is_completed = target.get("is_completed", False)
        
        # Calculate percentage
        percentage = (current / target_amount * 100) if target_amount > 0 else 0
        
        # Progress bar
        filled = int(percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        # Status emoji
        if is_completed or percentage >= 100:
            status = "✅"
        elif percentage >= 75:
            status = "🔥"
        elif percentage >= 50:
            status = "💪"
        else:
            status = "🎯"
        
        msg += f"{status} *{name}*\n"
        msg += f"└ [{bar}] {percentage:.1f}%\n"
        msg += f"   {format_currency(current)} / {format_currency(target_amount)}\n"
        
        if not is_completed and percentage < 100:
            remaining = target_amount - current
            monthly = int(remaining / max(months, 1))
            msg += f"   📊 Sisa: {format_currency(remaining)} ({months} bulan)\n"
        
        msg += "\n"
    
    msg += "─────────────────\n"
    msg += "💡 Ketik /nabung untuk tambah tabungan"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def nabung_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /nabung command - add to savings target."""
    user = update.effective_user
    
    # Check if user exists
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text(
            "❌ Kamu belum terdaftar. Ketik /start untuk memulai."
        )
        return ConversationHandler.END
    
    context.user_data["db_user"] = db_user
    
    # Get incomplete targets
    targets = await db.get_user_savings_targets(db_user["id"])
    incomplete = [t for t in targets if not t.get("is_completed", False) and 
                  (t.get("current_amount", 0) or 0) < t["target_amount"]]
    
    if not incomplete:
        await update.message.reply_text(
            "📭 Tidak ada target yang aktif.\n\n"
            "Ketik /target untuk membuat target baru.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    context.user_data["savings_targets"] = incomplete
    
    # Build selection keyboard
    keyboard = []
    for target in incomplete:
        current = target.get("current_amount", 0) or 0
        percentage = (current / target["target_amount"] * 100) if target["target_amount"] > 0 else 0
        
        btn_text = f"🎯 {target['name']} ({percentage:.0f}%)"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"nabung_{target['id']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("❌ Batal", callback_data="nabung_cancel")
    ])
    
    await update.message.reply_text(
        "💰 *Tambah Tabungan*\n\n"
        "Pilih target:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return NABUNG_SELECT


async def nabung_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target selection for adding savings."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "nabung_cancel":
        await query.edit_message_text("❌ Dibatalkan")
        return ConversationHandler.END
    
    target_id = int(data.replace("nabung_", ""))
    
    # Find target
    targets = context.user_data.get("savings_targets", [])
    target = next((t for t in targets if t["id"] == target_id), None)
    
    if not target:
        await query.edit_message_text("❌ Target tidak ditemukan")
        return ConversationHandler.END
    
    context.user_data["nabung_target"] = target
    
    current = target.get("current_amount", 0) or 0
    remaining = target["target_amount"] - current
    
    await query.edit_message_text(
        f"🎯 *{target['name']}*\n\n"
        f"💰 Progress: {format_currency(current)} / {format_currency(target['target_amount'])}\n"
        f"📊 Sisa: {format_currency(remaining)}\n\n"
        "Masukkan nominal yang ingin ditabung:",
        parse_mode="Markdown"
    )
    return NABUNG_AMOUNT


async def nabung_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle savings amount input."""
    text = update.message.text.strip()
    amount = parse_amount(text)
    
    if not amount or amount <= 0:
        await update.message.reply_text(
            "❌ Nominal tidak valid\n\n"
            "Contoh: 100000, 100rb, 100k"
        )
        return NABUNG_AMOUNT
    
    target = context.user_data.get("nabung_target")
    if not target:
        await update.message.reply_text("❌ Session expired. Ketik /nabung lagi.")
        return ConversationHandler.END
    
    # Update target
    current = target.get("current_amount", 0) or 0
    new_amount = current + amount
    is_completed = new_amount >= target["target_amount"]
    
    try:
        await db.update_savings_target(
            target_id=target["id"],
            data={
                "current_amount": new_amount,
                "is_completed": is_completed
            }
        )
        
        # Clear temp data
        context.user_data.pop("nabung_target", None)
        context.user_data.pop("savings_targets", None)
        
        percentage = (new_amount / target["target_amount"] * 100) if target["target_amount"] > 0 else 0
        
        if is_completed:
            msg = (
                "🎉 *SELAMAT! Target Tercapai!*\n\n"
                f"🎯 {target['name']}\n"
                f"✅ {format_currency(new_amount)} / {format_currency(target['target_amount'])}\n\n"
                "🎊 Kerja bagus! Terus semangat nabung!"
            )
        else:
            remaining = target["target_amount"] - new_amount
            msg = (
                "✅ *Tabungan Ditambahkan!*\n\n"
                f"🎯 {target['name']}\n"
                f"➕ +{format_currency(amount)}\n"
                f"💰 Progress: {format_currency(new_amount)} ({percentage:.1f}%)\n"
                f"📊 Sisa: {format_currency(remaining)}"
            )
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error updating savings: {e}")
        await update.message.reply_text("❌ Gagal menambah tabungan.")
    
    return ConversationHandler.END


async def cancel_savings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel savings operation."""
    context.user_data.pop("target_name", None)
    context.user_data.pop("target_amount", None)
    context.user_data.pop("nabung_target", None)
    context.user_data.pop("savings_targets", None)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Dibatalkan")
    else:
        await update.message.reply_text("❌ Dibatalkan")
    
    return ConversationHandler.END


# ==================== Handlers ====================

def get_savings_handler() -> ConversationHandler:
    """Get savings target conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("target", target_command),
            CommandHandler("nabung", nabung_command),
        ],
        states={
            TARGET_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, target_name_input)
            ],
            TARGET_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, target_amount_input)
            ],
            TARGET_DEADLINE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, target_deadline_input)
            ],
            NABUNG_SELECT: [
                CallbackQueryHandler(nabung_select_callback, pattern=r"^nabung_"),
            ],
            NABUNG_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, nabung_amount_input)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_savings),
            CallbackQueryHandler(cancel_savings, pattern=r"^nabung_cancel$"),
        ],
        per_user=True,
        per_chat=True,
        per_message=False,
    )


def get_progress_handler():
    """Get progress command handler."""
    return CommandHandler("progress", progress_command)
