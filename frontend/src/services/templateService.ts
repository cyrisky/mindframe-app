import { apiClient, apiUtils } from './apiClient';
import {
  Template,
  CreateTemplateData,
  UpdateTemplateData,
  TemplateSearchParams,
  TemplateSearchResult,
  TemplatePreviewData,
  TemplateValidationResult,
  TemplateCategory,
  TemplateType
} from '../types/template';

/**
 * Template Service
 * Handles all template-related API operations
 */
export class TemplateService {
  private readonly baseUrl = '/api/templates';

  /**
   * Get all templates with optional filtering
   */
  async getTemplates(params?: TemplateSearchParams): Promise<TemplateSearchResult> {
    const queryString = params ? apiUtils.buildQueryString(params) : '';
    const url = queryString ? `${this.baseUrl}?${queryString}` : this.baseUrl;
    
    const response = await apiClient.get(url);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get a single template by ID
   */
  async getTemplate(id: string): Promise<Template> {
    const response = await apiClient.get(`${this.baseUrl}/${id}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Create a new template
   */
  async createTemplate(data: CreateTemplateData): Promise<Template> {
    const response = await apiClient.post(this.baseUrl, data);
    return apiUtils.handleResponse(response);
  }

  /**
   * Update an existing template
   */
  async updateTemplate(data: UpdateTemplateData): Promise<Template> {
    const { id, ...updateData } = data;
    const response = await apiClient.put(`${this.baseUrl}/${id}`, updateData);
    return apiUtils.handleResponse(response);
  }

  /**
   * Delete a template
   */
  async deleteTemplate(id: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}`);
  }

  /**
   * Duplicate a template
   */
  async duplicateTemplate(id: string, name?: string): Promise<Template> {
    const response = await apiClient.post(`${this.baseUrl}/${id}/duplicate`, { name });
    return apiUtils.handleResponse(response);
  }

  /**
   * Preview a template with sample data
   */
  async previewTemplate(data: TemplatePreviewData): Promise<{ html: string; pdf?: string }> {
    const response = await apiClient.post(`${this.baseUrl}/preview`, data);
    return apiUtils.handleResponse(response);
  }

  /**
   * Validate template content and variables
   */
  async validateTemplate(id: string): Promise<TemplateValidationResult> {
    const response = await apiClient.post(`${this.baseUrl}/${id}/validate`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get template categories
   */
  async getCategories(): Promise<TemplateCategory[]> {
    const response = await apiClient.get(`${this.baseUrl}/categories`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get template types
   */
  async getTypes(): Promise<TemplateType[]> {
    const response = await apiClient.get(`${this.baseUrl}/types`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get popular templates
   */
  async getPopularTemplates(limit = 10): Promise<Template[]> {
    const response = await apiClient.get(`${this.baseUrl}/popular?limit=${limit}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get recent templates
   */
  async getRecentTemplates(limit = 10): Promise<Template[]> {
    const response = await apiClient.get(`${this.baseUrl}/recent?limit=${limit}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get templates by category
   */
  async getTemplatesByCategory(category: TemplateCategory): Promise<Template[]> {
    const response = await apiClient.get(`${this.baseUrl}/category/${category}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Search templates
   */
  async searchTemplates(query: string, filters?: Partial<TemplateSearchParams>): Promise<TemplateSearchResult> {
    const params = { query, ...filters };
    return this.getTemplates(params);
  }

  /**
   * Get template usage statistics
   */
  async getTemplateStats(id: string): Promise<{
    usageCount: number;
    lastUsed: string;
    averageRating: number;
    totalRatings: number;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/stats`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Rate a template
   */
  async rateTemplate(id: string, rating: number, comment?: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/${id}/rate`, { rating, comment });
  }

  /**
   * Get template ratings
   */
  async getTemplateRatings(id: string): Promise<{
    ratings: Array<{
      id: string;
      rating: number;
      comment?: string;
      createdAt: string;
      user: {
        id: string;
        name: string;
      };
    }>;
    average: number;
    total: number;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/ratings`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Export template
   */
  async exportTemplate(id: string, format: 'json' | 'zip' = 'json'): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/export?format=${format}`, {
      responseType: 'blob'
    });
    return response.data;
  }

  /**
   * Import template
   */
  async importTemplate(file: File): Promise<Template> {
    const formData = apiUtils.createFormData({ file });
    const response = await apiClient.post(`${this.baseUrl}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return apiUtils.handleResponse(response);
  }

  /**
   * Get template versions
   */
  async getTemplateVersions(id: string): Promise<Array<{
    version: number;
    createdAt: string;
    createdBy: string;
    changes: string[];
    isActive: boolean;
  }>> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/versions`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Restore template version
   */
  async restoreTemplateVersion(id: string, version: number): Promise<Template> {
    const response = await apiClient.post(`${this.baseUrl}/${id}/versions/${version}/restore`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Share template
   */
  async shareTemplate(id: string, userIds: string[], permissions: string[] = ['read']): Promise<void> {
    await apiClient.post(`${this.baseUrl}/${id}/share`, { userIds, permissions });
  }

  /**
   * Unshare template
   */
  async unshareTemplate(id: string, userIds: string[]): Promise<void> {
    await apiClient.post(`${this.baseUrl}/${id}/unshare`, { userIds });
  }

  /**
   * Get shared templates
   */
  async getSharedTemplates(): Promise<Template[]> {
    const response = await apiClient.get(`${this.baseUrl}/shared`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get template permissions
   */
  async getTemplatePermissions(id: string): Promise<{
    owner: string;
    sharedWith: Array<{
      userId: string;
      userName: string;
      permissions: string[];
      sharedAt: string;
    }>;
    isPublic: boolean;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/permissions`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Update template permissions
   */
  async updateTemplatePermissions(id: string, permissions: {
    isPublic?: boolean;
    sharedWith?: Array<{
      userId: string;
      permissions: string[];
    }>;
  }): Promise<void> {
    await apiClient.put(`${this.baseUrl}/${id}/permissions`, permissions);
  }

  /**
   * Get template tags
   */
  async getTemplateTags(): Promise<string[]> {
    const response = await apiClient.get(`${this.baseUrl}/tags`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Add tags to template
   */
  async addTemplateTags(id: string, tags: string[]): Promise<void> {
    await apiClient.post(`${this.baseUrl}/${id}/tags`, { tags });
  }

  /**
   * Remove tags from template
   */
  async removeTemplateTags(id: string, tags: string[]): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}/tags`, { data: { tags } });
  }

  /**
   * Get template by tag
   */
  async getTemplatesByTag(tag: string): Promise<Template[]> {
    const response = await apiClient.get(`${this.baseUrl}/tag/${encodeURIComponent(tag)}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Bulk operations
   */
  async bulkDeleteTemplates(ids: string[]): Promise<void> {
    await apiClient.post(`${this.baseUrl}/bulk/delete`, { ids });
  }

  async bulkUpdateTemplates(updates: Array<{ id: string; data: Partial<UpdateTemplateData> }>): Promise<Template[]> {
    const response = await apiClient.post(`${this.baseUrl}/bulk/update`, { updates });
    return apiUtils.handleResponse(response);
  }

  async bulkExportTemplates(ids: string[], format: 'json' | 'zip' = 'zip'): Promise<Blob> {
    const response = await apiClient.post(`${this.baseUrl}/bulk/export`, { ids, format }, {
      responseType: 'blob'
    });
    return response.data;
  }
}

// Create and export service instance
export const templateService = new TemplateService();
export default templateService;