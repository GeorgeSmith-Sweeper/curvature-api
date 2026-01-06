/**
 * RoutePlannerScreen - Tap-to-add route building
 * Build custom routes by selecting roads in sequence
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
  ScrollView,
  Platform,
} from 'react-native';
import { useRouteBuilder } from '../../contexts/RouteBuilderContext';
import { roadsApi, RoadSearchParams } from '../../api/roads';
import { routesApi } from '../../api/routes';
import { Road } from '../../types';

export function RoutePlannerScreen() {
  const routeBuilder = useRouteBuilder();
  const [availableRoads, setAvailableRoads] = useState<Road[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [routeName, setRouteName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRoads();
  }, []);

  const loadRoads = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: RoadSearchParams = { limit: 50 };
      const data = await roadsApi.search(params);
      setAvailableRoads(data);
    } catch (err) {
      console.error('Failed to load roads:', err);
      setError('Failed to load roads');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRoad = (road: Road) => {
    routeBuilder.addRoad(road);
  };

  const handleRemoveRoad = (roadId: number) => {
    routeBuilder.removeRoad(roadId);
  };

  const handleMoveUp = (index: number) => {
    if (index > 0) {
      routeBuilder.moveRoad(index, index - 1);
    }
  };

  const handleMoveDown = (index: number) => {
    if (index < routeBuilder.selectedRoads.length - 1) {
      routeBuilder.moveRoad(index, index + 1);
    }
  };

  const handleSaveRoute = async () => {
    if (routeBuilder.selectedRoads.length === 0) {
      if (Platform.OS === 'web') {
        window.alert('Please add at least one road to your route');
      }
      return;
    }

    if (!routeName.trim()) {
      if (Platform.OS === 'web') {
        window.alert('Please enter a route name');
      }
      return;
    }

    try {
      setSaving(true);
      const roadIds = routeBuilder.selectedRoads.map((r) => r.id);

      await routesApi.create({
        name: routeName,
        road_ids: roadIds,
      });

      if (Platform.OS === 'web') {
        window.alert('Route saved successfully!');
      }

      // Clear route and reset
      routeBuilder.clearRoute();
      setRouteName('');
      setShowSaveDialog(false);
    } catch (err) {
      console.error('Failed to save route:', err);
      if (Platform.OS === 'web') {
        window.alert('Failed to save route. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const renderAvailableRoad = ({ item }: { item: Road }) => {
    const isSelected = routeBuilder.selectedRoads.some((r) => r.id === item.id);

    return (
      <TouchableOpacity
        style={[styles.roadCard, isSelected && styles.roadCardSelected]}
        onPress={() => !isSelected && handleAddRoad(item)}
        disabled={isSelected}
      >
        <View style={styles.roadHeader}>
          <Text style={styles.roadName} numberOfLines={1}>
            {item.name || 'Unnamed Road'}
          </Text>
          <View style={[styles.curvatureBadge, isSelected && styles.curvatureBadgeSelected]}>
            <Text style={styles.curvatureText}>{item.curvature.toFixed(1)}</Text>
          </View>
        </View>
        <View style={styles.roadDetails}>
          <Text style={styles.detailText}>
            📏 {(item.length_meters / 1000).toFixed(1)} km
          </Text>
          {isSelected && <Text style={styles.selectedText}>✓ Added</Text>}
        </View>
      </TouchableOpacity>
    );
  };

  const renderSelectedRoad = ({ item, index }: { item: Road; index: number }) => (
    <View style={styles.selectedRoadCard}>
      <View style={styles.selectedRoadHeader}>
        <Text style={styles.orderNumber}>{index + 1}</Text>
        <View style={styles.selectedRoadInfo}>
          <Text style={styles.selectedRoadName} numberOfLines={1}>
            {item.name || 'Unnamed Road'}
          </Text>
          <Text style={styles.selectedRoadStats}>
            {item.curvature.toFixed(1)} • {(item.length_meters / 1000).toFixed(1)} km
          </Text>
        </View>
      </View>
      <View style={styles.selectedRoadActions}>
        <TouchableOpacity
          style={[styles.actionButton, index === 0 && styles.actionButtonDisabled]}
          onPress={() => handleMoveUp(index)}
          disabled={index === 0}
        >
          <Text style={styles.actionButtonText}>↑</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.actionButton,
            index === routeBuilder.selectedRoads.length - 1 && styles.actionButtonDisabled,
          ]}
          onPress={() => handleMoveDown(index)}
          disabled={index === routeBuilder.selectedRoads.length - 1}
        >
          <Text style={styles.actionButtonText}>↓</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.removeButton]}
          onPress={() => handleRemoveRoad(item.id)}
        >
          <Text style={styles.removeButtonText}>×</Text>
        </TouchableOpacity>
      </View>
    </View>
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
      <View style={styles.splitView}>
        <View style={styles.leftPanel}>
          <View style={styles.panelHeader}>
            <Text style={styles.panelTitle}>Available Roads</Text>
            <Text style={styles.panelSubtitle}>Tap to add to your route</Text>
          </View>
          <FlatList
            data={availableRoads}
            renderItem={renderAvailableRoad}
            keyExtractor={(item) => item.id.toString()}
            contentContainerStyle={styles.listContent}
          />
        </View>

        <View style={styles.rightPanel}>
          <View style={styles.panelHeader}>
            <Text style={styles.panelTitle}>Your Route</Text>
            <Text style={styles.panelSubtitle}>
              {routeBuilder.selectedRoads.length} road{routeBuilder.selectedRoads.length !== 1 ? 's' : ''}
            </Text>
          </View>

          {routeBuilder.selectedRoads.length > 0 ? (
            <>
              <View style={styles.statsContainer}>
                <View style={styles.statBox}>
                  <Text style={styles.statLabel}>Total Distance</Text>
                  <Text style={styles.statValue}>
                    {(routeBuilder.totalDistance / 1000).toFixed(1)} km
                  </Text>
                </View>
                <View style={styles.statBox}>
                  <Text style={styles.statLabel}>Total Curvature</Text>
                  <Text style={styles.statValue}>{routeBuilder.totalCurvature.toFixed(1)}</Text>
                </View>
              </View>

              <ScrollView style={styles.selectedRoadsList}>
                {routeBuilder.selectedRoads.map((road, index) => (
                  <View key={road.id}>
                    {renderSelectedRoad({ item: road, index })}
                  </View>
                ))}
              </ScrollView>

              <View style={styles.actionBar}>
                <TouchableOpacity style={styles.clearButton} onPress={routeBuilder.clearRoute}>
                  <Text style={styles.clearButtonText}>Clear All</Text>
                </TouchableOpacity>

                {!showSaveDialog ? (
                  <TouchableOpacity
                    style={styles.saveButton}
                    onPress={() => setShowSaveDialog(true)}
                  >
                    <Text style={styles.saveButtonText}>Save Route</Text>
                  </TouchableOpacity>
                ) : (
                  <View style={styles.saveDialog}>
                    <TextInput
                      style={styles.routeNameInput}
                      placeholder="Route name"
                      value={routeName}
                      onChangeText={setRouteName}
                      placeholderTextColor="#999"
                    />
                    <TouchableOpacity
                      style={styles.saveConfirmButton}
                      onPress={handleSaveRoute}
                      disabled={saving}
                    >
                      {saving ? (
                        <ActivityIndicator size="small" color="#fff" />
                      ) : (
                        <Text style={styles.saveButtonText}>✓</Text>
                      )}
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.saveCancelButton}
                      onPress={() => setShowSaveDialog(false)}
                    >
                      <Text style={styles.cancelButtonText}>×</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            </>
          ) : (
            <View style={styles.emptyRouteContainer}>
              <Text style={styles.emptyRouteText}>No roads selected</Text>
              <Text style={styles.emptyRouteSubtext}>Tap roads from the list to build your route</Text>
            </View>
          )}
        </View>
      </View>
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
  splitView: {
    flex: 1,
    flexDirection: 'row',
  },
  leftPanel: {
    flex: 1,
    borderRightWidth: 1,
    borderRightColor: '#ddd',
    backgroundColor: '#fff',
  },
  rightPanel: {
    flex: 1,
    backgroundColor: '#fff',
  },
  panelHeader: {
    padding: 16,
    paddingTop: Platform.OS === 'ios' ? 50 : 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    backgroundColor: '#fff',
  },
  panelTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  panelSubtitle: {
    fontSize: 14,
    color: '#666',
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
    borderWidth: 2,
    borderColor: 'transparent',
  },
  roadCardSelected: {
    backgroundColor: '#f5f5f5',
    borderColor: '#7B1FA2',
    opacity: 0.6,
  },
  roadHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  roadName: {
    flex: 1,
    fontSize: 16,
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
  curvatureBadgeSelected: {
    backgroundColor: '#999',
  },
  curvatureText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  roadDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailText: {
    fontSize: 14,
    color: '#666',
  },
  selectedText: {
    fontSize: 14,
    color: '#7B1FA2',
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 16,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#7B1FA2',
  },
  selectedRoadsList: {
    flex: 1,
    padding: 16,
  },
  selectedRoadCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  selectedRoadHeader: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  orderNumber: {
    width: 32,
    height: 32,
    backgroundColor: '#7B1FA2',
    borderRadius: 16,
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: 32,
    marginRight: 12,
  },
  selectedRoadInfo: {
    flex: 1,
  },
  selectedRoadName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  selectedRoadStats: {
    fontSize: 12,
    color: '#666',
  },
  selectedRoadActions: {
    flexDirection: 'row',
    gap: 4,
  },
  actionButton: {
    width: 32,
    height: 32,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionButtonDisabled: {
    opacity: 0.3,
  },
  actionButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  removeButton: {
    backgroundColor: '#ffebee',
  },
  removeButtonText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#c62828',
  },
  emptyRouteContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyRouteText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#999',
    marginBottom: 8,
  },
  emptyRouteSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  actionBar: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  clearButton: {
    flex: 1,
    height: 50,
    backgroundColor: '#fff',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  clearButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    height: 50,
    backgroundColor: '#7B1FA2',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  saveDialog: {
    flex: 1,
    flexDirection: 'row',
    gap: 8,
  },
  routeNameInput: {
    flex: 1,
    height: 50,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  saveConfirmButton: {
    width: 50,
    height: 50,
    backgroundColor: '#4caf50',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveCancelButton: {
    width: 50,
    height: 50,
    backgroundColor: '#f44336',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
});
