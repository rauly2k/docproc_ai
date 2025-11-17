# End-to-End Testing Guide: Document AI SaaS
## Complete Step-by-Step Testing After Phase 7 Implementation

**Version:** 1.0
**Last Updated:** 2025-11-17
**Purpose:** Comprehensive guide to test all features of the Document AI SaaS platform

---

## Table of Contents

1. [Pre-Testing Setup](#pre-testing-setup)
2. [Accessing the Application](#accessing-the-application)
3. [Testing Feature 1: Invoice Processing](#feature-1-invoice-processing)
4. [Testing Feature 2: Generic OCR](#feature-2-generic-ocr)
5. [Testing Feature 3: Document Summarization](#feature-3-document-summarization)
6. [Testing Feature 4: Chat with PDF](#feature-4-chat-with-pdf)
7. [Testing Feature 5: Document Filling](#feature-5-document-filling)
8. [Admin Features Testing](#admin-features-testing)
9. [Performance Testing](#performance-testing)
10. [Mobile/Responsive Testing](#mobileresponsive-testing)
11. [Security Testing](#security-testing)
12. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Pre-Testing Setup

### 1. Get Your Application URLs

After Phase 7 deployment, you should have:

```bash
# Backend API URL
export API_URL="https://api-gateway-xxx-uc.a.run.app"

# Frontend URL (deployed on Vercel)
export FRONTEND_URL="https://your-app.vercel.app"

# Check if services are running
curl $API_URL/health
# Expected: {"status": "healthy", "timestamp": "2025-11-17T..."}
```

### 2. Prepare Test Documents

Download or prepare these test documents:

1. **Sample Invoice PDF** (for invoice processing)
   - Download from: https://templates.invoicehome.com/sample-invoice.pdf
   - Or use any real invoice PDF you have

2. **Sample Contract PDF** (for OCR and summarization)
   - Any multi-page PDF with text (3-10 pages ideal)

3. **Sample Romanian ID Card Image** (for document filling)
   - High-quality photo or scan of a Romanian "Carte de Identitate"
   - Ensure all 4 corners are visible

4. **Handwritten Document** (for advanced OCR testing)
   - Photo of handwritten note or form

5. **Large PDF** (for performance testing)
   - Document with 50+ pages

### 3. Create Test Account Credentials

You'll need:
- A valid email address (for signup)
- A password (minimum 8 characters)
- Company name (for tenant creation)

---

## Accessing the Application

### Step 1: Open the Frontend

1. Open your browser (Chrome, Firefox, or Safari recommended)
2. Navigate to: `https://your-app.vercel.app`
3. You should see the **landing page** or **login screen**

**Expected View:**
```
┌─────────────────────────────────────┐
│   Document AI SaaS                  │
│                                     │
│   Intelligent Document Processing   │
│   with AI                           │
│                                     │
│   [Sign Up]  [Log In]              │
└─────────────────────────────────────┘
```

### Step 2: Sign Up (First Time)

1. Click **"Sign Up"** button
2. Enter:
   - **Email:** test@yourdomain.com
   - **Password:** YourPassword123!
   - **Company Name:** Test Company
3. Click **"Create Account"**
4. **Verify email:**
   - Check your email inbox
   - Click verification link
   - Return to login page

**Expected Outcome:**
- Redirected to email verification screen
- Receive email within 1-2 minutes
- After verification, account is active

### Step 3: Log In

1. Enter your email and password
2. Click **"Log In"**
3. You should be redirected to the **Dashboard**

**Expected Dashboard View:**
```
┌──────────────────────────────────────────────────────┐
│  📁 Document AI SaaS         [User Menu ▼]          │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Dashboard                                           │
│                                                      │
│  📊 Usage This Month                                 │
│  ├─ Documents Processed: 0                          │
│  ├─ Invoice Extractions: 0                          │
│  ├─ OCR Operations: 0                               │
│  ├─ Summaries Generated: 0                          │
│  └─ Chat Messages: 0                                │
│                                                      │
│  📄 Recent Documents                                 │
│  (No documents yet)                                  │
│                                                      │
│  [➕ Upload New Document]                            │
└──────────────────────────────────────────────────────┘
```

---

## Feature 1: Invoice Processing

### Objective
Test the automated invoice data extraction feature.

### Step-by-Step Testing

#### 1.1: Upload Invoice

1. From Dashboard, click **"Upload New Document"** or navigate to **Upload** page
2. Select document type: **"Invoice"**
3. Click **"Choose File"**
4. Select your sample invoice PDF
5. Click **"Upload and Process"**

**What to Observe:**
- Upload progress bar appears
- File uploads within 2-5 seconds
- You see "Processing..." status

**Expected Response:**
```json
{
  "document_id": "doc_abc123xyz",
  "status": "processing",
  "filename": "sample-invoice.pdf",
  "message": "Invoice processing started. This may take 15-20 seconds."
}
```

#### 1.2: Monitor Processing

1. You should be redirected to document details page
2. Watch the status change:
   - `uploading` → `processing` → `completed`
3. Processing should complete within 20-30 seconds

**Status Indicators:**
- **Uploading:** Blue spinning icon
- **Processing:** Orange pulsing icon + progress bar
- **Completed:** Green checkmark
- **Failed:** Red X with error message

#### 1.3: Review Extracted Data

Once processing is complete, you should see:

**Extracted Invoice Data:**
```
┌────────────────────────────────────────┐
│  Invoice Details                       │
├────────────────────────────────────────┤
│  Vendor Name: Acme Supplies Inc.       │
│  Invoice Number: INV-2025-001          │
│  Invoice Date: 2025-01-15              │
│  Due Date: 2025-02-15                  │
│                                        │
│  Subtotal: $1,000.00                   │
│  Tax (19%): $190.00                    │
│  Total Amount: $1,190.00               │
│  Currency: USD                         │
│                                        │
│  Line Items:                           │
│  1. Office Supplies (Qty: 10)          │
│     Unit Price: $50.00                 │
│     Amount: $500.00                    │
│                                        │
│  2. Printer Paper (Qty: 20)            │
│     Unit Price: $25.00                 │
│     Amount: $500.00                    │
│                                        │
│  Confidence Score: 92%                 │
│                                        │
│  [✏️ Edit] [✅ Validate] [📥 Export]   │
└────────────────────────────────────────┘
```

#### 1.4: Validate and Correct Data

1. Click **"Edit"** button
2. All fields become editable
3. Make a test change (e.g., change total from $1,190 to $1,200)
4. Add validation note: "Corrected total amount"
5. Click **"Save"** or **"Approve"**

**Expected Outcome:**
- Changes are saved
- Status changes to "Validated"
- You see confirmation message: "Invoice validated successfully"
- Audit log is created (viewable by admin)

#### 1.5: Export Data

1. Click **"Export"** dropdown
2. Choose format:
   - **JSON** (for developers/integrations)
   - **CSV** (for Excel/spreadsheets)
3. Click download

**Expected Files:**
- `invoice_doc_abc123xyz.json` (structured JSON)
- `invoice_doc_abc123xyz.csv` (spreadsheet-friendly)

**Sample JSON Export:**
```json
{
  "document_id": "doc_abc123xyz",
  "vendor_name": "Acme Supplies Inc.",
  "invoice_number": "INV-2025-001",
  "invoice_date": "2025-01-15",
  "total_amount": 1200.00,
  "currency": "USD",
  "line_items": [
    {
      "description": "Office Supplies",
      "quantity": 10,
      "unit_price": 50.00,
      "amount": 500.00
    }
  ],
  "is_validated": true,
  "validated_by": "user_xyz789",
  "validation_notes": "Corrected total amount"
}
```

#### 1.6: Test Edge Cases

**Test with:**

1. **Rotated PDF** (90° or 180°)
   - Upload and verify it still extracts correctly

2. **Scanned Invoice** (image quality)
   - Test with lower quality scan
   - Check if confidence score is lower

3. **Multi-currency Invoice** (EUR, RON, GBP)
   - Verify currency is correctly detected

4. **Missing Fields**
   - Upload invoice with missing vendor name or date
   - System should flag as "Requires Review"

**Success Criteria:**
- ✅ All invoices process within 30 seconds
- ✅ Extraction accuracy ≥ 85% (based on confidence scores)
- ✅ Validation workflow works correctly
- ✅ Export generates valid JSON/CSV
- ✅ No crashes or errors

---

## Feature 2: Generic OCR

### Objective
Extract text from any document (contracts, letters, forms).

### Step-by-Step Testing

#### 2.1: Upload Document for OCR

1. Navigate to **Upload** page
2. Select document type: **"Generic"**
3. Upload your sample contract or document
4. Select OCR method:
   - **Auto** (recommended)
   - **Standard OCR** (fast, for clean PDFs)
   - **Advanced OCR** (slower, better for poor quality)
5. Click **"Upload and Process"**

#### 2.2: View OCR Results

**Expected View:**
```
┌────────────────────────────────────────┐
│  OCR Results                           │
├────────────────────────────────────────┤
│  Document: contract.pdf                │
│  Pages: 5                              │
│  Confidence: 96%                       │
│  Processing Time: 12 seconds           │
│  OCR Method: Document AI Standard      │
│                                        │
│  Extracted Text:                       │
│  ┌──────────────────────────────────┐ │
│  │ This agreement is entered into   │ │
│  │ on January 1, 2025 between...    │ │
│  │                                  │ │
│  │ Article 1: Definitions           │ │
│  │ ...                              │ │
│  │                                  │ │
│  │ [Full text content]              │ │
│  └──────────────────────────────────┘ │
│                                        │
│  [📋 Copy Text] [📥 Download TXT]     │
└────────────────────────────────────────┘
```

#### 2.3: Test Advanced OCR

1. Upload a **handwritten document** or **low-quality scan**
2. Select **"Advanced OCR"** (uses Gemini Vision)
3. Wait for processing (may take 30-60 seconds)
4. Compare accuracy vs Standard OCR

**Expected Outcome:**
- Advanced OCR handles poor quality better
- Processing takes longer but accuracy improves
- Confidence score shown for each page

#### 2.4: Copy and Download

1. Click **"Copy Text"** - text copied to clipboard
2. Paste into notepad to verify
3. Click **"Download TXT"** - saves as plain text file

**Success Criteria:**
- ✅ Clean documents: 95%+ accuracy
- ✅ Scanned documents: 85%+ accuracy
- ✅ Handwritten: 70%+ accuracy (with Advanced OCR)
- ✅ Copy/download functions work
- ✅ Processing time < 60 seconds

---

## Feature 3: Document Summarization

### Objective
Generate AI summaries of long documents.

### Step-by-Step Testing

#### 3.1: Upload Long Document

1. Upload a multi-page PDF (5+ pages recommended)
2. Select document type: **"Contract"** or **"Generic"**
3. After upload, navigate to document details
4. Click **"Summarize"** tab or button

#### 3.2: Choose Summarization Options

**Options to Select:**
- **Summary Length:**
  - Concise (1 paragraph, ~100 words)
  - Detailed (multiple paragraphs, ~300 words)
- **Model:**
  - Flash (faster, good quality) - FREE
  - Pro (slower, highest quality) - May have costs

5. Click **"Generate Summary"**

#### 3.3: Review Summary

**Expected Summary View:**
```
┌────────────────────────────────────────┐
│  Document Summary                      │
├────────────────────────────────────────┤
│  Document: contract.pdf (10 pages)     │
│  Model Used: Gemini 1.5 Flash          │
│  Generated: 2025-11-17 10:30 AM        │
│  Processing Time: 18 seconds           │
│                                        │
│  Summary:                              │
│  This agreement establishes a service  │
│  contract between Party A and Party B  │
│  for software development services.    │
│  The contract term is 12 months with   │
│  a total value of $50,000. Key terms   │
│  include monthly deliverables, payment │
│  milestones, and intellectual property │
│  provisions.                           │
│                                        │
│  Key Points:                           │
│  • Contract Duration: 12 months        │
│  • Total Value: $50,000               │
│  • Payment Terms: Monthly installments │
│  • Deliverables: Software modules      │
│  • IP Rights: Transferred to client    │
│                                        │
│  [📋 Copy] [📥 Download] [🔄 Regenerate]│
└────────────────────────────────────────┘
```

#### 3.4: Test Different Document Types

**Test with:**
1. **Legal contract** → Should highlight terms, parties, obligations
2. **Research paper** → Should summarize findings, methodology
3. **Technical manual** → Should extract key instructions
4. **Financial report** → Should highlight numbers, trends

#### 3.5: Compare Models

1. Summarize same document with **Flash** model
2. Regenerate with **Pro** model
3. Compare:
   - Quality of summary
   - Processing time
   - Detail level

**Expected Differences:**
- Flash: 15-20 seconds, good summaries
- Pro: 30-40 seconds, more nuanced summaries

**Success Criteria:**
- ✅ Summaries are accurate and coherent
- ✅ Key points are identified correctly
- ✅ Processing time < 40 seconds
- ✅ Copy/download works
- ✅ No hallucinated information

---

## Feature 4: Chat with PDF

### Objective
Ask questions about document content using RAG (Retrieval Augmented Generation).

### Step-by-Step Testing

#### 4.1: Index Document for Chat

1. Upload a document (or use existing one)
2. Click **"Chat"** tab
3. If document not indexed, click **"Index for Chat"**
4. Wait for indexing (20-40 seconds for 10-page doc)

**Indexing Status:**
```
Indexing document...
Progress: [████████░░] 80%
Creating embeddings for 45 chunks...
```

#### 4.2: Ask Questions

**Example Questions to Test:**

1. **Factual Question:**
   - Question: "What is the total contract value?"
   - Expected: "$50,000" (with source citation)

2. **Comparative Question:**
   - Question: "What are the payment terms?"
   - Expected: "Monthly installments of $4,166.67 over 12 months"

3. **Summarization Question:**
   - Question: "Summarize the main obligations of Party A"
   - Expected: Paragraph listing obligations

4. **Complex Question:**
   - Question: "What happens if the project is delayed by more than 30 days?"
   - Expected: Answer from termination clause

#### 4.3: Chat Interface

**Expected Chat View:**
```
┌────────────────────────────────────────┐
│  Chat with: contract.pdf               │
├────────────────────────────────────────┤
│                                        │
│  You: What is the total contract value?│
│                                        │
│  🤖 Assistant:                         │
│  According to the contract, the total  │
│  value is $50,000, payable in monthly  │
│  installments over 12 months.          │
│                                        │
│  📄 Sources:                           │
│  • Page 2, Section 3.1 (Relevance: 94%)│
│                                        │
│  You: [Type your question...]          │
│  [Send]                                │
└────────────────────────────────────────┘
```

#### 4.4: Verify Source Citations

1. Click on **"Page 2, Section 3.1"** source link
2. PDF viewer should scroll to that exact location
3. Highlighted text should match the answer

#### 4.5: Multi-Document Chat (Advanced)

1. Select multiple documents (if supported)
2. Ask: "Compare the payment terms in both contracts"
3. System should reference both documents

#### 4.6: Test Edge Cases

**Test with:**
1. **Question not in document** → "I don't have information about that in this document"
2. **Ambiguous question** → System asks for clarification
3. **Long conversation** (10+ messages) → Context maintained
4. **Different languages** (if document has Romanian sections)

**Success Criteria:**
- ✅ Answers are accurate (verified against source)
- ✅ Source citations are correct
- ✅ Response time < 5 seconds
- ✅ Handles follow-up questions
- ✅ No hallucinations (makes up information)

---

## Feature 5: Document Filling

### Objective
Automatically fill PDF forms using data extracted from Romanian ID cards.

### Step-by-Step Testing

#### 5.1: Upload Romanian ID Card

1. Navigate to **Document Filling** page
2. Upload photo/scan of Romanian ID card (Buletin)
3. System extracts data automatically

**Expected Extraction:**
```
┌────────────────────────────────────────┐
│  ID Card Data Extraction               │
├────────────────────────────────────────┤
│  Extracted Fields:                     │
│                                        │
│  Nume (Surname): POPESCU               │
│  Prenume (Given Names): ION GEORGE     │
│  CNP: 1850612345678                    │
│  Data Nașterii (DOB): 12 Jun 1985      │
│  Locul Nașterii: București             │
│  Adresă: Str. Victoriei nr. 25,        │
│          București, Sector 1           │
│  Serie + Număr: RX 123456              │
│  Valabil până: 12 Jun 2030             │
│                                        │
│  Confidence: 91%                       │
│                                        │
│  [✏️ Edit] [Next: Choose Template]     │
└────────────────────────────────────────┘
```

#### 5.2: Correct Data (if needed)

1. Click **"Edit"** if any field is incorrect
2. Manually correct extracted data
3. Click **"Save"**

#### 5.3: Select PDF Template

1. Click **"Next: Choose Template"**
2. Select from available templates:
   - **Cerere tip** (Generic application form)
   - **Declarație pe propria răspundere** (Self-declaration)
   - **Formular înregistrare** (Registration form)
3. Click template to preview

#### 5.4: Generate Filled PDF

1. Review data mapping:
   - Field "Nume Prenume" ← POPESCU ION GEORGE
   - Field "CNP" ← 1850612345678
   - etc.
2. Click **"Generate Filled PDF"**
3. Wait 5-10 seconds

#### 5.5: Review and Download

**Filled PDF Preview:**
```
┌────────────────────────────────────────┐
│  Filled Form Preview                   │
├────────────────────────────────────────┤
│  Template: Cerere tip                  │
│                                        │
│  [PDF Preview with filled fields]      │
│                                        │
│  Nume: POPESCU                         │
│  Prenume: ION GEORGE                   │
│  CNP: 1850612345678                    │
│  Data nașterii: 12.06.1985             │
│  ...                                   │
│                                        │
│  [📥 Download PDF] [🔄 Regenerate]     │
└────────────────────────────────────────┘
```

1. Click **"Download PDF"**
2. Open PDF in viewer (Adobe, Chrome, etc.)
3. Verify all fields are correctly filled

#### 5.6: Test Different ID Types

**Test with:**
1. **Old format ID** (before 2009)
2. **New format ID** (after 2009)
3. **Worn/damaged ID** (test OCR robustness)
4. **Passport** (if supported)

**Success Criteria:**
- ✅ Data extraction accuracy ≥ 90%
- ✅ All fields correctly mapped to template
- ✅ PDF is downloadable and valid
- ✅ Forms can be opened in Adobe Reader
- ✅ Processing time < 15 seconds

---

## Admin Features Testing

### Objective
Test administrative functions for user management and monitoring.

### Step-by-Step Testing

#### 6.1: Access Admin Dashboard

1. Log in as admin user
2. Navigate to **Admin** section (sidebar or top menu)
3. You should see admin-only features

**Admin Dashboard:**
```
┌────────────────────────────────────────┐
│  Admin Dashboard                       │
├────────────────────────────────────────┤
│  📊 System Stats (Last 30 days)        │
│  ├─ Total Users: 12                    │
│  ├─ Active Users: 8                    │
│  ├─ Documents Processed: 145           │
│  ├─ Total Storage Used: 2.3 GB         │
│  └─ API Calls This Month: 1,203        │
│                                        │
│  🧑‍💼 User Management                     │
│  ├─ View All Users                     │
│  ├─ Create New User                    │
│  └─ Manage Roles                       │
│                                        │
│  📝 Audit Logs                         │
│  ├─ Recent Activity                    │
│  └─ Compliance Reports                 │
│                                        │
│  ⚙️ System Health                      │
│  ├─ API Status: 🟢 Healthy            │
│  ├─ Database: 🟢 Connected            │
│  ├─ Workers: 🟢 All Running           │
│  └─ Error Rate: 0.8%                  │
└────────────────────────────────────────┘
```

#### 6.2: View Audit Logs

1. Click **"Audit Logs"**
2. Filter by:
   - User
   - Action type (upload, validation, export)
   - Date range
3. Verify all actions are logged

**Sample Audit Log:**
```
| Timestamp          | User          | Action           | Details             |
|--------------------|---------------|------------------|---------------------|
| 2025-11-17 10:30   | user@test.com | document_upload  | invoice.pdf         |
| 2025-11-17 10:31   | user@test.com | invoice_validate | doc_abc123xyz       |
| 2025-11-17 10:32   | user@test.com | data_export      | JSON format         |
```

#### 6.3: User Management

1. Click **"View All Users"**
2. Select a user
3. Update role: User → Admin (or vice versa)
4. Save changes
5. Verify role change took effect

#### 6.4: Export User Data (GDPR)

1. Select a user
2. Click **"Export User Data"**
3. Download ZIP file
4. Verify ZIP contains:
   - All user documents
   - Extracted data (JSON)
   - Audit logs
   - Account information

#### 6.5: Delete User Account (GDPR)

1. Select test user account
2. Click **"Delete Account"**
3. Confirm deletion
4. Verify:
   - User can't log in
   - All documents deleted from GCS
   - Database records marked as deleted
   - Audit log entry created

**Success Criteria:**
- ✅ Admin dashboard loads correctly
- ✅ All stats are accurate
- ✅ Audit logs capture all actions
- ✅ User management functions work
- ✅ GDPR export/delete work correctly

---

## Performance Testing

### Objective
Verify application performs well under load.

### 7.1: Response Time Testing

**Test API Response Times:**

```bash
# Test document list endpoint
time curl -H "Authorization: Bearer $TOKEN" \
  $API_URL/v1/documents

# Expected: < 200ms

# Test document details
time curl -H "Authorization: Bearer $TOKEN" \
  $API_URL/v1/documents/doc_abc123xyz

# Expected: < 300ms (cached), < 500ms (uncached)
```

### 7.2: Upload Large File

1. Upload a 50 MB PDF
2. Monitor upload progress bar
3. Verify upload completes within 30 seconds (on good connection)

**Expected Behavior:**
- Upload progress updates smoothly
- No timeout errors
- Processing starts immediately after upload

### 7.3: Concurrent Processing

1. Upload 5 documents simultaneously
2. Watch processing status for all
3. Verify all complete within 2 minutes

### 7.4: Frontend Performance

**Use Lighthouse Audit:**

```bash
# Run Lighthouse
npx lighthouse https://your-app.vercel.app --view

# Target Scores:
# Performance: 90+
# Accessibility: 95+
# Best Practices: 90+
# SEO: 90+
```

**Check Bundle Size:**
```bash
# Open browser DevTools
# Network tab → Reload page
# Check:
# - Initial bundle < 500 KB
# - Total page weight < 2 MB
# - First Contentful Paint < 1.5s
# - Time to Interactive < 3s
```

### 7.5: Database Query Performance

**Monitor slow queries (Admin access required):**

```sql
-- Connect to Cloud SQL
gcloud sql connect documentai-db --user=postgres

-- Check slow queries
SELECT query, calls, mean_exec_time, max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Expected: All queries < 100ms average
```

**Success Criteria:**
- ✅ API responses < 200ms (p95)
- ✅ Document processing < 30s for invoices
- ✅ Frontend Lighthouse score 90+
- ✅ No timeouts under normal load
- ✅ Database queries optimized

---

## Mobile/Responsive Testing

### Objective
Ensure app works on mobile devices and tablets.

### 8.1: Test on Mobile Devices

**Devices to Test:**
- iPhone (Safari, Chrome)
- Android phone (Chrome)
- iPad/Tablet

**Or use Chrome DevTools:**
1. Open Chrome DevTools (F12)
2. Click device toolbar icon (Ctrl+Shift+M)
3. Select devices:
   - iPhone 12 Pro (390x844)
   - Samsung Galaxy S20 (360x800)
   - iPad Pro (1024x1366)

### 8.2: Mobile Navigation Test

**Test Flow:**
1. **Login** → Should fit screen, no horizontal scroll
2. **Dashboard** → Cards stack vertically, readable
3. **Upload** → File picker works, drag-drop disabled on mobile
4. **Document View** → PDF preview scales correctly
5. **Chat** → Input keyboard doesn't cover messages

**Expected Behavior:**
- All buttons large enough to tap (min 44x44px)
- No horizontal scrolling
- Text is readable without zooming
- Forms are easy to fill on mobile keyboard

### 8.3: Touch Gestures

**Test:**
- ✅ Tap buttons (no double-tap delay)
- ✅ Scroll lists smoothly
- ✅ Pinch to zoom on PDF previews
- ✅ Swipe gestures (if applicable)

### 8.4: Mobile-Specific Issues

**Check for:**
- Font sizes ≥ 16px (prevents zoom on iOS)
- Touch targets ≥ 44px
- No hover-only features
- Autocomplete works for login forms
- File upload works from camera

**Success Criteria:**
- ✅ App is fully functional on mobile
- ✅ No horizontal scrolling
- ✅ All features accessible via touch
- ✅ Upload from camera works (mobile)
- ✅ Lighthouse Mobile score 85+

---

## Security Testing

### Objective
Verify security measures are working.

### 9.1: Authentication Testing

**Test Cases:**

1. **Access without login:**
   ```bash
   curl $API_URL/v1/documents
   # Expected: 401 Unauthorized
   ```

2. **Invalid token:**
   ```bash
   curl -H "Authorization: Bearer invalid_token" \
     $API_URL/v1/documents
   # Expected: 401 Unauthorized
   ```

3. **Expired token:**
   - Log in
   - Wait 2 hours
   - Try to access document
   - Expected: Automatic token refresh or redirect to login

### 9.2: Tenant Isolation Testing

**Critical Security Test:**

1. Create two test accounts (User A and User B)
2. **User A:** Upload document, note document_id
3. **User B:** Try to access User A's document:
   ```
   GET /v1/documents/{user_a_document_id}
   ```
4. **Expected:** 404 Not Found (NOT 403, to prevent info disclosure)

5. **Try direct GCS access:**
   ```bash
   curl https://storage.googleapis.com/bucket/tenant_a/document.pdf
   # Expected: 403 Forbidden (no public access)
   ```

### 9.3: Input Validation Testing

**SQL Injection Attempt:**
```bash
curl -X GET "$API_URL/v1/documents?status='; DROP TABLE documents; --"
# Expected: 422 Validation Error (not SQL error!)
```

**XSS Attempt:**
1. Upload document with filename: `<script>alert('xss')</script>.pdf`
2. View document list
3. **Expected:** Filename is escaped, no script execution

**Path Traversal Attempt:**
```bash
curl -X POST $API_URL/v1/documents/upload \
  -F "file=@test.pdf" \
  -F "filename=../../../etc/passwd"
# Expected: 422 Validation Error
```

### 9.4: Rate Limiting Testing

**Test Upload Rate Limit:**
```bash
# Try to upload 15 documents rapidly (limit is 10/min)
for i in {1..15}; do
  curl -X POST $API_URL/v1/documents/upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test.pdf"
  echo "Upload $i"
done

# Expected: First 10 succeed, #11-15 return 429 Too Many Requests
```

### 9.5: Security Headers Check

```bash
curl -I $API_URL/health

# Verify headers present:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=31536000
# Content-Security-Policy: ...
```

**Success Criteria:**
- ✅ All unauthenticated requests blocked
- ✅ Tenant isolation enforced
- ✅ No SQL injection possible
- ✅ No XSS vulnerabilities
- ✅ Rate limiting works
- ✅ All security headers present

---

## Troubleshooting Common Issues

### Issue 1: Document Processing Stuck

**Symptoms:**
- Status shows "Processing..." for > 5 minutes
- No error message

**Debug Steps:**
1. Check worker logs:
   ```bash
   gcloud run services logs read invoice-worker \
     --region=europe-west1 --limit=50
   ```

2. Check Pub/Sub queue:
   ```bash
   gcloud pubsub subscriptions list
   # Check num_unacked_messages
   ```

3. **Fix:**
   - If worker crashed: Restart Cloud Run service
   - If queue backed up: Scale up workers
   - If document is corrupted: Mark as failed and notify user

### Issue 2: Login Fails

**Symptoms:**
- "Invalid credentials" error
- Or redirect loop

**Debug Steps:**
1. Check Firebase Auth status
2. Verify email is verified
3. Clear browser cache/cookies
4. Try incognito mode
5. Check API logs for auth errors

### Issue 3: Upload Fails

**Symptoms:**
- "Upload failed" error
- Or progress bar stuck at 0%

**Checks:**
- File size < 50 MB?
- File type is PDF, JPG, or PNG?
- Network connection stable?
- CORS errors in browser console?

**Fix:**
- Reduce file size (compress PDF)
- Convert file to PDF
- Check CORS configuration in API Gateway

### Issue 4: Slow Performance

**Symptoms:**
- Page loads slowly
- API responses > 2 seconds

**Debug Steps:**
1. Run Lighthouse audit
2. Check Network tab in DevTools
3. Identify slow requests
4. Check database query performance
5. Verify Redis cache is working

**Optimizations:**
- Enable caching
- Optimize database indexes
- Scale up Cloud Run instances
- Use CDN for static assets

### Issue 5: Blank Page or 500 Error

**Symptoms:**
- White screen
- "Internal Server Error"

**Debug Steps:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Check API logs:
   ```bash
   gcloud logging read "severity=ERROR" \
     --limit=20 --format=json
   ```

**Common Causes:**
- Database connection failure
- Missing environment variables
- Recent deployment broke something

**Fix:**
- Rollback to previous version
- Check env vars are set
- Restart services

---

## Testing Completion Checklist

### ✅ Functional Testing
- [ ] Invoice Processing (all test cases passed)
- [ ] Generic OCR (all test cases passed)
- [ ] Document Summarization (all test cases passed)
- [ ] Chat with PDF (all test cases passed)
- [ ] Document Filling (all test cases passed)
- [ ] Admin Features (all test cases passed)

### ✅ Performance Testing
- [ ] API response times < 200ms (p95)
- [ ] Document processing < 30s
- [ ] Frontend Lighthouse score ≥ 90
- [ ] No timeout errors
- [ ] Database queries optimized

### ✅ Mobile/Responsive Testing
- [ ] Works on iPhone
- [ ] Works on Android
- [ ] Works on iPad/Tablet
- [ ] No horizontal scrolling
- [ ] Touch gestures work

### ✅ Security Testing
- [ ] Authentication works correctly
- [ ] Tenant isolation enforced
- [ ] No SQL injection possible
- [ ] No XSS vulnerabilities
- [ ] Rate limiting works
- [ ] Security headers present

### ✅ Edge Cases
- [ ] Large files (50 MB) handled
- [ ] Poor quality scans processed
- [ ] Empty/missing fields handled gracefully
- [ ] Error messages are user-friendly
- [ ] Concurrent uploads work

---

## Final Verification

**After completing all tests:**

1. **Document Results:**
   - Create spreadsheet with test results
   - Note all issues found
   - Categorize: Critical, High, Medium, Low

2. **File Bugs:**
   - Create GitHub issues for all bugs
   - Add screenshots/logs
   - Assign priority and owner

3. **Sign-Off:**
   - All critical bugs fixed?
   - All features work as expected?
   - Performance meets targets?
   - Security audit passed?

4. **Ready for Beta/Launch:**
   - If YES → Proceed to beta user onboarding
   - If NO → Fix critical issues, re-test, repeat

---

## Quick Reference Commands

```bash
# Health check
curl $API_URL/health

# List documents (requires auth token)
curl -H "Authorization: Bearer $TOKEN" $API_URL/v1/documents

# Check Cloud Run services
gcloud run services list --region=europe-west1

# View logs
gcloud run services logs read api-gateway --region=europe-west1 --limit=50

# Check database
gcloud sql instances describe documentai-db

# Monitor dashboard
open https://console.cloud.google.com/monitoring/dashboards

# Run Lighthouse
npx lighthouse https://your-app.vercel.app --view
```

---

## Support and Documentation

- **User Guide:** `/docs/user-guide.md`
- **API Docs:** `https://api-gateway-xxx.run.app/docs`
- **Admin Guide:** `/docs/admin-guide.md`
- **Deployment Guide:** `/docs/deployment-guide.md`

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Maintained By:** Development Team
**Contact:** support@documentai.com
