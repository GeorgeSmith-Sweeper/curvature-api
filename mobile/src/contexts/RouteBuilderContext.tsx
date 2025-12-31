/**
 * RouteBuilderContext - Manages route building state
 * Handles tap-to-add sequential road selection
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Road, RouteBuilderState } from '../types';

interface RouteBuilderContextType extends RouteBuilderState {
  addRoad: (road: Road) => void;
  removeRoad: (roadId: number) => void;
  moveRoad: (fromIndex: number, toIndex: number) => void;
  clearRoute: () => void;
  toggleActive: () => void;
}

const RouteBuilderContext = createContext<RouteBuilderContextType | undefined>(undefined);

export function RouteBuilderProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<RouteBuilderState>({
    isActive: false,
    selectedRoads: [],
    totalDistance: 0,
    totalCurvature: 0,
  });

  const calculateTotals = (roads: Road[]) => {
    const totalDistance = roads.reduce((sum, road) => sum + road.length_meters, 0);
    const totalCurvature = roads.reduce((sum, road) => sum + road.curvature, 0);
    return { totalDistance, totalCurvature };
  };

  const addRoad = (road: Road) => {
    // Don't add if already in route
    if (state.selectedRoads.some((r) => r.id === road.id)) {
      return;
    }

    const newRoads = [...state.selectedRoads, road];
    const { totalDistance, totalCurvature } = calculateTotals(newRoads);

    setState({
      ...state,
      selectedRoads: newRoads,
      totalDistance,
      totalCurvature,
    });
  };

  const removeRoad = (roadId: number) => {
    const newRoads = state.selectedRoads.filter((r) => r.id !== roadId);
    const { totalDistance, totalCurvature } = calculateTotals(newRoads);

    setState({
      ...state,
      selectedRoads: newRoads,
      totalDistance,
      totalCurvature,
    });
  };

  const moveRoad = (fromIndex: number, toIndex: number) => {
    const newRoads = [...state.selectedRoads];
    const [removed] = newRoads.splice(fromIndex, 1);
    newRoads.splice(toIndex, 0, removed);

    setState({
      ...state,
      selectedRoads: newRoads,
    });
  };

  const clearRoute = () => {
    setState({
      ...state,
      selectedRoads: [],
      totalDistance: 0,
      totalCurvature: 0,
    });
  };

  const toggleActive = () => {
    setState({
      ...state,
      isActive: !state.isActive,
    });
  };

  const value: RouteBuilderContextType = {
    ...state,
    addRoad,
    removeRoad,
    moveRoad,
    clearRoute,
    toggleActive,
  };

  return <RouteBuilderContext.Provider value={value}>{children}</RouteBuilderContext.Provider>;
}

export function useRouteBuilder() {
  const context = useContext(RouteBuilderContext);
  if (context === undefined) {
    throw new Error('useRouteBuilder must be used within a RouteBuilderProvider');
  }
  return context;
}
