# NeuroScan AI

Beyin tümörü MRI sınıflandırma uygulaması. ResNet50V2 transfer learning modeli ile 4 sınıf tahmin eder: **Glioma · Meningioma · Pituitary · No Tumor**

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · Alembic · JWT | React 19 · React Router 7 · Vite 8 | Docker

---

## Özellikler

- Email doğrulamalı kayıt (6 haneli kod, 15 dk TTL)
- JWT access (15 dk) + refresh (7 gün) token — HTTP-only cookie
- Kullanıcı adı değiştirme (case-insensitive benzersizlik), hesap silme
- MRI yükleme (JPG/PNG, maks 10 MB) + anlık sınıflandırma
- Olasılık barları ile tüm sınıf sonuçları
- Scan geçmişi ve detay sayfası
- PDF rapor indirme (ReportLab)
- Soft delete (scan + kullanıcı)
- Rol tabanlı yetkilendirme: **user** / **admin**
- Admin panel: kullanıcı listesi, rol atama, scan görüntüleme

---

## Klasör yapısı

```
NeuroScan AI/
├── docker-compose.yml              PostgreSQL servisi (neuroscanai-db)
├── backend/
│   ├── .env                        ortam değişkenleri
│   ├── .env.example                şablon
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/           DB migration dosyaları
│   ├── ml/
│   │   ├── ResNet50V2_neuroscan.h5
│   │   └── ResNet50V2_neuroscan_classes.json
│   ├── uploads/                    yüklenen MRI dosyaları
│   └── app/
│       ├── main.py                 FastAPI app + lifespan (model yükleme, admin seed)
│       ├── config.py               pydantic-settings
│       ├── database.py             SQLAlchemy engine + session
│       ├── models/scan.py          ORM: User, Scan, TumorClass, UserRole
│       ├── schemas/scan.py         Pydantic şemaları
│       ├── core/auth.py            JWT, bcrypt, cookie helpers, dependency'ler
│       ├── routers/auth.py         /auth/* endpoint'leri
│       ├── routers/scans.py        /scans/* endpoint'leri + ModelState
│       └── utils/
│           ├── email.py            SMTP email gönderici
│           └── pdf_report.py       ReportLab PDF oluşturucu
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx                 router + AuthProvider + PublicOnlyRoute
        ├── App.css                 dark tema
        ├── api.js                  fetch wrapper (cookie, 15s timeout)
        ├── constants.js            CLASS_INFO renk/etiket haritası, DISCLAIMER
        ├── context/AuthContext.jsx global auth state (user, loading, aksiyon fonksiyonları)
        ├── components/
        │   ├── Header.jsx          nav + settings popup + logout/delete/username modal
        │   ├── ProtectedRoute.jsx  auth guard
        │   ├── ConfirmModal.jsx    onay dialog bileşeni (ESC + overlay ile kapat)
        │   ├── LoadingSpinner.jsx
        │   ├── ErrorAlert.jsx
        │   ├── ResultBadge.jsx     tahmin sonucu badge (sınıf, renk, confidence)
        │   └── ProbabilityBars.jsx sınıf olasılık barları (büyükten küçüğe sıralı)
        └── pages/
            ├── Landing.jsx         tanıtım (public)
            ├── Login.jsx           giriş formu
            ├── Register.jsx        kayıt; client-side şifre/username doğrulaması
            ├── Scan.jsx            MRI yükleme (drag-drop + click) + analiz + sonuç
            ├── History.jsx         geçmiş scan listesi (yeniden eskiye)
            └── ScanDetail.jsx      detay + PDF indirme + soft delete
```

---

## API

| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/` | servis bilgisi (versiyon, docs linki) |
| GET | `/health` | model yüklü mü + sınıf listesi |
| POST | `/auth/register` | kayıt — case-insensitive username kontrolü + email doğrulama kodu gönderir |
| POST | `/auth/verify-email` | kodu doğrula + token cookie set et + login |
| POST | `/auth/resend-code` | yeni doğrulama kodu gönder (doğrulanmamış kullanıcı için) |
| POST | `/auth/login` | giriş; timing-attack korumalı bcrypt |
| POST | `/auth/logout` | cookie temizle |
| GET | `/auth/me` | mevcut kullanıcı profili |
| PATCH | `/auth/me` | kullanıcı adı değiştir (case-insensitive çakışma kontrolü) |
| DELETE | `/auth/me` | hesabı sil (soft delete) + cookie temizle |
| POST | `/auth/refresh` | access token yenile (refresh token cookie gerekli) |
| POST | `/scans/predict` | MRI yükle + ResNet50V2 ile sınıflandır + kaydet |
| GET | `/scans/` | kullanıcının scan listesi (yeniden eskiye) |
| GET | `/scans/{id}` | scan detayı (all_probabilities dahil) |
| DELETE | `/scans/{id}` | soft delete |
| GET | `/scans/{id}/report` | PDF rapor indir (StreamingResponse) |

Swagger UI: `http://localhost:8000/docs`

---

## Frontend Sayfaları

| Rota | Bileşen | Erişim |
|---|---|---|
| `/` | Landing | Public — giriş yapmışsa `/scan`'a yönlendirir |
| `/login` | Login | Public — giriş yapmışsa `/scan`'a yönlendirir |
| `/register` | Register | Public — giriş yapmışsa `/scan`'a yönlendirir |
| `/scan` | Scan | Giriş gerekli |
| `/history` | History | Giriş gerekli |
| `/scans/:id` | ScanDetail | Giriş gerekli |
| `*` | — | `/`'a yönlendirir |

