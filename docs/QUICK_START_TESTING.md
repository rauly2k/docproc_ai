# Quick Start Testing Guide

This is a condensed version of the full [TESTING.md](TESTING.md) guide. Follow these steps to get up and running quickly.

## 🚀 Quick Setup (15 minutes)

### 1. Install Prerequisites

```bash
# Check if you have everything
python3.11 --version
node --version
docker --version
gcloud --version

# If missing anything, see full TESTING.md for installation instructions
```

### 2. Start PostgreSQL with Docker

```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name docproc-postgres \
  -e POSTGRES_DB=docproc_ai_dev \
  -e POSTGRES_USER=docproc_user \
  -e POSTGRES_PASSWORD=dev_password_12345 \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# Verify
docker ps | grep docproc-postgres
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r shared/requirements.txt
pip install -r api_gateway/requirements.txt

# Create .env file
cat > .env << 'EOF'
ENVIRONMENT=dev
DEBUG=true
PROJECT_ID=docai-mvp-prod
REGION=europe-west1
DATABASE_URL=postgresql://docproc_user:dev_password_12345@localhost:5432/docproc_ai_dev
FIREBASE_CREDENTIALS_PATH=./firebase-adminsdk.json
FIREBASE_PROJECT_ID=your-firebase-project
GCS_BUCKET_UPLOADS=docai-uploads-dev
GCS_BUCKET_PROCESSED=docai-processed-dev
VERTEX_AI_LOCATION=us-central1
EOF

# Run migrations
cd migrations
alembic upgrade head
cd ..
```

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env file
cat > .env << 'EOF'
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
EOF
```

### 5. Get Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create one)
3. **For Backend:**
   - Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save as `backend/firebase-adminsdk.json`
4. **For Frontend:**
   - Project Settings → General → Your apps → Web app
   - Copy config values to `frontend/.env`

---

## 🧪 Run Tests

### Backend Tests

```bash
cd backend

# Run linting
black --check .
ruff check .

# Run tests
pytest tests/ -v --cov=.

# Start API Gateway
cd api_gateway
uvicorn main:app --reload --port 8000

# In another terminal, test endpoints
curl http://localhost:8000/health
# Open http://localhost:8000/docs for interactive API docs
```

### Frontend Tests

```bash
cd frontend

# Run linting
npm run lint

# Run tests
npm test

# Start dev server
npm run dev

# Open http://localhost:5173 in browser
```

---

## 🎯 Manual Testing Checklist

### Test User Authentication

1. **Signup Flow:**
   ```
   ✓ Navigate to http://localhost:5173/signup
   ✓ Fill in: email, password, name, org
   ✓ Click "Create Account"
   ✓ Should redirect to dashboard
   ```

2. **Login Flow:**
   ```
   ✓ Navigate to http://localhost:5173/login
   ✓ Enter credentials
   ✓ Click "Sign In"
   ✓ Should see dashboard with stats
   ```

3. **Protected Routes:**
   ```
   ✓ Logout
   ✓ Try to access http://localhost:5173/
   ✓ Should redirect to /login
   ```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs

# Test signup (no auth needed)
curl -X POST http://localhost:8000/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User",
    "tenant_name": "Test Company"
  }'

# After login, test authenticated endpoints
# Get token from frontend (browser console: await firebase.auth().currentUser.getIdToken())
TOKEN="your-firebase-token"

curl http://localhost:8000/v1/documents \
  -H "Authorization: Bearer $TOKEN"
```

### Test Database

```bash
# Connect to database
docker exec -it docproc-postgres psql -U docproc_user -d docproc_ai_dev

# Check tables
\dt

# View users
SELECT id, email, full_name FROM users;

# View tenants
SELECT id, name FROM tenants;

# Exit
\q
```

---

## 🐛 Common Issues & Quick Fixes

### Issue: Backend won't start

```bash
# Check Python virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r shared/requirements.txt
```

### Issue: Database connection failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Restart if needed
docker start docproc-postgres

# Test connection
docker exec -it docproc-postgres psql -U docproc_user -d docproc_ai_dev -c "SELECT 1"
```

### Issue: Frontend won't start

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Issue: Firebase authentication not working

```bash
# Verify credentials file exists
ls -la backend/firebase-adminsdk.json

# Check .env files have correct values
cat backend/.env | grep FIREBASE
cat frontend/.env | grep VITE_FIREBASE
```

### Issue: Port already in use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
# OR
netstat -ano | findstr :8000  # Windows (find PID)
taskkill /PID <PID> /F  # Windows

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

---

## 📊 Verify Everything Works

Run this checklist:

```bash
# Backend
cd backend
source venv/bin/activate
python -c "import fastapi, sqlalchemy, firebase_admin, google.cloud.aiplatform; print('✅ All imports work')"

# Database
docker exec -it docproc-postgres psql -U docproc_user -d docproc_ai_dev -c "SELECT 1"
# ✅ Should return: 1

# API Gateway
curl http://localhost:8000/health
# ✅ Should return: {"status":"healthy"}

# Frontend
cd ../frontend
npm run build
# ✅ Should build without errors
```

---

## 🚀 Next Steps

1. ✅ Complete local setup
2. ✅ Run all tests
3. 📖 Read full [TESTING.md](TESTING.md) for advanced testing
4. 🏗️ Deploy to GCP (see [terraform/README.md](../terraform/README.md))
5. 🔄 Set up CI/CD (see [.github/workflows/README.md](../.github/workflows/README.md))

---

## 💡 Pro Tips

**Speed up development:**

```bash
# Use tmux/tmuxinator for multi-terminal setup
# Terminal 1: Backend
# Terminal 2: Frontend
# Terminal 3: Database

# Or use VS Code tasks
# Create .vscode/tasks.json for one-click startup
```

**Debug faster:**

```bash
# Backend: Add to code
import ipdb; ipdb.set_trace()

# Frontend: Use React DevTools
# Install Chrome extension

# Database: Use DBeaver or pgAdmin
# Connect to localhost:5432
```

**Auto-reload on changes:**

```bash
# Backend already has --reload
# Frontend already has hot reload

# Watch tests
pytest --watch  # backend
npm run test:watch  # frontend
```

---

**Need more details?** See the full [TESTING.md](TESTING.md) guide.

**Issues?** Check [GitHub Issues](https://github.com/rauly2k/docproc_ai/issues) or [TESTING.md#troubleshooting](TESTING.md#troubleshooting).
