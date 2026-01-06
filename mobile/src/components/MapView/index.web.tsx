/**
 * MapView component for Web
 * Uses Leaflet for web mapping
 */

import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { MapContainer, TileLayer, Polyline, Popup, useMap } from 'react-leaflet';
import { Road } from '../../types';
import 'leaflet/dist/leaflet.css';

export interface BBox {
  min_lon: number;
  max_lon: number;
  min_lat: number;
  max_lat: number;
}

interface MapViewProps {
  roads: Road[];
  onRoadPress?: (road: Road) => void;
  onViewportChange?: (bounds: BBox) => void;
  style?: any;
}

// Component to handle initial map bounds (only on first load)
function MapBoundsHandler({ roads, disabled }: { roads: Road[], disabled?: boolean }) {
  const map = useMap();

  useEffect(() => {
    // Only auto-fit bounds if not disabled and we have initial roads
    if (disabled || roads.length === 0 || !roads.some(r => r.geometry)) {
      return;
    }

    // Calculate bounds from all road geometries
    const bounds: [number, number][] = [];

    roads.forEach(road => {
      if (road.geometry && road.geometry.coordinates) {
        road.geometry.coordinates.forEach(coord => {
          // GeoJSON format is [longitude, latitude]
          // Leaflet expects [latitude, longitude]
          bounds.push([coord[1], coord[0]]);
        });
      }
    });

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, []); // Run only once on mount

  return null;
}

// Component to track viewport changes
function ViewportChangeHandler({ onViewportChange }: { onViewportChange?: (bounds: BBox) => void }) {
  const map = useMap();

  useEffect(() => {
    if (!onViewportChange) return;

    const handleMoveEnd = () => {
      const bounds = map.getBounds();
      const bbox: BBox = {
        min_lon: bounds.getWest(),
        max_lon: bounds.getEast(),
        min_lat: bounds.getSouth(),
        max_lat: bounds.getNorth(),
      };
      onViewportChange(bbox);
    };

    // Listen to moveend (fired after pan/zoom completes)
    map.on('moveend', handleMoveEnd);

    // Initial load - trigger viewport change when map first loads
    handleMoveEnd();

    return () => {
      map.off('moveend', handleMoveEnd);
    };
  }, [map, onViewportChange]);

  return null;
}

export function MapView({ roads, onRoadPress, onViewportChange, style }: MapViewProps) {
  // Default center (US)
  const defaultCenter: [number, number] = [37.0902, -95.7129];
  const defaultZoom = 4;

  return (
    <View style={[styles.container, style]}>
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Disable auto-zoom when using viewport-based loading */}
        <MapBoundsHandler roads={roads} disabled={!!onViewportChange} />
        <ViewportChangeHandler onViewportChange={onViewportChange} />

        {roads.map((road) => {
          if (!road.geometry || !road.geometry.coordinates) {
            return null;
          }

          // Convert GeoJSON coordinates [lon, lat] to Leaflet format [lat, lon]
          const positions: [number, number][] = road.geometry.coordinates.map(
            (coord) => [coord[1], coord[0]]
          );

          // Color based on curvature
          const color = getCurvatureColor(road.curvature);

          return (
            <Polyline
              key={road.id}
              positions={positions}
              color={color}
              weight={4}
              opacity={0.8}
              eventHandlers={{
                click: () => {
                  if (onRoadPress) {
                    onRoadPress(road);
                  }
                },
              }}
            >
              <Popup>
                <div style={{ minWidth: '200px' }}>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>
                    {road.name || 'Unnamed Road'}
                  </h3>
                  <div style={{ fontSize: '14px', color: '#666' }}>
                    <div>🌀 Curvature: <strong>{road.curvature.toFixed(1)}</strong></div>
                    <div>📏 Length: <strong>{(road.length_meters / 1000).toFixed(1)} km</strong></div>
                    <div>🛣️ Surface: <strong>{road.surface || 'unknown'}</strong></div>
                  </div>
                </div>
              </Popup>
            </Polyline>
          );
        })}
      </MapContainer>
    </View>
  );
}

// Helper function to get color based on curvature (optimized for 300+ roads)
function getCurvatureColor(curvature: number): string {
  if (curvature >= 2000) return '#d32f2f'; // Red - extremely curvy (2000+)
  if (curvature >= 1000) return '#f57c00'; // Orange - very curvy (1000-2000)
  if (curvature >= 600) return '#fbc02d'; // Yellow - curvy (600-1000)
  if (curvature >= 400) return '#7b1fa2'; // Purple - moderately curvy (400-600)
  if (curvature >= 300) return '#1976d2'; // Blue - curvy (300-400)
  return '#4caf50'; // Green - slight curves (<300)
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
