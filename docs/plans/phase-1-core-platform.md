# Phase 1: Core Platform Implementation (Weeks 2-3)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build API Gateway with Firebase authentication, file upload to GCS, Pub/Sub job publishing, and basic React frontend.

**Duration:** 2 weeks (80 hours)

**Prerequisites:** Phase 0 completed (infrastructure deployed, database migrated)

---

## Task 1.1: Authentication Routes (Completed in Phase 0)

✓ Already implemented in main plan

---

## Task 1.2: Document Upload Endpoint (4 hours)

**Files:**
- Create: `backend/api_gateway/routes/documents.py`
- Create: `backend/shared/gcs.py`
- Create: `backend/shared/pubsub.py`

**Step 1: Create GCS utility module**

Create file: `backend/shared/gcs.py`

```python
"""Google Cloud Storage utilities."""

from google.cloud import storage
from typing import BinaryIO
import uuid
from datetime import datetime

from .config import get_settings

settings = get_settings()


class GCSManager:
    """Manage Google Cloud Storage operations."""

    def __init__(self):
        self.client = storage.Client(project=settings.project_id)
        self.bucket_uploads = self.client.bucket(settings.gcs_bucket_uploads)
        self.bucket_processed = self.client.bucket(settings.gcs_bucket_processed)
        self.bucket_temp = self.client.bucket(settings.gcs_bucket_temp)

    def upload_document(
        self,
        file: BinaryIO,
        tenant_id: str,
        document_id: str,
        filename: str,
        content_type: str = "application/pdf"
    ) -> str:
        """
        Upload document to GCS.

        Args:
            file: File object to upload
            tenant_id: Tenant UUID
            document_id: Document UUID
            filename: Original filename
            content_type: MIME type

        Returns:
            GCS URI (gs://bucket/path)
        """
        # Generate blob path: {tenant_id}/{document_id}/original.pdf
        blob_name = f"{tenant_id}/{document_id}/{filename}"
        blob = self.bucket_uploads.blob(blob_name)

        # Upload with metadata
        blob.metadata = {
            "tenant_id": tenant_id,
            "document_id": document_id,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        blob.upload_from_file(file, content_type=content_type)

        # Return GCS URI
        return f"gs://{self.bucket_uploads.name}/{blob_name}"

    def download_document(self, gcs_uri: str) -> bytes:
        """Download document from GCS."""
        # Parse GCS URI: gs://bucket/path
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        return blob.download_as_bytes()

    def get_signed_url(self, gcs_uri: str, expiration_minutes: int = 15) -> str:
        """Generate signed URL for temporary access."""
        from datetime import timedelta

        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )

        return url

    def delete_document(self, gcs_uri: str):
        """Delete document from GCS."""
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.delete()
```

**Step 2: Create Pub/Sub utility module**

Create file: `backend/shared/pubsub.py`

```python
"""Google Cloud Pub/Sub utilities."""

from google.cloud import pubsub_v1
import json
from typing import Dict, Any

from .config import get_settings

settings = get_settings()


class PubSubPublisher:
    """Publish messages to Pub/Sub topics."""

    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.project_id = settings.project_id

    def _get_topic_path(self, topic_name: str) -> str:
        """Get full topic path."""
        return self.publisher.topic_path(self.project_id, topic_name)

    def publish_invoice_processing(self, message: Dict[str, Any]) -> str:
        """Publish invoice processing job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_invoice)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_ocr_processing(self, message: Dict[str, Any]) -> str:
        """Publish OCR processing job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_ocr)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_summarization(self, message: Dict[str, Any]) -> str:
        """Publish summarization job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_summary)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_rag_ingestion(self, message: Dict[str, Any]) -> str:
        """Publish RAG ingestion job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_rag_ingest)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_document_filling(self, message: Dict[str, Any]) -> str:
        """Publish document filling job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_docfill)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_message(self, topic_name: str, message: Dict[str, Any]) -> str:
        """Generic publish method."""
        topic_path = self._get_topic_path(topic_name)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()
```

**Step 3: Create document routes**

Create file: `backend/api_gateway/routes/documents.py`

