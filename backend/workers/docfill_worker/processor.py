"""Document filling processor - extract ID data and fill PDF forms."""

from google.cloud import documentai_v1 as documentai, storage
from google.api_core.client_options import ClientOptions
from pypdfform import PdfWrapper
from typing import Dict, Any, Optional
import os
import tempfile
import re
from datetime import datetime

from backend.shared.config import get_settings

settings = get_settings()


class DocumentFillingProcessor:
    """Extract data from IDs and fill PDF forms."""

    def __init__(self):
        self.project_id = settings.project_id
        self.location = "eu"  # EU location for Document AI
        self.id_processor_id = os.getenv("DOCUMENTAI_ID_PROCESSOR_ID")

        if not self.id_processor_id:
            raise ValueError("DOCUMENTAI_ID_PROCESSOR_ID not set")

        # Initialize Document AI client
        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        self.documentai_client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # Storage client
        self.storage_client = storage.Client()

        # Processor name
        self.processor_name = self.documentai_client.processor_path(
            self.project_id, self.location, self.id_processor_id
        )

    def extract_id_data(self, gcs_uri: str) -> Dict[str, Any]:
        """
        Extract data from ID card using Document AI.

        Supports:
        - Romanian ID cards (Carte de Identitate)
        - EU ID cards
        - Passports

        Args:
            gcs_uri: GCS URI of ID card image

        Returns:
            Extracted ID data
        """
        # Configure process request
        request = documentai.ProcessRequest(
            name=self.processor_name,
            gcs_document=documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type="image/jpeg"  # Or auto-detect
            )
        )

        # Process document
        result = self.documentai_client.process_document(request=request)
        document = result.document

        # Extract ID fields
        extracted_data = {
            "document_type": None,
            "family_name": None,
            "given_names": None,
            "date_of_birth": None,
            "place_of_birth": None,
            "nationality": None,
            "document_number": None,
            "issue_date": None,
            "expiry_date": None,
            "address": None,
            "cnp": None,  # Romanian Personal Numeric Code
            "confidence_scores": {},
            "raw_text": document.text,
        }

        # Parse entities
        for entity in document.entities:
            entity_type = entity.type_
            entity_text = entity.mention_text
            confidence = entity.confidence

            # Map Document AI entity types
            field_mapping = {
                "document_type": "document_type",
                "family_name": "family_name",
                "given_name": "given_names",
                "given_names": "given_names",
                "date_of_birth": "date_of_birth",
                "birth_date": "date_of_birth",
                "place_of_birth": "place_of_birth",
                "nationality": "nationality",
                "document_number": "document_number",
                "national_id": "document_number",
                "issue_date": "issue_date",
                "expiration_date": "expiry_date",
                "expiry_date": "expiry_date",
                "address": "address",
            }

            if entity_type in field_mapping:
                field_name = field_mapping[entity_type]
                extracted_data[field_name] = entity_text
                extracted_data["confidence_scores"][field_name] = confidence

            # Romanian-specific: CNP (Cod Numeric Personal)
            if entity_type == "personal_number" or entity_type == "national_id":
                # Validate CNP format (13 digits)
                if re.match(r'^\d{13}$', entity_text):
                    extracted_data["cnp"] = entity_text
                    extracted_data["confidence_scores"]["cnp"] = confidence

        # Post-process dates
        for date_field in ["date_of_birth", "issue_date", "expiry_date"]:
            if extracted_data[date_field]:
                extracted_data[date_field] = self._normalize_date(extracted_data[date_field])

        # Calculate average confidence
        confidences = list(extracted_data["confidence_scores"].values())
        extracted_data["average_confidence"] = (
            sum(confidences) / len(confidences) if confidences else 0
        )

        return extracted_data

    def fill_pdf_form(
        self,
        template_name: str,
        data: Dict[str, Any],
        output_gcs_path: str
    ) -> str:
        """
        Fill PDF form with extracted data.

        Args:
            template_name: Name of PDF template
            data: Extracted ID data
            output_gcs_path: Where to save filled PDF

        Returns:
            GCS URI of filled PDF
        """
        # Get template path
        template_path = self._get_template_path(template_name)
        if not template_path:
            raise ValueError(f"Template {template_name} not found")

        # Map data fields to PDF form fields
        form_data = self._map_data_to_form_fields(data, template_name)

        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_output_path = temp_file.name

        try:
            # Fill PDF form
            pdf = PdfWrapper(template_path)
            filled_pdf = pdf.fill(form_data)

            # Save to temporary file
            with open(temp_output_path, "wb+") as output_file:
                filled_pdf.stream.write_to(output_file)

            # Upload to GCS
            gcs_uri = self._upload_to_gcs(temp_output_path, output_gcs_path)

            return gcs_uri

        finally:
            # Clean up temporary file
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)

    def _get_template_path(self, template_name: str) -> Optional[str]:
        """Get path to PDF template."""
        # Templates stored in backend/shared/pdf_templates/
        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "shared",
            "pdf_templates"
        )

        template_path = os.path.join(templates_dir, f"{template_name}.pdf")

        if os.path.exists(template_path):
            return template_path

        return None

    def _map_data_to_form_fields(
        self,
        data: Dict[str, Any],
        template_name: str
    ) -> Dict[str, str]:
        """
        Map extracted data to PDF form field names.

        Different templates have different field names.
        """
        # Standard Romanian form field mapping
        if template_name == "romanian_standard_form":
            return {
                "nume": data.get("family_name", ""),
                "prenume": data.get("given_names", ""),
                "cnp": data.get("cnp", ""),
                "data_nasterii": data.get("date_of_birth", ""),
                "locul_nasterii": data.get("place_of_birth", ""),
                "adresa": data.get("address", ""),
                "seria_ci": data.get("document_number", "")[:2] if data.get("document_number") else "",
                "numar_ci": data.get("document_number", "")[2:] if data.get("document_number") else "",
                "emis_la": data.get("issue_date", ""),
                "valabil_pana": data.get("expiry_date", ""),
            }

        # Generic mapping
        return {
            "family_name": data.get("family_name", ""),
            "given_names": data.get("given_names", ""),
            "date_of_birth": data.get("date_of_birth", ""),
            "place_of_birth": data.get("place_of_birth", ""),
            "nationality": data.get("nationality", ""),
            "document_number": data.get("document_number", ""),
            "address": data.get("address", ""),
            "cnp": data.get("cnp", ""),
        }

    def _upload_to_gcs(self, local_path: str, gcs_path: str) -> str:
        """Upload file to GCS and return URI."""
        # Parse GCS path
        parts = gcs_path.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1] if len(parts) > 1 else ""

        # Upload
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        blob.upload_from_filename(local_path, content_type="application/pdf")

        return f"gs://{bucket_name}/{blob_path}"

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format."""
        import dateutil.parser

        try:
            parsed = dateutil.parser.parse(date_str)
            return parsed.strftime("%Y-%m-%d")
        except:
            return date_str
