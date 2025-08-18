// Template-related types and interfaces

export interface Template {
  id: string;
  name: string;
  description?: string;
  category: TemplateCategory;
  type: TemplateType;
  content: string;
  variables: TemplateVariable[];
  metadata: TemplateMetadata;
  settings: TemplateSettings;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  isActive: boolean;
  version: number;
  tags: string[];
}

export interface TemplateVariable {
  name: string;
  type: VariableType;
  label: string;
  description?: string;
  required: boolean;
  defaultValue?: any;
  validation?: VariableValidation;
  options?: VariableOption[];
  placeholder?: string;
  group?: string;
}

export interface VariableValidation {
  min?: number;
  max?: number;
  pattern?: string;
  message?: string;
  custom?: string;
}

export interface VariableOption {
  label: string;
  value: any;
  description?: string;
}

export interface TemplateMetadata {
  author?: string;
  authorEmail?: string;
  license?: string;
  documentation?: string;
  examples?: TemplateExample[];
  changelog?: TemplateChange[];
  dependencies?: string[];
  compatibility?: string[];
}

export interface TemplateExample {
  name: string;
  description?: string;
  data: Record<string, any>;
  expectedOutput?: string;
}

export interface TemplateChange {
  version: string;
  date: string;
  changes: string[];
  author?: string;
}

export interface TemplateSettings {
  pageSize: PageSize;
  margins: Margins;
  orientation: PageOrientation;
  fonts: FontSettings[];
  colors: ColorSettings;
  layout: LayoutSettings;
  output: OutputSettings;
}

export interface PageSize {
  width: number;
  height: number;
  unit: SizeUnit;
  preset?: PageSizePreset;
}

export interface Margins {
  top: number;
  right: number;
  bottom: number;
  left: number;
  unit: SizeUnit;
}

export interface FontSettings {
  family: string;
  size: number;
  weight: FontWeight;
  style: FontStyle;
  color?: string;
  lineHeight?: number;
}

export interface ColorSettings {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
  border: string;
  custom: Record<string, string>;
}

export interface LayoutSettings {
  columns: number;
  columnGap: number;
  rowGap: number;
  alignment: TextAlignment;
  direction: TextDirection;
  breakBefore: BreakBehavior;
  breakAfter: BreakBehavior;
}

export interface OutputSettings {
  format: OutputFormat;
  quality: number;
  compression: boolean;
  metadata: boolean;
  watermark?: WatermarkSettings;
  security?: SecuritySettings;
}

export interface WatermarkSettings {
  text: string;
  opacity: number;
  position: WatermarkPosition;
  rotation: number;
  fontSize: number;
  color: string;
}

export interface SecuritySettings {
  password?: string;
  permissions: PDFPermission[];
  encryption: EncryptionLevel;
}

// Template creation and update interfaces
export interface CreateTemplateData {
  name: string;
  description?: string;
  category: TemplateCategory;
  type: TemplateType;
  content: string;
  variables: Omit<TemplateVariable, 'name'>[];
  settings?: Partial<TemplateSettings>;
  tags?: string[];
  metadata?: Partial<TemplateMetadata>;
}

export interface UpdateTemplateData extends Partial<CreateTemplateData> {
  id: string;
  version?: number;
}

export interface TemplatePreviewData {
  templateId: string;
  variables: Record<string, any>;
  settings?: Partial<TemplateSettings>;
}

export interface TemplateValidationResult {
  isValid: boolean;
  errors: TemplateValidationError[];
  warnings: TemplateValidationWarning[];
}

export interface TemplateValidationError {
  field: string;
  message: string;
  code: string;
  line?: number;
  column?: number;
}

export interface TemplateValidationWarning {
  field: string;
  message: string;
  suggestion?: string;
}

// Template search and filtering
export interface TemplateSearchParams {
  query?: string;
  category?: TemplateCategory;
  type?: TemplateType;
  tags?: string[];
  author?: string;
  dateFrom?: string;
  dateTo?: string;
  isActive?: boolean;
  sortBy?: TemplateSortField;
  sortOrder?: SortOrder;
  page?: number;
  limit?: number;
}