---

## Kurulum

### 1. Environment dosyası

```powershell
cd backend
copy .env.example .env
```

`.env` dosyasında şu alanları doldur:

```
DATABASE_URL=postgresql://neuroscanai:neuroscan_dev_pass@localhost:5432/neuroscanai

JWT_SECRET=<openssl rand -hex 32 çıktısı>

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<gmail adresin>
SMTP_PASSWORD=<Gmail App Password>
EMAIL_FROM=<gmail adresin>

# Startup'ta bu email sahibi otomatik admin yapılır
ADMIN_EMAIL=<admin olmasını istediğin email>
```

> Gmail App Password: Google Hesabı → Güvenlik → 2 Adımlı Doğrulama → Uygulama Şifreleri

### 2. PostgreSQL başlat

```powershell
# proje kökünden:
docker compose up -d
docker ps   # neuroscanai-db görünmeli
```

### 3. Backend bağımlılıkları

```powershell
cd backend
pip install -r requirements.txt
```

### 4. Migration uygula

```powershell
# backend/ klasöründeyken:
alembic upgrade head
```

Doğrula:

```powershell
docker exec -it neuroscanai-db psql -U neuroscanai -d neuroscanai -c "\dt"
```

`users` ve `scans` tablolarını görmelisin.

### 5. ML model dosyaları

`backend/ml/` klasörüne ekle:
- `ResNet50V2_neuroscan.h5`
- `ResNet50V2_neuroscan_classes.json` → `{ "class_names": ["glioma", "meningioma", "notumor", "pituitary"] }`

### 6. Backend başlat

```powershell
# backend/ klasöründeyken:
uvicorn app.main:app --reload
```

### 7. Frontend başlat

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

---

## Veri modeli

**User:** `user_id` · `email` · `username` · `password_hash` · `role` (user/admin) · `email_verified` · `verification_code` · `verification_code_expires_at` · `created_at` · `deleted_at`

**Scan:** `scan_id` · `user_id` · `file_path` · `original_filename` · `upload_date` · `has_tumor` · `tumor_class` · `confidence` · `all_probabilities (JSONB)` · `deleted_at`

Tüm silme işlemleri soft delete — `deleted_at` timestamp set edilir, kayıtlar korunur.

---

## Auth akışı

1. Kayıt → email + username (case-insensitive benzersizlik) + şifre → doğrulama kodu gönderilir → `/verify-email` sayfasında kod girilir → login
2. Giriş → email doğrulanmamışsa otomatik yeni kod gönderilir → `/verify-email`'e yönlendirilir
3. Access token süresi dolunca `POST /auth/refresh` ile yenilenir (refresh token cookie otomatik gönderilir)
4. Şifre hash'leme: bcrypt (72 byte limit, otomatik kırpma)
5. Timing attack koruması: kullanıcı bulunamasa da bcrypt çalıştırılır

---

## Database takibi

Proje **PostgreSQL** kullanır. Bağlantı bilgileri `backend/.env` dosyasındaki `DATABASE_URL` satırında bulunur:

```
DATABASE_URL=postgresql://neuroscanai:neuroscan_dev_pass@localhost:5432/neuroscanai
```

### GUI araçları (önerilen)

| Araç | Açıklama |
|------|----------|
| **pgAdmin 4** | PostgreSQL'in resmi GUI'si. Tablo yapısı, veri, sorgu editörü. PostgreSQL kurulumunda gelir veya [pgadmin.org](https://www.pgadmin.org/download/)'dan indirilir. |
| **DBeaver** | Daha hafif, birden fazla DB destekler. `DATABASE_URL`'yi yapıştırarak bağlanılır. [dbeaver.io](https://dbeaver.io/download/) |

Her iki araçta da bağlantı eklerken şu bilgileri gir:
- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `neuroscanai`
- **Username:** `neuroscanai`
- **Password:** `.env`'deki şifre

### Terminal ile hızlı kontrol

Tabloları listele:
```powershell
docker exec -it neuroscanai-db psql -U neuroscanai -d neuroscanai -c "\dt"
```

Tüm kullanıcıları gör:
```powershell
docker exec -it neuroscanai-db psql -U neuroscanai -d neuroscanai -c "SELECT user_id, email, username, role, email_verified, deleted_at FROM users;"
```

Tüm scan kayıtlarını gör:
```powershell
docker exec -it neuroscanai-db psql -U neuroscanai -d neuroscanai -c "SELECT scan_id, user_id, tumor_class, confidence, upload_date, deleted_at FROM scans ORDER BY upload_date DESC;"
```

### Migration geçmişi

Schema değişiklikleri `backend/alembic/versions/` klasöründe tutulur. Migration durumunu görmek için:

```powershell
cd backend
alembic history       # tüm migration listesi
alembic current       # veritabanının şu anki versiyonu
alembic upgrade head  # tüm migration'ları uygula
```

---

## Güvenlik özeti

| Önlem | Detay |
|-------|-------|
| Şifre | bcrypt 12 round, 72 byte truncation |
| JWT | HS256, ayrı access/refresh token, tip doğrulama |
| Cookie | HTTP-only, Secure (prod), SameSite=Lax |
| Timing attack | Login'de kullanıcı bulunamazsa da bcrypt çalışır |
| CORS | Yalnızca frontend URL'lerine izin verilir |
| Input | Pydantic ile tüm gelen veri doğrulanır |
| Soft delete | Fiziksel silme yok, audit trail korunur |
