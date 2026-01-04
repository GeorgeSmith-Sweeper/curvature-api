/**
 * ExploreScreen - Browse and discover roads
 * TODO: Add map view with roads
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export function ExploreScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Explore Roads</Text>
      <Text style={styles.subtitle}>Map view coming soon...</Text>
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
