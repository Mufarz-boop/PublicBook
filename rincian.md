publicbook/                  # Nama folder project (root)
├── app/                     # Semua kode utama ada di sini
│   ├── __init__.py
│   ├── main.py              # File utama FastAPI (entry point)
│   ├── config.py            # Konfigurasi (database, secret key, dll)
│   ├── database.py          # Koneksi ke MySQL
│   │
│   ├── models/              # Model database (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── service.py
│   │   └── booking.py
│   │
│   ├── schemas/             # Pydantic models (data yang masuk/keluar)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── booking.py
│   │
│   ├── routers/             # Semua endpoint/API routes
│   │   ├── __init__.py
│   │   ├── auth.py          # Login & Register
│   │   ├── user.py
│   │   ├── booking.py
│   │   └── admin.py
│   │
│   └── templates/           # HTML files (menggunakan Jinja2)
│       ├── base.html        # Template dasar (navbar, footer, dll)
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── user/
│       │   ├── dashboard.html
│       │   ├── daftar_layanan.html
│       │   └── booking.html
│       └── admin/
│           ├── dashboard.html
│           └── kelola_booking.html
│
├── static/                  # CSS, JavaScript, gambar
│   ├── css/
│   ├── js/
│   └── assets/
│
├── .env                     # Simpan password database dll (jangan di-upload ke GitHub)
├── .gitignore
├── requirements.txt
├── README.md
└── rincian.md