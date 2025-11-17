import React from 'react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp?: Date;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  role,
  content,
  sources,
  timestamp
}) => {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          <p className="whitespace-pre-wrap">{content}</p>
        </div>

        {sources && sources.length > 0 && (
          <div className="mt-2 text-sm">
            <details className="cursor-pointer">
              <summary className="text-gray-600 hover:text-gray-900">
                📚 Sources ({sources.length})
              </summary>
              <div className="mt-2 space-y-2">
                {sources.map((source, idx) => (
                  <div key={idx} className="bg-gray-50 p-2 rounded border border-gray-200">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-medium text-gray-700">
                        Chunk {source.chunk_index + 1}
                      </span>
                      <span className="text-xs text-gray-500">
                        {source.relevance_score}% relevant
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">{source.content}</p>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        {timestamp && (
          <div className="mt-1 text-xs text-gray-500">
            {timestamp.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};
