import axios from 'axios';
import type {
  HealthCheckResponse,
  UploadSession,
  Transaction,
  AnalysisResult,
  RecurringGroup,
  Category,
} from '../types';

export interface TransactionQueryParams {
  page?: number;
  per_page?: number;
  category?: Category | 'All';
  sort_by?: 'date' | 'amount' | 'category';
  order?: 'asc' | 'desc';
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health
  getHealth: async (): Promise<HealthCheckResponse> => {
    const response = await apiClient.get<HealthCheckResponse>('/health');
    return response.data;
  },

  // Upload statement file
  uploadStatement: async (file: File, bankHint?: string): Promise<UploadSession> => {
    const formData = new FormData();
    formData.append('file', file);
    if (bankHint) {
      formData.append('bank_hint', bankHint);
    }
    const response = await apiClient.post<UploadSession>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Session status
  getSession: async (sessionId: string): Promise<UploadSession> => {
    const response = await apiClient.get<UploadSession>(`/sessions/${sessionId}`);
    return response.data;
  },

  // Transactions
  getTransactions: async (
    sessionId: string,
    params?: TransactionQueryParams,
  ): Promise<{ data: Transaction[]; total: number; page: number; limit: number }> => {
    const response = await apiClient.get(`/sessions/${sessionId}/transactions`, { params });
    return response.data;
  },

  // Category Override
  overrideCategory: async (sessionId: string, txnId: number, category: Category): Promise<Transaction> => {
    const response = await apiClient.patch(`/sessions/${sessionId}/transactions/${txnId}`, { category });
    return response.data;
  },

  // Recurring payments
  getRecurring: async (sessionId: string): Promise<RecurringGroup[]> => {
    const response = await apiClient.get<RecurringGroup[]>(`/sessions/${sessionId}/recurring`);
    return response.data;
  },

  // Analytics & Insights
  getAnalytics: async (sessionId: string): Promise<AnalysisResult> => {
    const response = await apiClient.get<AnalysisResult>(`/sessions/${sessionId}/analytics`);
    return response.data;
  },

  getInsights: async (sessionId: string): Promise<{ session_id: string; insights: string[] }> => {
    const response = await apiClient.get<{ session_id: string; insights: string[] }>(`/sessions/${sessionId}/insights`);
    return response.data;
  },
};