export interface TemplateSearchResult {
  templates: Template[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// Enums and constants
export enum TemplateCategory {
  REPORT = 'report',
  INVOICE = 'invoice',
  CERTIFICATE = 'certificate',
  LETTER = 'letter',
  FORM = 'form',
  PRESENTATION = 'presentation',
  CUSTOM = 'custom'
}

export enum TemplateType {
  HTML = 'html',
  MARKDOWN = 'markdown',
  JSON = 'json',
  XML = 'xml'
}

export enum VariableType {
  TEXT = 'text',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  DATE = 'date',
  EMAIL = 'email',
  URL = 'url',
  SELECT = 'select',
  MULTISELECT = 'multiselect',
  TEXTAREA = 'textarea',
  FILE = 'file',
  IMAGE = 'image',
  COLOR = 'color',
  ARRAY = 'array',
  OBJECT = 'object'
}

export enum PageOrientation {
  PORTRAIT = 'portrait',
  LANDSCAPE = 'landscape'
}

export enum SizeUnit {
  PX = 'px',
  MM = 'mm',
  CM = 'cm',
  IN = 'in',
  PT = 'pt'
}

export enum PageSizePreset {
  A4 = 'A4',
  A3 = 'A3',
  A5 = 'A5',
  LETTER = 'Letter',
  LEGAL = 'Legal',
  TABLOID = 'Tabloid',
  CUSTOM = 'Custom'
}

export enum FontWeight {
  NORMAL = 'normal',
  BOLD = 'bold',
  LIGHTER = 'lighter',
  BOLDER = 'bolder'
}

export enum FontStyle {
  NORMAL = 'normal',
  ITALIC = 'italic',
  OBLIQUE = 'oblique'
}

export enum TextAlignment {
  LEFT = 'left',
  CENTER = 'center',
  RIGHT = 'right',
  JUSTIFY = 'justify'
}

export enum TextDirection {
  LTR = 'ltr',
  RTL = 'rtl'
}

export enum BreakBehavior {
  AUTO = 'auto',
  ALWAYS = 'always',
  AVOID = 'avoid',
  PAGE = 'page'
}

export enum OutputFormat {
  PDF = 'pdf',
  PNG = 'png',
  JPEG = 'jpeg',
  HTML = 'html'
}

export enum WatermarkPosition {
  CENTER = 'center',
  TOP_LEFT = 'top-left',
  TOP_RIGHT = 'top-right',
  BOTTOM_LEFT = 'bottom-left',
  BOTTOM_RIGHT = 'bottom-right'
}

export enum PDFPermission {
  PRINT = 'print',
  COPY = 'copy',
  MODIFY = 'modify',
  ANNOTATE = 'annotate',
  FILL_FORMS = 'fill-forms',
  EXTRACT = 'extract',
  ASSEMBLE = 'assemble'
}

export enum EncryptionLevel {
  NONE = 'none',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}

export enum TemplateSortField {
  NAME = 'name',
  CREATED_AT = 'createdAt',
  UPDATED_AT = 'updatedAt',
  CATEGORY = 'category',
  AUTHOR = 'author'
}

export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc'
}

// Default values and constants
export const DEFAULT_TEMPLATE_SETTINGS: TemplateSettings = {
  pageSize: {
    width: 210,
    height: 297,
    unit: SizeUnit.MM,
    preset: PageSizePreset.A4
  },
  margins: {
    top: 20,
    right: 20,
    bottom: 20,
    left: 20,
    unit: SizeUnit.MM
  },
  orientation: PageOrientation.PORTRAIT,
  fonts: [{
    family: 'Arial',
    size: 12,
    weight: FontWeight.NORMAL,
    style: FontStyle.NORMAL,
    color: '#000000'
  }],
  colors: {
    primary: '#007bff',
    secondary: '#6c757d',
    accent: '#28a745',
    background: '#ffffff',
    text: '#000000',
    border: '#dee2e6',
    custom: {}
  },
  layout: {
    columns: 1,
    columnGap: 0,
    rowGap: 0,
    alignment: TextAlignment.LEFT,
    direction: TextDirection.LTR,
    breakBefore: BreakBehavior.AUTO,
    breakAfter: BreakBehavior.AUTO
  },
  output: {
    format: OutputFormat.PDF,
    quality: 100,
    compression: true,
    metadata: true
  }
};

export const TEMPLATE_CATEGORIES = Object.values(TemplateCategory);
export const TEMPLATE_TYPES = Object.values(TemplateType);
export const VARIABLE_TYPES = Object.values(VariableType);
export const PAGE_SIZE_PRESETS = Object.values(PageSizePreset);
export const OUTPUT_FORMATS = Object.values(OutputFormat);

// Helper functions
export const getTemplateDisplayName = (template: Template): string => {
  return template.name || `Template ${template.id}`;
};

export const getTemplateCategoryLabel = (category: TemplateCategory): string => {
  const labels: Record<TemplateCategory, string> = {
    [TemplateCategory.REPORT]: 'Report',
    [TemplateCategory.INVOICE]: 'Invoice',
    [TemplateCategory.CERTIFICATE]: 'Certificate',
    [TemplateCategory.LETTER]: 'Letter',
    [TemplateCategory.FORM]: 'Form',
    [TemplateCategory.PRESENTATION]: 'Presentation',
    [TemplateCategory.CUSTOM]: 'Custom'
  };
  return labels[category] || category;
};

export const getVariableTypeLabel = (type: VariableType): string => {
  const labels: Record<VariableType, string> = {
    [VariableType.TEXT]: 'Text',
    [VariableType.NUMBER]: 'Number',
    [VariableType.BOOLEAN]: 'Boolean',
    [VariableType.DATE]: 'Date',
    [VariableType.EMAIL]: 'Email',
    [VariableType.URL]: 'URL',
    [VariableType.SELECT]: 'Select',
    [VariableType.MULTISELECT]: 'Multi-select',
    [VariableType.TEXTAREA]: 'Text Area',
    [VariableType.FILE]: 'File',
    [VariableType.IMAGE]: 'Image',
    [VariableType.COLOR]: 'Color',
    [VariableType.ARRAY]: 'Array',
    [VariableType.OBJECT]: 'Object'
  };
  return labels[type] || type;
};

export const validateTemplateVariable = (variable: TemplateVariable, value: any): string | null => {
  if (variable.required && (value === null || value === undefined || value === '')) {
    return `${variable.label} is required`;
  }

  if (value === null || value === undefined || value === '') {
    return null; // Optional field, no validation needed
  }

  const validation = variable.validation;
  if (!validation) return null;

  switch (variable.type) {
    case VariableType.TEXT:
    case VariableType.TEXTAREA:
      if (validation.min && value.length < validation.min) {
        return validation.message || `${variable.label} must be at least ${validation.min} characters`;
      }
      if (validation.max && value.length > validation.max) {
        return validation.message || `${variable.label} must be no more than ${validation.max} characters`;
      }
      if (validation.pattern && !new RegExp(validation.pattern).test(value)) {
        return validation.message || `${variable.label} format is invalid`;
      }
      break;

    case VariableType.NUMBER:
      const numValue = Number(value);
      if (isNaN(numValue)) {
        return `${variable.label} must be a valid number`;
      }
      if (validation.min !== undefined && numValue < validation.min) {
        return validation.message || `${variable.label} must be at least ${validation.min}`;
      }
      if (validation.max !== undefined && numValue > validation.max) {
        return validation.message || `${variable.label} must be no more than ${validation.max}`;
      }
      break;

    case VariableType.EMAIL:
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(value)) {
        return validation.message || `${variable.label} must be a valid email address`;
      }
      break;

    case VariableType.URL:
      try {
        new URL(value);
      } catch {
        return validation.message || `${variable.label} must be a valid URL`;
      }
      break;
  }

  return null;
};