```python
"""Document management routes."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from backend.shared.database import get_db
from backend.shared.models import Document, User, AuditLog
from backend.shared.schemas import DocumentResponse, DocumentUpload
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.gcs import GCSManager
from backend.shared.pubsub import PubSubPublisher

router = APIRouter()

# Initialize managers
gcs_manager = GCSManager()
pubsub_publisher = PubSubPublisher()


@router.post("/upload", response_model=DocumentResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(..., pattern="^(invoice|contract|id|generic)$"),
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Upload document and trigger async processing.

    Flow:
    1. Validate file (type, size)
    2. Get user and tenant_id
    3. Create document record (status: uploaded)
    4. Upload to GCS
    5. Publish Pub/Sub message for processing
    6. Return 202 Accepted with document info
    """
    # Validate file size (10 MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    # Reset file pointer
    await file.seek(0)

    # Get tenant_id from token
    tenant_id = get_tenant_id_from_token(token_data)

    # Get user
    user = db.query(User).filter(User.firebase_uid == token_data["uid"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate document ID
    document_id = uuid.uuid4()

    try:
        # Upload to GCS
        gcs_path = gcs_manager.upload_document(
            file=file.file,
            tenant_id=str(tenant_id),
            document_id=str(document_id),
            filename=file.filename,
            content_type=file.content_type or "application/pdf"
        )

        # Create document record
        document = Document(
            id=document_id,
            tenant_id=tenant_id,
            user_id=user.id,
            filename=file.filename,
            original_filename=file.filename,
            mime_type=file.content_type,
            file_size_bytes=len(file_content),
            document_type=document_type,
            gcs_path=gcs_path,
            status="processing",
            processing_started_at=datetime.utcnow(),
        )
        db.add(document)

        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user.id,
            document_id=document_id,
            action="document_uploaded",
            details={
                "filename": file.filename,
                "document_type": document_type,
                "file_size": len(file_content),
            }
        )
        db.add(audit_log)

        db.commit()
        db.refresh(document)

        # Publish to appropriate Pub/Sub topic based on document type
        message = {
            "tenant_id": str(tenant_id),
            "user_id": str(user.id),
            "document_id": str(document_id),
            "gcs_path": gcs_path,
            "document_type": document_type,
            "filename": file.filename,
        }

        if document_type == "invoice":
            pubsub_publisher.publish_invoice_processing(message)
        elif document_type == "id":
            pubsub_publisher.publish_document_filling(message)
        else:
            # Generic document: publish to OCR
            pubsub_publisher.publish_ocr_processing(message)

        return DocumentResponse.from_orm(document)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """List documents for current tenant (paginated)."""
    tenant_id = get_tenant_id_from_token(token_data)

    documents = (
        db.query(Document)
        .filter(Document.tenant_id == tenant_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [DocumentResponse.from_orm(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get document details."""
    tenant_id = get_tenant_id_from_token(token_data)

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id  # Tenant isolation!
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.from_orm(document)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Delete document."""
    tenant_id = get_tenant_id_from_token(token_data)

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Delete from GCS
        gcs_manager.delete_document(document.gcs_path)

        # Delete from database (cascades to related records)
        db.delete(document)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get signed URL for document download."""
    tenant_id = get_tenant_id_from_token(token_data)

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Generate signed URL (valid for 15 minutes)
    signed_url = gcs_manager.get_signed_url(document.gcs_path, expiration_minutes=15)

    return {
        "download_url": signed_url,
        "expires_in_minutes": 15,
    }
```

**Step 4: Update main.py to include documents router**

Edit `backend/api_gateway/main.py` (already done in Phase 0, verify):

```python
# Include routers
app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])  # ✓ Added
```

**Step 5: Test document upload**

Create file: `tests/backend/test_documents.py`

```python
"""Tests for document endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.api_gateway.main import app
import io

client = TestClient(app)


def get_auth_token():
    """Helper to get auth token."""
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": "doctest@example.com",
            "password": "SecurePass123!",
            "full_name": "Doc Test User",
            "tenant_name": "Doc Test Company"
        }
    )
    return response.json()["access_token"]


def test_upload_document_success():
    """Test document upload."""
    token = get_auth_token()

    # Create fake PDF file
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
    fake_pdf.name = "test_invoice.pdf"

    response = client.post(
        "/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_invoice.pdf", fake_pdf, "application/pdf")},
        data={"document_type": "invoice"}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["filename"] == "test_invoice.pdf"
    assert data["status"] == "processing"
    assert "document_id" in str(data["id"])


def test_upload_file_too_large():
    """Test upload with oversized file."""
    token = get_auth_token()

    # Create 11 MB file
    large_file = io.BytesIO(b"x" * (11 * 1024 * 1024))
    large_file.name = "large.pdf"

    response = client.post(
        "/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("large.pdf", large_file, "application/pdf")},
        data={"document_type": "invoice"}
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_list_documents():
    """Test listing documents."""
    token = get_auth_token()

    # Upload a document first
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf")
    client.post(
        "/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.pdf", fake_pdf, "application/pdf")},
        data={"document_type": "invoice"}
    )

    # List documents
    response = client.get(
        "/v1/documents",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
```

