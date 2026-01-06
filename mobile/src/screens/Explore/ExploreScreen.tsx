/**
 * ExploreScreen - Browse and discover curvy roads
 * Shows a list of roads sorted by curvature
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import { roadsApi, RoadSearchParams, BBoxParams } from '../../api/roads';
import { Road } from '../../types';
import { MapView, BBox } from '../../components/MapView';

type ViewMode = 'list' | 'map';

// Simple debounce utility
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function ExploreScreen() {
  const [roads, setRoads] = useState<Road[]>([]);
  const [loading, setLoading] = useState(false);
  const [minCurvature, setMinCurvature] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('map'); // Default to map view
  const loadedBoundsRef = useRef<Set<string>>(new Set()); // Cache loaded areas

  // Debounced viewport change handler for map view
  const handleViewportChange = useCallback(
    debounce(async (bbox: BBox) => {
      try {
        // Create cache key with coarse rounding (2 decimal degrees ~= 200km)
        // This prevents loading the same area multiple times on small movements
        const cacheKey = `${(bbox.min_lon / 2).toFixed(0)},${(bbox.min_lat / 2).toFixed(0)},${(bbox.max_lon / 2).toFixed(0)},${(bbox.max_lat / 2).toFixed(0)}`;

        // Skip if already loaded this area
        if (loadedBoundsRef.current.has(cacheKey)) {
          console.log('Skipping - area already loaded:', cacheKey);
          return;
        }

        console.log('Loading roads for viewport:', cacheKey);
        setLoading(true);

        // Expand bbox to load roads beyond viewport for smoother scrolling
        const expandedBbox = {
          min_lon: bbox.min_lon - 1.0,
          max_lon: bbox.max_lon + 1.0,
          min_lat: bbox.min_lat - 0.5,
          max_lat: bbox.max_lat + 0.5,
        };

        const params: BBoxParams = {
          ...expandedBbox,
          limit: 500, // Load up to 500 roads per viewport
        };

        if (minCurvature && !isNaN(parseFloat(minCurvature))) {
          params.min_curvature = parseFloat(minCurvature);
        }

        const newRoads = await roadsApi.getBBox(params);
        console.log(`Loaded ${newRoads.length} new roads`);

        // Merge with existing roads (avoid duplicates)
        setRoads((prevRoads) => {
          const existingIds = new Set(prevRoads.map(r => r.id));
          const uniqueNewRoads = newRoads.filter(r => !existingIds.has(r.id));
          console.log(`Adding ${uniqueNewRoads.length} unique roads (${prevRoads.length} existing)`);
          return [...prevRoads, ...uniqueNewRoads];
        });

        // Mark this area as loaded
        loadedBoundsRef.current.add(cacheKey);

      } catch (err) {
        console.error('Failed to load roads for viewport:', err);
        setError('Failed to load roads. Please try again.');
      } finally {
        setLoading(false);
      }
    }, 1000), // Increased to 1 second debounce to reduce API calls
    [minCurvature]
  );

  // Clear cache when filter changes
  useEffect(() => {
    loadedBoundsRef.current.clear();
    setRoads([]);
  }, [minCurvature]);

  // Note: Search is now handled by viewport changes in map view
  // List view shows roads loaded by viewport when switching from map

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

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Explore Curvy Roads</Text>

        <View style={styles.viewToggle}>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'list' && styles.toggleButtonActive]}
            onPress={() => setViewMode('list')}
          >
            <Text style={[styles.toggleButtonText, viewMode === 'list' && styles.toggleButtonTextActive]}>
              List
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'map' && styles.toggleButtonActive]}
            onPress={() => setViewMode('map')}
          >
            <Text style={[styles.toggleButtonText, viewMode === 'map' && styles.toggleButtonTextActive]}>
              Map
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            placeholder="Min. curvature (auto-filters map)"
            value={minCurvature}
            onChangeText={setMinCurvature}
            keyboardType="numeric"
            placeholderTextColor="#999"
          />
        </View>
        {minCurvature && (
          <TouchableOpacity
            style={styles.clearButton}
            onPress={() => setMinCurvature('')}
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

      {viewMode === 'map' ? (
        <MapView
          roads={roads}
          onRoadPress={(road) => {
            console.log('Road tapped:', road.name);
          }}
          onViewportChange={handleViewportChange}
          style={styles.map}
        />
      ) : (
        <FlatList
          data={roads}
          renderItem={renderRoadItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No roads found</Text>
              <Text style={styles.emptySubtext}>
                Switch to map view to load roads by scrolling
              </Text>
            </View>
          }
        />
      )}
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
    marginBottom: 12,
  },
  viewToggle: {
    flexDirection: 'row',
    marginBottom: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 4,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
  },
  toggleButtonActive: {
    backgroundColor: '#7B1FA2',
  },
  toggleButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  toggleButtonTextActive: {
    color: '#fff',
  },
  map: {
    flex: 1,
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
