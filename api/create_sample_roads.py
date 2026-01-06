#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Create Sample Roads
===================
Populate the database with sample curvy roads for testing the mobile app.
"""

import sys
import json
from pathlib import Path
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

# Add parent directory to path so we can import api modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import SessionLocal
from api.models import Road


def create_sample_roads():
    """Create sample roads with varying curvature levels."""

    db = SessionLocal()

    # Sample roads with different curvature levels
    sample_roads = [
        {
            "name": "Blue Ridge Parkway",
            "curvature": 150.5,
            "length_meters": 50000,
            "surface": "paved",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-82.5, 35.5],
                    [-82.52, 35.52],
                    [-82.54, 35.54]
                ]
            }
        },
        {
            "name": "Tail of the Dragon",
            "curvature": 318.0,
            "length_meters": 17700,
            "surface": "paved",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-83.9, 35.5],
                    [-83.92, 35.52],
                    [-83.94, 35.54]
                ]
            }
        },
        {
            "name": "Pacific Coast Highway",
            "curvature": 95.2,
            "length_meters": 65000,
            "surface": "paved",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-121.9, 36.4],
                    [-121.92, 36.42],
                    [-121.94, 36.44]
                ]
            }
        },
        {
            "name": "Beartooth Highway",
            "curvature": 210.8,
            "length_meters": 48000,
            "surface": "paved",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-109.5, 45.0],
                    [-109.52, 45.02],
                    [-109.54, 45.04]
                ]
            }
        },
        {
            "name": "Mulholland Drive",
            "curvature": 125.3,
            "length_meters": 35000,
            "surface": "paved",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-118.4, 34.1],
                    [-118.42, 34.12],
                    [-118.44, 34.14]
                ]
            }
        },
        {
            "name": "Going-to-the-Sun Road",
            "curvature": 185.6,
            "length_meters": 80000,
            "surface": "paved",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-113.7, 48.7],
                    [-113.72, 48.72],
                    [-113.74, 48.74]
                ]
            }
        },
        {
            "name": "Highway 1 Big Sur",
            "curvature": 142.0,
            "length_meters": 72000,
            "surface": "paved",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-121.8, 36.2],
                    [-121.82, 36.22],
                    [-121.84, 36.24]
                ]
            }
        },
        {
            "name": "Cherohala Skyway",
            "curvature": 165.9,
            "length_meters": 69000,
            "surface": "paved",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-84.1, 35.4],
                    [-84.12, 35.42],
                    [-84.14, 35.44]
                ]
            }
        }
    ]

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
