# PDF Form Templates

This directory contains PDF form templates that can be filled with data extracted from ID documents.

## How to Add a Template

1. Create a fillable PDF form using Adobe Acrobat, LibreOffice, or similar tools
2. Name the form fields according to the mapping in `docfill_worker/processor.py`
3. Save the PDF with a descriptive name (e.g., `romanian_standard_form.pdf`)
4. Place it in this directory
5. Update the template list in `api_gateway/routes/filling.py`

## Standard Field Names

For Romanian forms, use these field names:
- `nume` - Family name (Nume)
- `prenume` - Given names (Prenume)
- `cnp` - Personal Numeric Code (Cod Numeric Personal)
- `data_nasterii` - Date of birth (Data nașterii)
- `locul_nasterii` - Place of birth (Locul nașterii)
- `adresa` - Address (Adresă)
- `seria_ci` - ID series (Seria CI)
- `numar_ci` - ID number (Număr CI)
- `emis_la` - Issue date (Emis la)
- `valabil_pana` - Expiry date (Valabil până la)

For generic forms, use these field names:
- `family_name`
- `given_names`
- `date_of_birth`
- `place_of_birth`
- `nationality`
- `document_number`
- `address`
- `cnp`

## Creating Fillable PDFs

### Using LibreOffice Writer:
1. Create your form in LibreOffice Writer
2. Insert form controls: View → Toolbars → Form Controls
3. Add text fields and set their names
4. Export as PDF: File → Export as PDF → Check "Create PDF Form"

### Using Adobe Acrobat:
1. Open an existing PDF or create one
2. Tools → Prepare Form
3. Add text fields and name them appropriately
4. Save the PDF

## Testing

To test a template:
1. Place the PDF in this directory
2. Upload an ID document through the frontend
3. Select your template from the dropdown
4. Process and download the filled PDF
