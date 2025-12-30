#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Populate Roads Table
====================
Script to populate the roads table from curvature msgpack files.

This script:
1. Loads road data from a msgpack file
2. Converts it to database format
3. Inserts roads into the PostgreSQL database
4. Creates spatial indexes for efficient queries

Usage:
    python populate_roads.py /path/to/data.msgpack
"""

import sys
import os
from typing import List, Dict

# Add parent directory to path so we can import from api package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import msgpack
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

from api.database import engine, SessionLocal
from api.models import Base, Road
from curvature.output import OutputTools


def load_msgpack_file(filepath: str) -> List[dict]:
    """
    Load a curvature msgpack file and return the road collections.

    Args:
        filepath: Path to the .msgpack file

    Returns:
        List of road collection dictionaries
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")

    collections = []
    print(f"Loading msgpack file: {filepath}")

    with open(filepath, 'rb') as f:
        unpacker = msgpack.Unpacker(f, use_list=True, raw=False, strict_map_key=False)
        for collection in unpacker:
            collections.append(collection)

    print(f"Loaded {len(collections)} road collections")
    return collections


def collection_to_road(collection: dict, tools: OutputTools) -> Dict:
    """
    Convert a curvature collection to a Road model.

    Args:
        collection: Curvature collection dictionary
        tools: OutputTools instance for extracting properties

    Returns:
        Dictionary of road properties ready for database insertion
    """
    # Extract properties using OutputTools
    curvature = tools.get_collection_curvature(collection)
    length = tools.get_collection_length(collection)  # Returns meters
    name = tools.get_collection_name(collection)
    surface = tools.get_collection_paved_style(collection)  # 'paved', 'unpaved', or 'unknown'

    # Build LineString geometry from all segments
    coordinates = []
    for way in collection.get('ways', []):
        for segment in way.get('segments', []):
            # Segments have [lat, lng] format, convert to [lng, lat] for PostGIS
            start = segment.get('start', [])
            if len(start) == 2:
                coordinates.append((start[1], start[0]))  # [lng, lat]

            end = segment.get('end', [])
            if len(end) == 2:
                coordinates.append((end[1], end[0]))  # [lng, lat]

    # Remove duplicate consecutive coordinates
    unique_coords = []
    for coord in coordinates:
        if not unique_coords or coord != unique_coords[-1]:
            unique_coords.append(coord)

    # Create LineString geometry
    if len(unique_coords) >= 2:
        linestring = LineString(unique_coords)
        geometry_wkb = from_shape(linestring, srid=4326)
    else:
        print(f"Warning: Collection '{name}' has insufficient coordinates, skipping geometry")
        geometry_wkb = None

    # Generate unique collection ID
    collection_id = f"road_{hash(str(collection)) % 1000000000}"

    return {
        'collection_id': collection_id,
        'name': name or 'Unnamed Road',
        'curvature': curvature,
        'length_meters': length,
        'surface': surface,
        'join_type': collection.get('join_type', 'none'),
        'geometry': geometry_wkb,
        'properties': {
            'ways_count': len(collection.get('ways', [])),
            'tags': collection.get('tags', {})
        }
    }


def populate_database(msgpack_path: str, batch_size: int = 100):
    """
    Populate the roads table from a msgpack file.

    Args:
        msgpack_path: Path to the msgpack file
        batch_size: Number of roads to insert per batch (default: 100)
    """
    # Initialize database (create tables if they don't exist)
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)

    # Load msgpack data
    collections = load_msgpack_file(msgpack_path)

    # Initialize OutputTools
    tools = OutputTools('km')

    # Create database session
    db = SessionLocal()

    try:
        # Check if roads already exist
        existing_count = db.query(Road).count()
        if existing_count > 0:
            print(f"\nWarning: Database already contains {existing_count} roads.")
            response = input("Do you want to continue and add more roads? (y/n): ")
            if response.lower() != 'y':
                print("Aborted.")
                return

        # Process collections in batches
        print(f"\nProcessing {len(collections)} collections...")
        added_count = 0
        skipped_count = 0

        for i in range(0, len(collections), batch_size):
            batch = collections[i:i + batch_size]

            for collection in batch:
                try:
                    road_data = collection_to_road(collection, tools)

                    # Skip roads with no geometry
                    if road_data['geometry'] is None:
                        skipped_count += 1
                        continue

                    # Create Road object
                    road = Road(**road_data)
                    db.add(road)
                    added_count += 1

                except Exception as e:
                    print(f"Error processing collection: {e}")
                    skipped_count += 1
                    continue

            # Commit batch
            db.commit()
            print(f"Processed {min(i + batch_size, len(collections))}/{len(collections)} collections...")

        print(f"\n✅ Successfully added {added_count} roads to database")
        if skipped_count > 0:
            print(f"⚠️  Skipped {skipped_count} collections due to errors or missing geometry")

        # Print some statistics
        total_roads = db.query(Road).count()
        print(f"\n📊 Database now contains {total_roads} total roads")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python populate_roads.py <path_to_msgpack_file>")
        print("\nExample:")
        print("  python populate_roads.py /tmp/vermont-latest.msgpack")
        sys.exit(1)

    msgpack_path = sys.argv[1]

    if not os.path.exists(msgpack_path):
        print(f"Error: File not found: {msgpack_path}")
        sys.exit(1)

    print("=" * 60)
    print("Curvature Roads Database Population Script")
    print("=" * 60)

    populate_database(msgpack_path)

    print("\n✅ Done!")
    print("\nNext steps:")
    print("  1. Start the API server: python server.py")
    print("  2. Test the endpoints: http://localhost:8000/docs")
    print("  3. Query roads: GET /roads/geojson?min_curvature=1000")


if __name__ == "__main__":
    main()
