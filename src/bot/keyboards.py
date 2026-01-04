"""
Bot Catatan Keuangan AI - Keyboard Utilities
Inline and Reply keyboard builders.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from utils.constants import BUTTONS, Category, CATEGORY_ICONS


def get_confirm_keyboard(transaction_id: str = "") -> InlineKeyboardMarkup:
    """Get confirmation keyboard for transaction preview."""
    keyboard = [
        [
            InlineKeyboardButton(BUTTONS["confirm"], callback_data=f"confirm_{transaction_id}"),
            InlineKeyboardButton(BUTTONS["edit"], callback_data=f"edit_{transaction_id}"),
        ],
        [
            InlineKeyboardButton(BUTTONS["cancel"], callback_data=f"cancel_{transaction_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_category_keyboard(selected: str = None) -> InlineKeyboardMarkup:
    """Get category selection keyboard."""
    keyboard = []
    row = []
    
    for i, category in enumerate(Category):
        icon = CATEGORY_ICONS.get(category, "📦")
        text = f"{icon} {category.value}"
        
        # Mark selected category
        if selected and category.value == selected:
            text = f"✓ {text}"
        
        row.append(InlineKeyboardButton(
            text,
            callback_data=f"category_{category.value}"
        ))
        
        # 2 buttons per row
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    # Add remaining buttons
    if row:
        keyboard.append(row)
    
    # Add cancel button
    keyboard.append([
        InlineKeyboardButton(BUTTONS["cancel"], callback_data="cancel_category")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard(prefix: str = "") -> InlineKeyboardMarkup:
    """Get simple Yes/No keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(BUTTONS["yes"], callback_data=f"{prefix}_yes"),
            InlineKeyboardButton(BUTTONS["no"], callback_data=f"{prefix}_no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_report_period_keyboard() -> InlineKeyboardMarkup:
    """Get report period selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📅 Hari Ini", callback_data="report_today"),
            InlineKeyboardButton("📆 Minggu Ini", callback_data="report_week"),
        ],
        [
            InlineKeyboardButton("📊 Bulan Ini", callback_data="report_month"),
            InlineKeyboardButton("📈 Custom", callback_data="report_custom"),
        ],
        [
            InlineKeyboardButton(BUTTONS["cancel"], callback_data="report_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get settings menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔐 Ubah PIN", callback_data="settings_pin"),
        ],
        [
            InlineKeyboardButton("🔒 Mode Aman", callback_data="settings_safe_mode"),
        ],
        [
            InlineKeyboardButton("🗑️ Auto Hapus Pesan", callback_data="settings_auto_delete"),
        ],
        [
            InlineKeyboardButton("📋 Google Sheets", callback_data="settings_sheets"),
        ],
        [
            InlineKeyboardButton(BUTTONS["back"], callback_data="settings_back"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu reply keyboard."""
    keyboard = [
        [KeyboardButton("📝 Tambah"), KeyboardButton("📋 List")],
        [KeyboardButton("📊 Laporan"), KeyboardButton("🎯 Target")],
        [KeyboardButton("💡 Insight"), KeyboardButton("⚙️ Pengaturan")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Simple back button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BUTTONS["back"], callback_data="back")]
    ])


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    prefix: str = "page"
) -> InlineKeyboardMarkup:
    """Get pagination keyboard."""
    keyboard = []
    row = []
    
    if current_page > 1:
        row.append(InlineKeyboardButton(
            "⬅️ Prev",
            callback_data=f"{prefix}_{current_page - 1}"
        ))
    
    row.append(InlineKeyboardButton(
        f"{current_page}/{total_pages}",
        callback_data="noop"
    ))
    
    if current_page < total_pages:
        row.append(InlineKeyboardButton(
            "➡️ Next",
            callback_data=f"{prefix}_{current_page + 1}"
        ))
    
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)
