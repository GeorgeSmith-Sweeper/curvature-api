#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Curvature API Server
====================
A FastAPI-based REST API for querying curvature road data.

This server provides endpoints to:
- Search for curvy roads by various criteria
- Return GeoJSON for map visualization
- Serve the web interface

Author: George Smith-Sweeper (contribution to adamfranco/curvature)
"""

import os
import sys
import json
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import msgpack

# Add parent directory to path to import curvature modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    from curvature.output import OutputTools
    CURVATURE_AVAILABLE = True
except ImportError:
    CURVATURE_AVAILABLE = False
    OutputTools = None

# Import configuration (API keys, etc.)
try:
    from api import config
    GOOGLE_MAPS_API_KEY = config.GOOGLE_MAPS_API_KEY
except ImportError:
    GOOGLE_MAPS_API_KEY = None
    print("Warning: api/config.py not found. Please copy config.example.py to config.py and add your API keys.")

# Import new route modules for authentication, routes, and favorites
from api.auth_routes import router as auth_router
from api.route_routes import router as routes_router
from api.favorites_routes import router as favorites_router
from api.roads_routes import router as roads_router

# Initialize FastAPI app
app = FastAPI(
    title="Curvature API",
    description="API for finding and exploring curvy roads with user authentication, route planning, and favorites",
    version="2.0.0"
)

# Enable CORS so web browsers can access the API
# CORS = Cross-Origin Resource Sharing - allows JavaScript from your web page to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for new features
app.include_router(auth_router)
app.include_router(routes_router)
app.include_router(roads_router)
app.include_router(favorites_router)

# Initialize output tools (provides utility methods for working with collections)
tools = OutputTools('km') if CURVATURE_AVAILABLE else None

# Global variable to store loaded road data
# In a production app, you'd use a database, but for now we'll load from msgpack files
road_collections = []
data_loaded = False


def load_msgpack_file(filepath: str) -> List[dict]:
    """
    Load a curvature msgpack file and return the road collections.

    Args:
        filepath: Path to the .msgpack file

    Returns:
        List of road collection dictionaries

    Explanation:
        - msgpack is a binary format (like JSON but more compact)
        - Unpacker reads the file piece by piece (streaming)
        - Each item is a 'collection' - a group of connected road segments
    """
    collections = []

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")

    with open(filepath, 'rb') as f:
        # Create an unpacker that reads from the file
        # use_list=True means arrays become Python lists (not tuples)
        # raw=False means byte strings are decoded to Python strings
        unpacker = msgpack.Unpacker(f, use_list=True, raw=False, strict_map_key=False)

        # Iterate over each collection in the msgpack stream
        for collection in unpacker:
            collections.append(collection)

    return collections


def collection_to_geojson_feature(collection: dict) -> dict:
    """
    Convert a curvature collection to a GeoJSON Feature.

    Args:
        collection: A road collection from curvature

    Returns:
        A GeoJSON Feature dictionary

    Explanation:
        GeoJSON is a standard format for geographic data that maps understand.
        A Feature has:
        - geometry: the shape (LineString = a line)
        - properties: metadata (name, curvature score, etc.)
    """
    # Build the line coordinates from all segments in all ways
    coords = []

    for way in collection['ways']:
        # Check if this way has been processed with segments
        if 'segments' in way and len(way['segments']) > 0:
            # Add the starting point of the first segment
            first_segment = way['segments'][0]
            coords.append([first_segment['start'][1], first_segment['start'][0]])  # [lon, lat]

            # Add all endpoint coordinates
            for segment in way['segments']:
                coords.append([segment['end'][1], segment['end'][0]])  # [lon, lat]

    # Calculate useful properties using the OutputTools
    curvature = tools.get_collection_curvature(collection)
    length = tools.get_collection_length(collection)
    name = tools.get_collection_name(collection)
    surface = tools.get_collection_paved_style(collection)

    # Build the GeoJSON Feature
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coords
        },
        "properties": {
            "name": name,
            "curvature": round(curvature, 2),
            "length_km": round(length / 1000, 2),
            "length_mi": round(length / 1609, 2),
            "surface": surface,
            "join_type": collection.get('join_type', 'none'),
        }
    }

    return feature


# API Endpoints
# =============

@app.get("/")
async def root():
    """
    Root endpoint - returns API info.
    """
    return {
        "name": "Curvature API",
        "version": "1.0.0",
        "endpoints": {
            "/roads": "Search for roads",
            "/roads/geojson": "Get roads as GeoJSON",
            "/config": "Get frontend configuration",
            "/docs": "Interactive API documentation"
        }
    }


@app.get("/config")
async def get_config():
    """
    Get frontend configuration including API keys.

    This endpoint serves configuration to the frontend in a secure way.
    The actual API keys are stored in api/config.py which is gitignored.

    Returns:
        Configuration object with Google Maps API key and other settings
    """
    if GOOGLE_MAPS_API_KEY is None:
        raise HTTPException(
            status_code=500,
            detail="Google Maps API key not configured. Please create api/config.py from api/config.example.py"
        )

    return {
        "google_maps_api_key": GOOGLE_MAPS_API_KEY,
        "default_center": {
            "lat": 44.0,
            "lng": -72.7
        },
        "default_zoom": 8
    }


@app.post("/data/load")
async def load_data(filepath: str):
    """
    Load a msgpack data file into memory.

    Args:
        filepath: Path to the .msgpack file to load

    Example:
        POST /data/load?filepath=/tmp/vermont.msgpack
    """
    if not CURVATURE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Curvature library not available. This legacy endpoint requires the curvature library to be installed."
        )

    global road_collections, data_loaded

    try:
        road_collections = load_msgpack_file(filepath)
        data_loaded = True
        return {
            "status": "success",
            "message": f"Loaded {len(road_collections)} road collections",
            "filepath": filepath
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


@app.get("/roads/geojson")
async def get_roads_geojson(
    min_curvature: Optional[float] = Query(300, description="Minimum curvature score"),
    max_curvature: Optional[float] = Query(None, description="Maximum curvature score"),
    surface: Optional[str] = Query(None, description="Surface type: paved, unpaved, or unknown"),
    limit: Optional[int] = Query(100, description="Maximum number of roads to return")
):
    """
    Get roads as GeoJSON FeatureCollection (legacy msgpack endpoint).

    Query parameters let you filter results:
    - min_curvature: Only roads curvier than this (default: 300)
    - max_curvature: Only roads less curvy than this
    - surface: Filter by surface type
    - limit: Max number of results (default: 100)

    Returns:
        GeoJSON FeatureCollection that can be directly loaded into maps

    Example:
        GET /roads/geojson?min_curvature=1000&surface=paved&limit=50
    """
    if not CURVATURE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Curvature library not available. This legacy endpoint requires the curvature library to be installed."
        )

    if not data_loaded:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Please POST to /data/load first."
        )

    # Filter collections based on criteria
    filtered = []

    for collection in road_collections:
        # Calculate curvature for this collection
        curvature = tools.get_collection_curvature(collection)

        # Apply filters
        if curvature < min_curvature:
            continue

        if max_curvature and curvature > max_curvature:
            continue

        if surface:
            collection_surface = tools.get_collection_paved_style(collection)
            if collection_surface != surface:
                continue

        # Passed all filters - add to results
        filtered.append(collection)

        # Check limit
        if len(filtered) >= limit:
            break

    # Convert to GeoJSON features
    features = []
    for collection in filtered:
        try:
            feature = collection_to_geojson_feature(collection)
            features.append(feature)
        except Exception as e:
            # Skip collections that can't be converted (e.g., no segments)
            continue

    # Build GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_collections": len(road_collections),
            "filtered_count": len(features),
            "filters": {
                "min_curvature": min_curvature,
                "max_curvature": max_curvature,
                "surface": surface,
                "limit": limit
            }
        }
    }

    return JSONResponse(content=geojson)


@app.get("/roads")
async def search_roads(
    min_curvature: Optional[float] = Query(300, description="Minimum curvature score"),
    limit: Optional[int] = Query(20, description="Maximum number of roads to return")
):
    """
    Search for roads and return as simple JSON (legacy msgpack endpoint).

    Useful for getting a quick list without the full geometry.

    Returns:
        List of road objects with name, curvature, length
    """
    if not CURVATURE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Curvature library not available. This legacy endpoint requires the curvature library to be installed."
        )

    if not data_loaded:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Please POST to /data/load first."
        )

    results = []

    for collection in road_collections:
        curvature = tools.get_collection_curvature(collection)

        if curvature < min_curvature:
            continue

        results.append({
            "name": tools.get_collection_name(collection),
            "curvature": round(curvature, 2),
            "length_km": round(tools.get_collection_length(collection) / 1000, 2),
            "length_mi": round(tools.get_collection_length(collection) / 1609, 2),
            "surface": tools.get_collection_paved_style(collection)
        })

        if len(results) >= limit:
            break

    return {
        "total_found": len(results),
        "roads": results
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - useful for monitoring.
    """
    return {
        "status": "healthy",
        "data_loaded": data_loaded,
        "collections_count": len(road_collections) if data_loaded else 0
    }


# Mount the web interface static files
# This allows serving HTML/CSS/JS files from the /web directory
web_path = Path(__file__).parent.parent / "web" / "static"
if web_path.exists():
    app.mount("/static", StaticFiles(directory=str(web_path)), name="static")


# Run the server
# ==============
if __name__ == "__main__":
    import uvicorn

    # Start the server on http://localhost:8000
    # reload=True means the server restarts when code changes (great for development)
    uvicorn.run(
        "server:app",
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,
        reload=True
    )
