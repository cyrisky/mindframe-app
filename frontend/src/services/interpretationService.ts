import { apiClient } from './apiClient';
import {
  Interpretation,
  CreateInterpretationRequest,
  UpdateInterpretationRequest,
  InterpretationResponse
} from '../types/interpretation';

class InterpretationService {
  private baseUrl = '/api/interpretations';

  constructor() {
    console.log('[InterpretationService] Initialized', {
      serviceBasePath: this.baseUrl,
      axiosBaseURL: apiClient.defaults.baseURL,
    });
  }

  private logRequest(method: string, path: string, data?: any) {
    const absoluteUrl = `${apiClient.defaults.baseURL || ''}${path}`;
    console.log(`[InterpretationService] ${method} ${path}`, {
      axiosBaseURL: apiClient.defaults.baseURL,
      absoluteUrl,
      payload: data ?? null,
    });
  }

  private logResponse(method: string, path: string, status: number, meta?: any) {
    console.log(`[InterpretationService] Response ${method} ${path}`, {
      status,
      ...(meta || {}),
    });
  }

  private logError(method: string, path: string, error: any) {
    console.error(`[InterpretationService] Error ${method} ${path}`, {
      message: (error as any)?.message,
      code: (error as any)?.code,
      responseStatus: (error as any)?.response?.status,
      responseData: (error as any)?.response?.data,
    });
  }

  async getAll(): Promise<Interpretation[]> {
    this.logRequest('GET', this.baseUrl);
    try {
      const response = await apiClient.get<any>(this.baseUrl);
      this.logResponse('GET', this.baseUrl, response.status, {
        count: Array.isArray(response.data?.interpretations)
          ? response.data.interpretations.length
          : undefined,
      });
      // Handle both old and new response formats
      if (response.data?.success !== undefined) {
        // New format with success field
        return response.data.interpretations || [];
      } else {
        // Legacy format - direct array
        return Array.isArray(response.data) ? response.data : [];
      }
    } catch (error) {
      this.logError('GET', this.baseUrl, error);
      throw error;
    }
  }

  async getById(id: string): Promise<Interpretation> {
    const path = `${this.baseUrl}/${id}`;
    this.logRequest('GET', path);
    try {
      const response = await apiClient.get<InterpretationResponse>(path);
      this.logResponse('GET', path, response.status);
      return response.data.interpretation;
    } catch (error) {
      this.logError('GET', path, error);
      throw error;
    }
  }

  async getByTestName(testName: string): Promise<Interpretation> {
    const path = `${this.baseUrl}/test/${testName}`;
    this.logRequest('GET', path);
    try {
      const response = await apiClient.get<InterpretationResponse>(path);
      this.logResponse('GET', path, response.status);
      return response.data.interpretation;
    } catch (error) {
      // Don't log 404 errors as they are expected when checking for duplicates
      if ((error as any)?.code !== '404') {
        this.logError('GET', path, error);
      }
      throw error;
    }
  }

  /**
   * Check if a test name already exists without generating 404 errors
   * Uses the list endpoint with filtering instead of individual lookup
   */
  async checkTestNameExists(testName: string): Promise<boolean> {
    const path = `${this.baseUrl}?testName=${encodeURIComponent(testName)}`;
    this.logRequest('GET', path);
    try {
      const response = await apiClient.get<any>(path);
      this.logResponse('GET', path, response.status, {
        count: Array.isArray(response.data?.interpretations)
          ? response.data.interpretations.length
          : undefined,
      });
      
      // Handle both old and new response formats
      let interpretations: Interpretation[] = [];
      if (response.data?.success !== undefined) {
        // New format with success field
        interpretations = response.data.interpretations || [];
      } else {
        // Legacy format - direct array
        interpretations = Array.isArray(response.data) ? response.data : [];
      }
      
      // Check if any interpretation has the exact testName
      return interpretations.some(interpretation => interpretation.testName === testName);
    } catch (error) {
      this.logError('GET', path, error);
      // On error, assume no duplicate to allow proceeding
      return false;
    }
  }

  async create(data: CreateInterpretationRequest): Promise<Interpretation> {
    const path = this.baseUrl;
    this.logRequest('POST', path, data);
    try {
      const response = await apiClient.post<InterpretationResponse>(path, data);
      this.logResponse('POST', path, response.status);
      return response.data.interpretation;
    } catch (error) {
      this.logError('POST', path, error);
      throw error;
    }
  }

  async update(id: string, data: UpdateInterpretationRequest): Promise<Interpretation> {
    const path = `${this.baseUrl}/${id}`;
    this.logRequest('PUT', path, data);
    try {
      const response = await apiClient.put<InterpretationResponse>(path, data);
      this.logResponse('PUT', path, response.status);
      return response.data.interpretation;
    } catch (error) {
      this.logError('PUT', path, error);
      throw error;
    }
  }

  async delete(id: string): Promise<void> {
    const path = `${this.baseUrl}/${id}`;
    this.logRequest('DELETE', path);
    try {
      const response = await apiClient.delete(path);
      this.logResponse('DELETE', path, response.status);
    } catch (error) {
      this.logError('DELETE', path, error);
      throw error;
    }
  }

  async duplicate(id: string, newTestName: string): Promise<Interpretation> {
    const path = `${this.baseUrl}/${id}/duplicate`;
    const payload = { testName: newTestName };
    this.logRequest('POST', path, payload);
    try {
      const response = await apiClient.post<InterpretationResponse>(path, payload);
      this.logResponse('POST', path, response.status);
      return response.data.interpretation;
    } catch (error) {
      this.logError('POST', path, error);
      throw error;
    }
  }
}

export const interpretationService = new InterpretationService();
export default interpretationService;