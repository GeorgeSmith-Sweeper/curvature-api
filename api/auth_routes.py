#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Authentication Routes
=====================
FastAPI routes for user authentication.

Endpoints:
- POST /auth/register: Create new user account
- POST /auth/login: Login and get access + refresh tokens
- POST /auth/logout: Revoke refresh token
- POST /auth/refresh: Get new access token using refresh token
- GET /auth/me: Get current user profile
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
    decode_token,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from api.database import get_db
from api.dependencies import get_current_user
from api.models import User, UserSession


# Create router for auth endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response validation
class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class UserResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    display_name: Optional[str]
    created_at: datetime
    email_verified: bool
    subscription_tier: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Args:
        user_data: User registration data (email, password, display_name)
        db: Database session

    Returns:
        TokenResponse: Access token, refresh token, and user data

    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Create new user
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_pw,
        display_name=user_data.display_name or user_data.email.split('@')[0]
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate tokens
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

    # Store refresh token in database
    session = UserSession(
        user_id=new_user.id,
        refresh_token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(new_user.id),
            "email": new_user.email,
            "display_name": new_user.display_name,
            "subscription_tier": new_user.subscription_tier
        }
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.

    Args:
        credentials: Login credentials (email, password)
        db: Database session

    Returns:
        TokenResponse: Access token, refresh token, and user data

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Store refresh token in database
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "subscription_tier": user.subscription_tier
        }
    )


@router.post("/refresh", response_model=dict)
async def refresh_access_token(token_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Get a new access token using a refresh token.

    Args:
        token_data: Refresh token
        db: Database session

    Returns:
        dict: New access token

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    # Decode refresh token
    payload = decode_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check if refresh token exists in database
    token_hash = hash_token(token_data.refresh_token)
    session = db.query(UserSession).filter(
        UserSession.refresh_token_hash == token_hash,
        UserSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked"
        )

    # Check if token is expired
    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )

    # Update last_used_at
    session.last_used_at = datetime.utcnow()
    db.commit()

    # Generate new access token
    access_token = create_access_token(data={"sub": user_id})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token_data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout by revoking the refresh token.

    Args:
        token_data: Refresh token to revoke
        current_user: Current authenticated user
        db: Database session

    Returns:
        None (204 No Content)
    """
    # Find and delete the session
    token_hash = hash_token(token_data.refresh_token)
    session = db.query(UserSession).filter(
        UserSession.refresh_token_hash == token_hash,
        UserSession.user_id == current_user.id
    ).first()

    if session:
        db.delete(session)
        db.commit()

    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: User profile data
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        created_at=current_user.created_at,
        email_verified=current_user.email_verified,
        subscription_tier=current_user.subscription_tier
    )
