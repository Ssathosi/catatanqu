"""
Bot Catatan Keuangan AI - Constants
"""
from enum import Enum


class InputSource(str, Enum):
    """Source of transaction input."""
    TEXT = "text"
    VOICE = "voice"
    RECEIPT = "receipt"


class Category(str, Enum):
    """Default transaction categories."""
    MAKAN = "Makan"
    TRANSPORT = "Transport"
    BELANJA = "Belanja"
    HIBURAN = "Hiburan"
    TAGIHAN = "Tagihan"
    KESEHATAN = "Kesehatan"
    PENDIDIKAN = "Pendidikan"
    LAINNYA = "Lainnya"


class WalletType(str, Enum):
    """Types of wallets/accounts."""
    EWALLET = "ewallet"
    BANK = "bank"
    CASH = "cash"


# Category icons mapping
CATEGORY_ICONS = {
    Category.MAKAN: "🍔",
    Category.TRANSPORT: "🚗",
    Category.BELANJA: "🛒",
    Category.HIBURAN: "🎮",
    Category.TAGIHAN: "📄",
    Category.KESEHATAN: "💊",
    Category.PENDIDIKAN: "📚",
    Category.LAINNYA: "📦",
}


# Wallet type icons
WALLET_TYPE_ICONS = {
    WalletType.EWALLET: "📱",
    WalletType.BANK: "🏦",
    WalletType.CASH: "💵",
}


# Wallet presets
WALLET_PRESETS = {
    WalletType.EWALLET: [
        {"name": "GoPay", "icon": "🟢"},
        {"name": "Dana", "icon": "🔵"},
        {"name": "OVO", "icon": "🟣"},
        {"name": "ShopeePay", "icon": "🟠"},
        {"name": "LinkAja", "icon": "🔴"},
        {"name": "QRIS", "icon": "📲"},
    ],
    WalletType.BANK: [
        {"name": "BCA", "icon": "🏦"},
        {"name": "BRI", "icon": "🏦"},
        {"name": "Mandiri", "icon": "🏦"},
        {"name": "BNI", "icon": "🏦"},
        {"name": "CIMB Niaga", "icon": "🏦"},
        {"name": "Bank Jago", "icon": "🏦"},
        {"name": "Jenius", "icon": "🏦"},
        {"name": "SeaBank", "icon": "🏦"},
    ],
    WalletType.CASH: [
        {"name": "Tunai", "icon": "💵"},
    ],
}


# Category keywords for rule-based categorization
CATEGORY_KEYWORDS = {
    Category.MAKAN: [
        "makan", "kopi", "coffee", "nasi", "ayam", "sate", "bakso", 
        "mie", "noodle", "snack", "jajan", "sarapan", "lunch", "dinner",
        "breakfast", "resto", "restaurant", "cafe", "warung", "kantin",
        "gofood", "grabfood", "shopeefood", "es", "minuman", "drink"
    ],
    Category.TRANSPORT: [
        "grab", "gojek", "ojek", "ojol", "taxi", "taksi", "bus", 
        "kereta", "train", "mrt", "lrt", "bensin", "fuel", "parkir",
        "tol", "toll", "angkot", "transjakarta", "uber", "maxim"
    ],
    Category.BELANJA: [
        "indomaret", "alfamart", "supermarket", "mall", "belanja",
        "beli", "shop", "shopping", "tokopedia", "shopee", "lazada",
        "bukalapak", "blibli", "baju", "sepatu", "tas", "gadget"
    ],
    Category.HIBURAN: [
        "netflix", "spotify", "youtube", "game", "bioskop", "cinema",
        "nonton", "film", "movie", "konser", "concert", "wisata",
        "vacation", "liburan", "karaoke", "billiard", "bowling"
    ],
    Category.TAGIHAN: [
        "listrik", "pln", "air", "pdam", "wifi", "internet", "indihome",
        "telkom", "pulsa", "paket data", "cicilan", "kredit", "pinjaman",
        "asuransi", "insurance", "pajak", "tax", "iuran", "sewa", "kost"
    ],
    Category.KESEHATAN: [
        "obat", "apotek", "pharmacy", "dokter", "doctor", "rumah sakit",
        "hospital", "klinik", "clinic", "vitamin", "supplement", "gym",
        "fitness", "medical", "kesehatan", "health"
    ],
    Category.PENDIDIKAN: [
        "buku", "book", "kursus", "course", "les", "tutor", "sekolah",
        "kuliah", "universitas", "university", "udemy", "coursera",
        "skill", "training", "seminar", "workshop"
    ],
}


