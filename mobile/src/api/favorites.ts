/**
 * Favorites API endpoints
 */

import { apiClient } from './client';
import { UserFavorite, CreateFavoriteData } from '../types';

export const favoritesApi = {
  /**
   * Get all user's favorites
   */
  list: async (): Promise<UserFavorite[]> => {
    return apiClient.get<UserFavorite[]>('/favorites');
  },

  /**
   * Add a road to favorites
   */
  add: async (data: CreateFavoriteData): Promise<UserFavorite> => {
    return apiClient.post<UserFavorite>('/favorites', data);
  },

  /**
   * Remove a road from favorites
   */
  remove: async (roadId: number): Promise<void> => {
    return apiClient.delete(`/favorites/${roadId}`);
  },

  /**
   * Check if a road is favorited
   */
  isFavorited: async (roadId: number, favorites: UserFavorite[]): Promise<boolean> => {
    return favorites.some((fav) => fav.road_id === roadId);
  },
};
