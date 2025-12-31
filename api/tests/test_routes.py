#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Route Planning Tests
====================
Integration tests for route planning endpoints.

Tests:
- List routes
- Create route
- Get route details
- Update route
- Delete route
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.models import UserRoute, Road


def test_list_routes_empty(client: TestClient, auth_headers: dict):
    """Test listing routes when user has none."""
    response = client.get("/routes", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_create_route(client: TestClient, auth_headers: dict, multiple_test_roads: list[Road]):
    """Test creating a new route."""
    road_ids = [road.id for road in multiple_test_roads[:2]]

    response = client.post("/routes", headers=auth_headers, json={
        "name": "My Test Route",
        "description": "A scenic route",
        "road_ids": road_ids,
        "tags": ["scenic", "easy"]
    })

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "My Test Route"
    assert data["description"] == "A scenic route"
    assert data["road_count"] == 2
    assert data["tags"] == ["scenic", "easy"]
    assert data["total_distance_meters"] > 0
    assert data["total_curvature"] > 0
    assert len(data["roads"]) == 2

    # Verify roads are in correct order
    assert data["roads"][0]["road_id"] == road_ids[0]
    assert data["roads"][1]["road_id"] == road_ids[1]
    assert data["roads"][0]["position"] == 0
    assert data["roads"][1]["position"] == 1


def test_create_route_invalid_road(client: TestClient, auth_headers: dict):
    """Test creating route with non-existent road."""
    response = client.post("/routes", headers=auth_headers, json={
        "name": "Invalid Route",
        "road_ids": [99999]  # Non-existent road ID
    })

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_route_unauthorized(client: TestClient, multiple_test_roads: list[Road]):
    """Test creating route without authentication."""
    road_ids = [road.id for road in multiple_test_roads[:2]]

    response = client.post("/routes", json={
        "name": "My Test Route",
        "road_ids": road_ids
    })

    assert response.status_code == 403  # No credentials


def test_list_routes(client: TestClient, auth_headers: dict, multiple_test_roads: list[Road], db: Session):
    """Test listing user's routes."""
    # Create some routes first
    road_ids = [road.id for road in multiple_test_roads]

    client.post("/routes", headers=auth_headers, json={
        "name": "Route 1",
        "road_ids": road_ids[:2]
    })

    client.post("/routes", headers=auth_headers, json={
        "name": "Route 2",
        "road_ids": road_ids[1:]
    })

    # List routes
    response = client.get("/routes", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] in ["Route 1", "Route 2"]
    assert data[1]["name"] in ["Route 1", "Route 2"]


def test_get_route(client: TestClient, auth_headers: dict, multiple_test_roads: list[Road]):
    """Test getting a specific route."""
    # Create route
    road_ids = [road.id for road in multiple_test_roads[:2]]

    create_response = client.post("/routes", headers=auth_headers, json={
        "name": "Test Route",
        "road_ids": road_ids
    })

    route_id = create_response.json()["id"]

    # Get route
    response = client.get(f"/routes/{route_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Test Route"
    assert data["road_count"] == 2
    assert len(data["roads"]) == 2


def test_get_route_not_found(client: TestClient, auth_headers: dict):
    """Test getting non-existent route."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/routes/{fake_uuid}", headers=auth_headers)

    assert response.status_code == 404


def test_update_route(client: TestClient, auth_headers: dict, multiple_test_roads: list[Road]):
    """Test updating route metadata."""
    # Create route
    road_ids = [road.id for road in multiple_test_roads[:2]]

    create_response = client.post("/routes", headers=auth_headers, json={
        "name": "Original Name",
        "description": "Original description",
        "road_ids": road_ids
    })

    route_id = create_response.json()["id"]

    # Update route
    response = client.patch(f"/routes/{route_id}", headers=auth_headers, json={
        "name": "Updated Name",
        "description": "Updated description",
        "tags": ["updated", "test"]
    })

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"
    assert data["tags"] == ["updated", "test"]


def test_update_route_partial(client: TestClient, auth_headers: dict, multiple_test_roads: list[Road]):
    """Test partial update of route."""
    # Create route
    road_ids = [road.id for road in multiple_test_roads[:2]]

    create_response = client.post("/routes", headers=auth_headers, json={
        "name": "Original Name",
        "description": "Original description",
        "road_ids": road_ids
    })

    route_id = create_response.json()["id"]

    # Update only name
    response = client.patch(f"/routes/{route_id}", headers=auth_headers, json={
        "name": "New Name"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "New Name"
    assert data["description"] == "Original description"  # Unchanged


def test_delete_route(client: TestClient, auth_headers: dict, multiple_test_roads: list[Road], db: Session):
    """Test deleting a route."""
    # Create route
    road_ids = [road.id for road in multiple_test_roads[:2]]

    create_response = client.post("/routes", headers=auth_headers, json={
        "name": "Route to Delete",
        "road_ids": road_ids
    })

    route_id = create_response.json()["id"]

    # Delete route
    response = client.delete(f"/routes/{route_id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify deletion
    from uuid import UUID
    route = db.query(UserRoute).filter(UserRoute.id == UUID(route_id)).first()
    assert route is None


def test_delete_route_not_found(client: TestClient, auth_headers: dict):
    """Test deleting non-existent route."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/routes/{fake_uuid}", headers=auth_headers)

    assert response.status_code == 404
