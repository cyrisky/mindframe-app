// Report-related types and interfaces

import { Template, TemplateSettings } from './template';
import { User } from './auth';

export interface Report {
  id: string;
  name: string;
  description?: string;
  templateId: string;
  template?: Template;
  data: Record<string, any>;
  settings: ReportSettings;
  status: ReportStatus;
  output?: ReportOutput;
  metadata: ReportMetadata;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  user?: User;
  tags: string[];
  isPublic: boolean;
  sharedWith: string[];
  version: number;
}

export interface ReportSettings extends TemplateSettings {
  generatePDF: boolean;
  generateHTML: boolean;
  generateImages: boolean;
  emailDelivery?: EmailDeliverySettings;
  webhookDelivery?: WebhookDeliverySettings;
  storageSettings?: StorageSettings;
  scheduledGeneration?: ScheduledGenerationSettings;
}

export interface EmailDeliverySettings {
  enabled: boolean;
  recipients: string[];
  subject: string;
  body?: string;
  attachments: boolean;
  sendImmediately: boolean;
}

export interface WebhookDeliverySettings {
  enabled: boolean;
  url: string;
  method: 'POST' | 'PUT';
  headers?: Record<string, string>;
  authentication?: WebhookAuth;
  retryAttempts: number;
  timeout: number;
}

export interface WebhookAuth {
  type: 'none' | 'basic' | 'bearer' | 'api-key';
  username?: string;
  password?: string;
  token?: string;
  apiKey?: string;
  apiKeyHeader?: string;
}

export interface StorageSettings {
  provider: StorageProvider;
  bucket?: string;
  path?: string;
  publicAccess: boolean;
  retention?: RetentionSettings;
}

export interface RetentionSettings {
  enabled: boolean;
  days: number;
  autoDelete: boolean;
}

export interface ScheduledGenerationSettings {
  enabled: boolean;
  schedule: CronSchedule;
  timezone: string;
  nextRun?: string;
  lastRun?: string;
}

export interface CronSchedule {
  minute: string;
  hour: string;
  dayOfMonth: string;
  month: string;
  dayOfWeek: string;
  expression?: string;
}

export interface ReportOutput {
  files: ReportFile[];
  urls: ReportUrl[];
  deliveries: ReportDelivery[];
  generatedAt: string;
  size: number;
  pageCount?: number;
}

export interface ReportFile {
  id: string;
  filename: string;
  format: string;
  size: number;
  url: string;
  downloadUrl?: string;
  expiresAt?: string;
  checksum?: string;
}

export interface ReportUrl {
  type: 'preview' | 'download' | 'share';
  url: string;
  expiresAt?: string;
  accessCount?: number;
  maxAccess?: number;
}

export interface ReportDelivery {
  id: string;
  type: DeliveryType;
  status: DeliveryStatus;
  destination: string;
  attempts: number;
  lastAttempt?: string;
  nextAttempt?: string;
  error?: string;
  deliveredAt?: string;
}

export interface ReportMetadata {
  processingTime?: number;
  memoryUsage?: number;
  templateVersion?: number;
  generationId?: string;
  jobId?: string;
  priority?: ReportPriority;
  source?: ReportSource;
  userAgent?: string;
  ipAddress?: string;
  requestId?: string;
}

// Report creation and update interfaces
export interface CreateReportData {
  name: string;
  description?: string;
  templateId: string;
  data: Record<string, any>;
  settings?: Partial<ReportSettings>;
  tags?: string[];
  isPublic?: boolean;
  sharedWith?: string[];
  generateImmediately?: boolean;
}

export interface UpdateReportData extends Partial<CreateReportData> {
  id: string;
  version?: number;
}

export interface GenerateReportRequest {
  reportId?: string;
  templateId: string;
  data: Record<string, any>;
  settings?: Partial<ReportSettings>;
  async?: boolean;
  priority?: ReportPriority;
  callbackUrl?: string;
}

export interface GenerateReportResponse {
  reportId?: string;
  jobId?: string;
  status: ReportStatus;
  output?: ReportOutput;
  estimatedTime?: number;
  queuePosition?: number;
}

// Report search and filtering
export interface ReportSearchParams {
  query?: string;
  templateId?: string;
  status?: ReportStatus;
  createdBy?: string;
  tags?: string[];
  dateFrom?: string;
  dateTo?: string;
  isPublic?: boolean;
  sortBy?: ReportSortField;
  sortOrder?: SortOrder;
  page?: number;
  limit?: number;
}

export interface ReportSearchResult {
  reports: Report[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// Report analytics and statistics
export interface ReportAnalytics {
  totalReports: number;
  reportsToday: number;
  reportsThisWeek: number;
  reportsThisMonth: number;
  averageProcessingTime: number;
  successRate: number;
  popularTemplates: TemplateUsageStats[];
  statusDistribution: StatusDistribution[];
  sizeDistribution: SizeDistribution[];
  timeSeriesData: TimeSeriesData[];
}

export interface TemplateUsageStats {
  templateId: string;
  templateName: string;
  usageCount: number;
  lastUsed: string;
}

export interface StatusDistribution {
  status: ReportStatus;
  count: number;
  percentage: number;
}

export interface SizeDistribution {
  range: string;
  count: number;
  percentage: number;
}

export interface TimeSeriesData {
  date: string;
  count: number;
  successCount: number;
  failureCount: number;
  averageTime: number;
}

// Enums and constants
export enum ReportStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  EXPIRED = 'expired'
}

export enum ReportPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum ReportSource {
  WEB = 'web',
  API = 'api',
  WEBHOOK = 'webhook',
  SCHEDULED = 'scheduled',
  BATCH = 'batch'
}

export enum StorageProvider {
  LOCAL = 'local',
  AWS_S3 = 'aws-s3',
  GOOGLE_DRIVE = 'google-drive',
  AZURE_BLOB = 'azure-blob',
  DROPBOX = 'dropbox'
}

export enum DeliveryType {
  EMAIL = 'email',
  WEBHOOK = 'webhook',
  STORAGE = 'storage',
  DOWNLOAD = 'download'
}

export enum DeliveryStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  DELIVERED = 'delivered',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  RETRYING = 'retrying'
}

