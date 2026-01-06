/**
 * MapView component for Native (iOS/Android)
 * Uses react-native-maps
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Road } from '../../types';

interface MapViewProps {
  roads: Road[];
  onRoadPress?: (road: Road) => void;
  style?: any;
}

export function MapView({ roads, onRoadPress, style }: MapViewProps) {
  // TODO: Implement native MapView using react-native-maps
  // For now, show placeholder
  return (
    <View style={[styles.container, style]}>
      <Text style={styles.text}>
        Native map view coming soon...
      </Text>
      <Text style={styles.subtext}>
        {roads.length} roads available
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  text: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
  },
  subtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
  },
});