**Step 6: Run tests**

```bash
cd backend
pytest tests/backend/test_documents.py -v
```

Expected: Tests pass (or GCS/Pub/Sub setup issues to resolve)

**Step 7: Commit**

```bash
git add backend/shared/gcs.py backend/shared/pubsub.py backend/api_gateway/routes/documents.py tests/backend/test_documents.py
git commit -m "feat: add document upload with GCS and Pub/Sub integration"
```

---

## Task 1.3: Build and Deploy API Gateway to Cloud Run (3 hours)

**Files:**
- Modify: `backend/api_gateway/Dockerfile`
- Create: `backend/api_gateway/.dockerignore`
- Create: `scripts/deploy-api-gateway.sh`

**Step 1: Optimize Dockerfile**

Edit `backend/api_gateway/Dockerfile`:

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY shared/ /app/backend/shared/
COPY api_gateway/ /app/backend/api_gateway/

WORKDIR /app/backend/api_gateway

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Create deployment script**

Create file: `scripts/deploy-api-gateway.sh`

```bash
#!/bin/bash

set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="api-gateway"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

echo "Building Docker image..."
cd backend
docker build -t $IMAGE_NAME:latest -f api_gateway/Dockerfile .

echo "Pushing to Artifact Registry..."
docker push $IMAGE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account api-gateway@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,REGION=$REGION,ENVIRONMENT=prod \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest \
  --min-instances 1 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80

echo "Deployment complete!"
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
```

**Step 3: Make script executable**

```bash
chmod +x scripts/deploy-api-gateway.sh
```

**Step 4: Build image locally (test)**

```bash
cd backend
docker build -t docai-api-gateway:local -f api_gateway/Dockerfile .
```

Expected: Image builds successfully

**Step 5: Test image locally**

```bash
docker run -p 8000:8000 \
  -e PROJECT_ID=docai-mvp-prod \
  -e ENVIRONMENT=dev \
  -e DATABASE_URL=postgresql://docai:password@host.docker.internal:5432/docai \
  docai-api-gateway:local
```

Test: Visit http://localhost:8000/docs

Expected: FastAPI documentation loads

**Step 6: Push to Artifact Registry**

```bash
# Tag for Artifact Registry
docker tag docai-api-gateway:local \
  europe-west1-docker.pkg.dev/docai-mvp-prod/docai-images/api-gateway:latest

# Configure Docker auth
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Push
docker push europe-west1-docker.pkg.dev/docai-mvp-prod/docai-images/api-gateway:latest
```

Expected: Image pushed successfully

**Step 7: Deploy to Cloud Run**

```bash
./scripts/deploy-api-gateway.sh
```

Expected: Service deployed, URL returned

**Step 8: Test deployed API**

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe api-gateway --region europe-west1 --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test docs
open "$SERVICE_URL/docs"
```

Expected: API is accessible

**Step 9: Commit**

```bash
git add backend/api_gateway/Dockerfile scripts/deploy-api-gateway.sh
git commit -m "feat: add Cloud Run deployment for API Gateway"
```

---

## Task 1.4: React Frontend Setup (6 hours)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/services/firebase.ts`
- Create: `frontend/src/services/api.ts`

**Step 1: Initialize React project**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
```

Expected: Vite React TypeScript project created

**Step 2: Install dependencies**

```bash
npm install
npm install firebase axios react-router-dom @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Step 3: Configure Tailwind CSS**

Edit `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
    },
  },
  plugins: [],
}
```

**Step 4: Add Tailwind directives to CSS**

Edit `frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
```

**Step 5: Create Firebase config**

Create file: `frontend/src/services/firebase.ts`

```typescript
/**
 * Firebase configuration and initialization
 */

import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';

// Firebase configuration (from Firebase Console)
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { auth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut };
export default app;
```

**Step 6: Create API client**

Create file: `frontend/src/services/api.ts`

