# Phases 4-7: Remaining Implementation (Weeks 7-12)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

This document covers the final 4 phases of the MVP implementation.

---

# Phase 4: Text Summarization (Week 7)

**Goal:** Implement document summarization using Vertex AI (Gemini/Claude).

## Task 4.1: Summarizer Worker (4 hours)

**Files:**
- Create: `backend/workers/summarizer_worker/main.py`
- Create: `backend/workers/summarizer_worker/summarizer.py`
- Create: `backend/workers/summarizer_worker/Dockerfile`

**Implementation:**

```python
# backend/workers/summarizer_worker/summarizer.py
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import storage
import PyPDF2
import io

class DocumentSummarizer:
    def __init__(self):
        self.flash_model = GenerativeModel("gemini-1.5-flash")
        self.pro_model = GenerativeModel("gemini-1.5-pro")
        self.storage_client = storage.Client()

    def summarize_document(self, gcs_uri: str, use_premium: bool = False) -> dict:
        # Extract text from PDF
        text = self._extract_text_from_pdf(gcs_uri)

        # Choose model based on preference
        model = self.pro_model if use_premium else self.flash_model

        # Generate summary
        prompt = f"""Summarize the following document in 3-5 concise bullet points.
        Focus on the main points and key takeaways.

        Document:
        {text[:50000]}  # Limit to fit context

        Summary:"""

        response = model.generate_content(prompt)
        summary = response.text

        # Extract key points
        key_points = self._extract_key_points(summary)

        return {
            "summary": summary,
            "key_points": key_points,
            "word_count": len(summary.split()),
            "model_used": "gemini-1.5-pro" if use_premium else "gemini-1.5-flash",
        }

    def _extract_text_from_pdf(self, gcs_uri: str) -> str:
        # Download PDF from GCS
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        pdf_bytes = blob.download_as_bytes()

        # Extract text
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        return text

    @staticmethod
    def _extract_key_points(summary: str) -> list:
        # Parse bullet points from summary
        lines = summary.split("\n")
        points = []
        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("• ") or line.startswith("* "):
                points.append(line[2:].strip())
        return points
```

**Deployment:**

```bash
# scripts/deploy-summarizer-worker.sh
#!/bin/bash
set -e
PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="summarizer-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

cd backend
docker build -t $IMAGE_NAME:latest -f workers/summarizer_worker/Dockerfile .
docker push $IMAGE_NAME:latest

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,VERTEX_AI_LOCATION=us-central1 \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

gcloud pubsub subscriptions create summarization-processing-sub \
  --topic=summarization-processing \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600
```

## Task 4.2: Summaries API & UI (3 hours)

**API Routes:**

```python
# backend/api_gateway/routes/summaries.py
@router.post("/{document_id}/generate", status_code=202)
async def generate_summary(document_id: uuid.UUID, ...):
    # Publish to Pub/Sub
    pubsub_publisher.publish_summarization(message)
    return {"message": "Summarization started"}

@router.get("/{document_id}")
async def get_summary(document_id: uuid.UUID, ...):
    summary = db.query(DocumentSummary).filter(...).first()
    return summary
```

**Frontend Component:**

```typescript
// frontend/src/components/Summaries/SummaryView.tsx
export const SummaryView: React.FC<{documentId: string}> = ({documentId}) => {
  const {data: summary} = useQuery({
    queryKey: ['summary', documentId],
    queryFn: () => apiClient.getSummary(documentId),
  });

  return (
    <div>
      <h3>Document Summary</h3>
      <p>{summary?.summary}</p>
      <h4>Key Points:</h4>
      <ul>
        {summary?.key_points.map((point, i) => <li key={i}>{point}</li>)}
      </ul>
    </div>
  );
};
```

**Commit:**
```bash
git add backend/workers/summarizer_worker/ backend/api_gateway/routes/summaries.py frontend/src/components/Summaries/
git commit -m "feat: add document summarization with Gemini"
```

---

# Phase 5: Chat with PDF (RAG) (Weeks 8-9)

**Goal:** Implement RAG pipeline with pgvector for document Q&A.

## Task 5.1: RAG Ingestion Worker (6 hours)

**Files:**
- Create: `backend/workers/rag_ingest_worker/main.py`
- Create: `backend/workers/rag_ingest_worker/ingestion.py`

**Implementation:**

