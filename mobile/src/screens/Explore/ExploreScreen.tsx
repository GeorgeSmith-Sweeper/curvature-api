/**
 * ExploreScreen - Browse and discover curvy roads
 * Shows a list of roads sorted by curvature
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { roadsApi, RoadSearchParams } from '../../api/roads';
import { Road } from '../../types';

export function ExploreScreen() {
  const [roads, setRoads] = useState<Road[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [minCurvature, setMinCurvature] = useState('');
  const [error, setError] = useState<string | null>(null);

  const loadRoads = async (refresh = false) => {
    try {
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const params: RoadSearchParams = {
        limit: 50,
      };

      if (minCurvature && !isNaN(parseFloat(minCurvature))) {
        params.min_curvature = parseFloat(minCurvature);
      }

      const data = await roadsApi.search(params);
      setRoads(data);
    } catch (err) {
      console.error('Failed to load roads:', err);
      setError('Failed to load roads. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadRoads();
  }, []);

  const handleSearch = () => {
    loadRoads();
  };

  const renderRoadItem = ({ item }: { item: Road }) => (
    <TouchableOpacity style={styles.roadCard}>
      <View style={styles.roadHeader}>
        <Text style={styles.roadName} numberOfLines={1}>
          {item.name || 'Unnamed Road'}
        </Text>
        <View style={styles.curvatureBadge}>
          <Text style={styles.curvatureText}>{item.curvature.toFixed(1)}</Text>
        </View>
      </View>
      <View style={styles.roadDetails}>
        <Text style={styles.detailText}>
          📏 {(item.length_meters / 1000).toFixed(1)} km
        </Text>
        <Text style={styles.detailText}>
          🛣️ {item.surface || 'unknown'}
        </Text>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#7B1FA2" />
        <Text style={styles.loadingText}>Loading roads...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Explore Curvy Roads</Text>
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            placeholder="Min. curvature"
            value={minCurvature}
            onChangeText={setMinCurvature}
            keyboardType="numeric"
            placeholderTextColor="#999"
          />
          <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        </View>
        {minCurvature && (
          <TouchableOpacity
            style={styles.clearButton}
            onPress={() => {
              setMinCurvature('');
              setTimeout(() => loadRoads(), 100);
            }}
          >
            <Text style={styles.clearButtonText}>Clear Filter</Text>
          </TouchableOpacity>
        )}
      </View>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <FlatList
        data={roads}
        renderItem={renderRoadItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshing={refreshing}
        onRefresh={() => loadRoads(true)}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No roads found</Text>
            <Text style={styles.emptySubtext}>
              Try adjusting your search filters
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
    marginBottom: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  searchInput: {
    flex: 1,
    height: 44,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  searchButton: {
    backgroundColor: '#7B1FA2',
    paddingHorizontal: 24,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  clearButton: {
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  clearButtonText: {
    color: '#7B1FA2',
    fontSize: 14,
    fontWeight: '500',
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
  roadCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  roadHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  roadName: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginRight: 8,
  },
  curvatureBadge: {
    backgroundColor: '#7B1FA2',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  curvatureText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  roadDetails: {
    flexDirection: 'row',
    gap: 16,
  },
  detailText: {
    fontSize: 14,
    color: '#666',
  },
  emptyContainer: {
    padding: 32,
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
  },
});
