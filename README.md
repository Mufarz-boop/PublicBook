# 🏛️ PublicBook — Sistem Booking Layanan Publik

<div align="center">
  <h2>PRODUCT REQUIREMENTS DOCUMENT</h2>
</div>

**Versi**: 1.0.0  
**Tanggal**: 08 April 2026  
**Dibuat oleh**: Afdal Adha Firnansyah (Frontend & Backend)  
**Diketuai oleh**: Shafira Zahirah (Team Lead & UI/UX)  
**Status**: Final — Siap untuk Development (MVP)  

[![Dibuat oleh](https://img.shields.io/badge/Created%20by-Afdal%20Adha%20Firnansyah-2ECC71.svg?style=for-the-badge&logo=calendar&logoColor=white)](https://github.com/Mufarz-boop)

## 👥 Tim Pengembang

| Nama | Role | Tanggung Jawab |
|------|------|----------------|
| **Shafira Zahirah** | 👑 Team Lead & 🎨 UI/UX | Koordinasi tim, desain interface, user experience, frontend support |
| **Afdal Adha Firnansyah** | 💻 Frontend & ⚙️ Backend | Web development, API integration, database design |
| **Arafa Syahputra** | 💻 Frontend & ⚙️ Backend | Server-side logic, database management, system architecture |
| **Nasyilla Syifa** | 🧪 Tester | Quality assurance, bug testing, user acceptance testing |

## 📖 1. Pendahuluan & Latar Belakang

### 1.1 Konteks Global dan Regional

Indonesia telah menunjukkan kemajuan pesat dalam transformasi digital pemerintahan. Menurut **UN E-Government Survey 2024** (dirilis September 2024 oleh UN DESA), Indonesia naik **13 peringkat** dari posisi ke-77 (2022) menjadi peringkat **ke-64 dari 193 negara** dengan skor **E-Government Development Index (EGDI) 0.7991**, sehingga masuk kategori **Very High EGDI** untuk pertama kalinya. E-Participation Index juga mencapai **0.7945**(peringkat 35 global).

Namun, kemajuan indeks nasional belum sepenuhnya terasa di tingkat operasional. Sistem layanan publik masih menghadapi **fragmentasi yang parah** antar instansi (siloed systems). Berdasarkan analisis GovInsider (Maret 2026), “setiap instansi membangun aplikasi sendiri, sehingga muncul layanan yang terpisah, data tidak terintegrasi, dan user experience yang buruk”.

### 1.2 Permasalahan Spesifik (Analisis Mendalam)

| Indikator | Kondisi Terkini (2024-2025) | Sumber Terpercaya | Gap yang Masih Ada |
|-----------|----------|-------------|-----|
| **Penerbitan Akta Kelahiran** | Cakupan anak usia 0-5 tahun naik dari 73% (2015) menjadi **85% (2024)**; beberapa sumber mencatat hingga 94.7% (2023) | UNESCAP CRVS Research & Kemendagri e-database | Masih ada disparitas antar kabupaten (25%-100%). Proses ≤60 hari belum mencapai target nasional. |
| **Penerbitan Akta Kematian** | Peningkatan signifikan melalui CRVS Decade (2015–2024), tetapi data lengkap masih terbatas | UNESCAP Progress Report 2025 & World Bank ISR P175218 | Keterlambatan tetap tinggi di daerah terpencil; integrasi data vital statistics belum optimal. |
| **Waktu Tunggu Layanan** | Rata-rata 60–90 menit di kantor fisik (Dukcapil, Dinas Sosial, dll) | World Bank “ID for Inclusive Service Delivery” Project (2024–2025) | Belum ada sistem antrian real-time yang terintegrasi. |
| **Fragmentasi Digital** | >80% layanan publik masih berbasis aplikasi terpisah per instansi | GovInsider (2026) & Kearney Analysis | Tidak ada single portal; user harus registrasi ulang di setiap layanan. |

**Kesimpulan Analisis Masalah**
Meskipun EGDI tinggi, **kesenjangan implementasi** tetap besar:

- Sistem reactive (bukan proactive)
- User experience diabaikan
- Tidak ada feedback loop
- Belum ada manajemen antrian terpadu

PublicBook hadir untuk menutup gap ini dengan sistem **booking terintegrasi** yang berfokus pada citizen-centric experience.

## 2. Visi, Misi & Tujuan

### 2.1 Visi
Menjadikan Indonesia sebagai negara dengan sistem pelayanan publik **terbaik di Asia Tenggara pada 2030** melalui transformasi digital yang inklusif, transparan, dan berpusat pada masyarakat.

### 2.2 Misi (dengan KPI)

| No | Misi | KPI | Target 2027 |
|----|------|-----|-------------|
| M1 | Mengurangi waktu tunggu | Rata-rata Waktu Tunggu | <15 menit (penurunan 83%) |
| M2 | Meningkatkan transparansi | Skor Kepuasan Pengguna | ≥90% |
| M3 | Memberdayakan instansi | Tingkat Adopsi Instansi | ≥500 instansi |
| M4 | Aksesibilitas universal | Kepatuhan WCAG 2.1 AA + inklusi difabel | 100% kepatuhan |

### 2.3 Nilai Inti (CORE)
#### **C**itizen-Centric • **O**pen & Transparent • **R**eliable • **E**fficient

## 3. Target Pengguna & Persona

### 3.1 Segmen Utama
- **Warga (Citizen)** (masyarakat umum, usia 18–60)
- **Admin Instansi (Agency Admin)** (petugas Dukcapil, Dinas, Kantor Desa)
- **Admin Utama (Super Admin)** (pemerintah pusat/kabupaten)

### 3.2 User Persona (Detail)

**Persona 1: Ibu Rumah Tangga (Rina, 32 tahun)**
- Lokasi: Kabupaten pinggiran
- Kebutuhan: Memesan layanan akta kelahiran anak tanpa harus antre berjam-jam
- Pain point: Harus bolak-balik ke kantor sambil mengurus anak kecil

**Persona 2: Pekerja Kantoran (Budi, 28 tahun)**
- Lokasi: Kota besar
- Kebutuhan: Memesan layanan KTP/SKCK di luar jam kerja
- Pain point: Jadwal sering penuh dan tidak mengetahui estimasi waktu layanan

**Persona 3: Petugas Dukcapil (Pak Joko, 45 tahun)**
- Lokasi: Provinsi wilayah timur
- Kebutuhan: Dashboard antrean real-time dan laporan harian otomatis
- Pain point: Pembuatan laporan harian secara manual terasa melelahkan

## 4. Ruang Lingkup (Scope)

### In-Scope
- Sistem pemesanan (booking) + manajemen antrean secara real-time
- Notifikasi multi-channel (WhatsApp Business API, Email, SMS, In-App)
- Portal Warga (Citizen Portal) + Dashboard Instansi (Agency Dashboard) + Panel Admin Utama (Super Admin Panel)
- Sistem penilaian (rating) & umpan balik (feedback)
- Analitik dasar untuk instansi

### Out-of-Scope (Fase 2+)
- Pembayaran atau retribusi online
- Penerbitan dokumen digital (e-akta)
- Integrasi dengan layanan pihak swasta

## 5. Glosarium

| Istilah | Definisi |
|---------|----------|
| **Slot** | Waktu layanan yang tersedia (contoh: 09:00–09:30) |
| **Pemesanan (Booking)** | Reservasi slot oleh warga |
| **Antrean (Queue)** | Antrean virtual dengan estimasi waktu |
| **Instansi (Agency)** | Instansi pemerintah penyedia layanan |

## 6. User Stories & Kebutuhan Fungsional

### 6.1 User Stories (Prioritas MoSCoW)

**Portal Warga (Citizen Portal)**

- **P0** Sebagai warga, saya ingin **mencari layanan dan lokasi terdekat** agar dapat melakukan pemesanan tanpa harus datang terlebih dahulu.
- **P0** Sebagai warga, saya ingin **memilih slot waktu secara real-time** agar saya yakin ketersediaan layanan.
- **P0** Sebagai warga, saya ingin **menerima notifikasi 24 jam dan 1 jam sebelumnya** melalui WhatsApp.
- **P1** Sebagai warga, saya ingin **melihat riwayat pemesanan dan status** dalam satu tempat.
- **P1** Sebagai warga, saya ingin **memberikan rating dan umpan balik** setelah layanan selesai.

**Dashboard Instansi (Agency Dashboard)**

- **P0** Sebagai admin instansi, saya ingin **memantau antrean secara real-time** dan memanggil nomor antrean.
- **P1** Sebagai admin instansi, saya ingin **mengelola jadwal petugas dan slot layanan** per hari.
- **P2** Sebagai admin instansi, saya ingin **melihat analitik** (jumlah pemesanan, waktu tunggu, tingkat kepuasan).

**Admin Utama (Super Admin)**

- Mengelola instansi, peran (role), hak akses (permission), dan audit log.

### 6.2 Kebutuhan Fungsional Detail (Contoh)

**FR-01 Smart Booking**

- Sistem harus menampilkan slot yang tersedia secara real-time (pembaruan < 2 detik).
- Jika slot penuh, sistem harus menyarankan 3 slot alternatif terdekat (radius maksimal 10 km).

**Acceptance Criteria:**
- Diberikan slot penuh, ketika pengguna memilih “Cari alternatif”, maka sistem menampilkan daftar slot alternatif beserta estimasi waktu dan jarak.

**FR-02 Sistem Notifikasi**

- Sistem harus mengirim 3 jenis notifikasi:
  - Pengingat H-1
  - Pengingat H-1 jam
  - Notifikasi “Anda telah dilayani”
- Kanal notifikasi:
  - WhatsApp Business API (prioritas utama)
  - Email
  - SMS sebagai cadangan (fallback)

## 7. Kebutuhan Non-Fungsional

| Kategori | Persyaratan | Target |
|----------|-------------|--------|
| **Performa** | Waktu respons halaman booking | ≤ 2 detik |
| **Skalabilitas** | Jumlah pengguna bersamaan (MVP) | 500 pengguna |
| **Keamanan** | Autentikasi | OAuth2 + JWT, 2FA opsional |
| **Keandalan** | Waktu aktif (uptime) | 99,5% |
| **Aksesibilitas** | Standar | WCAG 2.1 AA + Bahasa Indonesia |
| **Privasi Data** | Kepatuhan | PDPA Indonesia & standar setara GDPR |

## 8. Pertimbangan Teknis

- **Frontend**: HTML, CSS, dan JavaScript murni (vanilla) untuk membangun antarmuka pengguna yang ringan, responsif, dan mudah di-maintain.
- **Backend**: Python untuk implementasi logika bisnis, pemrosesan data, dan integrasi sistem.
- **Database**: MySQL yang dikelola melalui phpMyAdmin untuk administrasi dan pengembangan database yang intuitif.
- **API**: Arsitektur RESTful API yang dikombinasikan dengan WebSocket untuk mendukung manajemen antrean secara real-time (pembaruan data < 2 detik).
- **Notifikasi**: Email sebagai kanal utama pengiriman notifikasi.
- **Deployment**: Vercel (frontend) + Railway atau DigitalOcean (backend)

## 9. Asumsi & Ketergantungan

- **Asumsi**:
  - Koneksi internet stabil di kantor instansi
  - Petugas telah memiliki smartphone

- **Ketergantungan**:
  - API WhatsApp Business (telah disetujui/approved)
  - Koordinasi dengan Dukcapil/Kemendagri untuk data master layanan
  - Google Maps API untuk layanan lokasi

## 10. Metode Pengukuran Keberhasilan (Success Metrics)

- **Keberhasilan MVP**: ≥100 pemesanan berhasil dalam 2 minggu pilot
- **Kepuasan Pengguna**: ≥85% (NPS ≥50)
- **Pengurangan Waktu Tunggu**: ≥75% di lokasi pilot
- **Adopsi Instansi**: Minimal 3 instansi pilot aktif

## 11. Roadmap Pengembangan

| Phase | Keterangan |
|-------|------------|
| **Phase 0** | Perencanaan & Desain (Minggu 1–2) |
| **Phase 1** | Pengembangan MVP (Minggu 3–10) – 5 Sprint | 
| **Phase 2** | Pengujian & Penyempurnaan (Minggu 11–12) |
| **Phase 3** | Demo & Penyerahan (Minggu 13–14) |

## Penutup

**Dokumen ini merupakan PRD resmi PublicBook.**  
Seluruh tim wajib mengikuti spesifikasi yang telah ditetapkan.  
Setiap perubahan ruang lingkup (scope) harus melalui proses **Change Request** dan mendapatkan persetujuan dari Team Lead.

## 📞 Kontak PublicBook

<div align="center">

| 🌐 Website | 📧 Email | 📱 Instagram | 📺 YouTube |
|:----------:|:--------:|:------------:|:----------:|
| [publicbook.id](https://publicbook.id) | [hello@publicbook.id](mailto:hello@publicbook.id) | [@publicbook.id](https://instagram.com/publicbook.id) | [PublicBook](https://youtube.com/@publicbook) |

<br>

[![GitHub Issues](https://img.shields.io/badge/🐛%20Laporkan%20Bug-GitHub%20Issues-181717?style=for-the-badge&logo=github)](https://github.com/Mufarz-boop/publicbook/issues)

</div>

<p align="center">
  <br>
  🏛️ <strong>PublicBook</strong> — Dari Pelajar, Untuk Masyarakat
  <br>
  <em>"Proyek Tugas Kelompok — 2026"</em>
  <br>
  <p align="center">Dibuat oleh <strong>PublicBook</strong></p>
</p>