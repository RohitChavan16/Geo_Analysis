import sys
import argparse
from datetime import datetime
from data_fetchers.datagov_fetcher import fetch_datagov_data
from data_fetchers.osm_fetcher import fetch_osm_shops
from data_fetchers.onemap_fetcher import fetch_onemap_shops
from processors.normalizer import normalize_datagov
from processors.matcher import match_shops, merge_shop_groups
from signal_engine.signal_calculator import calculate_confidence, enrich_record
from db.database import init_database
from db.crud import create_shop, count_shops, create_sync_log, complete_sync_log
import uuid


def get_mock_data():
    """Return mock data for testing when APIs are unavailable."""
    return {
        'datagov': [
            {
                'name': 'Toa Payoh Supermarket',
                'business_name': 'TPS',
                'address': 'Blk 75 Toa Payoh Lorong 5, Singapore 310075',
                'latitude': 1.3305,
                'longitude': 103.8533,
            },
            {
                'name': 'Ang Mo Kio Market',
                'address': 'AMK Hub, Ang Mo Kio, Singapore',
                'latitude': 1.3741,
                'longitude': 103.8449,
            }
        ],
        'osm': [
            {
                "name": "Toa Payoh Supermarket",
                "address": "Blk 75 Toa Payoh Lorong 5",
                "lat": 1.3305,
                "lng": 103.8533,
                "source": "osm",
                "shop_type": "supermarket",
                "phone": "+65 6123 4567",
            },
            {
                "name": "Bukit Timah Plaza",
                "address": "1 Jln Anak Bukit, Singapore 588996",
                "lat": 1.3404,
                "lng": 103.7768,
                "source": "osm",
                "shop_type": "mall",
            }
        ],
        'onemap': [
            {
                "name": "OneMap Shop",
                "address": "123 Orchard Road, Singapore 238888",
                "lat": 1.3048,
                "lng": 103.8318,
                "source": "onemap",
                "postal_code": "238888",
            }
        ]
    }


def run_pipeline(verbose=True, use_mock=False):
    """Run the complete data processing pipeline."""

    if verbose:
        print("\n" + "="*60)
        print("GeoShop Engine - Data Processing Pipeline")
        print("="*60 + "\n")

    # Initialize database
    try:
        init_database()
        db_available = True
    except Exception:
        print("⚠️  Database not available - running in offline mode")
        db_available = False

    # Create sync log
    run_id = str(uuid.uuid4())
    sync_log_id = None
    if db_available:
        sync_log_id = create_sync_log(run_id)

    try:
        # Fetch data
        if verbose:
            print("📥 Fetching data from all sources...")

        if use_mock:
            mock_data = get_mock_data()
            datagov_raw = mock_data['datagov']
            osm_raw = mock_data['osm']
            onemap_raw = mock_data['onemap']
            if verbose:
                print("   📝 Using mock data (APIs unavailable)")
        else:
            datagov_raw = fetch_datagov_data(collection_id=2)
            osm_raw = fetch_osm_shops()
            onemap_raw = fetch_onemap_shops()

        total_raw = len(datagov_raw) + len(osm_raw) + len(onemap_raw)
        if verbose:
            print(f"   ✓ data.gov.sg: {len(datagov_raw)} records")
            print(f"   ✓ OpenStreetMap: {len(osm_raw)} records")
            print(f"   ✓ OneMap: {len(onemap_raw)} records")
            print(f"   ✓ Total: {total_raw} records\n")

        # Normalize
        if verbose:
            print("⚙️  Normalizing data...")

        datagov_clean = normalize_datagov(datagov_raw)
        all_clean = osm_raw + datagov_clean + onemap_raw
        if verbose:
            print(f"   ✓ Normalized {len(all_clean)} records\n")

        # Match
        if verbose:
            print("🔗 Matching shops across sources...")

        matched_groups = match_shops(all_clean, distance_threshold=0.05)
        if verbose:
            print(f"   ✓ Found {len(matched_groups)} unique shops\n")

        # Score
        if verbose:
            print("⭐ Calculating confidence scores...")

        enriched_shops = []
        for group in matched_groups:
            merged = merge_shop_groups(group)
            confidence = calculate_confidence(merged)
            enriched = enrich_record(merged, confidence)
            enriched_shops.append(enriched)

        if verbose:
            print(f"   ✓ Scored {len(enriched_shops)} records\n")

        # Store
        if verbose:
            print("💾 Storing in database...")

        stored_count = 0
        if db_available:
            for shop in enriched_shops:
                try:
                    shop_data = {
                        'name': shop.get('name'),
                        'address': shop.get('address'),
                        'lat': shop.get('lat'),
                        'lng': shop.get('lng'),
                        'sources': shop.get('sources', []),
                        'phone': shop.get('phone'),
                        'website': shop.get('website'),
                        'opening_hours': shop.get('opening_hours'),
                        'shop_type': shop.get('shop_type'),
                        'postal_code': shop.get('postal_code'),
                        'confidence_score': shop.get('confidence_score', 0),
                        'confidence_level': shop.get('confidence_level', 'LOW'),
                        'match_quality': shop.get('match_quality'),
                        'raw_data': shop.get('all_records'),
                        'is_active': True,
                        'created_at': datetime.utcnow(),
                        'last_updated': datetime.utcnow()
                    }
                    create_shop(shop_data)
                    stored_count += 1
                except Exception as e:
                    if verbose:
                        print(f"   ⚠ Error storing shop: {e}")
            
            if verbose:
                print(f"   ✓ Stored {stored_count} records")
                print(f"   ✓ Total in DB: {count_shops()}\n")
        else:
            if verbose:
                print("   ⚠ Database not available - skipping storage")
                stored_count = len(enriched_shops)
                print(f"   ✓ Processed {stored_count} records (not stored)\n")
        
        if verbose and enriched_shops:
            print("Sample output (first 3 records):\n")
            for shop in enriched_shops[:3]:
                print(f"  📍 {shop.get('name')}")
                print(f"     Address: {shop.get('address')}")
                print(f"     Sources: {shop.get('sources')}")
                print(f"     Confidence: {shop.get('confidence_score'):.1f}% ({shop.get('confidence_level')})")
                print()

        # Complete sync log
        if db_available:
            complete_sync_log(run_id, "success", f"Processed {stored_count} shops")

        return {
            "success": True,
            "run_id": run_id,
            "total_raw": total_raw,
            "stored_count": stored_count,
            "total_in_db": count_shops() if db_available else 0
        }

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}\n")

        # Complete sync log with error
        if db_available:
            complete_sync_log(run_id, "failed", error_msg)

        return {
            "success": False,
            "run_id": run_id,
            "error": error_msg
        }


def main():
    """Main entry point with CLI options."""
    
    parser = argparse.ArgumentParser(description="GeoShop Engine - Multi-source data pipeline")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "demo", "schedule", "test"],
        help="Command to execute"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real APIs"
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_pipeline(verbose=not args.quiet, use_mock=args.mock)
    
    elif args.command == "demo":
        print("\n🎭 Running demo with mock data...\n")
        run_pipeline(verbose=True, use_mock=True)
    
    elif args.command == "schedule":
        print("\n🕐 Starting scheduler (runs pipeline every 3 days)...")
        print("   Press Ctrl+C to stop\n")
        try:
            schedule_jobs()
        except KeyboardInterrupt:
            print("\n✓ Scheduler stopped")
    
    elif args.command == "test":
        print("\n🧪 Running single pipeline execution...\n")
        run_once()


if __name__ == "__main__":
    main()
