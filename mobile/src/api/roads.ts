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
  // Future: Add bounding box for map viewport queries
  // bbox?: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
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
};
