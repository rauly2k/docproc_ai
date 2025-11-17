"""Invoice processing using Google Document AI."""

from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from typing import Dict, Any, List
import os

from backend.shared.config import get_settings

settings = get_settings()


class InvoiceProcessor:
    """Process invoices using Document AI."""

    def __init__(self):
        self.project_id = settings.project_id
        self.location = "us"  # Document AI location
        self.processor_id = os.getenv("DOCUMENTAI_INVOICE_PROCESSOR_ID")

        if not self.processor_id:
            raise ValueError("DOCUMENTAI_INVOICE_PROCESSOR_ID environment variable not set")

        # Initialize Document AI client
        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        self.client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # Construct processor name
        self.processor_name = self.client.processor_path(
            self.project_id, self.location, self.processor_id
        )

    def process_invoice_from_gcs(self, gcs_uri: str) -> Dict[str, Any]:
        """
        Process invoice from Google Cloud Storage.

        Args:
            gcs_uri: GCS URI (gs://bucket/path/to/invoice.pdf)

        Returns:
            Parsed invoice data
        """
        # Configure the process request
        request = documentai.ProcessRequest(
            name=self.processor_name,
            gcs_document=documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type="application/pdf"
            )
        )

        # Process the document
        result = self.client.process_document(request=request)
        document = result.document

        # Extract invoice data
        return self._extract_invoice_data(document)

    def _extract_invoice_data(self, document: documentai.Document) -> Dict[str, Any]:
        """
        Extract structured data from Document AI response.

        Returns:
            Dictionary with invoice fields
        """
        extracted_data = {
            "vendor_name": None,
            "vendor_address": None,
            "vendor_tax_id": None,
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "subtotal": None,
            "tax_amount": None,
            "total_amount": None,
            "currency": "EUR",
            "line_items": [],
            "confidence_scores": {},
            "raw_text": document.text,
        }

        # Extract entities
        for entity in document.entities:
            entity_type = entity.type_
            entity_text = entity.mention_text
            confidence = entity.confidence

            # Map Document AI entity types to our schema
            if entity_type == "supplier_name":
                extracted_data["vendor_name"] = entity_text
                extracted_data["confidence_scores"]["vendor_name"] = confidence

            elif entity_type == "supplier_address":
                extracted_data["vendor_address"] = entity_text
                extracted_data["confidence_scores"]["vendor_address"] = confidence

            elif entity_type == "supplier_tax_id":
                extracted_data["vendor_tax_id"] = entity_text
                extracted_data["confidence_scores"]["vendor_tax_id"] = confidence

            elif entity_type == "invoice_id":
                extracted_data["invoice_number"] = entity_text
                extracted_data["confidence_scores"]["invoice_number"] = confidence

            elif entity_type == "invoice_date":
                extracted_data["invoice_date"] = self._parse_date(entity_text)
                extracted_data["confidence_scores"]["invoice_date"] = confidence

            elif entity_type == "due_date":
                extracted_data["due_date"] = self._parse_date(entity_text)
                extracted_data["confidence_scores"]["due_date"] = confidence

            elif entity_type == "net_amount":
                extracted_data["subtotal"] = self._parse_amount(entity_text)
                extracted_data["confidence_scores"]["subtotal"] = confidence

            elif entity_type == "total_tax_amount":
                extracted_data["tax_amount"] = self._parse_amount(entity_text)
                extracted_data["confidence_scores"]["tax_amount"] = confidence

            elif entity_type == "total_amount":
                extracted_data["total_amount"] = self._parse_amount(entity_text)
                extracted_data["confidence_scores"]["total_amount"] = confidence

            elif entity_type == "currency":
                extracted_data["currency"] = entity_text

            # Extract line items
            elif entity_type == "line_item":
                line_item = self._extract_line_item(entity)
                if line_item:
                    extracted_data["line_items"].append(line_item)

        # Calculate average confidence
        confidences = list(extracted_data["confidence_scores"].values())
        extracted_data["average_confidence"] = (
            sum(confidences) / len(confidences) if confidences else 0
        )

        return extracted_data

    def _extract_line_item(self, entity: documentai.Document.Entity) -> Dict[str, Any]:
        """Extract line item details."""
        line_item = {
            "description": None,
            "quantity": None,
            "unit_price": None,
            "amount": None,
        }

        for prop in entity.properties:
            prop_type = prop.type_
            prop_text = prop.mention_text

            if prop_type == "line_item/description":
                line_item["description"] = prop_text
            elif prop_type == "line_item/quantity":
                line_item["quantity"] = self._parse_number(prop_text)
            elif prop_type == "line_item/unit_price":
                line_item["unit_price"] = self._parse_amount(prop_text)
            elif prop_type == "line_item/amount":
                line_item["amount"] = self._parse_amount(prop_text)

        return line_item

    @staticmethod
    def _parse_date(date_str: str) -> str:
        """Parse date string to ISO format."""
        from datetime import datetime
        import dateutil.parser

        try:
            parsed = dateutil.parser.parse(date_str)
            return parsed.strftime("%Y-%m-%d")
        except:
            return date_str

    @staticmethod
    def _parse_amount(amount_str: str) -> float:
        """Parse amount string to float."""
        import re

        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[^\d.,]', '', amount_str)

        # Handle European format (1.234,56) vs US format (1,234.56)
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rindex(',') > cleaned.rindex('.'):
                # European format
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Assume decimal comma
            cleaned = cleaned.replace(',', '.')

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_number(num_str: str) -> int:
        """Parse number string to int."""
        import re

        cleaned = re.sub(r'[^\d]', '', num_str)
        try:
            return int(cleaned)
        except ValueError:
            return 0
