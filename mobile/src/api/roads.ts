/**
 * Roads API endpoints
 */

import { apiClient } from './client';
import { Road } from '../types';

export interface RoadSearchParams {
  min_curvature?: number;
  max_curvature?: number;
  surface?: 'paved' | 'unpaved' | 'unknown';
  limit?: number;
}

export interface BBoxParams {
  min_lon: number;
  max_lon: number;
  min_lat: number;
  max_lat: number;
  min_curvature?: number;
  limit?: number;
}

export const roadsApi = {
  /**
   * Search for roads (future database endpoint)
   * Note: This endpoint will need to be implemented in the backend
   * to query the roads table instead of msgpack
   */
  search: async (params: RoadSearchParams = {}): Promise<Road[]> => {
    return apiClient.get<Road[]>('/roads/search', { params });
  },

  /**
   * Get a specific road by ID
   */
  getById: async (id: number): Promise<Road> => {
    return apiClient.get<Road>(`/roads/${id}`);
  },

  /**
   * Get roads near a location (future endpoint)
   * This will be useful for the map view
   */
  getNearby: async (
    latitude: number,
    longitude: number,
    radiusMeters: number = 10000
  ): Promise<Road[]> => {
    return apiClient.get<Road[]>('/roads/nearby', {
      params: { latitude, longitude, radius: radiusMeters },
    });
  },

  /**
   * Get roads within a bounding box (viewport-based loading)
   * Optimized for map viewport queries using PostGIS spatial indexes
   */
  getBBox: async (params: BBoxParams): Promise<Road[]> => {
    return apiClient.get<Road[]>('/roads/bbox', { params });
  },
};