```typescript
/**
 * API client for backend communication
 */

import axios, { AxiosInstance } from 'axios';
import { auth } from './firebase';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth interceptor
    this.client.interceptors.request.use(
      async (config) => {
        const user = auth.currentUser;
        if (user) {
          const token = await user.getIdToken();
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  // Auth endpoints
  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Document endpoints
  async uploadDocument(file: File, documentType: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await this.client.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async listDocuments(skip = 0, limit = 50) {
    const response = await this.client.get('/documents', {
      params: { skip, limit },
    });
    return response.data;
  }

  async getDocument(documentId: string) {
    const response = await this.client.get(`/documents/${documentId}`);
    return response.data;
  }

  async deleteDocument(documentId: string) {
    await this.client.delete(`/documents/${documentId}`);
  }

  async getDownloadUrl(documentId: string) {
    const response = await this.client.get(`/documents/${documentId}/download`);
    return response.data.download_url;
  }
}

export const apiClient = new APIClient();
```

**Step 7: Create environment variables template**

Create file: `frontend/.env.example`

```bash
VITE_API_URL=http://localhost:8000/v1
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=docai-mvp-prod.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=docai-mvp-prod
VITE_FIREBASE_STORAGE_BUCKET=docai-mvp-prod.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

**Step 8: Create authentication context**

Create file: `frontend/src/contexts/AuthContext.tsx`

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, onAuthStateChanged } from 'firebase/auth';
import { auth } from '../services/firebase';

interface AuthContextType {
  user: User | null;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
```

**Step 9: Create Login component**

Create file: `frontend/src/components/Auth/Login.tsx`

```typescript
import React, { useState } from 'react';
import { signInWithEmailAndPassword } from '../../services/firebase';
import { useNavigate } from 'react-router-dom';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signInWithEmailAndPassword(auth, email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Document AI
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <input
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

**Step 10: Create Signup component**

Create file: `frontend/src/components/Auth/Signup.tsx`

```typescript
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

export const Signup: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: '',
    tenantName: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/auth/signup`, {
        email: formData.email,
        password: formData.password,
        full_name: formData.fullName,
        tenant_name: formData.tenantName,
      });

      // Signup successful, redirect to login
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div className="rounded-md shadow-sm space-y-4">
            <input
              type="text"
              required
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="Company Name"
              value={formData.tenantName}
              onChange={(e) => setFormData({ ...formData, tenantName: e.target.value })}
            />
            <input
              type="text"
              required
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="Full Name"
              value={formData.fullName}
              onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
            />
            <input
              type="email"
              required
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="Email address"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <input
              type="password"
              required
              minLength={8}
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="Password (min 8 characters)"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {loading ? 'Creating account...' : 'Sign up'}
          </button>
        </form>
      </div>
    </div>
  );
};
```

**Step 11: Create App with routing**

Edit `frontend/src/App.tsx`:

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Login } from './components/Auth/Login';
import { Signup } from './components/Auth/Signup';
import { Dashboard } from './pages/Dashboard';

const queryClient = new QueryClient();

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return user ? <>{children}</> : <Navigate to="/login" />;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route
              path="/dashboard"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
```

**Step 12: Create simple Dashboard placeholder**

Create file: `frontend/src/pages/Dashboard.tsx`

```typescript
import React from 'react';
import { signOut } from '../services/firebase';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleLogout = async () => {
    await signOut(auth);
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Document AI</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
            <p className="text-gray-500">Dashboard coming soon...</p>
          </div>
        </div>
      </main>
    </div>
  );
};
```

**Step 13: Run frontend locally**

```bash
cd frontend
npm run dev
```

Expected: Frontend running on http://localhost:5173

**Step 14: Test signup and login flow**

1. Open http://localhost:5173
2. Go to /signup
3. Create account
4. Login
5. See dashboard

**Step 15: Commit**

```bash
git add frontend/
git commit -m "feat: add React frontend with Firebase auth"
```

---

## Task 1.5: Document Upload UI (4 hours)

**Files:**
- Create: `frontend/src/components/Documents/DocumentUpload.tsx`
- Create: `frontend/src/components/Documents/DocumentList.tsx`
- Modify: `frontend/src/pages/Dashboard.tsx`

**Step 1: Create document upload component**

Create file: `frontend/src/components/Documents/DocumentUpload.tsx`

```typescript
import React, { useState } from 'react';
import { apiClient } from '../../services/api';

