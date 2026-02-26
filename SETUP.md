# 🚀 Quick Setup Guide

## Prerequisites

- Python 3.9+ installed
- pip package manager
- Terminal/Command Prompt

---

## Setup Steps

### 1. Navigate to Backend Directory

```bash
cd surveillance_backend
```

### 2. Create Virtual Environment (Recommended)

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Expected output:
```
Installing collected packages: fastapi, uvicorn, sqlalchemy...
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 ...
```

### 4. Run the Server

```bash
cd app
python main.py
```

Or alternatively:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify It's Running

**Open your browser:**
- API Docs: http://localhost:8000/docs
- Root: http://localhost:8000
- Health: http://localhost:8000/health

You should see:
```json
{
  "name": "Surveillance Intelligence System",
  "version": "1.0.0",
  "status": "operational"
}
```

---

## Test Authentication

### Using the API Docs (Easiest)

1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/auth/login`
3. Click "Try it out"
4. Use credentials:
   ```json
   {
     "username": "admin",
     "password": "admin123"
   }
   ```
5. Click "Execute"
6. Copy the `access_token` from response

### Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

---

## Database

**Automatic Setup:**
- Database is created automatically on first run
- Demo data (100 sample events) loaded automatically
- Located at: `surveillance.db` in app directory

**Reset Database:**
```bash
# Stop server, then:
rm app/surveillance.db
# Restart server - new database will be created
```

---

## Common Issues

### Port 8000 Already in Use

**Solution 1 - Use Different Port:**
```bash
uvicorn app.main:app --port 8001
```

**Solution 2 - Kill Process:**

**Linux/Mac:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Import Errors

**Make sure you're in the correct directory:**
```bash
cd surveillance_backend
python app/main.py  # Run from project root
```

### Dependencies Not Found

**Reinstall requirements:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

## Next Steps

1. ✅ Server running
2. ✅ Authentication working
3. 📝 Create remaining API routes (events, alerts, analytics)
4. 🎨 Build frontend dashboard
5. 🔌 Connect frontend to backend

---

## Development Workflow

### Run with Auto-Reload (for development)

```bash
uvicorn app.main:app --reload
```

Changes to code will automatically restart the server.

### Check Logs

Logs are printed to console. Look for:
- `INFO: Application startup complete`
- `✅ System initialization complete`
- Request logs: `POST /api/v1/auth/login - Status: 200`

### Debug Mode

Edit `app/core/config.py`:
```python
DEBUG = True
```

This enables:
- SQL query logging
- Detailed error messages
- Debug endpoints

---

## Production Deployment

For production, you'll need to:

1. **Switch to PostgreSQL:**
   ```bash
   # In .env
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
   ```

2. **Set Strong Secret Key:**
   ```bash
   openssl rand -hex 32
   # Copy output to .env as SECRET_KEY
   ```

3. **Disable Debug:**
   ```bash
   # In .env
   DEBUG=false
   ENVIRONMENT=production
   ```

4. **Use Production Server:**
   ```bash
   gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
   ```

---

## Testing the System

### Test Threat Scoring

```python
from app.services.threat_engine import calculate_threat
from datetime import datetime

result = calculate_threat(
    object_type="human",
    zone_sensitivity="critical",
    confidence=0.94,
    detected_at=datetime(2024, 2, 7, 23, 0, 0)  # 11 PM
)

print(result)
# {'threat_score': 88.5, 'threat_level': 'critical', 'breakdown': {...}}
```

### Check Database

```bash
sqlite3 app/surveillance.db
.tables
SELECT COUNT(*) FROM events;
.quit
```

---

## File Structure Reference

```
surveillance_backend/
├── app/
│   ├── main.py              ← Start here
│   ├── core/                ← Configuration
│   ├── api/routes/          ← API endpoints
│   ├── services/            ← Intelligence engines
│   ├── models/              ← Database models
│   ├── schemas/             ← Request/response schemas
│   └── database/            ← DB connection
├── requirements.txt         ← Dependencies
├── README.md               ← Full documentation
└── SETUP.md                ← This file
```

---

## Support

**Issues?**
1. Check logs for error messages
2. Verify all dependencies installed: `pip list`
3. Ensure Python version: `python --version` (need 3.9+)
4. Try deleting database and restarting

**Still stuck?**
- Check README.md for detailed documentation
- Review code comments in main.py
- Check FastAPI docs: https://fastapi.tiangolo.com

---

✅ **You're all set! The backend is running and ready for development.**
