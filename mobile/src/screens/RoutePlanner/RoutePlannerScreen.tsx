/**
 * RoutePlannerScreen - Tap-to-add route building
 * TODO: Add map with tap-to-select roads
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export function RoutePlannerScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Plan Your Route</Text>
      <Text style={styles.subtitle}>Tap roads to build your route...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
});
