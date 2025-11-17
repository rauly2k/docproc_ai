import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface SummaryGeneratorProps {
  documentId: string;
  onComplete?: () => void;
}

export const SummaryGenerator: React.FC<SummaryGeneratorProps> = ({
  documentId,
  onComplete
}) => {
  const queryClient = useQueryClient();
  const [modelPreference, setModelPreference] = useState<'auto' | 'flash' | 'pro'>('auto');
  const [summaryType, setSummaryType] = useState<'concise' | 'detailed'>('concise');

  const generateMutation = useMutation({
    mutationFn: () => apiClient.generateSummary(documentId, {
      model_preference: modelPreference,
      summary_type: summaryType,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summary', documentId] });
      if (onComplete) onComplete();
    },
  });

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-4">Generate Summary</h3>

      <div className="space-y-4">
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quality Level
          </label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                value="auto"
                checked={modelPreference === 'auto'}
                onChange={(e) => setModelPreference('auto')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">Auto (Recommended)</div>
                <div className="text-sm text-gray-500">
                  Automatically selects the best model based on document complexity
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input
                type="radio"
                value="flash"
                checked={modelPreference === 'flash'}
                onChange={(e) => setModelPreference('flash')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">Fast (Gemini Flash)</div>
                <div className="text-sm text-gray-500">
                  Quick summaries for straightforward documents
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input
                type="radio"
                value="pro"
                checked={modelPreference === 'pro'}
                onChange={(e) => setModelPreference('pro')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">High Quality (Gemini Pro)</div>
                <div className="text-sm text-gray-500">
                  Best quality for complex or technical documents
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Summary Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Summary Length
          </label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                value="concise"
                checked={summaryType === 'concise'}
                onChange={(e) => setSummaryType('concise')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">Concise (3-5 bullet points)</div>
                <div className="text-sm text-gray-500">
                  Quick overview of main points
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input
                type="radio"
                value="detailed"
                checked={summaryType === 'detailed'}
                onChange={(e) => setSummaryType('detailed')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">Detailed (Comprehensive)</div>
                <div className="text-sm text-gray-500">
                  Full summary with key sections and findings
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50"
        >
          {generateMutation.isPending ? 'Generating...' : 'Generate Summary'}
        </button>

        {generateMutation.isError && (
          <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
            Failed to generate summary. Please try again.
          </div>
        )}

        {generateMutation.isSuccess && (
          <div className="bg-green-50 border border-green-400 text-green-700 px-4 py-3 rounded">
            Summary generation started! It will appear below when ready.
          </div>
        )}
      </div>
    </div>
  );
};
