import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import toast from 'react-hot-toast';

// API response interface
interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

// API error interface
interface ApiError {
  message: string;
  code?: string;
  field?: string;
  details?: any;
}

// Create axios instance
const createApiClient = (): AxiosInstance => {
  const baseURL = import.meta.env.VITE_API_URL || '';
  
  const client = axios.create({
    baseURL,
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor to add auth token
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    async (error: AxiosError) => {
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

      // Handle 401 errors (unauthorized)
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          // Get refresh token from localStorage
          const refreshToken = localStorage.getItem('refreshToken');
          if (!refreshToken) {
            throw new Error('No refresh token available');
          }
          
          // Try to refresh token
          const refreshResponse = await axios.post(`${baseURL}/api/auth/refresh`, {
            refresh_token: refreshToken
          });

          const newToken = refreshResponse.data.token;
          localStorage.setItem('token', newToken);

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return client(originalRequest);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      // Handle other errors
      const apiError: ApiError = {
        message: 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
      };

      if (error.response?.data) {
        const errorData = error.response.data as any;
        apiError.message = errorData.message || errorData.error || apiError.message;
        apiError.code = errorData.code || error.response.status.toString();
        apiError.field = errorData.field;
        apiError.details = errorData.details;
      } else if (error.request) {
        apiError.message = 'Network error - please check your connection';
        apiError.code = 'NETWORK_ERROR';
      }

      // Show error toast for non-401 and non-404 errors
      // 404 errors are expected when checking for duplicates
      if (error.response?.status !== 401 && error.response?.status !== 404) {
        toast.error(apiError.message);
      }

      return Promise.reject(apiError);
    }
  );

  return client;
};

// Create and export the API client instance
export const apiClient = createApiClient();

// Utility functions for common API operations
export const apiUtils = {
  /**
   * Handle API response and extract data
   */
  handleResponse: <T>(response: AxiosResponse<ApiResponse<T>>): T => {
    return response.data.data;
  },

  /**
   * Create form data from object
   */
  createFormData: (data: Record<string, any>): FormData => {
    const formData = new FormData();
    
    Object.keys(data).forEach(key => {
      const value = data[key];
      if (value !== null && value !== undefined) {
        if (value instanceof File) {
          formData.append(key, value);
        } else if (Array.isArray(value)) {
          value.forEach((item, index) => {
            formData.append(`${key}[${index}]`, item);
          });
        } else if (typeof value === 'object') {
          formData.append(key, JSON.stringify(value));
        } else {
          formData.append(key, value.toString());
        }
      }
    });
    
    return formData;
  },

  /**
   * Build query string from parameters
   */
  buildQueryString: (params: Record<string, any>): string => {
    const searchParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      const value = params[key];
      if (value !== null && value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach(item => searchParams.append(key, item.toString()));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });
    
    return searchParams.toString();
  },

  /**
   * Download file from response
   */
  downloadFile: (response: AxiosResponse, filename?: string): void => {
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Try to get filename from response headers
    const contentDisposition = response.headers['content-disposition'];
    if (contentDisposition && !filename) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }
    
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  /**
   * Check if error is a specific type
   */
  isApiError: (error: any, code?: string): boolean => {
    return error && typeof error === 'object' && 'message' in error && 
           (!code || error.code === code);
  },

  /**
   * Get error message from error object
   */
  getErrorMessage: (error: any): string => {
    if (typeof error === 'string') return error;
    if (error?.message) return error.message;
    if (error?.response?.data?.message) return error.response.data.message;
    return 'An unexpected error occurred';
  },
};

export default apiClient;