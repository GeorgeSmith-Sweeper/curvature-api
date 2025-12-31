/**
 * Routes API endpoints
 */

import { apiClient } from './client';
import { UserRoute, CreateRouteData, UpdateRouteData } from '../types';

export const routesApi = {
  /**
   * Get all user's routes
   */
  list: async (): Promise<UserRoute[]> => {
    return apiClient.get<UserRoute[]>('/routes');
  },

  /**
   * Get a specific route by ID
   */
  getById: async (id: string): Promise<UserRoute> => {
    return apiClient.get<UserRoute>(`/routes/${id}`);
  },

  /**
   * Create a new route
   */
  create: async (data: CreateRouteData): Promise<UserRoute> => {
    return apiClient.post<UserRoute>('/routes', data);
  },

  /**
   * Update an existing route
   */
  update: async (id: string, data: UpdateRouteData): Promise<UserRoute> => {
    return apiClient.patch<UserRoute>(`/routes/${id}`, data);
  },

  /**
   * Delete a route
   */
  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/routes/${id}`);
  },

  /**
   * Export route to GPX (future feature)
   */
  exportToGpx: async (id: string): Promise<Blob> => {
    return apiClient.get(`/routes/${id}/export/gpx`, {
      responseType: 'blob',
    });
  },
};
