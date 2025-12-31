/**
 * MyRoutesScreen - List of saved routes
 * TODO: Add route cards with thumbnails
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export function MyRoutesScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>My Routes</Text>
      <Text style={styles.subtitle}>Your saved routes will appear here...</Text>
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
