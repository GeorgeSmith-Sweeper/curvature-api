/**
 * MyRoutesScreen - List of saved routes
 * View and manage your saved routes
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { routesApi } from '../../api/routes';
import { UserRoute } from '../../types';

export function MyRoutesScreen() {
  const [routes, setRoutes] = useState<UserRoute[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedRoute, setExpandedRoute] = useState<string | null>(null);

  useEffect(() => {
    loadRoutes();
  }, []);

  const loadRoutes = async (refresh = false) => {
    try {
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const data = await routesApi.list();
      setRoutes(data);
    } catch (err) {
      console.error('Failed to load routes:', err);
      setError('Failed to load routes');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleDeleteRoute = async (routeId: string, routeName: string) => {
    const confirmed = Platform.OS === 'web'
      ? window.confirm(`Delete route "${routeName}"?`)
      : true;

    if (!confirmed) return;

    try {
      await routesApi.delete(routeId);
      await loadRoutes();

      if (Platform.OS === 'web') {
        window.alert('Route deleted successfully');
      }
    } catch (err) {
      console.error('Failed to delete route:', err);
      if (Platform.OS === 'web') {
        window.alert('Failed to delete route. Please try again.');
      }
    }
  };

  const toggleRouteDetails = async (routeId: string) => {
    if (expandedRoute === routeId) {
      setExpandedRoute(null);
    } else {
      setExpandedRoute(routeId);
    }
  };

  const renderRouteCard = ({ item }: { item: UserRoute }) => {
    const isExpanded = expandedRoute === item.id;

    return (
      <View style={styles.routeCard}>
        <TouchableOpacity
          style={styles.routeHeader}
          onPress={() => toggleRouteDetails(item.id)}
        >
          <View style={styles.routeHeaderLeft}>
            <Text style={styles.routeName}>{item.name}</Text>
            <Text style={styles.routeDate}>
              Created {new Date(item.created_at).toLocaleDateString()}
            </Text>
          </View>
          <Text style={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</Text>
        </TouchableOpacity>

        <View style={styles.routeStats}>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Roads</Text>
            <Text style={styles.statValue}>{item.road_count}</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Distance</Text>
            <Text style={styles.statValue}>
              {item.total_distance_meters
                ? (item.total_distance_meters / 1000).toFixed(1) + ' km'
                : 'N/A'}
            </Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Curvature</Text>
            <Text style={styles.statValue}>
              {item.total_curvature ? item.total_curvature.toFixed(1) : 'N/A'}
            </Text>
          </View>
        </View>

        {isExpanded && (
          <View style={styles.routeActions}>
            {item.description && (
              <View style={styles.descriptionContainer}>
                <Text style={styles.descriptionText}>{item.description}</Text>
              </View>
            )}
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={() => handleDeleteRoute(item.id, item.name)}
            >
              <Text style={styles.deleteButtonText}>Delete Route</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#7B1FA2" />
        <Text style={styles.loadingText}>Loading your routes...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>My Routes</Text>
        <Text style={styles.subtitle}>
          {routes.length} route{routes.length !== 1 ? 's' : ''} saved
        </Text>
      </View>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <FlatList
        data={routes}
        renderItem={renderRouteCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        refreshing={refreshing}
        onRefresh={() => loadRoutes(true)}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No routes yet</Text>
            <Text style={styles.emptySubtext}>
              Create your first route in the Route Planner
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#fff',
    padding: 16,
    paddingTop: Platform.OS === 'ios' ? 50 : 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 12,
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 8,
  },
  errorText: {
    color: '#c62828',
    fontSize: 14,
  },
  listContent: {
    padding: 16,
  },
  routeCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  routeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingBottom: 12,
  },
  routeHeaderLeft: {
    flex: 1,
  },
  routeName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  routeDate: {
    fontSize: 12,
    color: '#999',
  },
  expandIcon: {
    fontSize: 16,
    color: '#7B1FA2',
    marginLeft: 12,
  },
  routeStats: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#eee',
    marginHorizontal: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#7B1FA2',
  },
  routeActions: {
    borderTopWidth: 1,
    borderTopColor: '#eee',
    padding: 16,
    gap: 12,
  },
  descriptionContainer: {
    backgroundColor: '#f5f5f5',
    padding: 12,
    borderRadius: 8,
  },
  descriptionText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  deleteButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#f44336',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  deleteButtonText: {
    color: '#f44336',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    padding: 48,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#999',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});
