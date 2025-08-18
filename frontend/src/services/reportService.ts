import { apiClient, apiUtils } from './apiClient';
import {
  Report,
  CreateReportData,
  UpdateReportData,
  GenerateReportRequest,
  GenerateReportResponse,
  ReportSearchParams,
  ReportSearchResult,
  ReportAnalytics,
  ReportStatus,
  ReportPriority
} from '../types/report';

/**
 * Report Service
 * Handles all report-related API operations
 */
export class ReportService {
  private readonly baseUrl = '/api/reports';

  /**
   * Get all reports with optional filtering
   */
  async getReports(params?: ReportSearchParams): Promise<ReportSearchResult> {
    const queryString = params ? apiUtils.buildQueryString(params) : '';
    const url = queryString ? `${this.baseUrl}?${queryString}` : this.baseUrl;
    
    const response = await apiClient.get(url);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get a single report by ID
   */
  async getReport(id: string): Promise<Report> {
    const response = await apiClient.get(`${this.baseUrl}/${id}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Create a new report
   */
  async createReport(data: CreateReportData): Promise<Report> {
    const response = await apiClient.post(this.baseUrl, data);
    return apiUtils.handleResponse(response);
  }

  /**
   * Update an existing report
   */
  async updateReport(data: UpdateReportData): Promise<Report> {
    const { id, ...updateData } = data;
    const response = await apiClient.put(`${this.baseUrl}/${id}`, updateData);
    return apiUtils.handleResponse(response);
  }

  /**
   * Delete a report
   */
  async deleteReport(id: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}`);
  }

  /**
   * Generate a report
   */
  async generateReport(data: GenerateReportRequest): Promise<GenerateReportResponse> {
    const response = await apiClient.post(`${this.baseUrl}/generate`, data);
    return apiUtils.handleResponse(response);
  }

  /**
   * Regenerate an existing report
   */
  async regenerateReport(id: string, settings?: any): Promise<GenerateReportResponse> {
    const response = await apiClient.post(`${this.baseUrl}/${id}/regenerate`, { settings });
    return apiUtils.handleResponse(response);
  }

  /**
   * Get report generation status
   */
  async getReportStatus(id: string): Promise<{
    status: ReportStatus;
    progress: number;
    estimatedTime?: number;
    error?: string;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/status`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Cancel report generation
   */
  async cancelReport(id: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/${id}/cancel`);
  }

  /**
   * Download report file
   */
  async downloadReport(id: string, format: string = 'pdf'): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/download?format=${format}`, {
      responseType: 'blob'
    });
    return response.data;
  }

  /**
   * Get report preview URL
   */
  async getReportPreviewUrl(id: string): Promise<{ url: string; expiresAt: string }> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/preview-url`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Share report
   */
  async shareReport(id: string, options: {
    emails?: string[];
    userIds?: string[];
    isPublic?: boolean;
    expiresAt?: string;
    password?: string;
  }): Promise<{ shareUrl: string; shareId: string }> {
    const response = await apiClient.post(`${this.baseUrl}/${id}/share`, options);
    return apiUtils.handleResponse(response);
  }

  /**
   * Unshare report
   */
  async unshareReport(id: string, shareId?: string): Promise<void> {
    const url = shareId ? `${this.baseUrl}/${id}/unshare/${shareId}` : `${this.baseUrl}/${id}/unshare`;
    await apiClient.post(url);
  }

