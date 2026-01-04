# Bot Catatan Keuangan AI

Bot Telegram berbasis AI untuk mencatat, menganalisis, dan mengelola keuangan pribadi.

## ✨ Features

- 📝 Input transaksi natural language
- 🎤 Voice note support
- 📸 OCR struk belanja
- 🤖 AI kategorisasi otomatis
- 📊 Laporan & insight
- 🎯 Target tabungan
- 🔐 PIN security
- 📋 Google Sheets backup

## 🛠️ Tech Stack

- **Bot Framework**: python-telegram-bot
- **AI**: Google Gemini API
- **Database**: Supabase (PostgreSQL)
- **Hosting**: Vercel (Serverless)

## 📁 Project Structure

```
src/
├── bot/
│   ├── handlers/       # Command & message handlers
│   ├── keyboards/      # Inline & reply keyboards
│   └── middleware/     # Auth, logging
├── services/           # Business logic & APIs
├── database/           # Models & repository
├── utils/              # Helpers & constants
└── config.py           # Environment config
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
# Copy example env
copy .env.example .env

# Edit .env with your API keys
```

### 3. Run Bot

```bash
python src/main.py
```

## 📋 Commands

| Command | Deskripsi |
|---------|-----------|
| `/start` | Mulai & onboarding |
| `/tambah` | Input transaksi |
| `/list` | Transaksi hari ini |
| `/laporan` | Laporan keuangan |
| `/kategori` | Breakdown kategori |
| `/target` | Set target tabungan |
| `/progress` | Progress tabungan |
| `/insight` | AI insight |
| `/pengaturan` | Settings |
| `/bantuan` | Help |

## 🔒 Security

- PIN protection untuk data sensitif
- Enkripsi nominal di database
- Auto-delete message (opsional)
- Mode aman (hide saldo)

## 📄 License

MIT License
