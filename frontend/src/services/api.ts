import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

class APIClient {
  private client;
/**
 * API Client for Document AI Platform
 * API client for backend communication
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
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

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
    // Add auth interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // In a real app, get token from Firebase auth
    // Add auth token interceptor
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('authToken');
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
  // ===== OCR Methods =====

  async getOCRResult(documentId: string) {
    const response = await this.client.get(`/v1/ocr/${documentId}`);
    return response.data;
  }

  async extractText(documentId: string) {
    const response = await this.client.post(`/v1/ocr/${documentId}/extract`);
    return response.data;
  }

  // ===== Document Methods =====

  async uploadDocument(file: File, documentType: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await this.client.post('/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async deleteSummary(documentId: string) {
    await this.client.delete(`/summaries/${documentId}`);
  }

  // Document endpoints (stub for integration)
  async listDocuments(skip = 0, limit = 50) {
    const response = await this.client.get('/documents', {
  async getDocument(documentId: string) {
    const response = await this.client.get(`/v1/documents/${documentId}`);
    return response.data;
  }

  async listDocuments(page: number = 1, pageSize: number = 20) {
    const response = await this.client.get('/v1/documents', {
      params: { page, page_size: pageSize },
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

  // Document endpoints
  async listDocuments(skip = 0, limit = 50) {
    const response = await this.client.get('/documents', {
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
  async deleteDocument(documentId: string) {
    const response = await this.client.delete(`/v1/documents/${documentId}`);
    return response.data;
  }

  // ===== Invoice Methods =====

  async processInvoice(documentId: string) {
    const response = await this.client.post('/v1/invoices/process', {
      document_id: documentId,
    });
    return response.data;
  }

  async getInvoiceData(documentId: string) {
    const response = await this.client.get(`/v1/invoices/${documentId}`);
    return response.data;
  }

  async validateInvoice(documentId: string, corrections: any, notes: string, isApproved: boolean) {
    const response = await this.client.patch(`/v1/invoices/${documentId}/validate`, {
      corrections,
      validation_notes: notes,
      is_approved: isApproved,
    });
    return response.data;
  }

  // ===== Summary Methods =====

  async generateSummary(documentId: string, model?: string) {
    const response = await this.client.post('/v1/summaries/generate', {
      document_id: documentId,
      model: model || 'gemini-1.5-flash',
    });
    return response.data;
  }

  async getSummary(documentId: string) {
    const response = await this.client.get(`/v1/summaries/${documentId}`);
    return response.data;
  }

  // ===== Chat/RAG Methods =====

  async indexDocumentForChat(documentId: string) {
    const response = await this.client.post('/v1/chat/index', {
      document_id: documentId,
    });
    return response.data;
  }

  async queryDocument(documentIds: string[], question: string, maxChunks?: number) {
    const response = await this.client.post('/v1/chat/query', {
      document_ids: documentIds,
      question,
      max_chunks: maxChunks || 5,
    });
    return response.data;
  }

  // ===== Auth Methods =====

  async signup(email: string, password: string, fullName: string) {
    const response = await this.client.post('/v1/auth/signup', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/v1/auth/login', {
      email,
      password,
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/v1/auth/me');
    return response.data;
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

  // ===== Document Filling Methods =====

  async getFillingTemplates() {
    const response = await this.client.get('/v1/filling/templates');
    return response.data;
  }

  async extractAndFill(documentId: string, templateName: string) {
    const response = await this.client.post('/v1/filling/extract-and-fill', {
      document_id: documentId,
      template_name: templateName,
    });
    return response.data;
  }

  async getFillingResult(documentId: string) {
    const response = await this.client.get(`/v1/filling/${documentId}`);
    return response.data;
  }

  async getFilledPdfDownloadUrl(documentId: string) {
    const response = await this.client.get(`/v1/filling/${documentId}/download`);
    return response.data;
  }
}

export const apiClient = new APIClient();
