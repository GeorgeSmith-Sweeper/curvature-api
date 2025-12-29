#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Database Connection
===================
Database connection and session management for the Curvature API.

This module provides:
- SQLAlchemy engine configuration
- Database session factory
- Dependency injection for FastAPI endpoints
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from api.models import Base


# Database URL from environment variable or default to local PostgreSQL
# Format: postgresql://username:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://curvature_user:curvature_pass@localhost:5432/curvature_db"
)

# Create SQLAlchemy engine
# echo=True logs all SQL statements (useful for debugging, disable in production)
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,  # Connection pool size
    max_overflow=20  # Max connections beyond pool_size
)

# Create session factory
# autocommit=False: Require explicit commits
# autoflush=False: Require explicit flushes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database by creating all tables.

    WARNING: This creates tables but doesn't handle migrations.
    For production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI endpoints to get a database session.

    Usage in FastAPI:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            # Use db session here
            pass

    Yields:
        Session: SQLAlchemy database session

    This function ensures:
    - A new session is created for each request
    - The session is automatically closed after the request
    - Exceptions are handled properly (rollback on error)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """
    Test database connection.
    Returns True if connection successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
