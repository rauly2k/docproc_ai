import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { ChatInterface } from '../components/Chat/ChatInterface';

export const ChatWithPDF: React.FC = () => {
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  // Filter to only indexed documents
  const indexedDocs = documents?.filter((d: any) => d.rag_indexed) || [];

  const toggleDocument = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId)
        ? prev.filter((id) => id !== docId)
        : [...prev, docId]
    );
  };

  return (
    <div className="h-screen flex flex-col p-6">
      <h2 className="text-2xl font-bold mb-4">Chat with Your Documents</h2>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 overflow-hidden">
        {/* Document Selector */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow p-4 overflow-y-auto">
          <h3 className="font-medium mb-3">Select Documents</h3>

          {isLoading ? (
            <div className="text-sm text-gray-500">Loading...</div>
          ) : indexedDocs.length === 0 ? (
            <div className="text-sm text-gray-500">
              No indexed documents. Index a document from the Documents page.
            </div>
          ) : (
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedDocIds.length === 0}
                  onChange={() => setSelectedDocIds([])}
                  className="mr-2"
                />
                <span className="text-sm">All documents</span>
              </label>

              <hr className="my-2" />

              {indexedDocs.map((doc: any) => (
                <label key={doc.id} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedDocIds.includes(doc.id)}
                    onChange={() => toggleDocument(doc.id)}
                    className="mr-2"
                  />
                  <span className="text-sm truncate">{doc.filename}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Chat Interface */}
        <div className="lg:col-span-3 overflow-hidden">
          <ChatInterface
            documentIds={selectedDocIds.length > 0 ? selectedDocIds : undefined}
          />
        </div>
      </div>
    </div>
  );
};
