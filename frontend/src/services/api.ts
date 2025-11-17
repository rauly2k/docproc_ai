/**
 * API client for backend communication
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // In a real app, get token from Firebase auth
        // const user = auth.currentUser;
        // if (user) {
        //   const token = await user.getIdToken();
        //   config.headers.Authorization = `Bearer ${token}`;
        // }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  // Document endpoints
  async listDocuments(skip = 0, limit = 50) {
    const response = await this.client.get('/documents', {
      params: { skip, limit },
    });
    return response.data;
  }

  async getDocument(documentId: string) {
    const response = await this.client.get(`/documents/${documentId}`);
    return response.data;
  }

  // Chat endpoints
  async indexDocumentForChat(documentId: string) {
    const response = await this.client.post(`/chat/${documentId}/index`);
    return response.data;
  }

  async queryChatRAG(query: {
    question: string;
    document_ids?: string[];
    max_chunks?: number;
    model?: 'flash' | 'pro';
  }) {
    const response = await this.client.post('/chat/query', query);
    return response.data;
  }

  async getDocumentChunks(documentId: string) {
    const response = await this.client.get(`/chat/${documentId}/chunks`);
    return response.data;
  }
}

export const apiClient = new APIClient();
