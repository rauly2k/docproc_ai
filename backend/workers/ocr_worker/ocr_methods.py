"""Multiple OCR methods for different document types."""

from google.cloud import documentai_v1 as documentai, vision, storage
from google.api_core.client_options import ClientOptions
from vertexai.preview.generative_models import GenerativeModel, Part
from typing import Dict, Any
import os

from backend.shared.config import get_settings

settings = get_settings()


class OCRProcessor:
    """Hybrid OCR processor using multiple methods."""

    def __init__(self):
        self.project_id = settings.project_id
        self.location = "us"

        # Document AI client
        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        self.documentai_client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # Vision API client
        self.vision_client = vision.ImageAnnotatorClient()

        # Gemini model
        self.gemini_model = GenerativeModel("gemini-1.5-flash")

        # OCR processor ID
        self.ocr_processor_id = os.getenv("DOCUMENTAI_OCR_PROCESSOR_ID")

    def process_document(self, gcs_uri: str, method: str = "auto") -> Dict[str, Any]:
        """
        Process document with specified OCR method.

        Args:
            gcs_uri: GCS URI of document
            method: OCR method to use (auto, documentai, vision, gemini)

        Returns:
            Extracted text and metadata
        """
        if method == "auto":
            # Auto-select based on file type
            method = self._select_best_method(gcs_uri)

        if method == "documentai":
            return self._ocr_with_documentai(gcs_uri)
        elif method == "vision":
            return self._ocr_with_vision(gcs_uri)
        elif method == "gemini":
            return self._ocr_with_gemini(gcs_uri)
        else:
            raise ValueError(f"Unknown OCR method: {method}")

    def _select_best_method(self, gcs_uri: str) -> str:
        """Auto-select best OCR method based on file."""
        # For MVP, default to Document AI
        # Future: analyze file and choose method
        return "documentai"

    def _ocr_with_documentai(self, gcs_uri: str) -> Dict[str, Any]:
        """OCR using Document AI OCR Processor."""
        processor_name = self.documentai_client.processor_path(
            self.project_id, self.location, self.ocr_processor_id
        )

        request = documentai.ProcessRequest(
            name=processor_name,
            gcs_document=documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type="application/pdf"
            )
        )

        result = self.documentai_client.process_document(request=request)
        document = result.document

        return {
            "extracted_text": document.text,
            "confidence_score": self._calculate_confidence(document),
            "page_count": len(document.pages),
            "ocr_method": "document-ai",
            "layout_data": self._extract_layout(document),
        }

    def _ocr_with_vision(self, gcs_uri: str) -> Dict[str, Any]:
        """OCR using Vision API."""
        image = vision.Image()
        image.source.image_uri = gcs_uri

        response = self.vision_client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")

        text = response.full_text_annotation.text if response.full_text_annotation else ""

        return {
            "extracted_text": text,
            "confidence_score": 0.95,  # Vision API doesn't provide per-doc confidence
            "page_count": len(response.full_text_annotation.pages) if response.full_text_annotation else 1,
            "ocr_method": "vision-api",
            "layout_data": None,
        }

    def _ocr_with_gemini(self, gcs_uri: str) -> Dict[str, Any]:
        """OCR using Gemini Vision (best for handwritten/messy docs)."""
        # Load image from GCS
        image_part = Part.from_uri(gcs_uri, mime_type="image/jpeg")

        prompt = """Extract all text from this image.
        Return only the text content, maintaining the original layout and formatting.
        Do not add any commentary or explanations."""

        response = self.gemini_model.generate_content([prompt, image_part])
        extracted_text = response.text

        return {
            "extracted_text": extracted_text,
            "confidence_score": 0.90,  # Estimate
            "page_count": 1,
            "ocr_method": "gemini-vision",
            "layout_data": None,
        }

    @staticmethod
    def _calculate_confidence(document: documentai.Document) -> float:
        """Calculate average confidence from Document AI response."""
        if not document.pages:
            return 0.0

        confidences = []
        for page in document.pages:
            for token in page.tokens:
                if token.layout and token.layout.confidence:
                    confidences.append(token.layout.confidence)

        return sum(confidences) / len(confidences) if confidences else 0.0

    @staticmethod
    def _extract_layout(document: documentai.Document) -> Dict[str, Any]:
        """Extract layout information from Document AI response."""
        layout = {
            "pages": [],
            "blocks": [],
            "paragraphs": [],
        }

        for page in document.pages:
            page_data = {
                "page_number": page.page_number,
                "width": page.dimension.width if page.dimension else 0,
                "height": page.dimension.height if page.dimension else 0,
            }
            layout["pages"].append(page_data)

        return layout
