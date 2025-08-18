// User interface
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'psychologist' | 'user';
  isActive: boolean;
  isEmailVerified: boolean;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
  profilePicture?: string;
  organization?: string;
  licenseNumber?: string;
  specializations?: string[];
  preferences?: UserPreferences;
}

// User preferences
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  emailNotifications: boolean;
  reportDefaults: {
    templateId?: string;
    format: 'pdf' | 'html';
    includeCharts: boolean;
  };
}

// Login credentials
export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

// Registration data
export interface RegisterData {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  organization?: string;
  licenseNumber?: string;
  role?: 'psychologist' | 'user';
  acceptTerms: boolean;
}

// Auth response
export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresIn: number;
}

// Token refresh response
export interface RefreshTokenResponse {
  user: User;
  token: string;
  expiresIn: number;
}

// Password reset request
export interface PasswordResetRequest {
  email: string;
}

// Password reset data
export interface PasswordResetData {
  token: string;
  password: string;
  confirmPassword: string;
}

// Change password data
export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

// Email verification data
export interface EmailVerificationData {
  token: string;
}

// Profile update data
export interface ProfileUpdateData {
  firstName?: string;
  lastName?: string;
  organization?: string;
  licenseNumber?: string;
  specializations?: string[];
  preferences?: Partial<UserPreferences>;
}

// Auth error
export interface AuthError {
  message: string;
  code: string;
  field?: string;
}

// JWT payload
export interface JWTPayload {
  sub: string; // user id
  email: string;
  role: string;
  iat: number;
  exp: number;
}

// Session info
export interface SessionInfo {
  id: string;
  userId: string;
  deviceInfo: string;
  ipAddress: string;
  userAgent: string;
  createdAt: string;
  lastAccessedAt: string;
  isActive: boolean;
}

// Auth state
export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

// Permission types
export type Permission = 
  | 'read:reports'
  | 'write:reports'
  | 'delete:reports'
  | 'read:templates'
  | 'write:templates'
  | 'delete:templates'
  | 'read:users'
  | 'write:users'
  | 'delete:users'
  | 'admin:system';

// Role permissions mapping
export const ROLE_PERMISSIONS: Record<User['role'], Permission[]> = {
  admin: [
    'read:reports',
    'write:reports',
    'delete:reports',
    'read:templates',
    'write:templates',
    'delete:templates',
    'read:users',
    'write:users',
    'delete:users',
    'admin:system',
  ],
  psychologist: [
    'read:reports',
    'write:reports',
    'delete:reports',
    'read:templates',
    'write:templates',
    'delete:templates',
  ],
  user: [
    'read:reports',
    'write:reports',
    'read:templates',
  ],
};

// Helper function to check permissions
export const hasPermission = (user: User | null, permission: Permission): boolean => {
  if (!user) return false;
  return ROLE_PERMISSIONS[user.role].includes(permission);
};

// Helper function to check multiple permissions
export const hasAnyPermission = (user: User | null, permissions: Permission[]): boolean => {
  if (!user) return false;
  return permissions.some(permission => hasPermission(user, permission));
};

// Helper function to check all permissions
export const hasAllPermissions = (user: User | null, permissions: Permission[]): boolean => {
  if (!user) return false;
  return permissions.every(permission => hasPermission(user, permission));
};