```python
# backend/workers/rag_ingest_worker/ingestion.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from vertexai.language_models import TextEmbeddingModel
from google.cloud import storage
import PyPDF2

class RAGIngestionPipeline:
    def __init__(self):
        self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.storage_client = storage.Client()

    def ingest_document(self, gcs_uri: str, document_id: str, tenant_id: str, db):
        # Extract text
        text = self._extract_text(gcs_uri)

        # Split into chunks
        chunks = self.text_splitter.split_text(text)

        # Generate embeddings and save
        for i, chunk in enumerate(chunks):
            # Get embedding
            embeddings = self.embedding_model.get_embeddings([chunk])
            embedding_vector = embeddings[0].values

            # Save to database
            chunk_record = DocumentChunk(
                document_id=document_id,
                tenant_id=tenant_id,
                chunk_index=i,
                content=chunk,
                token_count=len(chunk.split()),
                embedding=embedding_vector,
                metadata={"page": i // 3}  # Rough page estimate
            )
            db.add(chunk_record)

        db.commit()

    def _extract_text(self, gcs_uri: str) -> str:
        # Similar to summarizer
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        pdf_bytes = blob.download_as_bytes()

        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
```

## Task 5.2: RAG Query Service (6 hours)

**Implementation:**

```python
# backend/api_gateway/routes/chat.py
from sqlalchemy import text as sql_text

@router.post("/query")
async def query_documents(
    query_request: ChatQueryRequest,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    tenant_id = get_tenant_id_from_token(token_data)

    # Embed query
    embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
    query_embedding = embedding_model.get_embeddings([query_request.question])[0].values

    # Vector similarity search with pgvector
    query = sql_text("""
        SELECT content, document_id, chunk_index,
               1 - (embedding <=> :query_vector) as similarity
        FROM document_chunks
        WHERE tenant_id = :tenant_id
        ORDER BY embedding <=> :query_vector
        LIMIT :max_chunks
    """)

    results = db.execute(query, {
        "query_vector": str(query_embedding),
        "tenant_id": str(tenant_id),
        "max_chunks": query_request.max_chunks or 5
    }).fetchall()

    # Build context
    context = "\n\n".join([r.content for r in results])

    # Generate answer with Gemini
    model = GenerativeModel("gemini-1.5-flash")
    prompt = f"""Answer the following question based only on the provided context.
    If the answer cannot be found in the context, say "I don't have enough information to answer that."

    Context:
    {context}

    Question: {query_request.question}

    Answer:"""

    response = model.generate_content(prompt)

    return {
        "answer": response.text,
        "sources": [
            {"document_id": str(r.document_id), "chunk_index": r.chunk_index, "relevance": r.similarity}
            for r in results
        ],
        "model_used": "gemini-1.5-flash"
    }
```

**Frontend Component:**

```typescript
// frontend/src/components/Chat/ChatInterface.tsx
export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    const response = await apiClient.queryChatRAG({
      question: input,
      document_ids: selectedDocs,
      max_chunks: 5
    });

    setMessages([...messages,
      {role: 'user', content: input},
      {role: 'assistant', content: response.answer, sources: response.sources}
    ]);
    setInput('');
  };

  return (
    <div className="chat-container">
      {messages.map((msg, i) => (
        <div key={i} className={msg.role}>
          {msg.content}
          {msg.sources && <Sources sources={msg.sources} />}
        </div>
      ))}
      <input value={input} onChange={e => setInput(e.target.value)} />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
};
```

**Deployment:**

```bash
# Deploy both RAG workers
./scripts/deploy-rag-ingest-worker.sh
./scripts/deploy-api-gateway.sh  # Updated with chat routes
```

**Commit:**
```bash
git add backend/workers/rag_ingest_worker/ backend/api_gateway/routes/chat.py frontend/src/components/Chat/
git commit -m "feat: add RAG pipeline with pgvector for Chat with PDF"
```

---

# Phase 6: Document Filling (Week 10)

**Goal:** Extract ID data and auto-fill PDF forms.

## Task 6.1: Document Filling Worker (5 hours)

**Implementation:**

