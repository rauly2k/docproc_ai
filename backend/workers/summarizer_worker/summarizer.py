"""Document summarization using Vertex AI (Gemini and Claude)."""

from google.cloud import storage
from vertexai.preview.generative_models import GenerativeModel
import vertexai
import PyPDF2
import io
from typing import Dict, Any, List
import re

from backend.shared.config import get_settings

settings = get_settings()


class DocumentSummarizer:
    """Summarize documents using Vertex AI models."""

    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(project=settings.project_id, location=settings.vertex_ai_location)

        # Initialize models
        self.flash_model = GenerativeModel("gemini-1.5-flash")
        self.pro_model = GenerativeModel("gemini-1.5-pro")

        # Storage client
        self.storage_client = storage.Client()

        # Model configurations
        self.generation_config = {
            "temperature": 0.3,  # Lower temperature for more focused summaries
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

    def summarize_document(
        self,
        gcs_uri: str,
        model_preference: str = "flash",
        summary_type: str = "concise"
    ) -> Dict[str, Any]:
        """
        Summarize document from GCS.

        Args:
            gcs_uri: GCS URI of document
            model_preference: "flash" (fast), "pro" (high quality), or "auto"
            summary_type: "concise" (3-5 points) or "detailed" (comprehensive)

        Returns:
            Summary data with key points
        """
        # Extract text from document
        text = self._extract_text_from_pdf(gcs_uri)

        # Check document length to auto-select model
        if model_preference == "auto":
            model_preference = self._auto_select_model(text)

        # Select model
        model = self.pro_model if model_preference == "pro" else self.flash_model

        # Generate summary
        summary_text = self._generate_summary(text, model, summary_type)

        # Extract key points
        key_points = self._extract_key_points(summary_text)

        # Calculate metrics
        word_count = len(summary_text.split())

        return {
            "summary": summary_text,
            "key_points": key_points,
            "word_count": word_count,
            "model_used": f"gemini-1.5-{model_preference}",
            "summary_type": summary_type,
            "original_length": len(text.split()),
            "compression_ratio": round(len(text.split()) / word_count, 2) if word_count > 0 else 0,
        }

    def _extract_text_from_pdf(self, gcs_uri: str) -> str:
        """Extract text from PDF in GCS."""
        # Parse GCS URI
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        # Download PDF
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        pdf_bytes = blob.download_as_bytes()

        # Extract text
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"

        return text

    def _auto_select_model(self, text: str) -> str:
        """Auto-select model based on document characteristics."""
        word_count = len(text.split())

        # For very long documents or complex content, use Pro
        if word_count > 10000:
            return "pro"

        # Check for complex indicators (tables, technical terms, etc.)
        has_tables = bool(re.search(r'\|\s+\w+\s+\|', text))
        has_numbers = len(re.findall(r'\d+', text)) > 100

        if has_tables or has_numbers:
            return "pro"

        # Default to Flash for speed and cost
        return "flash"

    def _generate_summary(
        self,
        text: str,
        model: GenerativeModel,
        summary_type: str
    ) -> str:
        """Generate summary using selected model."""
        # Truncate text if too long (50k characters max)
        max_chars = 50000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Document truncated for processing]"

        # Build prompt based on summary type
        if summary_type == "concise":
            prompt = f"""Summarize the following document in 3-5 concise bullet points.
Focus on the main ideas, key findings, and important takeaways.
Use clear, professional language.

Document:
{text}

Summary (3-5 bullet points):"""

        else:  # detailed
            prompt = f"""Provide a comprehensive summary of the following document.

Include:
1. Main topic and purpose (1-2 sentences)
2. Key points and findings (5-7 bullet points)
3. Important details, data, or conclusions (3-4 bullet points)
4. Overall significance or implications (1-2 sentences)

Use clear, professional language suitable for business use.

Document:
{text}

Detailed Summary:"""

        # Generate summary
        response = model.generate_content(
            prompt,
            generation_config=self.generation_config,
        )

        return response.text

    def _extract_key_points(self, summary: str) -> List[str]:
        """Extract bullet points from summary text."""
        key_points = []

        # Split by lines
        lines = summary.split("\n")

        for line in lines:
            line = line.strip()

            # Match various bullet point formats
            # - Bullet point
            # • Bullet point
            # * Bullet point
            # 1. Numbered point
            # - **Bold:** point

            bullet_patterns = [
                r'^[-•*]\s+(.+)$',  # Dash, bullet, asterisk
                r'^\d+\.\s+(.+)$',  # Numbered
                r'^[-•*]\s+\*\*[^:]+:\*\*\s+(.+)$',  # Bold prefix
            ]

            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    point = match.group(1).strip()
                    # Clean up markdown
                    point = re.sub(r'\*\*(.+?)\*\*', r'\1', point)  # Remove bold
                    point = re.sub(r'\*(.+?)\*', r'\1', point)  # Remove italics
                    key_points.append(point)
                    break

        # If no bullet points found, extract sentences as key points
        if not key_points:
            sentences = re.split(r'[.!?]\s+', summary)
            key_points = [s.strip() for s in sentences if len(s.strip()) > 20][:5]

        return key_points[:10]  # Limit to 10 points


class ClaudeSummarizer:
    """Summarize using Claude via Vertex AI (for premium tier)."""

    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(project=settings.project_id, location=settings.vertex_ai_location)

        # Note: Claude on Vertex AI requires special setup
        # This is a placeholder for future premium feature
        self.available = False

    def summarize_document(self, gcs_uri: str) -> Dict[str, Any]:
        """Summarize using Claude (premium feature)."""
        if not self.available:
            raise NotImplementedError("Claude summarization not yet available")

        # Implementation would be similar to Gemini
        # but using Anthropic's Claude model via Vertex AI
        pass
