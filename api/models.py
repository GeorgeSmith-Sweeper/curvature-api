#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Database Models
===============
SQLAlchemy models for the Curvature API database.

Tables:
- users: User accounts
- user_sessions: Refresh token management
- roads: Road data populated from msgpack files
- user_routes: User-created custom routes
- route_roads: Roads within routes (ordered)
- user_favorites: User favorite roads
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from geoalchemy2 import Geography


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class User(Base):
    """User accounts table"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_tier: Mapped[str] = mapped_column(String(50), default='free')  # free, premium

    # Relationships
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    routes: Mapped[List["UserRoute"]] = relationship("UserRoute", back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[List["UserFavorite"]] = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', display_name='{self.display_name}')>"


class UserSession(Base):
    """User sessions for refresh token management"""
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    device_info: Mapped[Optional[dict]] = mapped_column(JSONB)  # device name, platform, app version
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class Road(Base):
    """Roads table populated from curvature msgpack data"""
    __tablename__ = "roads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collection_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)  # from curvature data
    name: Mapped[Optional[str]] = mapped_column(String(500))
    curvature: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    length_meters: Mapped[float] = mapped_column(Float, nullable=False)
    surface: Mapped[Optional[str]] = mapped_column(String(50), index=True)  # paved, unpaved, unknown
    join_type: Mapped[Optional[str]] = mapped_column(String(50))
    geometry = Column(Geography(geometry_type='LINESTRING', srid=4326, spatial_index=False))  # PostGIS geography column, index defined in __table_args__
    properties: Mapped[Optional[dict]] = mapped_column(JSONB)  # flexible storage for additional metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    route_roads: Mapped[List["RouteRoad"]] = relationship("RouteRoad", back_populates="road", cascade="all, delete-orphan")
    favorites: Mapped[List["UserFavorite"]] = relationship("UserFavorite", back_populates="road", cascade="all, delete-orphan")

    # Indexes for spatial queries
    __table_args__ = (
        Index('idx_roads_geometry', 'geometry', postgresql_using='gist'),
    )

    def __repr__(self):
        return f"<Road(id={self.id}, name='{self.name}', curvature={self.curvature})>"


class UserRoute(Base):
    """User-created custom routes"""
    __tablename__ = "user_routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    total_distance_meters: Mapped[Optional[float]] = mapped_column(Float)
    total_curvature: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[dict]] = mapped_column(JSONB)  # ["motorcycle", "scenic", "technical"]

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="routes")
    route_roads: Mapped[List["RouteRoad"]] = relationship("RouteRoad", back_populates="route", cascade="all, delete-orphan", order_by="RouteRoad.position")

    def __repr__(self):
        return f"<UserRoute(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class RouteRoad(Base):
    """Roads within a route (ordered list)"""
    __tablename__ = "route_roads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_routes.id", ondelete="CASCADE"), nullable=False, index=True)
    road_id: Mapped[int] = mapped_column(Integer, ForeignKey("roads.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # order in route (0, 1, 2...)
    connection_type: Mapped[str] = mapped_column(String(50), default='direct')  # 'direct' or 'routing'
    connection_geometry = Column(Geography(geometry_type='LINESTRING', srid=4326, spatial_index=False))  # connector road from routing API, index defined in __table_args__
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    route: Mapped["UserRoute"] = relationship("UserRoute", back_populates="route_roads")
    road: Mapped["Road"] = relationship("Road", back_populates="route_roads")

    # Indexes for efficient lookups
    __table_args__ = (
        Index('idx_route_roads_route_position', 'route_id', 'position'),
        Index('idx_route_roads_connection_geometry', 'connection_geometry', postgresql_using='gist'),
    )

    def __repr__(self):
        return f"<RouteRoad(id={self.id}, route_id={self.route_id}, road_id={self.road_id}, position={self.position})>"


class UserFavorite(Base):
    """User favorite roads (quick-save)"""
    __tablename__ = "user_favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    road_id: Mapped[int] = mapped_column(Integer, ForeignKey("roads.id"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    road: Mapped["Road"] = relationship("Road", back_populates="favorites")

    # Unique constraint: user can favorite a road only once
    __table_args__ = (
        Index('idx_user_favorites_unique', 'user_id', 'road_id', unique=True),
    )

    def __repr__(self):
        return f"<UserFavorite(id={self.id}, user_id={self.user_id}, road_id={self.road_id})>"
