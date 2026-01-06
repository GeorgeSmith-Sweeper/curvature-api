#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Load KML Data
=============
Download and load road data from KML/KMZ files into the database.

This script:
1. Downloads KML/KMZ files for a specified region
2. Extracts road geometries and properties
3. Inserts roads into the PostgreSQL database

Usage:
    python load_kml_data.py california
    python load_kml_data.py vermont --curvature 300
"""

import sys
import os
import argparse
import zipfile
import tempfile
from typing import List, Dict, Optional
from pathlib import Path
import xml.etree.ElementTree as ET

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

from api.database import engine, SessionLocal
from api.models import Base, Road


# KML namespace
KML_NS = {'kml': 'http://www.opengis.net/kml/2.2'}


def download_kml(region: str, curvature_threshold: int = 300) -> Path:
    """
    Download KML file for a region.

    Args:
        region: US state name (e.g., 'california', 'vermont')
        curvature_threshold: Minimum curvature threshold (300 or 1000)

    Returns:
        Path to downloaded KMZ file
    """
    base_url = "https://kml.roadcurvature.com/north_america/us"
    filename = f"{region.lower()}.c_{curvature_threshold}.kmz"
    url = f"{base_url}/{filename}"

    print(f"Downloading {filename}...")
    print(f"URL: {url}")

    response = requests.get(url, verify=False)  # SSL cert expired
    response.raise_for_status()

    # Save to temp file
    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / filename

    with open(output_path, 'wb') as f:
        f.write(response.content)

    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ Downloaded {file_size:.1f} MB")

    return output_path


def extract_kmz(kmz_path: Path) -> Path:
    """
    Extract KML file from KMZ archive.

    Args:
        kmz_path: Path to KMZ file

    Returns:
        Path to extracted KML file
    """
    print("Extracting KMZ...")

    with zipfile.ZipFile(kmz_path, 'r') as zip_ref:
        # Find the KML file (usually doc.kml)
        kml_files = [f for f in zip_ref.namelist() if f.endswith('.kml')]

        if not kml_files:
            raise ValueError("No KML file found in KMZ archive")

        kml_filename = kml_files[0]

        # Extract to same directory as KMZ
        extract_dir = kmz_path.parent
        zip_ref.extract(kml_filename, extract_dir)

        kml_path = extract_dir / kml_filename
        print(f"✅ Extracted {kml_filename}")

        return kml_path


def parse_kml(kml_path: Path) -> List[Dict]:
    """
    Parse KML file and extract road data.

    Args:
        kml_path: Path to KML file

    Returns:
        List of road dictionaries
    """
    print("Parsing KML file...")

    tree = ET.parse(kml_path)
    root = tree.getroot()

    roads = []

    # Find all Placemarks (roads)
    placemarks = root.findall('.//kml:Placemark', KML_NS)

    for placemark in placemarks:
        try:
            # Extract name
            name_elem = placemark.find('kml:name', KML_NS)
            name = name_elem.text if name_elem is not None else 'Unnamed Road'

            # Extract description (contains curvature info)
            desc_elem = placemark.find('kml:description', KML_NS)
            description = desc_elem.text if desc_elem is not None else ''

            # Parse curvature from description
            curvature = parse_curvature(description)

            # Extract LineString coordinates
            linestring_elem = placemark.find('.//kml:LineString/kml:coordinates', KML_NS)

            if linestring_elem is None:
                continue

            coords_text = linestring_elem.text.strip()
            coordinates = parse_coordinates(coords_text)

            if len(coordinates) < 2:
                continue

            # Calculate approximate length (sum of distances between points)
            length_meters = calculate_length(coordinates)

            roads.append({
                'name': name,
                'curvature': curvature,
                'length_meters': length_meters,
                'coordinates': coordinates,
                'surface': 'paved',  # Default, KML doesn't have this info
            })

        except Exception as e:
            print(f"Warning: Error parsing placemark: {e}")
            continue

    print(f"✅ Parsed {len(roads)} roads")
    return roads


def parse_curvature(description: str) -> float:
    """Extract curvature value from description text."""
    try:
        # Description format in CDATA: "<div...>Curvature: 1234.5<br/>..."
        if 'Curvature:' in description:
            # Split by 'Curvature:' and get the next part
            after_label = description.split('Curvature:')[1]
            # Extract the number before '<br/>' or other HTML tags
            curvature_str = after_label.split('<')[0].strip()
            return float(curvature_str)
    except Exception as e:
        print(f"Warning: Could not parse curvature from: {description[:100]}")
    return 0.0


def parse_coordinates(coords_text: str) -> List[tuple]:
    """
    Parse KML coordinates string into list of (lon, lat) tuples.

    KML format: "lon1,lat1,alt1 lon2,lat2,alt2 ..."
    """
    coordinates = []

    for coord_str in coords_text.split():
        parts = coord_str.strip().split(',')
        if len(parts) >= 2:
            lon = float(parts[0])
            lat = float(parts[1])
            coordinates.append((lon, lat))

    return coordinates


def calculate_length(coordinates: List[tuple]) -> float:
    """
    Calculate approximate length of a LineString in meters.
    Uses Haversine formula for each segment.
    """
    import math

    def haversine(lon1, lat1, lon2, lat2):
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    total_length = 0.0
    for i in range(len(coordinates) - 1):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[i + 1]
        total_length += haversine(lon1, lat1, lon2, lat2)

    return total_length


def load_roads_to_db(roads: List[Dict], region: str):
    """
    Load roads into the database.

    Args:
        roads: List of road dictionaries
        region: Region name for reference
    """
    print(f"\nLoading {len(roads)} roads into database...")

    # Initialize database
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        added_count = 0
        skipped_count = 0

        for i, road_data in enumerate(roads):
            try:
                # Create LineString geometry
                linestring = LineString(road_data['coordinates'])
                geometry_wkb = from_shape(linestring, srid=4326)

                # Create Road object
                road = Road(
                    collection_id=f"{region}_{i}",
                    name=road_data['name'],
                    curvature=road_data['curvature'],
                    length_meters=road_data['length_meters'],
                    surface=road_data['surface'],
                    geometry=geometry_wkb,
                    properties={'region': region}
                )

                db.add(road)
                added_count += 1

                # Commit in batches
                if added_count % 100 == 0:
                    db.commit()
                    print(f"  Processed {added_count}/{len(roads)}...")

            except Exception as e:
                print(f"Warning: Error loading road: {e}")
                skipped_count += 1
                continue

        # Final commit
        db.commit()

        print(f"\n✅ Successfully added {added_count} roads")
        if skipped_count > 0:
            print(f"⚠️  Skipped {skipped_count} roads due to errors")

        # Print statistics
        total_roads = db.query(Road).count()
        print(f"\n📊 Database now contains {total_roads} total roads")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download and load road data from KML files'
    )
    parser.add_argument(
        'region',
        help='US state name (e.g., california, vermont, colorado)'
    )
    parser.add_argument(
        '--curvature',
        type=int,
        choices=[300, 1000],
        default=300,
        help='Minimum curvature threshold (default: 300)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing roads before loading'
    )

    args = parser.parse_args()

    print("=" * 60)
    print(f"Road Data Loader - {args.region.title()}")
    print("=" * 60)

    try:
        # Clear existing data if requested
        if args.clear:
            print("\nClearing existing roads...")
            db = SessionLocal()
            db.query(Road).delete()
            db.commit()
            db.close()
            print("✅ Cleared all roads")

        # Download KML
        kmz_path = download_kml(args.region, args.curvature)

        # Extract KML from KMZ
        kml_path = extract_kmz(kmz_path)

        # Parse KML
        roads = parse_kml(kml_path)

        # Load into database
        load_roads_to_db(roads, args.region)

        print("\n✅ Done!")
        print("\nNext steps:")
        print("  1. Start the API server if not running")
        print("  2. Test the map view in the mobile app")
        print(f"  3. You should see {len(roads)} roads from {args.region.title()}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
