# Document AI SaaS - User Guide

## Getting Started

### 1. Sign Up

Visit the application URL and click "Sign Up".

Enter your:
- Email address
- Password (minimum 8 characters)
- Company name

You'll receive a verification email. Click the link to activate your account.

### 2. Upload Your First Document

1. Click "Upload Document" in the sidebar
2. Select document type:
   - **Invoice**: For invoices, receipts, purchase orders
   - **Contract**: For contracts and agreements
   - **ID Card**: For Romanian ID cards, passports
   - **Generic**: For any other document
3. Click "Choose File" and select a PDF, JPG, or PNG (max 50 MB)
4. Click "Upload and Process"

Processing takes 10-30 seconds depending on document type.

## Features

### Invoice Processing

**What it does**: Extracts key data from invoices automatically.

**How to use**:
1. Upload invoice (PDF or image)
2. Wait for processing (15-20 seconds)
3. Review extracted data:
   - Supplier name
   - Invoice number
   - Date
   - Line items
   - Total amount
4. Click "Edit" to correct any errors
5. Click "Approve" to finalize
6. Export to JSON or CSV

**Tips**:
- Ensure invoice is clear and readable
- Best results with digital PDFs
- Scanned invoices work too (may be less accurate)

### Generic OCR

**What it does**: Extracts all text from any document.

**How to use**:
1. Upload document
2. Select "Generic OCR"
3. Choose OCR method:
   - **Auto**: We choose the best method (recommended)
   - **Standard**: Fast, good for clear documents
   - **Advanced**: Slower, better for poor quality
4. Wait for processing (10-60 seconds)
5. Copy or download extracted text

**Tips**:
- Use "Advanced" for handwritten or low-quality scans
- Text layout may not be preserved perfectly
- For tables, consider using spreadsheet export

### Document Summarization

**What it does**: Creates concise summaries of long documents.

**How to use**:
1. Upload document (works best with multi-page PDFs)
2. Select "Summarize"
3. Choose options:
   - **Length**: Concise (1 paragraph) or Detailed (multiple paragraphs)
   - **Model**: Flash (faster) or Pro (higher quality)
4. Wait for processing (20-40 seconds)
5. Review summary and key points
6. Copy or download

**Tips**:
- Best for documents over 2 pages
- Use "Pro" model for complex documents
- Summaries are in English (even if document is Romanian)

### Chat with PDF

**What it does**: Ask questions about your document in natural language.

**How to use**:
1. Upload document
2. Click "Chat" tab
3. Type your question (e.g., "What is the total contract value?")
4. Get instant answer with source citations
5. Continue conversation with follow-up questions

**Example questions**:
- "Summarize the main terms of this contract"
- "What are the payment terms?"
- "Who are the parties involved?"
- "What is the delivery date?"

**Tips**:
- Be specific in your questions
- System shows which page the answer came from
- Works best with structured documents

### Document Filling (Romanian IDs)

**What it does**: Automatically fills PDF forms using data from Romanian ID cards.

**How to use**:
1. Upload Romanian ID card (buletin) photo
2. Select "Document Filling"
3. Choose PDF template to fill (e.g., "Cerere tip")
4. System extracts: Name, CNP, Birth date, Address
5. Review pre-filled data
6. Click "Generate PDF"
7. Download filled form

**Tips**:
- Ensure ID card photo is clear and well-lit
- All 4 corners should be visible
- Review extracted data before generating PDF

## Account Management

### Usage Limits (Free Tier)

- 50 documents per month
- 500 chat messages per month
- Document storage: 30 days

### Data Export

To export all your data:
1. Go to Settings > Data & Privacy
2. Click "Export My Data"
3. Download ZIP file with all documents and extracted data

### Delete Account

To delete your account:
1. Go to Settings > Data & Privacy
2. Click "Delete Account"
3. Confirm deletion
4. All your data will be permanently deleted within 7 days

## Troubleshooting

### Processing Failed

**Possible causes**:
- Document quality too poor
- File corrupted
- Unsupported format

**Solutions**:
- Try higher quality scan
- Re-save PDF
- Convert to PDF if image

### Slow Processing

**Possible causes**:
- Large file size
- Complex document
- High server load

**Solutions**:
- Compress PDF before upload
- Try during off-peak hours
- Contact support if persistent

### Incorrect Data Extraction

**For invoices**:
- Use "Edit" feature to correct
- Send feedback to improve our system

**For OCR**:
- Try "Advanced" OCR method
- Improve document quality

## Support

- Email: support@documentai.com
- Live chat: Available in app (Mon-Fri 9 AM - 5 PM CET)
- Help center: https://help.documentai.com

## Privacy & Security

Your data security is our priority:
- All documents encrypted at rest and in transit
- Data stored in EU (GDPR compliant)
- You own your data - export or delete anytime
- No data shared with third parties
- Regular security audits

For full privacy policy, visit: /privacy-policy
