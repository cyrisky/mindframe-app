import axios, { AxiosResponse } from 'axios';
import {
  User,
  LoginCredentials,
  RegisterData,
  AuthResponse,
  RefreshTokenResponse,
  PasswordResetRequest,
  PasswordResetData,
  ChangePasswordData,
  EmailVerificationData,
  ProfileUpdateData,
} from '../types/auth';
import { apiClient } from './apiClient';

// Auth service class
class AuthService {
  private readonly baseURL = '/api/auth';

  /**
   * Login user with credentials
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await apiClient.post(
      `${this.baseURL}/login`,
      credentials
    );
    return response.data;
  }

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await apiClient.post(
      `${this.baseURL}/register`,
      data
    );
    return response.data;
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    await apiClient.post(`${this.baseURL}/logout`);
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response: AxiosResponse<User> = await apiClient.get(
      `${this.baseURL}/profile`
    );
    return response.data;
  }

  /**
   * Update user profile
   */
  async updateProfile(data: ProfileUpdateData): Promise<User> {
    const response: AxiosResponse<User> = await apiClient.put(
      `${this.baseURL}/profile`,
      data
    );
    return response.data;
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<RefreshTokenResponse> {
    const response: AxiosResponse<RefreshTokenResponse> = await apiClient.post(
      `${this.baseURL}/refresh`
    );
    return response.data;
  }

  /**
   * Change user password
   */
  async changePassword(data: ChangePasswordData): Promise<void> {
    await apiClient.post(`${this.baseURL}/change-password`, data);
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
    await apiClient.post(`${this.baseURL}/reset-password`, data);
  }

  /**
   * Reset password with token
   */
  async resetPassword(data: PasswordResetData): Promise<void> {
    await apiClient.post(`${this.baseURL}/reset-password/confirm`, data);
  }

  /**
   * Verify email with token
   */
  async verifyEmail(data: EmailVerificationData): Promise<void> {
    await apiClient.post(`${this.baseURL}/verify-email`, data);
  }

  /**
   * Resend email verification
   */
  async resendEmailVerification(): Promise<void> {
    await apiClient.post(`${this.baseURL}/verify-email/resend`);
  }

  /**
   * Get user sessions
   */
  async getSessions(): Promise<any[]> {
    const response = await apiClient.get(`${this.baseURL}/sessions`);
    return response.data;
  }

  /**
   * Revoke a specific session
   */
  async revokeSession(sessionId: string): Promise<void> {
    await apiClient.delete(`${this.baseURL}/sessions/${sessionId}`);
  }

  /**
   * Revoke all sessions except current
   */
  async revokeAllSessions(): Promise<void> {
    await apiClient.delete(`${this.baseURL}/sessions`);
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(user: User | null, permission: string): boolean {
    if (!user) return false;
    
    // Admin has all permissions
    if (user.role === 'admin') return true;
    
    // Define role-based permissions
    const rolePermissions: Record<string, string[]> = {
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
    
    const userPermissions = rolePermissions[user.role] || [];
    return userPermissions.includes(permission);
  }

  /**
   * Check if user has any of the specified permissions
   */
  hasAnyPermission(user: User | null, permissions: string[]): boolean {
    return permissions.some(permission => this.hasPermission(user, permission));
  }

  /**
   * Check if user has all of the specified permissions
   */
  hasAllPermissions(user: User | null, permissions: string[]): boolean {
    return permissions.every(permission => this.hasPermission(user, permission));
  }

  /**
   * Get user's full name
   */
  getFullName(user: User): string {
    return `${user.firstName} ${user.lastName}`.trim();
  }

  /**
   * Get user's initials
   */
  getInitials(user: User): string {
    const firstName = user.firstName?.charAt(0)?.toUpperCase() || '';
    const lastName = user.lastName?.charAt(0)?.toUpperCase() || '';
    return `${firstName}${lastName}`;
  }

  /**
   * Check if user's email is verified
   */
  isEmailVerified(user: User): boolean {
    return user.isEmailVerified;
  }

  /**
   * Check if user account is active
   */
  isAccountActive(user: User): boolean {
    return user.isActive;
  }

  /**
   * Get user's role display name
   */
  getRoleDisplayName(role: User['role']): string {
    const roleNames: Record<User['role'], string> = {
      admin: 'Administrator',
      psychologist: 'Psychologist',
      user: 'User',
    };
    return roleNames[role] || role;
  }

  /**
   * Format last login date
   */
  formatLastLogin(user: User): string {
    if (!user.lastLoginAt) return 'Never';
    
    const date = new Date(user.lastLoginAt);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    if (diffInHours < 48) return 'Yesterday';
    
    return date.toLocaleDateString();
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;