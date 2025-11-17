import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface OCRResultsProps {
  documentId: string;
}

export const OCRResults: React.FC<OCRResultsProps> = ({ documentId }) => {
  const { data: ocrResult, isLoading, error } = useQuery({
    queryKey: ['ocr', documentId],
    queryFn: () => apiClient.getOCRResult(documentId),
  });

  if (isLoading) return <div>Loading OCR results...</div>;
  if (error) return <div>OCR not completed yet</div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="mb-4">
        <h3 className="text-lg font-medium">Extracted Text</h3>
        <div className="text-sm text-gray-500">
          Method: {ocrResult.ocr_method} •
          Pages: {ocrResult.page_count} •
          Confidence: {(ocrResult.confidence_score * 100).toFixed(1)}%
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded border border-gray-200">
        <pre className="whitespace-pre-wrap text-sm font-mono">
          {ocrResult.extracted_text}
        </pre>
      </div>

      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => navigator.clipboard.writeText(ocrResult.extracted_text)}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        >
          Copy to Clipboard
        </button>
        <button
          onClick={() => {
            const blob = new Blob([ocrResult.extracted_text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `extracted-text-${documentId}.txt`;
            a.click();
          }}
          className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Download as TXT
        </button>
      </div>
    </div>
  );
};