interface DocumentUploadProps {
  onUploadComplete: () => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadComplete }) => {
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<string>('invoice');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      await apiClient.uploadDocument(file, documentType);
      setFile(null);
      onUploadComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Document</h2>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document Type
          </label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
          >
            <option value="invoice">Invoice</option>
            <option value="contract">Contract</option>
            <option value="id">ID Document</option>
            <option value="generic">Generic Document</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select File
          </label>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.jpg,.jpeg,.png"
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-primary-50 file:text-primary-700
              hover:file:bg-primary-100"
          />
          {file && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </div>
    </div>
  );
};
```

**Step 2: Create document list component**

Create file: `frontend/src/components/Documents/DocumentList.tsx`

```typescript
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface Document {
  id: string;
  filename: string;
  document_type: string;
  status: string;
  created_at: string;
}

export const DocumentList: React.FC = () => {
  const { data: documents, isLoading, error, refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  const getStatusBadge = (status: string) => {
    const colors = {
      uploaded: 'bg-gray-100 text-gray-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${colors[status] || colors.uploaded}`}>
        {status}
      </span>
    );
  };

  const handleDelete = async (documentId: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      await apiClient.deleteDocument(documentId);
      refetch();
    }
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading documents...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
        Failed to load documents
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      <ul className="divide-y divide-gray-200">
        {documents?.length === 0 ? (
          <li className="px-4 py-8 text-center text-gray-500">
            No documents yet. Upload your first document above!
          </li>
        ) : (
          documents?.map((doc: Document) => (
            <li key={doc.id}>
              <div className="px-4 py-4 flex items-center sm:px-6">
                <div className="min-w-0 flex-1 sm:flex sm:items-center sm:justify-between">
                  <div className="truncate">
                    <div className="flex text-sm">
                      <p className="font-medium text-primary-600 truncate">{doc.filename}</p>
                      <p className="ml-2 flex-shrink-0 font-normal text-gray-500">
                        {doc.document_type}
                      </p>
                    </div>
                    <div className="mt-2 flex">
                      <div className="flex items-center text-sm text-gray-500">
                        <p>
                          Uploaded {new Date(doc.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 flex-shrink-0 sm:mt-0 sm:ml-5">
                    <div className="flex space-x-2">
                      {getStatusBadge(doc.status)}
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="text-red-600 hover:text-red-900 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          ))
        )}
      </ul>
    </div>
  );
};
```

**Step 3: Update Dashboard to include components**

Edit `frontend/src/pages/Dashboard.tsx`:

```typescript
import React, { useState } from 'react';
import { signOut } from '../services/firebase';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { DocumentUpload } from '../components/Documents/DocumentUpload';
import { DocumentList } from '../components/Documents/DocumentList';
import { useQueryClient } from '@tanstack/react-query';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const handleLogout = async () => {
    await signOut(auth);
    navigate('/login');
  };

  const handleUploadComplete = () => {
    // Refetch documents list
    queryClient.invalidateQueries({ queryKey: ['documents'] });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Document AI</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Upload Section */}
            <div className="lg:col-span-1">
              <DocumentUpload onUploadComplete={handleUploadComplete} />
            </div>

            {/* Documents List */}
            <div className="lg:col-span-2">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Your Documents</h2>
              <DocumentList />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
```

**Step 4: Test complete upload flow**

```bash
npm run dev
```

1. Login to dashboard
2. Upload a test PDF
3. See document appear in list with "processing" status
4. Verify document uploaded to GCS (check Cloud Console)
5. Verify Pub/Sub message published (check Pub/Sub Console)

**Step 5: Deploy frontend to Vercel**

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel
```

Follow prompts, set environment variables in Vercel dashboard.

**Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: add document upload and list UI components"
```

---

## Phase 1 Complete ✓

**Summary:** Core platform implemented
- ✅ API Gateway with Firebase authentication
- ✅ Document upload to GCS
- ✅ Pub/Sub job publishing
- ✅ React frontend with auth flow
- ✅ Document management UI
- ✅ Deployed to Cloud Run and Vercel

**Next:** Phase 2 - Invoice Processing (Weeks 4-5)

---

## Verification Checklist

Before moving to Phase 2, verify:

- [ ] API Gateway deployed and accessible
- [ ] Health check endpoint returns 200
- [ ] Firebase authentication working
- [ ] Users can signup and login
- [ ] Documents upload to GCS successfully
- [ ] Pub/Sub messages published to correct topics
- [ ] Frontend deployed and accessible
- [ ] Document list shows uploaded documents
- [ ] Multi-tenancy working (users only see their own documents)
- [ ] Audit logs created for all actions
- [ ] Database migrations applied successfully
