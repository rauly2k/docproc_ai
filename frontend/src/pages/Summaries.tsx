import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { SummaryView } from '../components/Summaries/SummaryView';
import { SummaryGenerator } from '../components/Summaries/SummaryGenerator';

export const Summaries: React.FC = () => {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const { data: summaries, isLoading } = useQuery({
    queryKey: ['summaries'],
    queryFn: () => apiClient.listSummaries(),
  });

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  if (selectedDocId) {
    const document = documents?.find((d: any) => d.id === selectedDocId);

    return (
      <div>
        <button
          onClick={() => setSelectedDocId(null)}
          className="mb-4 text-primary-600 hover:text-primary-800 flex items-center"
        >
          ← Back to list
        </button>

        <h2 className="text-2xl font-bold mb-4">
          Summary: {document?.filename || 'Document'}
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <SummaryView documentId={selectedDocId} />
          </div>
          <div>
            <SummaryGenerator
              documentId={selectedDocId}
              onComplete={() => {
                // Refresh summary view
              }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Document Summaries</h2>

      {isLoading ? (
        <div className="text-center py-8">Loading summaries...</div>
      ) : summaries?.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No summaries yet. Generate a summary from the Documents page.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {summaries?.map((summary: any) => {
            const document = documents?.find((d: any) => d.id === summary.document_id);

            return (
              <div
                key={summary.id}
                className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedDocId(summary.document_id)}
              >
                <h3 className="font-medium text-gray-900 mb-2">
                  {document?.filename || 'Document'}
                </h3>
                <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                  {summary.key_points[0] || summary.summary.substring(0, 100)}...
                </p>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{summary.word_count} words</span>
                  <span>{summary.model_used}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
