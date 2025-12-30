#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Test Configuration
==================
Pytest fixtures and configuration for integration tests.

This module provides:
- Test database setup and teardown
- FastAPI test client
- Authenticated user fixtures
- Sample data fixtures
"""

import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test database URL
os.environ["DATABASE_URL"] = "postgresql://curvature_user:curvature_pass@localhost:5432/curvature_test_db"

from api.database import get_db
from api.models import Base, User, Road
from api.auth import hash_password


# Create test database engine
TEST_DATABASE_URL = os.environ["DATABASE_URL"]
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.

    This fixture:
    - Creates all tables before the test
    - Yields a database session
    - Drops all tables after the test

    Yields:
        Session: SQLAlchemy database session
    """
    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with test database.

    Args:
        db: Test database session

    Yields:
        TestClient: FastAPI test client
    """
    # Import server after setting environment variable
    from api.server import app

    # Override database dependency
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """
    Create a test user in the database.

    Args:
        db: Test database session

    Returns:
        User: Created test user
    """
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123"),
        display_name="Test User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """
    Get authentication headers for test requests.

    Args:
        client: FastAPI test client
        test_user: Test user

    Returns:
        dict: Authorization headers with Bearer token
    """
    # Login to get access token
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "TestPassword123"
    })

    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_road(db: Session) -> Road:
    """
    Create a test road in the database.

    Args:
        db: Test database session

    Returns:
        Road: Created test road
    """
    from geoalchemy2.shape import from_shape
    from shapely.geometry import LineString

    # Create a simple road with geometry
    coords = [(-72.5, 44.0), (-72.51, 44.01), (-72.52, 44.02)]
    linestring = LineString(coords)
    geometry_wkb = from_shape(linestring, srid=4326)

    road = Road(
        collection_id="test_road_1",
        name="Test Road",
        curvature=1500.0,
        length_meters=5000.0,
        surface="paved",
        join_type="none",
        geometry=geometry_wkb,
        properties={"test": True}
    )

    db.add(road)
    db.commit()
    db.refresh(road)
    return road


@pytest.fixture
def multiple_test_roads(db: Session) -> list[Road]:
    """
    Create multiple test roads in the database.

    Args:
        db: Test database session

    Returns:
        list[Road]: List of created test roads
    """
    from geoalchemy2.shape import from_shape
    from shapely.geometry import LineString

    roads = []

    road_data = [
        ("Road 1", 500.0, 3000.0, "paved"),
        ("Road 2", 1200.0, 8000.0, "paved"),
        ("Road 3", 2500.0, 12000.0, "unpaved"),
    ]

    for i, (name, curvature, length, surface) in enumerate(road_data):
        coords = [(-72.5 + i*0.1, 44.0), (-72.51 + i*0.1, 44.01)]
        linestring = LineString(coords)
        geometry_wkb = from_shape(linestring, srid=4326)

        road = Road(
            collection_id=f"test_road_{i+1}",
            name=name,
            curvature=curvature,
            length_meters=length,
            surface=surface,
            geometry=geometry_wkb
        )

        db.add(road)
        roads.append(road)

    db.commit()

    for road in roads:
        db.refresh(road)

    return roads