  /**
   * Get shared reports
   */
  async getSharedReports(): Promise<Report[]> {
    const response = await apiClient.get(`${this.baseUrl}/shared`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Duplicate report
   */
  async duplicateReport(id: string, name?: string): Promise<Report> {
    const response = await apiClient.post(`${this.baseUrl}/${id}/duplicate`, { name });
    return apiUtils.handleResponse(response);
  }

  /**
   * Get report analytics
   */
  async getReportAnalytics(dateRange?: { from: string; to: string }): Promise<ReportAnalytics> {
    const params = dateRange ? apiUtils.buildQueryString(dateRange) : '';
    const url = params ? `${this.baseUrl}/analytics?${params}` : `${this.baseUrl}/analytics`;
    
    const response = await apiClient.get(url);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get user's report analytics
   */
  async getUserReportAnalytics(userId?: string): Promise<ReportAnalytics> {
    const url = userId ? `${this.baseUrl}/analytics/user/${userId}` : `${this.baseUrl}/analytics/user`;
    const response = await apiClient.get(url);
    return apiUtils.handleResponse(response);
  }

  /**
   * Search reports
   */
  async searchReports(query: string, filters?: Partial<ReportSearchParams>): Promise<ReportSearchResult> {
    const params = { query, ...filters };
    return this.getReports(params);
  }

  /**
   * Get recent reports
   */
  async getRecentReports(limit = 10): Promise<Report[]> {
    const response = await apiClient.get(`${this.baseUrl}/recent?limit=${limit}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get reports by status
   */
  async getReportsByStatus(status: ReportStatus): Promise<Report[]> {
    const response = await apiClient.get(`${this.baseUrl}/status/${status}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get reports by template
   */
  async getReportsByTemplate(templateId: string): Promise<Report[]> {
    const response = await apiClient.get(`${this.baseUrl}/template/${templateId}`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Schedule report generation
   */
  async scheduleReport(data: {
    reportId?: string;
    templateId: string;
    data: Record<string, any>;
    schedule: {
      type: 'once' | 'recurring';
      datetime?: string;
      cron?: string;
      timezone?: string;
    };
    settings?: any;
  }): Promise<{ scheduleId: string; nextRun: string }> {
    const response = await apiClient.post(`${this.baseUrl}/schedule`, data);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get scheduled reports
   */
  async getScheduledReports(): Promise<Array<{
    id: string;
    reportId?: string;
    templateId: string;
    schedule: any;
    nextRun: string;
    lastRun?: string;
    isActive: boolean;
    createdAt: string;
  }>> {
    const response = await apiClient.get(`${this.baseUrl}/scheduled`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Update scheduled report
   */
  async updateScheduledReport(scheduleId: string, data: {
    schedule?: any;
    isActive?: boolean;
    settings?: any;
  }): Promise<void> {
    await apiClient.put(`${this.baseUrl}/scheduled/${scheduleId}`, data);
  }

  /**
   * Delete scheduled report
   */
  async deleteScheduledReport(scheduleId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/scheduled/${scheduleId}`);
  }

  /**
   * Get report queue status
   */
  async getQueueStatus(): Promise<{
    pending: number;
    processing: number;
    completed: number;
    failed: number;
    averageWaitTime: number;
    averageProcessingTime: number;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/queue/status`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Get report processing logs
   */
  async getReportLogs(id: string): Promise<Array<{
    timestamp: string;
    level: 'info' | 'warn' | 'error';
    message: string;
    details?: any;
  }>> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/logs`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Retry failed report
   */
  async retryReport(id: string, priority?: ReportPriority): Promise<GenerateReportResponse> {
    const response = await apiClient.post(`${this.baseUrl}/${id}/retry`, { priority });
    return apiUtils.handleResponse(response);
  }

  /**
   * Bulk operations
   */
  async bulkDeleteReports(ids: string[]): Promise<void> {
    await apiClient.post(`${this.baseUrl}/bulk/delete`, { ids });
  }

  async bulkUpdateReports(updates: Array<{ id: string; data: Partial<UpdateReportData> }>): Promise<Report[]> {
    const response = await apiClient.post(`${this.baseUrl}/bulk/update`, { updates });
    return apiUtils.handleResponse(response);
  }

  async bulkDownloadReports(ids: string[], format: string = 'pdf'): Promise<Blob> {
    const response = await apiClient.post(`${this.baseUrl}/bulk/download`, { ids, format }, {
      responseType: 'blob'
    });
    return response.data;
  }

  async bulkRegenerateReports(ids: string[], priority?: ReportPriority): Promise<GenerateReportResponse[]> {
    const response = await apiClient.post(`${this.baseUrl}/bulk/regenerate`, { ids, priority });
    return apiUtils.handleResponse(response);
  }

  /**
   * Export reports
   */
  async exportReports(params: {
    ids?: string[];
    filters?: ReportSearchParams;
    format: 'csv' | 'excel' | 'json';
    includeData?: boolean;
  }): Promise<Blob> {
    const response = await apiClient.post(`${this.baseUrl}/export`, params, {
      responseType: 'blob'
    });
    return response.data;
  }

  /**
   * Import reports
   */
  async importReports(file: File): Promise<{
    imported: number;
    failed: number;
    errors: string[];
  }> {
    const formData = apiUtils.createFormData({ file });
    const response = await apiClient.post(`${this.baseUrl}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return apiUtils.handleResponse(response);
  }

  /**
   * Get report permissions
   */
  async getReportPermissions(id: string): Promise<{
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
   * Update report permissions
   */
  async updateReportPermissions(id: string, permissions: {
    isPublic?: boolean;
    sharedWith?: Array<{
      userId: string;
      permissions: string[];
    }>;
  }): Promise<void> {
    await apiClient.put(`${this.baseUrl}/${id}/permissions`, permissions);
  }

  /**
   * Add comment to report
   */
  async addReportComment(id: string, comment: string): Promise<{
    id: string;
    comment: string;
    createdAt: string;
    user: {
      id: string;
      name: string;
    };
  }> {
    const response = await apiClient.post(`${this.baseUrl}/${id}/comments`, { comment });
    return apiUtils.handleResponse(response);
  }

  /**
   * Get report comments
   */
  async getReportComments(id: string): Promise<Array<{
    id: string;
    comment: string;
    createdAt: string;
    user: {
      id: string;
      name: string;
    };
  }>> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/comments`);
    return apiUtils.handleResponse(response);
  }

  /**
   * Delete report comment
   */
  async deleteReportComment(reportId: string, commentId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${reportId}/comments/${commentId}`);
  }
}

// Create and export service instance
export const reportService = new ReportService();
export default reportService;