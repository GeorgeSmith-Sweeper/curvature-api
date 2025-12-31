/**
 * Curvature Mobile App
 * Main entry point
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './src/contexts/AuthContext';
import { RouteBuilderProvider } from './src/contexts/RouteBuilderContext';
import { RootNavigator } from './src/navigation';

// Create React Query client for server state management
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouteBuilderProvider>
          <RootNavigator />
          <StatusBar style="auto" />
        </RouteBuilderProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
