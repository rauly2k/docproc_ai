/**
 * API Client for Document AI Platform
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { auth } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/v1';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add Firebase auth token interceptor
    this.client.interceptors.request.use(
      async (config) => {
        try {
          const user = auth.currentUser;
          if (user) {
            const token = await user.getIdToken();
            config.headers.Authorization = `Bearer ${token}`;
          }
        } catch (error) {
          console.error('Error getting auth token:', error);
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          console.error('Authentication error:', error.response.data);
          // Could trigger logout or token refresh here
        }
        return Promise.reject(error);
      }
    );
  }

  // ===== Auth Methods =====

  async signup(email: string, password: string, fullName: string, tenantName: string) {
    const response = await this.client.post('/auth/signup', {
      email,
      password,
      full_name: fullName,
      tenant_name: tenantName,
    });
    return response.data;
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', {
      email,
      password,
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // ===== Document Methods =====

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

  async getDocument(documentId: string) {
    const response = await this.client.get(`/documents/${documentId}`);
    return response.data;
  }

  async listDocuments(page: number = 1, pageSize: number = 20) {
    const response = await this.client.get('/documents', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async deleteDocument(documentId: string) {
    const response = await this.client.delete(`/documents/${documentId}`);
    return response.data;
  }

  // ===== Invoice Methods =====

  async processInvoice(documentId: string) {
    const response = await this.client.post('/invoices/process', {
      document_id: documentId,
    });
    return response.data;
  }

  async getInvoiceData(documentId: string) {
    const response = await this.client.get(`/invoices/${documentId}`);
    return response.data;
  }

  async listInvoices(page: number = 1, pageSize: number = 20) {
    const response = await this.client.get('/invoices', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async validateInvoice(
    documentId: string,
    corrections: any,
    validationNotes: string,
    isApproved: boolean
  ) {
    const response = await this.client.patch(`/invoices/${documentId}/validate`, {
      corrections,
      validation_notes: validationNotes,
      is_approved: isApproved,
    });
    return response.data;
  }

  // ===== OCR Methods =====

  async extractText(documentId: string, ocrMethod: string = 'document-ai') {
    const response = await this.client.post('/ocr/extract', {
      document_id: documentId,
      ocr_method: ocrMethod,
    });
    return response.data;
  }

  async getOCRResult(documentId: string) {
    const response = await this.client.get(`/ocr/${documentId}`);
    return response.data;
  }

  // ===== Summarization Methods =====

  async generateSummary(
    documentId: string,
    model: string = 'gemini-1.5-flash',
    maxWords: number = 200
  ) {
    const response = await this.client.post('/summaries/generate', {
      document_id: documentId,
      model,
      max_words: maxWords,
    });
    return response.data;
  }

  async getSummary(documentId: string) {
    const response = await this.client.get(`/summaries/${documentId}`);
    return response.data;
  }

  async listSummaries(page: number = 1, pageSize: number = 20) {
    const response = await this.client.get('/summaries', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async deleteSummary(documentId: string) {
    const response = await this.client.delete(`/summaries/${documentId}`);
    return response.data;
  }

  // ===== Chat/RAG Methods =====

  async indexDocumentForChat(documentId: string) {
    const response = await this.client.post('/chat/index', {
      document_id: documentId,
    });
    return response.data;
  }

  async queryDocument(
    documentIds: string[],
    question: string,
    maxChunks: number = 5,
    model: string = 'gemini-1.5-flash'
  ) {
    const response = await this.client.post('/chat/query', {
      document_ids: documentIds,
      question,
      max_chunks: maxChunks,
      model,
    });
    return response.data;
  }

  async getDocumentChunks(documentId: string) {
    const response = await this.client.get(`/chat/${documentId}/chunks`);
    return response.data;
  }

  // ===== Document Filling Methods =====

  async getFillingTemplates() {
    const response = await this.client.get('/filling/templates');
    return response.data;
  }

  async extractAndFill(documentId: string, templateName: string) {
    const response = await this.client.post('/filling/extract-and-fill', {
      document_id: documentId,
      template_name: templateName,
    });
    return response.data;
  }

  async getFillingResult(documentId: string) {
    const response = await this.client.get(`/filling/${documentId}`);
    return response.data;
  }

  async getFilledPdfDownloadUrl(documentId: string) {
    const response = await this.client.get(`/filling/${documentId}/download`);
    return response.data.url;
  }

  // ===== Admin Methods =====

  async getTenantStats() {
    const response = await this.client.get('/admin/stats');
    return response.data;
  }

  async updateUserRole(userId: string, role: 'admin' | 'user' | 'viewer') {
    const response = await this.client.patch(`/admin/users/${userId}/role`, {
      role,
    });
    return response.data;
  }
}

export const apiClient = new APIClient();
