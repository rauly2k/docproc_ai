import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

class APIClient {
  private client;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Summary endpoints
  async generateSummary(documentId: string, options: {
    model_preference?: 'auto' | 'flash' | 'pro';
    summary_type?: 'concise' | 'detailed';
  }) {
    const response = await this.client.post(
      `/summaries/${documentId}/generate`,
      options
    );
    return response.data;
  }

  async getSummary(documentId: string) {
    const response = await this.client.get(`/summaries/${documentId}`);
    return response.data;
  }

  async listSummaries(skip = 0, limit = 50) {
    const response = await this.client.get('/summaries', {
      params: { skip, limit },
    });
    return response.data;
  }

  async deleteSummary(documentId: string) {
    await this.client.delete(`/summaries/${documentId}`);
  }

  // Document endpoints (stub for integration)
  async listDocuments(skip = 0, limit = 50) {
    const response = await this.client.get('/documents', {
      params: { skip, limit },
    });
    return response.data;
  }
}

export const apiClient = new APIClient();
