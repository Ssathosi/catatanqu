# Panduan Mendapatkan API Keys

Step-by-step guide untuk mendapatkan semua API keys yang diperlukan.

---

## 1️⃣ Telegram Bot Token

### Langkah-langkah:

1. **Buka Telegram** dan cari **@BotFather**
   - Link: https://t.me/BotFather

2. **Mulai chat** dengan BotFather, ketik `/start`

3. **Buat bot baru** dengan command:
   ```
   /newbot
   ```

4. **Masukkan nama bot** (display name)
   ```
   Bot Catatan Keuangan
   ```

5. **Masukkan username bot** (harus diakhiri `bot`)
   ```
   catatan_keuangan_bot
   ```
   > Note: Username harus unik, coba variasi jika sudah diambil

6. **Copy Bot Token** yang diberikan
   ```
   Done! Congratulations on your new bot...
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

7. **Simpan token** ke file `.env`:
   ```
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### Commands Berguna di BotFather:
- `/setdescription` - Set deskripsi bot
- `/setabouttext` - Set about text
- `/setuserpic` - Set foto profil bot
- `/setcommands` - Set daftar commands

---

## 2️⃣ Google Gemini API Key

### Langkah-langkah:

1. **Buka Google AI Studio**
   - Link: https://aistudio.google.com/

2. **Login** dengan akun Google

3. **Klik "Get API Key"** di sidebar kiri
   - Atau langsung: https://aistudio.google.com/app/apikey

4. **Klik "Create API Key"**

5. **Pilih Project** (atau buat baru)
   - Klik "Create API key in new project" jika belum punya

6. **Copy API Key** yang muncul
   ```
   AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

7. **Simpan** ke file `.env`:
   ```
   GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Catatan Penting:
- **Free Tier Limits:**
  - 60 requests per menit
  - 1,500 requests per hari
  - Cukup untuk penggunaan personal

- **Models yang digunakan:**
  - `gemini-2.0-flash` (text & vision)

---

## 3️⃣ Supabase (Database)

### Langkah-langkah:

1. **Buka Supabase**
   - Link: https://supabase.com/

2. **Sign Up / Login**
   - Bisa pakai GitHub, Google, atau email

3. **Create New Project**
   - Klik "New Project"
   - Pilih organization (atau buat baru)

4. **Isi Detail Project:**
   - **Name**: `bot-catatan-keuangan`
   - **Database Password**: (buat password kuat, SIMPAN!)
   - **Region**: `Southeast Asia (Singapore)` (terdekat)
   - **Pricing Plan**: Free tier

5. **Tunggu project selesai dibuat** (~2 menit)

6. **Ambil Credentials:**
   - Pergi ke **Project Settings** (icon gear)
   - Klik **API** di sidebar

7. **Copy nilai berikut:**

   **Project URL:**
   ```
   https://xxxxxxxxxxxx.supabase.co
   ```

   **anon public key:**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

   **service_role key:** (klik "Reveal" dulu)
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

8. **Simpan ke `.env`:**
   ```
   SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

### Catatan:
- **Free Tier includes:**
  - 500 MB database
  - 1 GB file storage
  - 2 GB bandwidth
  - Unlimited API requests

---

## 4️⃣ Google Sheets API (Opsional)

### Langkah-langkah:

1. **Buka Google Cloud Console**
   - Link: https://console.cloud.google.com/

2. **Buat Project Baru** (atau gunakan existing)
   - Klik dropdown project > "New Project"
   - Nama: `bot-catatan-keuangan`

3. **Enable Google Sheets API:**
   - Pergi ke "APIs & Services" > "Library"
   - Cari "Google Sheets API"
   - Klik "Enable"

4. **Buat Service Account:**
   - Pergi ke "APIs & Services" > "Credentials"
   - Klik "Create Credentials" > "Service Account"
   - Isi nama: `sheets-bot`
   - Klik "Create and Continue"
   - Skip role, klik "Done"

5. **Generate Key:**
   - Klik service account yang baru dibuat
   - Tab "Keys" > "Add Key" > "Create new key"
   - Pilih "JSON"
   - File akan terdownload otomatis

6. **Simpan file JSON:**
   - Rename ke `service_account.json`
   - Taruh di folder `credentials/`
   - Update `.env`:
     ```
     GOOGLE_SHEETS_CREDENTIALS=./credentials/service_account.json
     ```

7. **Ingat email Service Account:**
   ```
   sheets-bot@your-project.iam.gserviceaccount.com
   ```
   > Email ini perlu di-share ke spreadsheet yang akan diakses

---

## 5️⃣ Generate Encryption Key

Untuk enkripsi data sensitif, generate random key:

### Menggunakan Python:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Menggunakan terminal:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Contoh output:
```
xK9mN2pQ4rS6tU8vW0xY2zA4bC6dE8fG
```

Simpan ke `.env`:
```
ENCRYPTION_KEY=xK9mN2pQ4rS6tU8vW0xY2zA4bC6dE8fG
```

---

## ✅ Checklist Final

Setelah semua selesai, pastikan file `.env` kamu berisi:

```env
# Telegram
TELEGRAM_BOT_TOKEN=✅ sudah diisi

# Gemini
GEMINI_API_KEY=✅ sudah diisi

# Supabase
SUPABASE_URL=✅ sudah diisi
SUPABASE_ANON_KEY=✅ sudah diisi
SUPABASE_SERVICE_KEY=✅ sudah diisi

# Encryption
ENCRYPTION_KEY=✅ sudah diisi

# Google Sheets (opsional)
# GOOGLE_SHEETS_CREDENTIALS=./credentials/service_account.json
```

---

## 🆘 Troubleshooting

### Telegram Bot Token Invalid
- Pastikan copy seluruh token (termasuk angka sebelum `:`)
- Jangan ada spasi di awal/akhir

### Gemini API Error
- Check quota di: https://aistudio.google.com/app/apikey
- Pastikan billing enabled jika melebihi free tier

### Supabase Connection Failed
- Pastikan URL benar (ada `https://` dan `.supabase.co`)
- Check apakah project masih aktif (free tier pause setelah 1 minggu inactive)

### Google Sheets Permission Denied
- Share spreadsheet ke email service account
- Pastikan role "Editor"

---

## 🔗 Quick Links

| Service | Dashboard | Docs |
|---------|-----------|------|
| Telegram | [@BotFather](https://t.me/BotFather) | [Bot API Docs](https://core.telegram.org/bots/api) |
| Gemini | [AI Studio](https://aistudio.google.com/) | [Gemini Docs](https://ai.google.dev/docs) |
| Supabase | [Dashboard](https://supabase.com/dashboard) | [Supabase Docs](https://supabase.com/docs) |
| Google Sheets | [Cloud Console](https://console.cloud.google.com/) | [Sheets API](https://developers.google.com/sheets/api) |
