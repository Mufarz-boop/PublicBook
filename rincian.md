publicbook/
│
├── publicbook/               ← venv
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   │
│   ├── database/
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── booking.py
│   │   ├── service.py
│   │   └── queue.py
│   │
│   └── routes/
│       ├── auth.py
│       ├── booking.py
│       ├── services.py
│       └── admin.py
│
├── frontend/
│   │
│   ├── pages/
│   │   ├── index.html              ← Landing page
│   │   │
│   │   ├── auth/
│   │   │   ├── login.html          ← Admin Login (dari desain)
│   │   │   └── register.html       ← Register Page
│   │   │
│   │   ├── user/
│   │   │   ├── base.html
│   │   │   ├── dashboard.html      ← Dashboard User
│   │   │   ├── layanan.html        ← Daftar Layanan
│   │   │   ├── booking.html        ← Form Booking + QR
│   │   │   ├── riwayat.html        ← Riwayat Pemesanan
│   │   │   └── profil.html         ← Profil Pengguna
│   │   │
│   │   ├── admin/
│   │   │   ├── base.html
│   │   │   ├── dashboard.html      ← Dashboard Admin
│   │   │   ├── antrean.html        ← Pantau Antrean Real-time
│   │   │   ├── booking-list.html   ← Daftar Semua Booking
│   │   │   ├── layanan.html        ← Kelola Layanan
│   │   │   ├── pengguna.html       ← Kelola User
│   │   │   └── security.html       ← Keamanan & Audit
│   │   │
│   │   └── legal/
│   │       ├── disclaimer.html
│   │       ├── privacy.html
│   │       ├── hubungi.html
│   │       ├── about.html
│   │       └── terms.html
│   │
│   └── assets/
│       │
│       ├── css/
│       │   ├── global.css          ← Reset, variable, utility
│       │   ├── auth.css            ← Login & Register styles
│       │   ├── user.css            ← User dashboard styles
│       │   ├── admin.css           ← Admin dashboard styles
│       │   └── components.css      ← Sidebar, cards, buttons, tables
│       │
│       ├── js/
│       │   ├── main.js             ← Sidebar toggle, navbar active
│       │   ├── auth.js             ← Login/register logic
│       │   ├── booking.js          ← Pilih slot, QR generate
│       │   ├── queue.js            ← Antrean real-time
│       │   ├── dashboard.js        ← Chart & statistik
│       │   └── api.js              ← Fetch helper ke backend
│       │
│       └── images/
│           ├── bg/
│           │   ├── Background PublicBook,jpg
│           │   └── login side.jpg
│           │
│           ├── icons/
│           │   └── Icon PublicBook.jpg
│           │
│           └── avatars/
│
├── .env
├── .gitignore
├── README.md
└── rincian.md