```python
# backend/workers/docfill_worker/processor.py
from google.cloud import documentai_v1 as documentai
from pypdfform import PdfWrapper

class DocumentFillingProcessor:
    def __init__(self):
        self.documentai_client = documentai.DocumentProcessorServiceClient(...)
        self.id_processor_id = os.getenv("DOCUMENTAI_ID_PROCESSOR_ID")

    def extract_id_data(self, gcs_uri: str) -> dict:
        """Extract data from ID card using Document AI."""
        processor_name = self.documentai_client.processor_path(
            project_id, location, self.id_processor_id
        )

        request = documentai.ProcessRequest(
            name=processor_name,
            gcs_document=documentai.GcsDocument(gcs_uri=gcs_uri, mime_type="image/jpeg")
        )

        result = self.documentai_client.process_document(request=request)

        # Extract ID fields
        extracted = {}
        for entity in result.document.entities:
            if entity.type_ == "family_name":
                extracted["nume"] = entity.mention_text
            elif entity.type_ == "given_name":
                extracted["prenume"] = entity.mention_text
            elif entity.type_ == "national_id":
                extracted["cnp"] = entity.mention_text
            elif entity.type_ == "address":
                extracted["adresa"] = entity.mention_text
            elif entity.type_ == "birth_date":
                extracted["data_nasterii"] = entity.mention_text

        return extracted

    def fill_pdf_form(self, template_path: str, data: dict, output_path: str):
        """Fill PDF form with extracted data."""
        pdf = PdfWrapper(template_path).fill(data)
        with open(output_path, "wb") as f:
            pdf.stream.write_to(f)
```

**API Routes:**

```python
# backend/api_gateway/routes/filling.py
@router.post("/extract-and-fill", status_code=202)
async def extract_and_fill(
    id_document_id: uuid.UUID,
    template_name: str,
    ...
):
    # Publish job
    pubsub_publisher.publish_document_filling({
        "id_document_id": str(id_document_id),
        "template_name": template_name,
        ...
    })
    return {"message": "Document filling started"}

@router.get("/{document_id}")
async def get_filled_pdf(document_id: uuid.UUID, ...):
    # Return signed URL for download
    return {"download_url": gcs_manager.get_signed_url(filled_pdf_path)}
```

**Commit:**
```bash
git add backend/workers/docfill_worker/ backend/api_gateway/routes/filling.py
git commit -m "feat: add ID extraction and PDF form filling"
```

---

# Phase 7: Polish & Beta Launch (Weeks 11-12)

**Goal:** Finalize MVP, add polish, monitoring, deploy, launch beta.

## Task 7.1: Frontend Polish (10 hours)

**Improvements:**
1. **Responsive Design**
   - Mobile-friendly layouts
   - Touch-friendly buttons
   - Responsive tables

2. **Loading States**
   ```typescript
   // Use skeleton loaders instead of spinners
   <div className="animate-pulse bg-gray-200 h-8 w-full rounded" />
   ```

3. **Error Handling**
   ```typescript
   // Global error boundary
   <ErrorBoundary fallback={<ErrorPage />}>
     <App />
   </ErrorBoundary>
   ```

4. **User Onboarding**
   - Welcome modal on first login
   - Feature tour
   - Sample documents

## Task 7.2: Monitoring & Logging (6 hours)

**Cloud Logging Setup:**

```bash
# View logs from all services
gcloud logging read "resource.type=cloud_run_revision" --limit 100 --format json

# Set up log-based metrics
gcloud logging metrics create invoice_processing_errors \
  --description="Invoice processing errors" \
  --log-filter='resource.type="cloud_run_revision" AND severity="ERROR" AND labels."service-name"="invoice-worker"'
```

**Cloud Monitoring Dashboards:**

1. Create dashboard in Cloud Console
2. Add charts:
   - API request rate
   - Worker processing time
   - Error rate by service
   - Database connection pool
   - GCS storage usage

**Error Tracking with Sentry:**

```python
# backend/shared/config.py
import sentry_sdk

if settings.environment == "prod":
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=0.1,
    )
```

## Task 7.3: Performance Optimization (8 hours)

**Database Optimization:**

```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_documents_tenant_status ON documents(tenant_id, status);
CREATE INDEX CONCURRENTLY idx_invoice_data_tenant_date ON invoice_data(tenant_id, invoice_date DESC);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM documents WHERE tenant_id = '...' ORDER BY created_at DESC LIMIT 50;
```

**API Caching:**

```python
# Add Redis caching for frequently accessed data
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="docai:")

@router.get("/documents")
@cache(expire=60)  # Cache for 60 seconds
async def list_documents(...):
    ...
```

