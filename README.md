# NeuroScan AI

Beyin tümörü MRI sınıflandırma uygulaması. ResNet50V2 transfer learning modeli ile MRI görüntülerini 4 sınıfa ayırır: **Glioma · Meningioma · Pituitary · No Tumor**

Kullanıcı email doğrulamalı kayıt olur, JWT ile giriş yapar, MRI yükler, anlık sınıflandırma + olasılık dağılımı görür, geçmiş scanlerini inceler ve PDF rapor indirir.

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · Alembic · JWT | React 19 · React Router 7 · Vite 8 | Docker

---

## Kurulum

### 1. Environment dosyası

```powershell
cd backend
copy .env.example .env
```

`.env` dosyasında şu alanları doldur:

```
DATABASE_URL=postgresql+psycopg2://neuroscanai:neuroscan_dev_pass@localhost:5432/neuroscanai

JWT_SECRET=<openssl rand -hex 32 çıktısı>

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<gmail adresin>
SMTP_PASSWORD=<Gmail App Password>
EMAIL_FROM=<gmail adresin>
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

### 5. ML model dosyaları

`backend/ml/` klasörüne ekle:
- `ResNet50V2_neuroscan.keras`
- `ResNet50V2_neuroscan_classes.json` → `{ "class_names": ["glioma", "meningioma", "notumor", "pituitary"] }`

---

## Çalıştırma

### Backend

```powershell
cd backend
uvicorn app.main:app --reload
```

API: `http://localhost:8000` · Swagger UI: `http://localhost:8000/docs`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`
