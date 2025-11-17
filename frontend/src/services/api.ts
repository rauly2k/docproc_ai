/**
 * API Client for Document AI platform
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to attach auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('firebase_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  // Document filling endpoints
  async getFillingTemplates() {
    const response = await this.client.get('/filling/templates');
    return response.data;
  }

  async extractAndFill(idDocumentId: string, templateName: string) {
    const response = await this.client.post('/filling/extract-and-fill', {
      id_document_id: idDocumentId,
      template_name: templateName,
    });
    return response.data;
  }

  async getFilledPdfDownloadUrl(documentId: string) {
    const response = await this.client.get(`/filling/${documentId}/download`);
    return response.data;
  }

  // Document endpoints
  async listDocuments() {
    const response = await this.client.get('/documents');
    return response.data;
  }

  async uploadDocument(file: File, documentType: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await this.client.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

export const apiClient = new ApiClient();