**Cloud Run Optimization:**

```bash
# Increase min instances to reduce cold starts
gcloud run services update api-gateway \
  --region europe-west1 \
  --min-instances 2 \
  --max-instances 20
```

## Task 7.4: Security Review (6 hours)

**Checklist:**

- [ ] All API endpoints require authentication
- [ ] Tenant isolation verified on all queries
- [ ] CORS configured to allow only frontend domain
- [ ] Rate limiting enabled
- [ ] SQL injection prevention (using ORM)
- [ ] XSS prevention (React auto-escapes)
- [ ] Secrets in Secret Manager (not environment variables)
- [ ] HTTPS everywhere (TLS 1.3)
- [ ] File upload validation (type, size)
- [ ] Input validation with Pydantic

**Penetration Testing:**

```bash
# Basic security scan with OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://your-api-url
```

## Task 7.5: Documentation (8 hours)

**Create Documentation:**

1. **User Guide** (`docs/user-guide.md`)
   - How to sign up
   - How to upload documents
   - How to validate invoices
   - How to use Chat with PDF

2. **API Documentation** (auto-generated from FastAPI)
   - Already available at `/docs`
   - Export to static HTML for offline use

3. **Admin Guide** (`docs/admin-guide.md`)
   - How to manage users
   - How to view audit logs
   - How to troubleshoot issues

4. **Deployment Guide** (`docs/deployment.md`)
   - Infrastructure setup
   - Environment variables
   - Deployment commands
   - Rollback procedures

## Task 7.6: Beta Launch (10 hours)

**Pre-launch Checklist:**

- [ ] All 5 AI features working
- [ ] Frontend deployed to production domain
- [ ] API Gateway deployed with SSL
- [ ] All workers deployed and tested
- [ ] Database backed up
- [ ] Monitoring dashboards configured
- [ ] Error alerts configured
- [ ] User documentation complete
- [ ] Privacy policy published
- [ ] Terms of service published

**Beta User Onboarding:**

1. **Create Landing Page**
   - Value proposition
   - Feature showcase
   - Beta signup form

2. **Email Invites** (10-20 beta users)
   - Personal email with login link
   - Quick start guide
   - Support contact

3. **Feedback Collection**
   - In-app feedback widget
   - Weekly email survey
   - Usage analytics (Google Analytics)

**Launch Day:**

```bash
# Final deployment
./scripts/deploy-all-services.sh

# Smoke test all endpoints
./scripts/smoke-test.sh

# Monitor logs in real-time
gcloud logging tail --resource=cloud_run_revision

# Send beta invites
python scripts/send_beta_invites.py --count 20
```

**Post-Launch Monitoring:**

- Monitor Cloud Logging for errors
- Track user signups and activity
- Collect feedback
- Fix critical bugs within 24 hours
- Weekly retrospective with metrics

---

## Final Commit

```bash
git add docs/ frontend/ backend/ scripts/
git commit -m "feat: complete MVP with all 5 AI features and beta launch"
git tag -a v1.0.0-beta -m "Beta launch - MVP complete"
git push origin main --tags
```

---

# MVP Complete! 🎉

**Delivered Features:**
1. ✅ Invoice Processing with human-in-the-loop validation
2. ✅ Generic OCR (Document AI + Vision + Gemini)
3. ✅ Document Summarization (Vertex AI)
4. ✅ Chat with PDF (RAG with pgvector)
5. ✅ Document Filling (ID extraction + PDF forms)

**Infrastructure:**
- ✅ All-Python microservices on Cloud Run
- ✅ PostgreSQL with pgvector
- ✅ Google Pub/Sub for async processing
- ✅ Cloud Storage for documents
- ✅ Firebase Authentication
- ✅ React frontend with TypeScript
- ✅ Terraform infrastructure as code
- ✅ GitHub Actions CI/CD

**Compliance:**
- ✅ MVP-level GDPR compliance
- ✅ EU AI Act human-in-the-loop validation
- ✅ Audit logging
- ✅ Data encryption at rest and in transit

**Next Steps:**
1. Gather beta user feedback
2. Identify highest-traction vertical
3. Pivot to vertical SaaS for that market
4. Add vertical-specific features
5. Launch paid tiers

**Cost Estimate:** $200-600/month during beta (within budget)

**Timeline:** 12 weeks from start to beta launch ✓
