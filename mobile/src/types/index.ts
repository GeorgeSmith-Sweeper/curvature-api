/**
 * TypeScript type definitions for Curvature Mobile App
 * Matches backend API models from api/models.py
 */

// ============================================================================
// User & Authentication Types
// ============================================================================

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  created_at: string;
  email_verified: boolean;
  subscription_tier: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  display_name?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ============================================================================
// Road Types
// ============================================================================

export interface Road {
  id: number;
  collection_id: string | null;
  name: string | null;
  curvature: number;
  length_meters: number;
  surface: string | null; // 'paved' | 'unpaved' | 'unknown'
  join_type: string | null;
  geometry: GeoJSON.LineString | null;
  properties: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Route Types
// ============================================================================

export interface UserRoute {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  total_distance_meters: number | null;
  total_curvature: number | null;
  created_at: string;
  updated_at: string;
  is_public: boolean;
  tags: string[] | null;
  road_count: number;
  roads?: RouteRoad[];
}

export interface RouteRoad {
  id: number;
  route_id: string;
  road_id: number;
  position: number;
  connection_type: string; // 'direct' | 'routing'
  connection_geometry: GeoJSON.LineString | null;
  created_at: string;
  road?: Road;
}

export interface CreateRouteData {
  name: string;
  description?: string;
  road_ids: number[];
  tags?: string[];
}

export interface UpdateRouteData {
  name?: string;
  description?: string;
  is_public?: boolean;
  tags?: string[];
}

// ============================================================================
// Favorite Types
// ============================================================================

export interface UserFavorite {
  id: number;
  user_id: string;
  road_id: number;
  notes: string | null;
  created_at: string;
  road_name: string | null;
  curvature: number;
  length_meters: number;
}

export interface CreateFavoriteData {
  road_id: number;
  notes?: string;
}

// ============================================================================
// Map & Location Types
// ============================================================================

export interface Region {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
}

export interface Coordinate {
  latitude: number;
  longitude: number;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================================================
// App State Types
// ============================================================================

export interface RouteBuilderState {
  isActive: boolean;
  selectedRoads: Road[];
  totalDistance: number;
  totalCurvature: number;
}
