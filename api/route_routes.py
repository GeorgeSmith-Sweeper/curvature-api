#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Route Planning Routes
=====================
FastAPI routes for user route planning and management.

Endpoints:
- GET /routes: List user's saved routes
- POST /routes: Create new route
- GET /routes/{id}: Get specific route with roads
- PATCH /routes/{id}: Update route metadata
- DELETE /routes/{id}: Delete route
- POST /routes/{id}/roads: Add road to route
- DELETE /routes/{id}/roads/{position}: Remove road from route
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from api.database import get_db
from api.dependencies import get_current_user
from api.models import User, UserRoute, RouteRoad, Road


# Create router for route endpoints
router = APIRouter(prefix="/routes", tags=["routes"])


# Pydantic models for request/response validation
class RoadInRoute(BaseModel):
    """Road within a route"""
    road_id: int
    position: int
    road_name: Optional[str] = None
    curvature: Optional[float] = None
    length_km: Optional[float] = None
    surface: Optional[str] = None


class RouteCreate(BaseModel):
    """Create route request"""
    name: str
    description: Optional[str] = None
    road_ids: List[int]  # List of road IDs in order
    tags: Optional[List[str]] = None


class RouteUpdate(BaseModel):
    """Update route request"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class RouteResponse(BaseModel):
    """Route response"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    total_distance_meters: Optional[float]
    total_curvature: Optional[float]
    created_at: datetime
    updated_at: datetime
    is_public: bool
    tags: Optional[List[str]]
    road_count: int


class RouteDetailResponse(RouteResponse):
    """Detailed route response with roads"""
    roads: List[RoadInRoute]


@router.get("", response_model=List[RouteResponse])
async def list_routes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all routes for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[RouteResponse]: List of user's routes
    """
    routes = db.query(UserRoute).filter(
        UserRoute.user_id == current_user.id
    ).order_by(UserRoute.updated_at.desc()).all()

    return [
        RouteResponse(
            id=str(route.id),
            user_id=str(route.user_id),
            name=route.name,
            description=route.description,
            total_distance_meters=route.total_distance_meters,
            total_curvature=route.total_curvature,
            created_at=route.created_at,
            updated_at=route.updated_at,
            is_public=route.is_public,
            tags=route.tags.get('tags', []) if route.tags else [],
            road_count=len(route.route_roads)
        )
        for route in routes
    ]


@router.post("", response_model=RouteDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    route_data: RouteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new route.

    Args:
        route_data: Route creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        RouteDetailResponse: Created route with roads

    Raises:
        HTTPException: 404 if any road not found
    """
    # Validate that all roads exist
    roads = db.query(Road).filter(Road.id.in_(route_data.road_ids)).all()
    if len(roads) != len(route_data.road_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more roads not found"
        )

    # Calculate total distance and curvature
    total_distance = sum(road.length_meters for road in roads)
    total_curvature = sum(road.curvature for road in roads)

    # Create route
    new_route = UserRoute(
        user_id=current_user.id,
        name=route_data.name,
        description=route_data.description,
        total_distance_meters=total_distance,
        total_curvature=total_curvature,
        is_public=False,
        tags={"tags": route_data.tags} if route_data.tags else None
    )

    db.add(new_route)
    db.flush()  # Get the route ID without committing

    # Add roads to route in order
    road_map = {road.id: road for road in roads}
    for position, road_id in enumerate(route_data.road_ids):
        route_road = RouteRoad(
            route_id=new_route.id,
            road_id=road_id,
            position=position
        )
        db.add(route_road)

    db.commit()
    db.refresh(new_route)

    # Build response with road details
    route_roads = []
    for rr in sorted(new_route.route_roads, key=lambda x: x.position):
        road = road_map[rr.road_id]
        route_roads.append(RoadInRoute(
            road_id=road.id,
            position=rr.position,
            road_name=road.name,
            curvature=road.curvature,
            length_km=road.length_meters / 1000 if road.length_meters else None,
            surface=road.surface
        ))

    return RouteDetailResponse(
        id=str(new_route.id),
        user_id=str(new_route.user_id),
        name=new_route.name,
        description=new_route.description,
        total_distance_meters=new_route.total_distance_meters,
        total_curvature=new_route.total_curvature,
        created_at=new_route.created_at,
        updated_at=new_route.updated_at,
        is_public=new_route.is_public,
        tags=new_route.tags.get('tags', []) if new_route.tags else [],
        road_count=len(route_roads),
        roads=route_roads
    )


@router.get("/{route_id}", response_model=RouteDetailResponse)
async def get_route(
    route_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific route with all roads.

    Args:
        route_id: Route ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        RouteDetailResponse: Route details with roads

    Raises:
        HTTPException: 404 if route not found or not owned by user
    """
    route = db.query(UserRoute).options(
        joinedload(UserRoute.route_roads).joinedload(RouteRoad.road)
    ).filter(
        UserRoute.id == route_id,
        UserRoute.user_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    # Build response with road details
    route_roads = []
    for rr in sorted(route.route_roads, key=lambda x: x.position):
        route_roads.append(RoadInRoute(
            road_id=rr.road.id,
            position=rr.position,
            road_name=rr.road.name,
            curvature=rr.road.curvature,
            length_km=rr.road.length_meters / 1000 if rr.road.length_meters else None,
            surface=rr.road.surface
        ))

    return RouteDetailResponse(
        id=str(route.id),
        user_id=str(route.user_id),
        name=route.name,
        description=route.description,
        total_distance_meters=route.total_distance_meters,
        total_curvature=route.total_curvature,
        created_at=route.created_at,
        updated_at=route.updated_at,
        is_public=route.is_public,
        tags=route.tags.get('tags', []) if route.tags else [],
        road_count=len(route_roads),
        roads=route_roads
    )


@router.patch("/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: UUID,
    route_data: RouteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update route metadata (name, description, tags, etc).

    Args:
        route_id: Route ID
        route_data: Route update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        RouteResponse: Updated route

    Raises:
        HTTPException: 404 if route not found or not owned by user
    """
    route = db.query(UserRoute).filter(
        UserRoute.id == route_id,
        UserRoute.user_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    # Update fields
    if route_data.name is not None:
        route.name = route_data.name
    if route_data.description is not None:
        route.description = route_data.description
    if route_data.is_public is not None:
        route.is_public = route_data.is_public
    if route_data.tags is not None:
        route.tags = {"tags": route_data.tags}

    route.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(route)

    return RouteResponse(
        id=str(route.id),
        user_id=str(route.user_id),
        name=route.name,
        description=route.description,
        total_distance_meters=route.total_distance_meters,
        total_curvature=route.total_curvature,
        created_at=route.created_at,
        updated_at=route.updated_at,
        is_public=route.is_public,
        tags=route.tags.get('tags', []) if route.tags else [],
        road_count=len(route.route_roads)
    )


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a route.

    Args:
        route_id: Route ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 404 if route not found or not owned by user
    """
    route = db.query(UserRoute).filter(
        UserRoute.id == route_id,
        UserRoute.user_id == current_user.id
    ).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    db.delete(route)
    db.commit()

    return None
