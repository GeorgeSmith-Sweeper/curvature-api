#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Create Sample Roads
===================
Populate the database with sample curvy roads for testing the mobile app.
"""

import sys
import json
import math
from pathlib import Path
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

# Add parent directory to path so we can import api modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import SessionLocal
from api.models import Road


def generate_curved_path(start_lon, start_lat, length_km, curvature, num_points=80):
    """
    Generate a realistic curved path with many coordinate points.

    Args:
        start_lon: Starting longitude
        start_lat: Starting latitude
        length_km: Total length in kilometers
        curvature: Curvature value (higher = more curves)
        num_points: Number of coordinate points to generate

    Returns:
        List of [lon, lat] coordinates
    """
    coords = []

    # Convert length to degrees (rough approximation: 111km per degree)
    length_deg = length_km / 111.0

    # Number of curves based on curvature value
    num_curves = max(1, int(curvature / 30))

    # Amplitude of curves (how far they deviate from straight line)
    amplitude = length_deg * (curvature / 300) * 0.15

    for i in range(num_points):
        t = i / (num_points - 1)  # 0 to 1

        # Base progression along the road
        lon = start_lon + (length_deg * t * 0.7)
        lat = start_lat + (length_deg * t * 0.3)

        # Add sinusoidal curves
        curve_offset = math.sin(t * num_curves * 2 * math.pi) * amplitude

        # Apply curves perpendicular to the direction
        lon += curve_offset * 0.5
        lat += curve_offset * 0.8

        coords.append([lon, lat])

    return coords


def create_sample_roads():
    """Create sample roads with varying curvature levels."""

    db = SessionLocal()

    # Sample roads with different curvature levels
    sample_roads_data = [
        {"name": "Blue Ridge Parkway", "curvature": 150.5, "length_meters": 50000, "surface": "paved", "start": [-82.5, 35.5]},
        {"name": "Tail of the Dragon", "curvature": 318.0, "length_meters": 17700, "surface": "paved", "start": [-83.9, 35.5]},
        {"name": "Pacific Coast Highway", "curvature": 95.2, "length_meters": 65000, "surface": "paved", "start": [-121.9, 36.4]},
        {"name": "Beartooth Highway", "curvature": 210.8, "length_meters": 48000, "surface": "paved", "start": [-109.5, 45.0]},
        {"name": "Mulholland Drive", "curvature": 125.3, "length_meters": 35000, "surface": "paved", "start": [-118.4, 34.1]},
        {"name": "Going-to-the-Sun Road", "curvature": 185.6, "length_meters": 80000, "surface": "paved", "start": [-113.7, 48.7]},
        {"name": "Highway 1 Big Sur", "curvature": 142.0, "length_meters": 72000, "surface": "paved", "start": [-121.8, 36.2]},
        {"name": "Cherohala Skyway", "curvature": 165.9, "length_meters": 69000, "surface": "paved", "start": [-84.1, 35.4]},
    ]

    # Generate curved paths for each road
    sample_roads = []
    for road_data in sample_roads_data:
        length_km = road_data['length_meters'] / 1000
        coords = generate_curved_path(
            road_data['start'][0],
            road_data['start'][1],
            length_km,
            road_data['curvature']
        )
        sample_roads.append({
            "name": road_data['name'],
            "curvature": road_data['curvature'],
            "length_meters": road_data['length_meters'],
            "surface": road_data['surface'],
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        })

    # Create Road objects, converting geometry dicts to proper PostGIS format
    roads = []
    for road_data in sample_roads:
        # Convert coordinates to Shapely LineString, then to PostGIS format
        coords = road_data['geometry']['coordinates']
        linestring = LineString(coords)
        road_data['geometry'] = from_shape(linestring, srid=4326)

        roads.append(Road(**road_data))

    # Add to database
    db.add_all(roads)
    db.commit()

    print(f"✅ Created {len(roads)} sample roads")
    for road in roads:
        print(f"   - {road.name}: {road.curvature} curvature, {road.length_meters/1000:.1f}km")

    db.close()


if __name__ == "__main__":
    print("Creating sample roads...")
    create_sample_roads()
    print("Done!")
