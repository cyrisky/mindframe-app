export interface ProductConfig {
  id?: string;
  _id?: string; // For backward compatibility
  productName: string;
  displayName?: string;
  description?: string;
  testCombinations?: TestCombination[];
  tests?: TestCombination[]; // Backend uses 'tests' field
  staticContent?: StaticContent;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface TestCombination {
  testName: string;
  order: number;
  isRequired: boolean;
}

export interface StaticContent {
  introduction: string;
  conclusion: string;
  coverPageTitle?: string;
  coverPageSubtitle?: string;
}

export interface CreateProductConfigRequest {
  productName: string;
  displayName: string;
  description?: string;
  testCombinations: TestCombination[];
  staticContent: StaticContent;
}

export interface UpdateProductConfigRequest {
  productName?: string;
  displayName?: string;
  description?: string;
  testCombinations?: TestCombination[];
  staticContent?: StaticContent;
  isActive?: boolean;
}

export interface ProductConfigListResponse {
  productConfigs: ProductConfig[];
  total: number;
  success: boolean;
}

export interface ProductConfigResponse {
  productConfig: ProductConfig;
  success: boolean;
}

export interface DeleteProductConfigResponse {
  success: boolean;
  message: string;
}

// Available test types for dropdown selection
export interface AvailableTest {
  testName: string;
  displayName: string;
  description?: string;
}