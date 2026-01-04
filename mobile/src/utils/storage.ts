/**
 * Platform-aware secure storage
 * Uses SecureStore on iOS/Android and localStorage on web
 */

import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

/**
 * Storage interface that works across all platforms
 */
export const storage = {
  async getItem(key: string): Promise<string | null> {
    if (Platform.OS === 'web') {
      // Use localStorage on web
      return localStorage.getItem(key);
    } else {
      // Use SecureStore on native platforms
      return await SecureStore.getItemAsync(key);
    }
  },

  async setItem(key: string, value: string): Promise<void> {
    if (Platform.OS === 'web') {
      localStorage.setItem(key, value);
    } else {
      await SecureStore.setItemAsync(key, value);
    }
  },

  async removeItem(key: string): Promise<void> {
    if (Platform.OS === 'web') {
      localStorage.removeItem(key);
    } else {
      await SecureStore.deleteItemAsync(key);
    }
  },
};
