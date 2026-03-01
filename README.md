# SimuTarget.ai

🎯 AI-Powered Synthetic Market Research Platform

## Hızlı Başlangıç

### 1. Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
cp .env.example .env
# .env dosyasını düzenle, API key'lerini ekle
```

### 3. Qdrant (Vector DB) Başlat
```bash
docker-compose up -d qdrant
```

### 4. API'yi Çalıştır
```bash
uvicorn src.api.main:app --reload
```

API: http://localhost:8000
Docs: http://localhost:8000/docs

## Proje Yapısı
```
src/
├── personas/       # Persona modelleri ve üretimi
├── inference/      # LLM entegrasyonu
├── database/       # Vector DB ve PostgreSQL
└── api/            # FastAPI endpoints
```

## Teknoloji Stack
- Python 3.11+
- FastAPI
- OpenAI API (GPT-4o-mini)
- Qdrant (Vector DB)
- PostgreSQL
- Docker

---
*SimuTarget.ai - 1M Synthetic Personas for Market Research*
