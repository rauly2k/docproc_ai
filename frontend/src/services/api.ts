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

    // Add auth interceptor if needed
    this.client.interceptors.request.use(
      async (config) => {
        // TODO: Add Firebase auth token
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

  // Invoice endpoints
  async getInvoice(documentId: string) {
    const response = await this.client.get(`/invoices/${documentId}`);
    return response.data;
  }

  async listInvoices(skip = 0, limit = 50) {
    const response = await this.client.get('/invoices', {
      params: { skip, limit },
    });
    return response.data;
  }

  async validateInvoice(documentId: string, validation: any) {
    const response = await this.client.patch(
      `/invoices/${documentId}/validate`,
      validation
    );
    return response.data;
  }

  async processInvoice(documentId: string) {
    const response = await this.client.post(`/invoices/${documentId}/process`);
    return response.data;
  }

  // Document endpoints (placeholder)
  async getDocument(documentId: string) {
    // TODO: Implement document endpoint
    return { id: documentId, gcs_path: '' };
  }
}

export const apiClient = new APIClient();
