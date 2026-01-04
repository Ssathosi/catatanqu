# API Requirements - Bot Catatan Keuangan AI

Daftar semua API dan kredensial yang diperlukan untuk menjalankan bot.

---

## 🔑 Daftar API Keys yang Diperlukan

| No | Nama API | Kegunaan | Prioritas | Status |
|----|----------|----------|-----------|--------|
| 1 | **Telegram Bot Token** | Interface utama bot | ⭐ WAJIB | ⬜ |
| 2 | **Google Gemini API Key** | NLP, Kategorisasi, OCR | ⭐ WAJIB | ⬜ |
| 3 | **Supabase URL** | Database PostgreSQL | ⭐ WAJIB | ⬜ |
| 4 | **Supabase Anon Key** | Database access (public) | ⭐ WAJIB | ⬜ |
| 5 | **Supabase Service Key** | Database access (admin) | ⭐ WAJIB | ⬜ |
| 6 | **Google Sheets API** | Backup & export data | 🔹 Opsional | ⬜ |

---

## 📋 Detail Setiap API

### 1. Telegram Bot Token
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```
- **Format**: `<bot_id>:<token_string>`
- **Panjang**: ~46 karakter
- **Didapat dari**: @BotFather di Telegram
- **Gratis**: ✅ Ya

---

### 2. Google Gemini API Key
```
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
- **Format**: Dimulai dengan `AIzaSy`
- **Panjang**: 39 karakter
- **Didapat dari**: Google AI Studio
- **Gratis**: ✅ Ya (dengan limit)
- **Free Tier**: 60 requests/menit, 1500 requests/hari

**Model yang digunakan:**
- `gemini-2.0-flash` - NLP & Kategorisasi
- `gemini-2.0-flash` - OCR/Vision untuk struk

---

### 3. Supabase Credentials
```
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
- **URL Format**: `https://<project-id>.supabase.co`
- **Key Format**: JWT token (panjang ~200+ karakter)
- **Didapat dari**: Supabase Dashboard > Project Settings > API
- **Gratis**: ✅ Ya (Free tier: 500MB database, 1GB bandwidth)

**Perbedaan Keys:**
- `anon key`: Client-side, terbatas RLS
- `service key`: Server-side, full access (JANGAN expose ke client!)

---

### 4. Google Sheets API (Opsional)
```
GOOGLE_SHEETS_CREDENTIALS=<path_to_service_account.json>
```
- **Format**: JSON file (Service Account)
- **Didapat dari**: Google Cloud Console
- **Gratis**: ✅ Ya (dengan quota limit)

---

## 📁 File `.env` Template

Buat file `.env` di root project dengan isi:

```env
# ================================
# BOT CATATAN KEUANGAN AI
# Environment Variables
# ================================

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# Encryption (generate random string 32 chars)
ENCRYPTION_KEY=your_32_character_encryption_key!

# Google Sheets (Opsional)
# GOOGLE_SHEETS_CREDENTIALS=./credentials/service_account.json

# App Settings
DEBUG=false
LOG_LEVEL=INFO
```

---

## ⚠️ Keamanan

> [!CAUTION]
> **JANGAN PERNAH:**
> - Commit file `.env` ke Git
> - Share `SUPABASE_SERVICE_KEY` ke client
> - Expose API keys di code yang public

**Pastikan `.gitignore` berisi:**
```
.env
.env.local
*.env
credentials/
service_account.json
```

---

## ✅ Checklist Sebelum Development

- [ ] Telegram Bot Token sudah didapat
- [ ] Gemini API Key sudah aktif
- [ ] Supabase project sudah dibuat
- [ ] Supabase URL & Keys sudah dicopy
- [ ] File `.env` sudah dibuat
- [ ] `.gitignore` sudah include `.env`