# Bot messages
MESSAGES = {
    # Welcome & Onboarding
    "welcome": """
👋 Selamat datang di *{bot_name}*!

Saya akan membantu kamu mencatat dan mengelola keuangan dengan mudah.

📝 *Fitur Utama:*
• Input transaksi via chat/voice/foto struk
• Kategorisasi otomatis dengan AI
• Kelola saldo e-wallet & bank
• Laporan & insight keuangan

🔐 Untuk keamanan, silakan buat PIN terlebih dahulu.
Ketik PIN 4-6 digit:
""",
    
    "pin_created": """
✅ PIN berhasil dibuat!

Sekarang kamu bisa mulai mencatat transaksi.

💡 *Cara Input:*
• Ketik langsung: "Beli kopi 15rb"
• Atau pakai command: /tambah 15000 kopi

📱 *Kelola Dompet:*
• /dompet - Tambah akun e-wallet/bank
• /saldo - Lihat semua saldo

Ketik /bantuan untuk melihat semua perintah.
""",
    
    "pin_required": "🔐 Masukkan PIN untuk melanjutkan:",
    "pin_wrong": "❌ PIN salah. Coba lagi:",
    "pin_success": "✅ PIN benar!",
    
    # Transaction
    "transaction_preview": """
📝 *Preview Transaksi*

💰 Nominal: Rp{amount:,}
📋 Deskripsi: {description}
{category_icon} Kategori: {category}
📅 Tanggal: {date}

Konfirmasi untuk menyimpan:
""",

    "transaction_preview_with_wallet": """
📝 *Preview Transaksi*

💰 Nominal: Rp{amount:,}
📋 Deskripsi: {description}
{category_icon} Kategori: {category}
{wallet_icon} Dari: {wallet_name}
📅 Tanggal: {date}

Konfirmasi untuk menyimpan:
""",
    
    "transaction_saved": """
✅ *Transaksi Dicatat!*

💰 Rp{amount:,}
📋 {description}
{category_icon} {category}
""",

    "transaction_saved_with_wallet": """
✅ *Transaksi Dicatat!*

💰 Rp{amount:,}
📋 {description}
{category_icon} {category}
{wallet_icon} {wallet_name}
💳 Sisa saldo: Rp{remaining:,}
""",
    
    "transaction_cancelled": "❌ Transaksi dibatalkan.",
    
    # Wallet
    "wallet_menu": """
💰 *Kelola Dompet*

Pilih aksi:
""",

    "wallet_list": """
💰 *Daftar Akun*

{wallet_list}

💎 *Total Aset:* Rp{total:,}
""",

    "wallet_empty": """
📭 Belum ada akun terdaftar.

Ketik /dompet untuk menambah akun e-wallet atau bank.
""",

    "wallet_added": """
✅ *Akun Ditambahkan!*

{icon} {name}
💰 Saldo: Rp{balance:,}
""",

    "wallet_topup_success": """
✅ *Top Up Berhasil!*

{icon} {name}
💰 Rp{old_balance:,} → Rp{new_balance:,}
➕ +Rp{amount:,}
""",

    "wallet_transfer_success": """
✅ *Transfer Berhasil!*

📤 {from_icon} {from_name}: Rp{from_old:,} → Rp{from_new:,}
📥 {to_icon} {to_name}: Rp{to_old:,} → Rp{to_new:,}
💸 Nominal: Rp{amount:,}
""",

    "wallet_select_source": "💳 *Pilih sumber dana:*",
    
    "wallet_insufficient": "❌ Saldo {name} tidak cukup (Rp{balance:,})",
    
    # Report
    "report_daily": """
📊 *Laporan Hari Ini*
📅 {date}

💰 Total Pengeluaran: Rp{total:,}
📝 Jumlah Transaksi: {count}

{breakdown}
""",
    
    "report_empty": "📭 Belum ada transaksi untuk periode ini.",
    
    # Error
    "error_generic": "❌ Terjadi kesalahan. Silakan coba lagi.",
    "error_parse": "🤔 Maaf, saya tidak mengerti. Coba format: 'Beli kopi 15rb'",
    
    # Help
    "help": """
📚 *Daftar Perintah*

*Transaksi:*
• /tambah - Input transaksi
• /list - Transaksi hari ini
• /edit - Edit transaksi
• /hapus - Hapus transaksi

*Dompet & Saldo:*
• /dompet - Kelola akun
• /saldo - Lihat semua saldo
• /topup - Tambah saldo
• /transfer - Transfer antar akun

*Laporan:*
• /laporan - Laporan harian
• /laporan\\_minggu - Laporan mingguan
• /laporan\\_bulan - Laporan bulanan
• /kategori - Breakdown kategori

*Tabungan:*
• /target - Set target tabungan
• /nabung - Tambah tabungan
• /progress - Progress target

*Lainnya:*
• /insight - AI insight
• /pengaturan - Settings
• /pin - Ubah PIN
• /bantuan - Tampilkan bantuan ini

💡 Atau langsung ketik seperti biasa:
"Makan siang 25rb"
"Ngopi 15k"
""",
}


# Keyboard button labels
BUTTONS = {
    "confirm": "✅ Simpan",
    "edit": "✏️ Edit",
    "cancel": "❌ Batal",
    "back": "⬅️ Kembali",
    "next": "➡️ Lanjut",
    "yes": "Ya",
    "no": "Tidak",
    # Wallet buttons
    "add_wallet": "➕ Tambah Akun",
    "view_wallets": "📋 Lihat Semua",
    "topup": "💰 Top Up",
    "transfer": "🔄 Transfer",
    "ewallet": "📱 E-Wallet",
    "bank": "🏦 Bank",
    "cash": "💵 Cash/Tunai",
    "skip_wallet": "⏭️ Lewati (tanpa akun)",
}

