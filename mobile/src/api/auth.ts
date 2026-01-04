/**
 * Authentication API endpoints
 */

import { apiClient } from './client';
import { AuthTokens, LoginCredentials, RegisterData, User } from '../types';

export const authApi = {
  /**
   * Register a new user account
   */
  register: async (data: RegisterData): Promise<AuthTokens> => {
    const tokens = await apiClient.post<AuthTokens>('/auth/register', data);
    await apiClient.saveTokens(tokens.access_token, tokens.refresh_token);
    return tokens;
  },

  /**
   * Login with email and password
   */
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const tokens = await apiClient.post<AuthTokens>('/auth/login', credentials);
    await apiClient.saveTokens(tokens.access_token, tokens.refresh_token);
    return tokens;
  },

  /**
   * Logout and clear tokens
   */
  logout: async (): Promise<void> => {
    try {
      const refreshToken = await apiClient.getRefreshToken();
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    } finally {
      await apiClient.clearTokens();
    }
  },

  /**
   * Get current user profile
   */
  getCurrentUser: async (): Promise<User> => {
    return apiClient.get<User>('/auth/me');
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: async (): Promise<boolean> => {
    const token = await apiClient.getAccessToken();
    return !!token;
  },
};
