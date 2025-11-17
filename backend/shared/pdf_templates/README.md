# PDF Form Templates

This directory contains fillable PDF form templates used by the document filling worker.

## Adding Templates

1. Create or obtain a fillable PDF form
2. Ensure form fields have proper names
3. Save the PDF file in this directory with a descriptive name (e.g., `romanian_standard_form.pdf`)
4. Update the field mapping in `backend/workers/docfill_worker/processor.py` if needed

## Current Templates

### romanian_standard_form.pdf

**Description:** Standard form for Romanian documents

**Required Fields:**
- `nume` - Family name (Last name)
- `prenume` - Given names (First name)
- `cnp` - Romanian Personal Numeric Code
- `data_nasterii` - Date of birth
- `locul_nasterii` - Place of birth
- `adresa` - Address
- `seria_ci` - ID card series
- `numar_ci` - ID card number
- `emis_la` - Issue date
- `valabil_pana` - Expiry date

## Creating Fillable PDFs

You can create fillable PDFs using:
- Adobe Acrobat Pro
- LibreOffice Draw
- Online tools like PDFescape
- Python libraries like reportlab (for programmatic creation)

## Testing

To test a template:

```bash
cd backend/workers/docfill_worker
python -c "from processor import DocumentFillingProcessor; p = DocumentFillingProcessor(); print(p._get_template_path('romanian_standard_form'))"
```

## Notes

- Template filenames should match the `template_name` used in API requests
- All templates must be fillable PDFs with named form fields
- Keep templates under 10 MB for optimal performance
