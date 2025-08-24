import { apiClient } from './apiClient';
import {
  ProductConfig,
  CreateProductConfigRequest,
  UpdateProductConfigRequest,
  AvailableTest
} from '../types/productConfig';

export const productConfigService = {
  // Get all product configurations
  getAll: async (): Promise<ProductConfig[]> => {
    try {
      const response = await apiClient.get('/api/admin/product-configs');
      return response.data.productConfigs || [];
    } catch (error) {
      console.error('Error fetching product configurations:', error);
      throw error;
    }
  },

  // Get product configuration by ID
  getById: async (id: string): Promise<ProductConfig> => {
    try {
      const response = await apiClient.get(`/api/admin/product-configs/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching product configuration:', error);
      throw error;
    }
  },

  // Get product configuration by product name
  getByProductName: async (productName: string): Promise<ProductConfig> => {
    try {
      const response = await apiClient.get(`/api/admin/product-configs/product/${productName}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching product configuration by name:', error);
      throw error;
    }
  },

  // Create new product configuration
  create: async (data: CreateProductConfigRequest): Promise<ProductConfig> => {
    try {
      const response = await apiClient.post('/api/admin/product-configs', data);
      return response.data;
    } catch (error) {
      console.error('Error creating product configuration:', error);
      throw error;
    }
  },

  // Update product configuration
  update: async (id: string, data: UpdateProductConfigRequest): Promise<ProductConfig> => {
    try {
      const response = await apiClient.put(`/api/admin/product-configs/${id}`, data);
      return response.data;
    } catch (error) {
      console.error('Error updating product configuration:', error);
      throw error;
    }
  },

  // Delete product configuration
  delete: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/api/admin/product-configs/${id}`);
    } catch (error) {
      console.error('Error deleting product configuration:', error);
      throw error;
    }
  },

  // Get available tests for configuration
  getAvailableTests: async (): Promise<AvailableTest[]> => {
    try {
      const response = await apiClient.get('/api/admin/available-tests');
      return response.data;
    } catch (error) {
      console.error('Error fetching available tests:', error);
      throw error;
    }
  },

  // Toggle active status
  toggleActive: async (id: string): Promise<ProductConfig> => {
    try {
      const response = await apiClient.patch(`/api/admin/product-configs/${id}/toggle`);
      return response.data;
    } catch (error) {
      console.error('Error toggling product configuration status:', error);
      throw error;
    }
  }
};

export default productConfigService;