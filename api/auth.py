#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Authentication Module
=====================
JWT authentication, password hashing, and token management.

This module provides:
- Password hashing and verification (bcrypt)
- JWT access token generation and validation
- Refresh token management
- User authentication helpers
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password: Plain-text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.

    Args:
        plain_password: Plain-text password
        hashed_password: Hashed password from database

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Dictionary of claims to encode in the token (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        dict: Token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """
    Hash a token for secure storage in database.

    Args:
        token: JWT token string

    Returns:
        str: SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def get_password_reset_token(email: str) -> str:
    """
    Generate a password reset token.

    Args:
        email: User email address

    Returns:
        str: Password reset token (valid for 1 hour)
    """
    data = {"sub": email, "type": "password_reset"}
    expire = timedelta(hours=1)
    return create_access_token(data, expires_delta=expire)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and return the email.

    Args:
        token: Password reset token

    Returns:
        str: Email if token is valid, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "password_reset":
        return payload.get("sub")
    return None
