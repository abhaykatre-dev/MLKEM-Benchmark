import {
  RecommendationFormInputs,
  RecommendationResult,
  BenchmarkRecord,
  ProcessorProfile,
  MLKEMVariantSpec,
  AnalyticsSummary,
  BackendSettings,
} from '../types';

export const getApiBaseUrl = (): string => {
  return localStorage.getItem('apiBaseUrl') || 'http://127.0.0.1:8000';
};

export const setApiBaseUrl = (url: string): void => {
  localStorage.setItem('apiBaseUrl', url);
};

/**
 * Fetch wrapper with timeout and error handling
 */
async function fetchWithTimeout<T>(endpoint: string, options: RequestInit = {}, timeoutMs = 6000): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  const baseUrl = getApiBaseUrl();

  try {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}${errorText ? ` (${errorText})` : ''}`);
    }

    return (await response.json()) as T;
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error?.name === 'AbortError') {
      throw new Error('Connection timed out while reaching backend API server.');
    }
    throw error;
  }
}

/**
 * API service for backend interaction
 */
export const apiService = {
  async getHealth(): Promise<{ status: string; version?: string }> {
    return fetchWithTimeout<{ status: string; version?: string }>('/api/health');
  },

  async getRecommendation(inputs: RecommendationFormInputs): Promise<RecommendationResult> {
    return fetchWithTimeout<RecommendationResult>('/api/recommendation', {
      method: 'POST',
      body: JSON.stringify(inputs),
    });
  },

  async getBenchmarks(type: 'baseline' | 'full' = 'baseline'): Promise<BenchmarkRecord[]> {
    return fetchWithTimeout<BenchmarkRecord[]>(`/api/benchmarks?type=${type}`);
  },

  async getProcessors(): Promise<ProcessorProfile[]> {
    return fetchWithTimeout<ProcessorProfile[]>('/api/processors');
  },

  async getVariants(): Promise<MLKEMVariantSpec[]> {
    return fetchWithTimeout<MLKEMVariantSpec[]>('/api/variants');
  },

  async getAnalytics(): Promise<AnalyticsSummary> {
    return fetchWithTimeout<AnalyticsSummary>('/api/analytics');
  },

  async getSettings(): Promise<BackendSettings> {
    return fetchWithTimeout<BackendSettings>('/api/settings');
  },

  async updateSettings(payload: Partial<BackendSettings>): Promise<{ status: string; settings: BackendSettings }> {
    return fetchWithTimeout<{ status: string; settings: BackendSettings }>('/api/settings', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
