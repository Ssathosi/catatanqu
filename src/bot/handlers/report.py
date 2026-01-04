"""
Bot Catatan Keuangan AI - Report Handler
Handles financial reports and summaries.
"""
from datetime import datetime, date, timedelta
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from database.db_service import db
from services.crypto_service import crypto
from utils.constants import MESSAGES, CATEGORY_ICONS, Category
from utils.helpers import format_currency, format_date
from bot.keyboards import get_report_period_keyboard


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /laporan command - daily report."""
    await _generate_report(update, context, "today")


async def report_week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /laporan_minggu command - weekly report."""
    await _generate_report(update, context, "week")


async def report_month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /laporan_bulan command - monthly report."""
    await _generate_report(update, context, "month")


async def category_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /kategori command - category breakdown."""
    # Check authentication
    if not context.user_data.get("is_authenticated"):
        await update.message.reply_text("🔒 Silakan /start dulu untuk login.")
        return
    
    user = update.effective_user
    
    # Check if user exists
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text(
            "❌ Kamu belum terdaftar. Ketik /start untuk memulai."
        )
        return

    
    # Get this month's transactions
    today = date.today()
    start_of_month = today.replace(day=1)
    
    transactions = await db.get_user_transactions(
        user_id=db_user["id"],
        start_date=start_of_month,
        end_date=today,
        limit=500
    )
    
    if not transactions:
        await update.message.reply_text(MESSAGES["report_empty"])
        return
    
    # Calculate totals by category
    category_totals = {}
    grand_total = 0
    
    for tx in transactions:
        amount = crypto.decrypt_amount(tx["amount_encrypted"])
        category = tx["category"]
        
        if category not in category_totals:
            category_totals[category] = 0
        category_totals[category] += amount
        grand_total += amount
    
    # Sort by amount descending
    sorted_categories = sorted(
        category_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Build message
    msg = f"📊 *Breakdown Kategori*\n"
    msg += f"📅 {start_of_month.strftime('%d/%m')} - {today.strftime('%d/%m/%Y')}\n\n"
    
    for category, total in sorted_categories:
        try:
            cat_enum = Category(category)
            icon = CATEGORY_ICONS.get(cat_enum, "📦")
        except ValueError:
            icon = "📦"
        
        percentage = (total / grand_total * 100) if grand_total > 0 else 0
        bar = _generate_bar(percentage)
        
        msg += f"{icon} *{category}*\n"
        msg += f"   {format_currency(total)} ({percentage:.1f}%)\n"
        msg += f"   {bar}\n\n"
    
    msg += f"─────────────────\n"
    msg += f"💵 *Total:* {format_currency(grand_total)}"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def _generate_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    period: str
):
    """Generate report for specified period."""
    # Check authentication
    if not context.user_data.get("is_authenticated"):
        await update.message.reply_text("🔒 Silakan /start dulu untuk login.")
        return
    
    user = update.effective_user
    
    # Check if user exists
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text(
            "❌ Kamu belum terdaftar. Ketik /start untuk memulai."
        )
        return

    
    # Calculate date range
    today = date.today()
    
    if period == "today":
        start_date = today
        end_date = today
        period_label = f"Hari Ini ({format_date(datetime.now(), 'long')})"
    elif period == "week":
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date = today
        period_label = f"Minggu Ini ({start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')})"
    elif period == "month":
        start_date = today.replace(day=1)
        end_date = today
        period_label = f"Bulan Ini ({start_date.strftime('%B %Y')})"
    else:
        start_date = today
        end_date = today
        period_label = "Hari Ini"
    
    # Get transactions
    transactions = await db.get_user_transactions(
        user_id=db_user["id"],
        start_date=start_date,
        end_date=end_date,
        limit=500
    )
    
    if not transactions:
        await update.message.reply_text(MESSAGES["report_empty"])
        return
    
    # Calculate statistics
    total = 0
    category_totals = {}
    
    for tx in transactions:
        amount = crypto.decrypt_amount(tx["amount_encrypted"])
        total += amount
        
        category = tx["category"]
        if category not in category_totals:
            category_totals[category] = 0
        category_totals[category] += amount
    
    # Build breakdown string
    sorted_categories = sorted(
        category_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]  # Top 5 categories
    
    breakdown = ""
    for category, cat_total in sorted_categories:
        try:
            cat_enum = Category(category)
            icon = CATEGORY_ICONS.get(cat_enum, "📦")
        except ValueError:
            icon = "📦"
        
        percentage = (cat_total / total * 100) if total > 0 else 0
        breakdown += f"  {icon} {category}: {format_currency(cat_total)} ({percentage:.1f}%)\n"
    
    # Build report message
    msg = f"📊 *Laporan {period_label}*\n\n"
    msg += f"💰 *Total Pengeluaran:* {format_currency(total)}\n"
    msg += f"📝 *Jumlah Transaksi:* {len(transactions)}\n\n"
    msg += f"*Top Kategori:*\n{breakdown}"
    
    # Add comparison with previous period (if applicable)
    if period in ["week", "month"]:
        if period == "week":
            prev_start = start_date - timedelta(days=7)
            prev_end = start_date - timedelta(days=1)
        else:
            # Previous month
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end.replace(day=1)
        
        prev_transactions = await db.get_user_transactions(
            user_id=db_user["id"],
            start_date=prev_start,
            end_date=prev_end,
            limit=500
        )
        
        prev_total = sum(
            crypto.decrypt_amount(tx["amount_encrypted"])
            for tx in prev_transactions
        )
        
        if prev_total > 0:
            change = ((total - prev_total) / prev_total) * 100
            change_icon = "📈" if change > 0 else "📉"
            change_text = f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"
            
            msg += f"\n*Dibanding periode lalu:*\n"
            msg += f"  {change_icon} {change_text} ({format_currency(abs(total - prev_total))})"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


def _generate_bar(percentage: float, width: int = 10) -> str:
    """Generate visual percentage bar."""
    filled = int(percentage / 100 * width)
    empty = width - filled
    return "█" * filled + "░" * empty


async def report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report period selection callback."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "report_cancel":
        await query.edit_message_text("❌ Dibatalkan")
        return
    
    # Map callback to period
    period_map = {
        "report_today": "today",
        "report_week": "week",
        "report_month": "month",
    }
    
    if data in period_map:
        # Create a fake update with the query message
        await query.edit_message_text("⏳ Menghasilkan laporan...")
        await _generate_report(query, context, period_map[data])


# Export handlers
def get_report_handlers():
    """Get all report-related handlers."""
    return [
        CommandHandler("laporan", report_command),
        CommandHandler("laporan_minggu", report_week_command),
        CommandHandler("laporan_bulan", report_month_command),
        CommandHandler("kategori", category_report_command),
        CallbackQueryHandler(report_callback, pattern=r"^report_"),
    ]
