import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface SummaryViewProps {
  documentId: string;
}

export const SummaryView: React.FC<SummaryViewProps> = ({ documentId }) => {
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['summary', documentId],
    queryFn: () => apiClient.getSummary(documentId),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return null; // No summary yet
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-medium">Document Summary</h3>
        <div className="text-sm text-gray-500">
          <span className="font-medium">{summary.model_used}</span>
          <span className="mx-2">•</span>
          <span>{summary.word_count} words</span>
        </div>
      </div>

      {/* Key Points */}
      {summary.key_points && summary.key_points.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Key Points:</h4>
          <ul className="space-y-2">
            {summary.key_points.map((point: string, index: number) => (
              <li key={index} className="flex items-start">
                <span className="inline-block w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span className="text-gray-700">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Full Summary */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Full Summary:</h4>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap">{summary.summary}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => navigator.clipboard.writeText(summary.summary)}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm"
        >
          Copy Summary
        </button>
        <button
          onClick={() => {
            const text = `Key Points:\n${summary.key_points.map((p: string) => `- ${p}`).join('\n')}\n\nFull Summary:\n${summary.summary}`;
            const blob = new Blob([text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `summary-${documentId}.txt`;
            a.click();
          }}
          className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
        >
          Download as TXT
        </button>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        Generated on {new Date(summary.created_at).toLocaleString()}
      </div>
    </div>
  );
};
