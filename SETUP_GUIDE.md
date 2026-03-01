# SimuTarget.ai - Google OAuth Kurulum Rehberi

## 🎯 Özet
Bu rehber, SimuTarget.ai'ye "Google ile Giriş" özelliği eklemenizi sağlar.

---

## 📋 Adım 1: Google Cloud Console Ayarları

### 1.1 Proje Oluştur
1. https://console.cloud.google.com adresine git
2. Üstteki proje seçiciden "New Project" tıkla
3. Proje adı: `simutarget-ai`
4. "Create" tıkla

### 1.2 OAuth Consent Screen
1. Sol menüden: **APIs & Services → OAuth consent screen**
2. User Type: **External** seç → Create
3. Formu doldur:
   - App name: `SimuTarget.ai`
   - User support email: senin email'in
   - Developer contact email: senin email'in
4. "Save and Continue" → Scopes'u atla → Test Users'ı atla → Summary → "Back to Dashboard"

### 1.3 OAuth Client ID Oluştur
1. Sol menüden: **APIs & Services → Credentials**
2. "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: **Web application**
4. Name: `SimuTarget Web Client`
5. **Authorized JavaScript origins** ekle:
   ```
   http://localhost:5173
   http://localhost:3000
   https://simutarget.ai
   https://www.simutarget.ai
   ```
6. "CREATE" tıkla
7. **Client ID'yi kopyala** (şuna benzer: `123456789-abc...apps.googleusercontent.com`)

---

## 📋 Adım 2: Backend Kurulumu

### 2.1 Gerekli Paketleri Yükle
```bash
cd backend
pip install google-auth google-auth-oauthlib --break-system-packages
```

### 2.2 .env Dosyasını Güncelle
```env
# backend/.env
GOOGLE_CLIENT_ID=123456789-abc...apps.googleusercontent.com
```

### 2.3 Migration Çalıştır
```bash
cd backend
alembic revision --autogenerate -m "add_google_oauth_fields"
alembic upgrade head
```

### 2.4 Router'ı Kaydet
```python
# backend/app/api/main.py içine ekle:
from .routes.auth_google import router as google_auth_router

app.include_router(google_auth_router)
```

---

## 📋 Adım 3: Frontend Kurulumu

### 3.1 Paketi Yükle
```bash
cd frontend
npm install @react-oauth/google
```

### 3.2 .env Dosyası Oluştur
```env
# frontend/.env
VITE_GOOGLE_CLIENT_ID=123456789-abc...apps.googleusercontent.com
```

### 3.3 Dosyaları Değiştir
- `src/main.jsx` → GoogleOAuthProvider ekle
- `src/pages/Login.jsx` → Yeni versiyonu kullan
- `src/pages/Register.jsx` → Yeni versiyonu kullan
- `src/stores/authStore.js` → loginWithGoogle fonksiyonu ekle

---

## 📋 Adım 4: Test Et

### Development
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Test Adımları
1. http://localhost:5173/login adresine git
2. "Sign in with Google" butonuna tıkla
3. Google hesabınla giriş yap
4. Dashboard'a yönlendirilmen lazım

---

## 🔧 Dosya Yapısı

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── auth_google.py    ← YENİ
│   └── models/
│       └── user.py               ← GÜNCELLENDİ (google_id, profile_picture)
└── .env                          ← GOOGLE_CLIENT_ID

frontend/
├── src/
│   ├── main.jsx                  ← GÜNCELLENDİ (GoogleOAuthProvider)
│   ├── pages/
│   │   ├── Login.jsx             ← GÜNCELLENDİ (Google butonu)
│   │   └── Register.jsx          ← GÜNCELLENDİ (Google butonu)
│   └── stores/
│       └── authStore.js          ← GÜNCELLENDİ (loginWithGoogle)
└── .env                          ← VITE_GOOGLE_CLIENT_ID
```

---

## 🎨 Buton Görünümü

Google'ın resmi butonu kullanılıyor:
- Koyu tema (dark mode uyumlu)
- Büyük boyut
- "Sign in with Google" / "Sign up with Google" yazısı

---

## ⚠️ Önemli Notlar

1. **Production'da HTTPS şart** - Google OAuth HTTP'de çalışmaz (localhost hariç)
2. **Client ID'yi gizli tutma** - .env dosyasını git'e commitlEME
3. **Verified domain gerekli** - Production için Google'da domain doğrulaması yapılmalı

---

## 🔐 Güvenlik

- Google token backend'de doğrulanıyor
- Kullanıcı yoksa otomatik kayıt
- Mevcut email varsa hesaplar birleştiriliyor
- Password null olabiliyor (sadece Google ile giriş yapanlar için)

---

## 📞 Sorun Giderme

### "popup_closed_by_user" hatası
- Popup blocker'ı kontrol et
- Farklı tarayıcı dene

### "invalid_client" hatası
- Client ID'yi kontrol et
- Authorized origins'i kontrol et

### "redirect_uri_mismatch" hatası
- Google Console'da origins eklenmiş mi kontrol et
- http vs https dikkat et

---

## ✅ Checklist

- [ ] Google Cloud projesi oluşturuldu
- [ ] OAuth consent screen ayarlandı
- [ ] OAuth Client ID alındı
- [ ] Backend .env güncellendi
- [ ] Frontend .env oluşturuldu
- [ ] npm install @react-oauth/google yapıldı
- [ ] pip install google-auth yapıldı
- [ ] Migration çalıştırıldı
- [ ] Test edildi ve çalışıyor
