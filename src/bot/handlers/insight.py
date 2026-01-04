"""
Bot Catatan Keuangan AI - Insight Handler
Handles AI-powered spending insights.
"""
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.db_service import db
from services.crypto_service import crypto
from services.ai_service import ai
from utils.constants import Category, CATEGORY_ICONS
from utils.helpers import format_currency


async def insight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /insight command - generate AI spending insight."""
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

    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🤖 *Menganalisis pengeluaran...*",
        parse_mode="Markdown"
    )
    
    try:
        # Get this month's transactions
        today = datetime.now()
        start_of_month = today.replace(day=1)
        
        transactions = await db.get_user_transactions(
            user_id=db_user["id"],
            start_date=start_of_month.date(),
            end_date=today.date(),
            limit=500
        )
        
        if not transactions:
            await processing_msg.edit_text(
                "📭 Belum ada transaksi bulan ini.\n\n"
                "Insight akan tersedia setelah kamu mulai mencatat transaksi."
            )
            return
        
        # Calculate spending breakdown
        total = 0
        by_category = {}
        
        for tx in transactions:
            amount = crypto.decrypt_amount(tx["amount_encrypted"])
            total += amount
            
            category = tx.get("category", "Lainnya")
            by_category[category] = by_category.get(category, 0) + amount
        
        # Get previous month for comparison
        prev_month_end = start_of_month - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        
        prev_transactions = await db.get_user_transactions(
            user_id=db_user["id"],
            start_date=prev_month_start.date(),
            end_date=prev_month_end.date(),
            limit=500
        )
        
        prev_total = 0
        for tx in prev_transactions:
            prev_total += crypto.decrypt_amount(tx["amount_encrypted"])
        
        # Build spending data for AI
        spending_data = {
            "total": total,
            "by_category": by_category,
            "transaction_count": len(transactions),
            "comparison": {
                "current": total,
                "previous": prev_total
            }
        }
        
        # Generate AI insight
        insight = await ai.generate_insight(spending_data, "bulanan")
        
        # Build message with stats
        msg = f"🤖 *AI Insight - {today.strftime('%B %Y')}*\n\n"
        
        # Quick stats
        msg += f"💰 Total Pengeluaran: {format_currency(total)}\n"
        msg += f"📝 Jumlah Transaksi: {len(transactions)}\n"
        
        if prev_total > 0:
            change = ((total - prev_total) / prev_total) * 100
            if change > 0:
                msg += f"📈 vs bulan lalu: +{change:.1f}%\n"
            else:
                msg += f"📉 vs bulan lalu: {change:.1f}%\n"
        
        msg += "\n"
        
        # Top categories
        msg += "*📊 Top Kategori:*\n"
        sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, amount in sorted_cats:
            try:
                cat_enum = Category(cat)
                icon = CATEGORY_ICONS.get(cat_enum, "📦")
            except:
                icon = "📦"
            pct = (amount / total * 100) if total > 0 else 0
            msg += f"{icon} {cat}: {format_currency(amount)} ({pct:.0f}%)\n"
        
        msg += "\n─────────────────\n\n"
        
        # AI insight
        msg += f"*💡 Insight:*\n{insight}"
        
        await processing_msg.edit_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error generating insight: {e}")
        
        # Fallback without AI
        await processing_msg.edit_text(
            "⚠️ *AI tidak tersedia saat ini*\n\n"
            "Gunakan /laporan\\_bulan untuk melihat ringkasan pengeluaran.",
            parse_mode="Markdown"
        )


def get_insight_handlers():
    """Get insight command handler."""
    return [CommandHandler("insight", insight_command)]
