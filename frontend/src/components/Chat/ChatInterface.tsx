import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../services/api';
import { ChatMessage } from './ChatMessage';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp: Date;
}

interface ChatInterfaceProps {
  documentIds?: string[];
  showDocumentSelector?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  documentIds,
  showDocumentSelector = false
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState<'flash' | 'pro'>('flash');
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const queryMutation = useMutation({
    mutationFn: (question: string) =>
      apiClient.queryChatRAG({
        question,
        document_ids: documentIds,
        max_chunks: 5,
        model: selectedModel,
      }),
    onSuccess: (data, question) => {
      // Add user message
      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          content: question,
          timestamp: new Date(),
        },
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          timestamp: new Date(),
        },
      ]);
    },
    onError: (error: any) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${error.response?.data?.detail || 'Failed to get answer'}`,
          timestamp: new Date(),
        },
      ]);
    },
  });

  const handleSend = () => {
    if (!input.trim() || queryMutation.isPending) return;

    queryMutation.mutate(input);
    setInput('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium">Chat with PDF</h3>
            <p className="text-sm text-gray-500">
              Ask questions about your documents
            </p>
          </div>
          <div className="flex space-x-2">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value as 'flash' | 'pro')}
              className="text-sm border border-gray-300 rounded-md px-2 py-1"
            >
              <option value="flash">Fast (Flash)</option>
              <option value="pro">High Quality (Pro)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-2">👋 Ask me anything about your documents!</p>
            <p className="text-sm">Try questions like:</p>
            <ul className="text-sm mt-2 space-y-1">
              <li>"What is the main topic of this document?"</li>
              <li>"Summarize the key findings"</li>
              <li>"What are the important dates mentioned?"</li>
            </ul>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <ChatMessage
              key={idx}
              role={msg.role}
              content={msg.content}
              sources={msg.sources}
              timestamp={msg.timestamp}
            />
          ))
        )}

        {queryMutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question..."
            rows={2}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || queryMutation.isPending}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};
