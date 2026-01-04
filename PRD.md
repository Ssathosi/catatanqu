# **Product Requirements Document (PRD)**

## **1. Ringkasan Produk**

**Nama Produk:** CatatanQu

**Deskripsi:**
Bot Telegram berbasis AI yang membantu pengguna mencatat, menganalisis, dan mengelola keuangan pribadi secara otomatis melalui chat, voice note, dan foto struk. Data disimpan aman dan dapat terintegrasi dengan Google Sheets.

**Target Pengguna:**

* Mahasiswa
* Pekerja muda
* Freelancer
* UMKM mikro (pribadi)

**Value Proposition:**

* Pencatatan keuangan **tanpa ribet**
* Input **natural language & multimodal**
* Insight keuangan berbasis AI
* Aman & privat

---

## **2. Tujuan Produk**

* Mempermudah pencatatan transaksi harian
* Mengurangi input manual
* Memberi insight & rekomendasi penghematan
* Menjaga keamanan data keuangan pengguna

---

## **3. Fitur Utama**

### **3.1 Input Transaksi (Multimodal)**

**Fungsi:**

* Input teks natural language
* Voice note
* Foto struk / nota

**Contoh:**

* "Beli kopi Rp15.000"
* Voice: "Tadi makan siang dua puluh lima ribu"
* Upload foto struk Indomaret

---

### **3.2 AI + OCR Struk Belanja**

**Fungsi:**

* OCR membaca struk
* AI mengekstrak:

  * Nama toko
  * Total belanja
  * Daftar item
  * Tanggal struk

**Output:**

* Draft transaksi otomatis
* User konfirmasi / edit

---

### **3.3 Integrasi Telegram & Google Sheets**

**Telegram:**

* Interface utama
* Command & chat natural

**Google Sheets:**

* Backup data
* Visualisasi lanjutan
* Data terenkripsi

---

### **3.4 Analisis & Insight Keuangan**

**Analisis:**

* Harian / Mingguan / Bulanan
* Per kategori
* Tren pengeluaran

**Insight AI:**

* "Pengeluaran makan naik 30% bulan ini"
* "Transport lebih boros di hari kerja"

---

### **3.5 AI Kategorisasi Otomatis**

**Fitur:**

* Kategorisasi otomatis (makan, transport, belanja, dll)
* Belajar dari riwayat user
* Koreksi dengan perintah sederhana

**Contoh:**

* "Ubah kategori kopi kemarin jadi nongkrong"

---

### **3.6 Target & Tabungan**

**Contoh Target:**

* "Nabung 10 juta dalam 12 bulan"

**Bot Menghitung:**

* Tabungan per bulan
* Proyeksi pencapaian
* Notifikasi progres

**Insight:**

* "Jika kurangi jajan 10%, target tercapai 1 bulan lebih cepat"

---

### **3.7 Keamanan & Privasi (Wajib)**

#### **PIN / Password Bot**

* Set PIN saat pertama kali pakai
* Akses saldo & laporan wajib PIN

#### **Enkripsi Data**

* Data lokal terenkripsi
* Google Sheets:

  * Nominal dienkripsi
  * Dekripsi hanya di bot

#### **Mode Aman**

* Sembunyikan saldo
* Ringkasan tanpa detail
* Auto-hapus pesan keuangan setelah X jam

---

## **4. Flow Pengguna (User Flow)**

### **4.1 Onboarding**

1. User start bot
2. Set PIN
3. Pilih mode aman (opsional)
4. Integrasi Google Sheets

### **4.2 Input Transaksi (Teks)**

1. User kirim chat
2. AI parsing transaksi
3. Kategorisasi otomatis
4. Simpan data
5. Konfirmasi

### **4.3 Input Struk**

1. Upload foto
2. OCR + AI ekstraksi
3. Preview data
4. User konfirmasi
5. Simpan

### **4.4 Lihat Laporan**

1. User minta laporan
2. Bot minta PIN
3. Tampilkan ringkasan / detail

---

## **5. Wireframe Sederhana (Teks)**

### **Chat Input**

```
User: Beli kopi Rp15.000
Bot: ☑️ Dicatat
     Kategori: Makan
     Total: Rp15.000
```

### **Insight**

```
📊 Insight Bulanan
- Makan: +30%
- Transport: -10%
Saran: Kurangi jajan sore
```

### **Target Tabungan**

```
🎯 Target: 10.000.000 / 12 bulan
Per bulan: Rp833.334
Progress: 25%
```

---

## **6. Rancangan Database**

### **Tabel: Transaksi**

* id_transaksi
* nama_toko
* total (terenkripsi)
* items (JSON)
* kategori
* tanggal_struk
* tanggal_input
* waktu_input
* sumber_input (teks / voice / struk)

---

## **7. Prioritas Fitur**

### **MVP (Wajib Ada)**

* Input teks natural language
* Kategorisasi otomatis
* Google Sheets integration
* Laporan dasar
* PIN keamanan

### **Fitur Lanjutan**

* Voice note input
* OCR struk
* Insight AI lanjutan
* Target tabungan
* Mode aman
* Rekomendasi penghematan

---

## **8. Risiko & Mitigasi**

* OCR tidak akurat → preview & konfirmasi
* Privasi → enkripsi + PIN
* Overkompleks → rilis bertahap

---

## **9. KPI Keberhasilan**

* Retensi user 30 hari
* Jumlah transaksi tercatat
* Insight dibaca
* Error OCR < 10%

---

## **10. Catatan Pengembangan**

* Modular AI service
* Logging terenkripsi
* Mudah dikembangkan ke WhatsApp / Web
