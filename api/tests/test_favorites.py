#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Favorites Tests
===============
Integration tests for favorites endpoints.

Tests:
- List favorites
- Add favorite
- Remove favorite
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.models import UserFavorite, Road


def test_list_favorites_empty(client: TestClient, auth_headers: dict):
    """Test listing favorites when user has none."""
    response = client.get("/favorites", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_add_favorite(client: TestClient, auth_headers: dict, test_road: Road):
    """Test adding a road to favorites."""
    response = client.post("/favorites", headers=auth_headers, json={
        "road_id": test_road.id,
        "notes": "Great curves!"
    })

    assert response.status_code == 201
    data = response.json()

    assert data["road_id"] == test_road.id
    assert data["road_name"] == test_road.name
    assert data["curvature"] == test_road.curvature
    assert data["notes"] == "Great curves!"
    assert "created_at" in data


def test_add_favorite_without_notes(client: TestClient, auth_headers: dict, test_road: Road):
    """Test adding favorite without notes."""
    response = client.post("/favorites", headers=auth_headers, json={
        "road_id": test_road.id
    })

    assert response.status_code == 201
    data = response.json()

    assert data["road_id"] == test_road.id
    assert data["notes"] is None


def test_add_favorite_invalid_road(client: TestClient, auth_headers: dict):
    """Test adding non-existent road to favorites."""
    response = client.post("/favorites", headers=auth_headers, json={
        "road_id": 99999  # Non-existent road
    })

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_add_favorite_duplicate(client: TestClient, auth_headers: dict, test_road: Road):
    """Test adding same road to favorites twice."""
    # Add favorite
    client.post("/favorites", headers=auth_headers, json={
        "road_id": test_road.id
    })

    # Try to add again
    response = client.post("/favorites", headers=auth_headers, json={
        "road_id": test_road.id
    })

    assert response.status_code == 409
    assert "already in favorites" in response.json()["detail"].lower()


def test_add_favorite_unauthorized(client: TestClient, test_road: Road):
    """Test adding favorite without authentication."""
    response = client.post("/favorites", json={
        "road_id": test_road.id
    })

    assert response.status_code == 403  # No credentials


def test_list_favorites(client: TestClient, auth_headers: dict, multiple_test_roads: list[Road]):
    """Test listing user's favorites."""
    # Add some favorites
    for road in multiple_test_roads[:2]:
        client.post("/favorites", headers=auth_headers, json={
            "road_id": road.id
        })

    # List favorites
    response = client.get("/favorites", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert all("road_name" in fav for fav in data)
    assert all("curvature" in fav for fav in data)


def test_remove_favorite(client: TestClient, auth_headers: dict, test_road: Road, db: Session):
    """Test removing a road from favorites."""
    # Add favorite
    client.post("/favorites", headers=auth_headers, json={
        "road_id": test_road.id
    })

    # Remove favorite
    response = client.delete(f"/favorites/{test_road.id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify removal
    favorite = db.query(UserFavorite).filter(
        UserFavorite.road_id == test_road.id
    ).first()
    assert favorite is None


def test_remove_favorite_not_found(client: TestClient, auth_headers: dict):
    """Test removing non-existent favorite."""
    response = client.delete("/favorites/99999", headers=auth_headers)

    assert response.status_code == 404