export enum ReportSortField {
  NAME = 'name',
  CREATED_AT = 'createdAt',
  UPDATED_AT = 'updatedAt',
  STATUS = 'status',
  TEMPLATE = 'template',
  SIZE = 'size'
}

export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc'
}

// Default values and constants
export const DEFAULT_REPORT_SETTINGS: Partial<ReportSettings> = {
  generatePDF: true,
  generateHTML: false,
  generateImages: false,
  emailDelivery: {
    enabled: false,
    recipients: [],
    subject: 'Your report is ready',
    attachments: true,
    sendImmediately: true
  },
  webhookDelivery: {
    enabled: false,
    url: '',
    method: 'POST',
    retryAttempts: 3,
    timeout: 30000
  },
  storageSettings: {
    provider: StorageProvider.LOCAL,
    publicAccess: false,
    retention: {
      enabled: false,
      days: 30,
      autoDelete: false
    }
  }
};

export const REPORT_STATUSES = Object.values(ReportStatus);
export const REPORT_PRIORITIES = Object.values(ReportPriority);
export const STORAGE_PROVIDERS = Object.values(StorageProvider);
export const DELIVERY_TYPES = Object.values(DeliveryType);

// Helper functions
export const getReportStatusLabel = (status: ReportStatus): string => {
  const labels: Record<ReportStatus, string> = {
    [ReportStatus.DRAFT]: 'Draft',
    [ReportStatus.PENDING]: 'Pending',
    [ReportStatus.PROCESSING]: 'Processing',
    [ReportStatus.COMPLETED]: 'Completed',
    [ReportStatus.FAILED]: 'Failed',
    [ReportStatus.CANCELLED]: 'Cancelled',
    [ReportStatus.EXPIRED]: 'Expired'
  };
  return labels[status] || status;
};

export const getReportStatusColor = (status: ReportStatus): string => {
  const colors: Record<ReportStatus, string> = {
    [ReportStatus.DRAFT]: '#6c757d',
    [ReportStatus.PENDING]: '#ffc107',
    [ReportStatus.PROCESSING]: '#17a2b8',
    [ReportStatus.COMPLETED]: '#28a745',
    [ReportStatus.FAILED]: '#dc3545',
    [ReportStatus.CANCELLED]: '#6c757d',
    [ReportStatus.EXPIRED]: '#fd7e14'
  };
  return colors[status] || '#6c757d';
};

export const getReportPriorityLabel = (priority: ReportPriority): string => {
  const labels: Record<ReportPriority, string> = {
    [ReportPriority.LOW]: 'Low',
    [ReportPriority.NORMAL]: 'Normal',
    [ReportPriority.HIGH]: 'High',
    [ReportPriority.URGENT]: 'Urgent'
  };
  return labels[priority] || priority;
};

export const getStorageProviderLabel = (provider: StorageProvider): string => {
  const labels: Record<StorageProvider, string> = {
    [StorageProvider.LOCAL]: 'Local Storage',
    [StorageProvider.AWS_S3]: 'Amazon S3',
    [StorageProvider.GOOGLE_DRIVE]: 'Google Drive',
    [StorageProvider.AZURE_BLOB]: 'Azure Blob Storage',
    [StorageProvider.DROPBOX]: 'Dropbox'
  };
  return labels[provider] || provider;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatProcessingTime = (milliseconds: number): string => {
  if (milliseconds < 1000) {
    return `${milliseconds}ms`;
  } else if (milliseconds < 60000) {
    return `${(milliseconds / 1000).toFixed(1)}s`;
  } else {
    const minutes = Math.floor(milliseconds / 60000);
    const seconds = Math.floor((milliseconds % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  }
};

export const isReportProcessing = (status: ReportStatus): boolean => {
  return [ReportStatus.PENDING, ReportStatus.PROCESSING].includes(status);
};

export const isReportCompleted = (status: ReportStatus): boolean => {
  return status === ReportStatus.COMPLETED;
};

export const isReportFailed = (status: ReportStatus): boolean => {
  return [ReportStatus.FAILED, ReportStatus.CANCELLED, ReportStatus.EXPIRED].includes(status);
};

export const canRetryReport = (status: ReportStatus): boolean => {
  return [ReportStatus.FAILED, ReportStatus.CANCELLED].includes(status);
};

export const canCancelReport = (status: ReportStatus): boolean => {
  return [ReportStatus.PENDING, ReportStatus.PROCESSING].includes(status);
};

export const getEstimatedCompletionTime = (queuePosition: number, averageProcessingTime: number): number => {
  // Estimate completion time based on queue position and average processing time
  return Date.now() + (queuePosition * averageProcessingTime);
};

export const validateReportData = (data: Record<string, any>, template: Template): string[] => {
  const errors: string[] = [];
  
  template.variables.forEach(variable => {
    const value = data[variable.name];
    
    if (variable.required && (value === null || value === undefined || value === '')) {
      errors.push(`${variable.label} is required`);
    }
    
    // Additional validation can be added here based on variable type
  });
  
  return errors;
};