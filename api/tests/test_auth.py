#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Authentication Tests
====================
Integration tests for authentication endpoints.

Tests:
- User registration
- User login
- Token refresh
- Logout
- Get current user
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.models import User


def test_register_user(client: TestClient, db: Session):
    """Test user registration."""
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123",
        "display_name": "New User"
    })

    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["display_name"] == "New User"

    # Verify user in database
    user = db.query(User).filter(User.email == "newuser@example.com").first()
    assert user is not None
    assert user.display_name == "New User"


def test_register_duplicate_email(client: TestClient, test_user: User):
    """Test registration with duplicate email."""
    response = client.post("/auth/register", json={
        "email": "test@example.com",  # Already exists
        "password": "SecurePass123",
        "display_name": "Another User"
    })

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_weak_password(client: TestClient):
    """Test registration with weak password."""
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "short",  # Less than 8 characters
        "display_name": "New User"
    })

    assert response.status_code == 400
    assert "at least 8 characters" in response.json()["detail"].lower()


def test_login_success(client: TestClient, test_user: User):
    """Test successful login."""
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "TestPassword123"
    })

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"


def test_login_wrong_password(client: TestClient, test_user: User):
    """Test login with wrong password."""
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPassword123"
    })

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user."""
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "SomePassword123"
    })

    assert response.status_code == 401


def test_get_current_user(client: TestClient, auth_headers: dict):
    """Test getting current user profile."""
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert "id" in data
    assert "created_at" in data


def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without authentication."""
    response = client.get("/auth/me")

    assert response.status_code == 403  # No credentials provided


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token."""
    response = client.get("/auth/me", headers={
        "Authorization": "Bearer invalid_token_here"
    })

    assert response.status_code == 401


def test_refresh_token(client: TestClient, test_user: User):
    """Test refreshing access token."""
    # Login to get refresh token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "TestPassword123"
    })

    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # Refresh the access token
    refresh_response = client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert refresh_response.status_code == 200
    data = refresh_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(client: TestClient):
    """Test refreshing with invalid token."""
    response = client.post("/auth/refresh", json={
        "refresh_token": "invalid_refresh_token"
    })

    assert response.status_code == 401


def test_logout(client: TestClient, test_user: User):
    """Test logout (revoke refresh token)."""
    # Login
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "TestPassword123"
    })

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # Logout
    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert logout_response.status_code == 204

    # Try to refresh with revoked token (should fail)
    refresh_response = client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert refresh_response.status_code == 401
