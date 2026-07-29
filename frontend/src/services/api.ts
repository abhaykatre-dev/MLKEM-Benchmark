import {
  RecommendationFormInputs,
  RecommendationResult,
  BenchmarkRecord,
  ProcessorProfile,
  MLKEMVariantSpec,
} from '../types';
import { runAIRecommendation } from './aiEngine';

const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * Fetch wrapper with timeout and error handling
 */
async function fetchWithTimeout<T>(endpoint: string, options: RequestInit = {}, timeoutMs = 5000): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

/**
 * Robust API service for backend interaction with client-side fallback
 */
export const apiService = {
  async getHealth(): Promise<{ status: string }> {
    return fetchWithTimeout<{ status: string }>('/api/health');
  },

  async getRecommendation(inputs: RecommendationFormInputs): Promise<RecommendationResult> {
    try {
      return await fetchWithTimeout<RecommendationResult>('/api/recommendation', {
        method: 'POST',
        body: JSON.stringify(inputs),
      });
    } catch (err) {
      console.warn('Backend API offline or unreachable, utilizing client-side inference fallback:', err);
      return runAIRecommendation(inputs);
    }
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
};
