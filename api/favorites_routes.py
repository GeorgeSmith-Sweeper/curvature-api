#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Favorites Routes
================
FastAPI routes for managing user favorite roads.

Endpoints:
- GET /favorites: List user's favorite roads
- POST /favorites: Add road to favorites
- DELETE /favorites/{road_id}: Remove road from favorites
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from api.database import get_db
from api.dependencies import get_current_user
from api.models import User, UserFavorite, Road


# Create router for favorites endpoints
router = APIRouter(prefix="/favorites", tags=["favorites"])


# Pydantic models for request/response validation
class FavoriteCreate(BaseModel):
    """Add favorite request"""
    road_id: int
    notes: Optional[str] = None


class FavoriteResponse(BaseModel):
    """Favorite response"""
    id: int
    road_id: int
    road_name: Optional[str]
    curvature: Optional[float]
    length_km: Optional[float]
    surface: Optional[str]
    notes: Optional[str]
    created_at: datetime


@router.get("", response_model=List[FavoriteResponse])
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all favorite roads for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[FavoriteResponse]: List of user's favorite roads
    """
    favorites = db.query(UserFavorite).options(
        joinedload(UserFavorite.road)
    ).filter(
        UserFavorite.user_id == current_user.id
    ).order_by(UserFavorite.created_at.desc()).all()

    return [
        FavoriteResponse(
            id=fav.id,
            road_id=fav.road.id,
            road_name=fav.road.name,
            curvature=fav.road.curvature,
            length_km=fav.road.length_meters / 1000 if fav.road.length_meters else None,
            surface=fav.road.surface,
            notes=fav.notes,
            created_at=fav.created_at
        )
        for fav in favorites
    ]


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a road to user's favorites.

    Args:
        favorite_data: Favorite creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        FavoriteResponse: Created favorite

    Raises:
        HTTPException: 404 if road not found
        HTTPException: 409 if road already in favorites
    """
    # Check if road exists
    road = db.query(Road).filter(Road.id == favorite_data.road_id).first()
    if not road:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Road not found"
        )

    # Check if already favorited
    existing = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.road_id == favorite_data.road_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Road already in favorites"
        )

    # Create favorite
    new_favorite = UserFavorite(
        user_id=current_user.id,
        road_id=favorite_data.road_id,
        notes=favorite_data.notes
    )

    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)

    return FavoriteResponse(
        id=new_favorite.id,
        road_id=road.id,
        road_name=road.name,
        curvature=road.curvature,
        length_km=road.length_meters / 1000 if road.length_meters else None,
        surface=road.surface,
        notes=new_favorite.notes,
        created_at=new_favorite.created_at
    )


@router.delete("/{road_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    road_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a road from user's favorites.

    Args:
        road_id: Road ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 404 if favorite not found
    """
    favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.road_id == road_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    db.delete(favorite)
    db.commit()

    return None
