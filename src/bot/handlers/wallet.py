"""
Bot Catatan Keuangan AI - Wallet Handler
Handles wallet/account management with PIN protection.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from database.db_service import db
from services.crypto_service import crypto
from utils.constants import (
    MESSAGES, BUTTONS, WalletType, WALLET_PRESETS, WALLET_TYPE_ICONS
)
from utils.helpers import format_currency, parse_amount


# Conversation states
VERIFY_PIN = 1
MENU = 2
SELECT_TYPE = 3
SELECT_WALLET_NAME = 4
ENTER_BALANCE = 5
TOPUP_SELECT_WALLET = 6
TOPUP_ENTER_AMOUNT = 7
TRANSFER_FROM = 8
TRANSFER_TO = 9
TRANSFER_AMOUNT = 10


async def verify_pin_for_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE, next_action: str):
    """Request PIN verification before wallet operations."""
    context.user_data["wallet_next_action"] = next_action
    await update.message.reply_text(MESSAGES["pin_required"])
    return VERIFY_PIN


async def handle_pin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PIN input for wallet operations."""
    pin = update.message.text.strip()
    user = update.effective_user
    
    # Delete PIN message
    try:
        await update.message.delete()
    except Exception:
        pass
    
    # Verify PIN
    db_user = await db.get_user(user.id)
    if not db_user:
        await update.message.reply_text("❌ User tidak ditemukan.")
        return ConversationHandler.END
    
    if not crypto.verify_pin(pin, db_user["pin_hash"]):
        await update.message.reply_text(MESSAGES["pin_wrong"])
        return VERIFY_PIN
    
    # PIN verified, execute next action
    next_action = context.user_data.get("wallet_next_action", "menu")
    context.user_data["pin_verified"] = True
    context.user_data["db_user"] = db_user
    
    if next_action == "saldo":
        return await show_saldo(update, context)
    elif next_action == "topup":
        return await start_topup_message(update, context)
    elif next_action == "transfer":
        return await start_transfer_message(update, context)
    elif next_action == "menu":
        return await show_wallet_menu_message(update, context)
    
    return ConversationHandler.END


# ==================== /dompet Command ====================

