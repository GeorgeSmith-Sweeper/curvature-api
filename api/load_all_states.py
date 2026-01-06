#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Load All US States
==================
Download and load road data for all 50 US states from KML files.

This script:
1. Downloads KML/KMZ files for all states (1000+ curvature threshold)
2. Extracts and parses road geometries
3. Loads into PostgreSQL database with resume capability
4. Tracks progress and handles errors

Usage:
    python load_all_states.py [--clear] [--curvature 1000]
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Set

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import SessionLocal
from api.models import Road
from api.load_kml_data import download_kml, extract_kmz, parse_kml, load_roads_to_db

# All 50 US states + DC
US_STATES = [
    'alabama', 'alaska', 'arizona', 'arkansas', 'california',
    'colorado', 'connecticut', 'delaware', 'florida', 'georgia',
    'hawaii', 'idaho', 'illinois', 'indiana', 'iowa',
    'kansas', 'kentucky', 'louisiana', 'maine', 'maryland',
    'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri',
    'montana', 'nebraska', 'nevada', 'new-hampshire', 'new-jersey',
    'new-mexico', 'new-york', 'north-carolina', 'north-dakota', 'ohio',
    'oklahoma', 'oregon', 'pennsylvania', 'rhode-island', 'south-carolina',
    'south-dakota', 'tennessee', 'texas', 'utah', 'vermont',
    'virginia', 'washington', 'west-virginia', 'wisconsin', 'wyoming',
    'district-of-columbia'
]


def get_loaded_regions() -> Set[str]:
    """
    Get list of regions already loaded in the database.

    Returns:
        Set of region names
    """
    db = SessionLocal()
    try:
        # Query distinct regions from properties JSONB column
        results = db.query(Road.properties['region'].astext).distinct().all()
        regions = {r[0] for r in results if r[0]}
        return regions
    finally:
        db.close()


def load_state(state: str, curvature_threshold: int) -> dict:
    """
    Load a single state's road data.

    Args:
        state: State name (e.g., 'california')
        curvature_threshold: Minimum curvature (300 or 1000)

    Returns:
        Dictionary with success status and stats
    """
    result = {
        'state': state,
        'success': False,
        'roads_loaded': 0,
        'error': None
    }

    try:
        print(f"\n{'=' * 60}")
        print(f"Processing: {state.replace('-', ' ').title()}")
        print(f"{'=' * 60}")

        # Download KML
        kmz_path = download_kml(state, curvature_threshold)

        # Extract KML from KMZ
        kml_path = extract_kmz(kmz_path)

        # Parse KML
        roads = parse_kml(kml_path)

        if not roads:
            result['error'] = "No roads found in KML file"
            return result

        # Load into database
        load_roads_to_db(roads, state)

        result['success'] = True
        result['roads_loaded'] = len(roads)

    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error loading {state}: {e}")

    return result


def load_all_states(curvature_threshold: int = 1000, clear: bool = False, resume: bool = True):
    """
    Load road data for all 50 US states.

    Args:
        curvature_threshold: Minimum curvature (default: 1000)
        clear: Clear existing roads before loading
        resume: Skip states already loaded (default: True)
    """
    print("=" * 60)
    print("Load All US States - Curvature Road Data")
    print("=" * 60)
    print(f"Curvature threshold: {curvature_threshold}+")
    print(f"Total states to process: {len(US_STATES)}")
    print()

    # Clear existing data if requested
    if clear:
        print("Clearing existing roads...")
        db = SessionLocal()
        deleted_count = db.query(Road).count()
        db.query(Road).delete()
        db.commit()
        db.close()
        print(f"✅ Cleared {deleted_count} roads\n")

    # Get already-loaded regions for resume capability
    loaded_regions = get_loaded_regions() if resume else set()
    if loaded_regions:
        print(f"📋 Already loaded regions ({len(loaded_regions)}): {', '.join(sorted(loaded_regions))}\n")

    # Track overall progress
    total_states = len(US_STATES)
    processed_states = 0
    successful_states = 0
    skipped_states = 0
    failed_states = []
    total_roads_loaded = 0

    # Process each state
    for i, state in enumerate(US_STATES, 1):
        # Skip if already loaded and resume is enabled
        if resume and state in loaded_regions:
            print(f"⏭️  [{i}/{total_states}] Skipping {state.replace('-', ' ').title()} (already loaded)")
            skipped_states += 1
            continue

        # Load state
        result = load_state(state, curvature_threshold)
        processed_states += 1

        if result['success']:
            successful_states += 1
            total_roads_loaded += result['roads_loaded']
            print(f"✅ [{i}/{total_states}] {state.replace('-', ' ').title()}: {result['roads_loaded']} roads loaded")
        else:
            failed_states.append((state, result['error']))
            print(f"❌ [{i}/{total_states}] {state.replace('-', ' ').title()}: FAILED - {result['error']}")

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total states: {total_states}")
    print(f"Processed: {processed_states}")
    print(f"Successful: {successful_states}")
    print(f"Skipped (already loaded): {skipped_states}")
    print(f"Failed: {len(failed_states)}")
    print(f"Total roads loaded: {total_roads_loaded:,}")

    if failed_states:
        print("\n⚠️  Failed states:")
        for state, error in failed_states:
            print(f"  - {state.replace('-', ' ').title()}: {error}")

    # Database statistics
    db = SessionLocal()
    total_db_roads = db.query(Road).count()
    db.close()

    print(f"\n📊 Total roads in database: {total_db_roads:,}")
    print("\n✅ All states processing complete!")
    print("\nNext steps:")
    print("  1. Start/restart the API server")
    print("  2. Test the map view to see roads nationwide")
    print("  3. Pan around the US to verify viewport-based loading")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download and load road data for all 50 US states'
    )
    parser.add_argument(
        '--curvature',
        type=int,
        choices=[300, 1000],
        default=1000,
        help='Minimum curvature threshold (default: 1000)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all existing roads before loading'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Disable resume (re-load all states even if already loaded)'
    )

    args = parser.parse_args()

    try:
        load_all_states(
            curvature_threshold=args.curvature,
            clear=args.clear,
            resume=not args.no_resume
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        print("Note: You can resume by running the script again (resume is enabled by default)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
