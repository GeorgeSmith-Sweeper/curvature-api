#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Roads Routes
============
FastAPI routes for browsing and searching roads.

Endpoints:
- GET /roads/search: Search roads with filters
- GET /roads/{road_id}: Get specific road by ID
- GET /roads/nearby: Get roads near a location
"""

from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from api.database import get_db
from api.models import Road
from api.dependencies import get_current_user_optional


# Create router for roads endpoints
router = APIRouter(prefix="/roads", tags=["roads"])


# Response models
class RoadResponse(BaseModel):
    """Road response model"""
    id: int
    name: Optional[str]
    curvature: float
    length_meters: float
    surface: Optional[str]
    # Note: geometry is excluded from list responses for performance
    # Include it only in detail responses

    class Config:
        from_attributes = True


@router.get("/search", response_model=List[RoadResponse])
async def search_roads(
    min_curvature: Optional[float] = Query(None, ge=0, description="Minimum curvature"),
    max_curvature: Optional[float] = Query(None, description="Maximum curvature"),
    surface: Optional[str] = Query(None, description="Road surface type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Search for roads with optional filters.

    Args:
        min_curvature: Minimum curvature threshold
        max_curvature: Maximum curvature threshold
        surface: Road surface type filter
        limit: Maximum number of results (default 100, max 1000)
        db: Database session

    Returns:
        List of roads matching the criteria
    """
    query = db.query(Road)

    # Apply filters
    if min_curvature is not None:
        query = query.filter(Road.curvature >= min_curvature)

    if max_curvature is not None:
        query = query.filter(Road.curvature <= max_curvature)

    if surface:
        query = query.filter(Road.surface == surface)

    # Order by curvature (most curvy first)
    query = query.order_by(Road.curvature.desc())

    # Limit results
    roads = query.limit(limit).all()

    return roads


@router.get("/{road_id}", response_model=dict)
async def get_road_by_id(
    road_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Get a specific road by ID with full geometry.

    Args:
        road_id: Road ID
        db: Database session

    Returns:
        Road details including geometry

    Raises:
        HTTPException: 404 if road not found
    """
    road = db.query(Road).filter(Road.id == road_id).first()

    if not road:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Road with ID {road_id} not found"
        )

    # Convert to dict and include geometry
    return {
        "id": road.id,
        "name": road.name,
        "curvature": road.curvature,
        "length_meters": road.length_meters,
        "surface": road.surface,
        "geometry": road.geometry,  # GeoJSON LineString
    }


@router.get("/nearby", response_model=List[RoadResponse])
async def get_nearby_roads(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(10000, ge=100, le=100000, description="Search radius in meters"),
    min_curvature: Optional[float] = Query(None, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Get roads near a geographic location.

    Note: This endpoint requires PostGIS spatial queries.
    For now, returns top roads by curvature as a placeholder.

    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius: Search radius in meters
        min_curvature: Optional minimum curvature filter
        limit: Maximum number of results
        db: Database session

    Returns:
        List of nearby roads
    """
    # TODO: Implement spatial query using PostGIS
    # For now, return top roads by curvature as placeholder
    query = db.query(Road).order_by(Road.curvature.desc())

    if min_curvature is not None:
        query = query.filter(Road.curvature >= min_curvature)

    roads = query.limit(limit).all()

    return roads