async def dompet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dompet command - wallet management menu."""
    return await verify_pin_for_wallet(update, context, "menu")


async def show_wallet_menu_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallet management menu via message."""
    keyboard = [
        [
            InlineKeyboardButton(BUTTONS["add_wallet"], callback_data="wallet_add"),
            InlineKeyboardButton(BUTTONS["view_wallets"], callback_data="wallet_list"),
        ],
        [
            InlineKeyboardButton(BUTTONS["topup"], callback_data="wallet_topup_start"),
            InlineKeyboardButton(BUTTONS["transfer"], callback_data="wallet_transfer_start"),
        ],
        [
            InlineKeyboardButton(BUTTONS["cancel"], callback_data="wallet_cancel"),
        ]
    ]
    
    await update.message.reply_text(
        MESSAGES["wallet_menu"],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MENU


# ==================== /saldo Command ====================

async def saldo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /saldo command - show all balances."""
    return await verify_pin_for_wallet(update, context, "saldo")


async def show_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all wallet balances."""
    db_user = context.user_data.get("db_user")
    if not db_user:
        db_user = await db.get_user(update.effective_user.id)
    
    wallets = await db.get_user_wallets(db_user["id"])
    
    if not wallets:
        await update.message.reply_text(MESSAGES["wallet_empty"])
        return ConversationHandler.END
    
    # Group by type
    ewallet_list = []
    bank_list = []
    cash_list = []
    total = 0
    
    for wallet in wallets:
        balance = crypto.decrypt_amount(wallet["balance_encrypted"])
        total += balance
        
        icon = wallet.get("icon", "💰")
        line = f"├ {icon} {wallet['name']}: {format_currency(balance)}"
        
        if wallet["type"] == WalletType.EWALLET.value:
            ewallet_list.append(line)
        elif wallet["type"] == WalletType.BANK.value:
            bank_list.append(line)
        else:
            cash_list.append(line)
    
    # Build message
    msg = "💰 *Laporan Saldo*\n\n"
    
    if ewallet_list:
        msg += "📱 *E-Wallet*\n"
        for line in ewallet_list[:-1]:
            msg += line + "\n"
        if ewallet_list:
            msg += ewallet_list[-1].replace("├", "└") + "\n"
        msg += "\n"
    
    if bank_list:
        msg += "🏦 *Bank*\n"
        for line in bank_list[:-1]:
            msg += line + "\n"
        if bank_list:
            msg += bank_list[-1].replace("├", "└") + "\n"
        msg += "\n"
    
    if cash_list:
        msg += "💵 *Cash*\n"
        for line in cash_list[:-1]:
            msg += line + "\n"
        if cash_list:
            msg += cash_list[-1].replace("├", "└") + "\n"
        msg += "\n"
    
    msg += "─────────────────\n"
    msg += f"💎 *Total Aset:* {format_currency(total)}"
    
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ConversationHandler.END


# ==================== Add Wallet Flow ====================

async def wallet_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add wallet flow."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton(BUTTONS["ewallet"], callback_data="wtype_ewallet"),
            InlineKeyboardButton(BUTTONS["bank"], callback_data="wtype_bank"),
        ],
        [
            InlineKeyboardButton(BUTTONS["cash"], callback_data="wtype_cash"),
        ],
        [
            InlineKeyboardButton(BUTTONS["back"], callback_data="wallet_back_menu"),
        ]
    ]
    
    await query.edit_message_text(
        "📱 *Pilih Jenis Akun*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_TYPE


async def wallet_back_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to wallet menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton(BUTTONS["add_wallet"], callback_data="wallet_add"),
            InlineKeyboardButton(BUTTONS["view_wallets"], callback_data="wallet_list"),
        ],
        [
            InlineKeyboardButton(BUTTONS["topup"], callback_data="wallet_topup_start"),
            InlineKeyboardButton(BUTTONS["transfer"], callback_data="wallet_transfer_start"),
        ],
        [
            InlineKeyboardButton(BUTTONS["cancel"], callback_data="wallet_cancel"),
        ]
    ]
    
    await query.edit_message_text(
        MESSAGES["wallet_menu"],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MENU


async def wallet_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet type selection."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    wallet_type = data.replace("wtype_", "")
    context.user_data["new_wallet_type"] = wallet_type
    
    # Get presets for this type
    try:
        type_enum = WalletType(wallet_type)
        presets = WALLET_PRESETS.get(type_enum, [])
    except ValueError:
        presets = []
    
    if not presets:
        await query.edit_message_text("❌ Tipe tidak valid")
        return ConversationHandler.END
    
    # Build keyboard with preset options
    keyboard = []
    row = []
    for preset in presets:
        btn = InlineKeyboardButton(
            f"{preset['icon']} {preset['name']}",
            callback_data=f"wname_{preset['name']}_{preset['icon']}"
        )
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Add custom option
    keyboard.append([
        InlineKeyboardButton("✏️ Nama Lain", callback_data="wname_custom"),
    ])
    keyboard.append([
        InlineKeyboardButton(BUTTONS["back"], callback_data="wallet_add"),
    ])
    
    type_icon = WALLET_TYPE_ICONS.get(type_enum, "💰")
    await query.edit_message_text(
        f"{type_icon} *Pilih {type_enum.value.title()}*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_WALLET_NAME


async def wallet_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet name selection."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "wname_custom":
        await query.edit_message_text(
            "✏️ Ketik nama akun yang diinginkan:",
            parse_mode="Markdown"
        )
        return SELECT_WALLET_NAME  # Will handle text input
    
    # Parse preset: wname_Dana_🔵
    parts = data.replace("wname_", "").rsplit("_", 1)
    if len(parts) == 2:
        name, icon = parts
    else:
        name = parts[0]
        icon = "💰"
    
    context.user_data["new_wallet_name"] = name
    context.user_data["new_wallet_icon"] = icon
    
    await query.edit_message_text(
        f"{icon} *{name}*\n\n💰 Masukkan saldo awal:",
        parse_mode="Markdown"
    )
    return ENTER_BALANCE


async def wallet_name_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom wallet name input."""
    name = update.message.text.strip()
    
    if len(name) > 50:
        await update.message.reply_text("❌ Nama terlalu panjang (max 50 karakter)")
        return SELECT_WALLET_NAME
    
    context.user_data["new_wallet_name"] = name
    context.user_data["new_wallet_icon"] = "💰"
    
    await update.message.reply_text(
        f"💰 *{name}*\n\nMasukkan saldo awal:",
        parse_mode="Markdown"
    )
    return ENTER_BALANCE


async def wallet_balance_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle initial balance input."""
    text = update.message.text.strip()
    balance = parse_amount(text)
    
    if balance is None or balance < 0:
        await update.message.reply_text(
            "❌ Nominal tidak valid\n\nContoh: 500000, 500rb, 500k"
        )
        return ENTER_BALANCE
    
    # Get user
    db_user = context.user_data.get("db_user")
    if not db_user:
        db_user = await db.get_user(update.effective_user.id)
    
    # Create wallet
    name = context.user_data.get("new_wallet_name", "Unknown")
    icon = context.user_data.get("new_wallet_icon", "💰")
    wallet_type = context.user_data.get("new_wallet_type", "cash")
    
    try:
        balance_encrypted = crypto.encrypt_amount(balance)
        
        wallet = await db.create_wallet(
            user_id=db_user["id"],
            name=name,
            wallet_type=wallet_type,
            balance_encrypted=balance_encrypted,
            icon=icon,
            is_default=False
        )
        
        # Log initial balance
        await db.update_wallet_balance(
            wallet_id=wallet["id"],
            new_balance_encrypted=balance_encrypted,
            old_balance_encrypted=crypto.encrypt_amount(0),
            amount_encrypted=balance_encrypted,
            log_type="initial",
            note="Saldo awal"
        )
        
        # Clear temp data
        context.user_data.pop("new_wallet_name", None)
        context.user_data.pop("new_wallet_icon", None)
        context.user_data.pop("new_wallet_type", None)
        
        await update.message.reply_text(
            MESSAGES["wallet_added"].format(
                icon=icon,
                name=name,
                balance=balance
            ),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"Error creating wallet: {e}")
        await update.message.reply_text(MESSAGES["error_generic"])
    
    return ConversationHandler.END


# ==================== /topup Command ====================

async def topup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /topup command."""
    return await verify_pin_for_wallet(update, context, "topup")


async def start_topup_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start topup flow from message."""
    db_user = context.user_data.get("db_user")
    if not db_user:
        db_user = await db.get_user(update.effective_user.id)
    
    wallets = await db.get_user_wallets(db_user["id"])
    
    if not wallets:
        await update.message.reply_text(MESSAGES["wallet_empty"])
        return ConversationHandler.END
    
    # Build wallet selection keyboard
    keyboard = []
    for wallet in wallets:
        balance = crypto.decrypt_amount(wallet["balance_encrypted"])
        icon = wallet.get("icon", "💰")
        btn_text = f"{icon} {wallet['name']} ({format_currency(balance)})"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"topup_{wallet['id']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(BUTTONS["cancel"], callback_data="wallet_cancel")
    ])
    
    await update.message.reply_text(
        "💰 *Top Up Saldo*\n\nPilih akun:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TOPUP_SELECT_WALLET


async def start_topup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start topup flow from callback."""
    query = update.callback_query
    await query.answer()
    
    db_user = context.user_data.get("db_user")
    if not db_user:
        db_user = await db.get_user(update.effective_user.id)
        context.user_data["db_user"] = db_user
    
    wallets = await db.get_user_wallets(db_user["id"])
    
    if not wallets:
        await query.edit_message_text(MESSAGES["wallet_empty"])
        return ConversationHandler.END
    
    # Build wallet selection keyboard
    keyboard = []
    for wallet in wallets:
        balance = crypto.decrypt_amount(wallet["balance_encrypted"])
        icon = wallet.get("icon", "💰")
        btn_text = f"{icon} {wallet['name']} ({format_currency(balance)})"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"topup_{wallet['id']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(BUTTONS["back"], callback_data="wallet_back_menu")
    ])
    
    await query.edit_message_text(
        "💰 *Top Up Saldo*\n\nPilih akun:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TOPUP_SELECT_WALLET


async def topup_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle topup wallet selection."""
    query = update.callback_query
    await query.answer()
    
    wallet_id = int(query.data.replace("topup_", ""))
    context.user_data["topup_wallet_id"] = wallet_id
    
    wallet = await db.get_wallet(wallet_id)
    if not wallet:
        await query.edit_message_text("❌ Akun tidak ditemukan")
        return ConversationHandler.END
    
    context.user_data["topup_wallet"] = wallet
    
    await query.edit_message_text(
        f"💰 *Top Up {wallet['icon']} {wallet['name']}*\n\n"
        f"Masukkan nominal top up:",
        parse_mode="Markdown"
    )
    return TOPUP_ENTER_AMOUNT


async def topup_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle topup amount input."""
    text = update.message.text.strip()
    amount = parse_amount(text)
    
    if amount is None or amount <= 0:
        await update.message.reply_text(
            "❌ Nominal tidak valid\n\nContoh: 100000, 100rb, 100k"
        )
        return TOPUP_ENTER_AMOUNT
    
    wallet = context.user_data.get("topup_wallet")
    if not wallet:
        await update.message.reply_text(MESSAGES["error_generic"])
        return ConversationHandler.END
    
    # Calculate new balance
    old_balance = crypto.decrypt_amount(wallet["balance_encrypted"])
    new_balance = old_balance + amount
    
    # Update balance
    await db.update_wallet_balance(
        wallet_id=wallet["id"],
        new_balance_encrypted=crypto.encrypt_amount(new_balance),
        old_balance_encrypted=wallet["balance_encrypted"],
        amount_encrypted=crypto.encrypt_amount(amount),
        log_type="topup",
        note=f"Top up +{format_currency(amount)}"
    )
    
    await update.message.reply_text(
        MESSAGES["wallet_topup_success"].format(
            icon=wallet["icon"],
            name=wallet["name"],
            old_balance=old_balance,
            new_balance=new_balance,
            amount=amount
        ),
        parse_mode="Markdown"
    )
    
    # Clear temp data
    context.user_data.pop("topup_wallet_id", None)
    context.user_data.pop("topup_wallet", None)
    
    return ConversationHandler.END


# ==================== /transfer Command ====================

async def transfer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /transfer command."""
    return await verify_pin_for_wallet(update, context, "transfer")


async def start_transfer_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start transfer flow from message."""
    db_user = context.user_data.get("db_user")
    if not db_user:
        db_user = await db.get_user(update.effective_user.id)
    
    wallets = await db.get_user_wallets(db_user["id"])
    
    if len(wallets) < 2:
        await update.message.reply_text(
            "❌ Butuh minimal 2 akun untuk transfer.\n\n"
            "Ketik /dompet untuk menambah akun."
        )
        return ConversationHandler.END
    
    context.user_data["transfer_wallets"] = wallets
    
    # Build wallet selection keyboard
    keyboard = []
    for wallet in wallets:
        balance = crypto.decrypt_amount(wallet["balance_encrypted"])
        icon = wallet.get("icon", "💰")
        btn_text = f"{icon} {wallet['name']} ({format_currency(balance)})"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"tfrom_{wallet['id']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(BUTTONS["cancel"], callback_data="wallet_cancel")
    ])
    
    await update.message.reply_text(
        "🔄 *Transfer Antar Akun*\n\n📤 Transfer dari:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TRANSFER_FROM


async def start_transfer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start transfer flow from callback."""
    query = update.callback_query
    await query.answer()
    
    db_user = context.user_data.get("db_user")
    if not db_user:
        db_user = await db.get_user(update.effective_user.id)
        context.user_data["db_user"] = db_user
    
    wallets = await db.get_user_wallets(db_user["id"])
    
    if len(wallets) < 2:
        await query.edit_message_text(
            "❌ Butuh minimal 2 akun untuk transfer.\n\n"
            "Ketik /dompet untuk menambah akun."
        )
        return ConversationHandler.END
    
    context.user_data["transfer_wallets"] = wallets
    
    # Build wallet selection keyboard
    keyboard = []
    for wallet in wallets:
        balance = crypto.decrypt_amount(wallet["balance_encrypted"])
        icon = wallet.get("icon", "💰")
        btn_text = f"{icon} {wallet['name']} ({format_currency(balance)})"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"tfrom_{wallet['id']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(BUTTONS["back"], callback_data="wallet_back_menu")
    ])
    
    await query.edit_message_text(
        "🔄 *Transfer Antar Akun*\n\n📤 Transfer dari:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TRANSFER_FROM


async def transfer_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transfer from wallet selection."""
    query = update.callback_query
    await query.answer()
    
    wallet_id = int(query.data.replace("tfrom_", ""))
    wallet = await db.get_wallet(wallet_id)
    
    if not wallet:
        await query.edit_message_text("❌ Akun tidak ditemukan")
        return ConversationHandler.END
    
    context.user_data["transfer_from"] = wallet
    
    # Show other wallets for destination
    wallets = context.user_data.get("transfer_wallets", [])
    keyboard = []
    
    for w in wallets:
        if w["id"] != wallet_id:
            balance = crypto.decrypt_amount(w["balance_encrypted"])
            icon = w.get("icon", "💰")
            btn_text = f"{icon} {w['name']} ({format_currency(balance)})"
            keyboard.append([
                InlineKeyboardButton(btn_text, callback_data=f"tto_{w['id']}")
            ])
    
    keyboard.append([
        InlineKeyboardButton(BUTTONS["back"], callback_data="wallet_transfer_start")
    ])
    
    await query.edit_message_text(
        f"🔄 *Transfer*\n\n"
        f"📤 Dari: {wallet['icon']} {wallet['name']}\n\n"
        f"📥 Transfer ke:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TRANSFER_TO


async def transfer_to_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transfer to wallet selection."""
    query = update.callback_query
    await query.answer()
    
    wallet_id = int(query.data.replace("tto_", ""))
    wallet = await db.get_wallet(wallet_id)
    
    if not wallet:
        await query.edit_message_text("❌ Akun tidak ditemukan")
        return ConversationHandler.END
    
    context.user_data["transfer_to"] = wallet
    
    from_wallet = context.user_data.get("transfer_from")
    from_balance = crypto.decrypt_amount(from_wallet["balance_encrypted"])
    
    await query.edit_message_text(
        f"🔄 *Transfer*\n\n"
        f"📤 Dari: {from_wallet['icon']} {from_wallet['name']}\n"
        f"📥 Ke: {wallet['icon']} {wallet['name']}\n"
        f"💰 Saldo tersedia: {format_currency(from_balance)}\n\n"
        f"Masukkan nominal transfer:",
        parse_mode="Markdown"
    )
    return TRANSFER_AMOUNT


async def transfer_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transfer amount input."""
    text = update.message.text.strip()
    amount = parse_amount(text)
    
    if amount is None or amount <= 0:
        await update.message.reply_text(
            "❌ Nominal tidak valid\n\nContoh: 100000, 100rb, 100k"
        )
        return TRANSFER_AMOUNT
    
    from_wallet = context.user_data.get("transfer_from")
    to_wallet = context.user_data.get("transfer_to")
    
    if not from_wallet or not to_wallet:
        await update.message.reply_text(MESSAGES["error_generic"])
        return ConversationHandler.END
    
    from_balance = crypto.decrypt_amount(from_wallet["balance_encrypted"])
    
    # Check sufficient balance
    if amount > from_balance:
        await update.message.reply_text(
            MESSAGES["wallet_insufficient"].format(
                name=from_wallet["name"],
                balance=from_balance
            )
        )
        return TRANSFER_AMOUNT
    
    # Execute transfer
    to_balance = crypto.decrypt_amount(to_wallet["balance_encrypted"])
    
    new_from_balance = from_balance - amount
    new_to_balance = to_balance + amount
    
    # Update from wallet
    await db.update_wallet_balance(
        wallet_id=from_wallet["id"],
        new_balance_encrypted=crypto.encrypt_amount(new_from_balance),
        old_balance_encrypted=from_wallet["balance_encrypted"],
        amount_encrypted=crypto.encrypt_amount(amount),
        log_type="transfer_out",
        note=f"Transfer ke {to_wallet['name']}"
    )
    
    # Update to wallet
    await db.update_wallet_balance(
        wallet_id=to_wallet["id"],
        new_balance_encrypted=crypto.encrypt_amount(new_to_balance),
        old_balance_encrypted=to_wallet["balance_encrypted"],
        amount_encrypted=crypto.encrypt_amount(amount),
        log_type="transfer_in",
        note=f"Transfer dari {from_wallet['name']}"
    )
    
    await update.message.reply_text(
        MESSAGES["wallet_transfer_success"].format(
            from_icon=from_wallet["icon"],
            from_name=from_wallet["name"],
            from_old=from_balance,
            from_new=new_from_balance,
            to_icon=to_wallet["icon"],
            to_name=to_wallet["name"],
            to_old=to_balance,
            to_new=new_to_balance,
            amount=amount
        ),
        parse_mode="Markdown"
    )
    
    # Clear temp data
    context.user_data.pop("transfer_from", None)
    context.user_data.pop("transfer_to", None)
    context.user_data.pop("transfer_wallets", None)
    
    return ConversationHandler.END


# ==================== Cancel & Callbacks ====================

async def wallet_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel wallet operation."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Dibatalkan")
    return ConversationHandler.END


async def wallet_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallet list from menu."""
    query = update.callback_query
    await query.answer()
    
    db_user = context.user_data.get("db_user")
    if not db_user:
        db_user = await db.get_user(update.effective_user.id)
    
    wallets = await db.get_user_wallets(db_user["id"])
    
    if not wallets:
        await query.edit_message_text(MESSAGES["wallet_empty"])
        return ConversationHandler.END
    
    # Build list
    wallet_lines = []
    total = 0
    
    for wallet in wallets:
        balance = crypto.decrypt_amount(wallet["balance_encrypted"])
        total += balance
        icon = wallet.get("icon", "💰")
        wallet_lines.append(f"{icon} {wallet['name']}: {format_currency(balance)}")
    
    msg = MESSAGES["wallet_list"].format(
        wallet_list="\n".join(wallet_lines),
        total=total
    )
    
    # Add back button
    keyboard = [[
        InlineKeyboardButton(BUTTONS["back"], callback_data="wallet_back_menu")
    ]]
    
    await query.edit_message_text(
        msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MENU


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation."""
    context.user_data.clear()
    await update.message.reply_text("❌ Operasi dibatalkan")
    return ConversationHandler.END


# ==================== Handlers ====================

def get_wallet_handler() -> ConversationHandler:
    """Get wallet conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("dompet", dompet_command),
            CommandHandler("saldo", saldo_command),
            CommandHandler("topup", topup_command),
            CommandHandler("transfer", transfer_command),
        ],
        states={
            VERIFY_PIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pin_input)
            ],
            MENU: [
                CallbackQueryHandler(wallet_add_callback, pattern=r"^wallet_add$"),
                CallbackQueryHandler(wallet_list_callback, pattern=r"^wallet_list$"),
                CallbackQueryHandler(start_topup_callback, pattern=r"^wallet_topup_start$"),
                CallbackQueryHandler(start_transfer_callback, pattern=r"^wallet_transfer_start$"),
                CallbackQueryHandler(wallet_back_menu_callback, pattern=r"^wallet_back_menu$"),
                CallbackQueryHandler(wallet_cancel_callback, pattern=r"^wallet_cancel$"),
            ],
            SELECT_TYPE: [
                CallbackQueryHandler(wallet_type_callback, pattern=r"^wtype_"),
                CallbackQueryHandler(wallet_add_callback, pattern=r"^wallet_add$"),
                CallbackQueryHandler(wallet_back_menu_callback, pattern=r"^wallet_back_menu$"),
                CallbackQueryHandler(wallet_cancel_callback, pattern=r"^wallet_cancel$"),
            ],
            SELECT_WALLET_NAME: [
                CallbackQueryHandler(wallet_name_callback, pattern=r"^wname_"),
                CallbackQueryHandler(wallet_add_callback, pattern=r"^wallet_add$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_name_text),
            ],
            ENTER_BALANCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_balance_input),
            ],
            TOPUP_SELECT_WALLET: [
                CallbackQueryHandler(topup_select_callback, pattern=r"^topup_\d+$"),
                CallbackQueryHandler(wallet_back_menu_callback, pattern=r"^wallet_back_menu$"),
                CallbackQueryHandler(wallet_cancel_callback, pattern=r"^wallet_cancel$"),
            ],
            TOPUP_ENTER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, topup_amount_input),
            ],
            TRANSFER_FROM: [
                CallbackQueryHandler(transfer_from_callback, pattern=r"^tfrom_\d+$"),
                CallbackQueryHandler(wallet_back_menu_callback, pattern=r"^wallet_back_menu$"),
                CallbackQueryHandler(wallet_cancel_callback, pattern=r"^wallet_cancel$"),
            ],
            TRANSFER_TO: [
                CallbackQueryHandler(transfer_to_callback, pattern=r"^tto_\d+$"),
                CallbackQueryHandler(start_transfer_callback, pattern=r"^wallet_transfer_start$"),
            ],
            TRANSFER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_amount_input),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(wallet_cancel_callback, pattern=r"^wallet_cancel$"),
        ],
        per_user=True,
        per_chat=True,
        per_message=False,
    )


def get_wallet_menu_handlers():
    """Get handlers for wallet menu callbacks (not used anymore)."""
    return []
