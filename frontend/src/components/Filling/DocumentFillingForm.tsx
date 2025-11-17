import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

export const DocumentFillingForm: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedIdDoc, setSelectedIdDoc] = useState<string>('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [filledDocId, setFilledDocId] = useState<string | null>(null);

  // Fetch ID documents
  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  // Fetch templates
  const { data: templates } = useQuery({
    queryKey: ['filling-templates'],
    queryFn: () => apiClient.getFillingTemplates(),
  });

  // Extract and fill mutation
  const fillMutation = useMutation({
    mutationFn: () => apiClient.extractAndFill(selectedIdDoc, selectedTemplate),
    onSuccess: (data) => {
      setFilledDocId(data.output_document_id);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Download mutation
  const downloadMutation = useMutation({
    mutationFn: () => apiClient.getFilledPdfDownloadUrl(filledDocId!),
    onSuccess: (data) => {
      window.open(data.download_url, '_blank');
    },
  });

  const handleFill = () => {
    if (!selectedIdDoc || !selectedTemplate) {
      alert('Please select both an ID document and a template');
      return;
    }
    fillMutation.mutate();
  };

  const idDocuments = documents?.filter((d: any) => d.document_type === 'id') || [];

  return (
    <div className="bg-white p-6 rounded-lg shadow max-w-2xl">
      <h3 className="text-lg font-medium mb-4">Fill PDF Form from ID</h3>

      <div className="space-y-4">
        {/* Select ID Document */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select ID Document
          </label>
          <select
            value={selectedIdDoc}
            onChange={(e) => setSelectedIdDoc(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">-- Choose ID Document --</option>
            {idDocuments.map((doc: any) => (
              <option key={doc.id} value={doc.id}>
                {doc.filename}
              </option>
            ))}
          </select>
          {idDocuments.length === 0 && (
            <p className="text-sm text-gray-500 mt-1">
              No ID documents found. Upload an ID document first.
            </p>
          )}
        </div>

        {/* Select Template */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Form Template
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">-- Choose Template --</option>
            {templates?.map((template: any) => (
              <option key={template.name} value={template.name}>
                {template.display_name}
              </option>
            ))}
          </select>
          {selectedTemplate && (
            <p className="text-sm text-gray-600 mt-1">
              {templates?.find((t: any) => t.name === selectedTemplate)?.description}
            </p>
          )}
        </div>

        {/* Fill Button */}
        <button
          onClick={handleFill}
          disabled={!selectedIdDoc || !selectedTemplate || fillMutation.isPending}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50"
        >
          {fillMutation.isPending ? 'Processing...' : 'Extract Data & Fill Form'}
        </button>

        {/* Status Messages */}
        {fillMutation.isError && (
          <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
            Failed to fill document. Please try again.
          </div>
        )}

        {fillMutation.isSuccess && (
          <div className="bg-green-50 border border-green-400 text-green-700 px-4 py-3 rounded">
            <p className="font-medium">Document filled successfully!</p>
            <p className="text-sm mt-1">Processing... The filled PDF will be ready shortly.</p>
          </div>
        )}

        {/* Download Button */}
        {filledDocId && (
          <div className="pt-4 border-t">
            <button
              onClick={() => downloadMutation.mutate()}
              disabled={downloadMutation.isPending}
              className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium"
            >
              {downloadMutation.isPending ? 'Getting download link...' : 'Download Filled PDF'}
            </button>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">How it works:</h4>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>Upload an ID card or identity document</li>
          <li>Select a PDF form template to fill</li>
          <li>AI extracts data from your ID (name, address, ID number, etc.)</li>
          <li>Data is automatically filled into the PDF form</li>
          <li>Download the completed, filled PDF</li>
        </ol>
      </div>
    </div>
  );
};
