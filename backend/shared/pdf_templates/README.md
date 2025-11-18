# PDF Form Templates

This directory contains fillable PDF form templates that can be used with the document filling feature.

## How to Add Templates

1. Create a fillable PDF form using Adobe Acrobat or similar tool
2. Name the form fields according to the mapping in `docfill_worker/processor.py`
3. Save the PDF file in this directory with a descriptive name (e.g., `romanian_standard_form.pdf`)
4. Update the field mapping in `processor.py` if using custom field names

## Required Templates

### romanian_standard_form.pdf
Romanian standard form with the following fields:
- `nume` - Family name (Nume)
- `prenume` - Given names (Prenume)
- `cnp` - Personal Numeric Code (CNP)
- `data_nasterii` - Date of birth
- `locul_nasterii` - Place of birth
- `adresa` - Address
- `seria_ci` - ID series
- `numar_ci` - ID number
- `emis_la` - Issue date
- `valabil_pana` - Expiry date

### Generic Template
For generic forms, use these field names:
- `family_name`
- `given_names`
- `date_of_birth`
- `place_of_birth`
- `nationality`
- `document_number`
- `address`
- `cnp`

## Creating Fillable PDF Forms

You can create fillable PDF forms using:
- **Adobe Acrobat Pro**: Prepare Form tool
- **LibreOffice**: Export to PDF with form fields
- **PDFtk**: Command-line tool to add form fields
- **Online tools**: JotForm, PDFescape, etc.

## Testing Templates

To test a template:
1. Place the PDF in this directory
2. Update the template list in `api_gateway/routes/filling.py`
3. Use the `/v1/filling/templates` endpoint to verify it appears
4. Test filling via the `/v1/filling/extract-and-fill` endpoint

## Notes

- All PDF files in this directory should be fillable forms
- Template names should match the filename without the `.pdf` extension
- Templates are version-controlled - do not include sensitive data
