import schedule
import time
import uuid
from datetime import datetime
from db.database import init_database
from db.crud import create_sync_log, complete_sync_log, create_shop, count_shops
from data_fetchers.datagov_fetcher import fetch_datagov_data
from data_fetchers.osm_fetcher import fetch_osm_shops
from data_fetchers.onemap_fetcher import fetch_onemap_shops
from processors.normalizer import normalize_datagov
from processors.matcher import match_shops, merge_shop_groups
from signal_engine.signal_calculator import calculate_confidence, enrich_record


def run_full_pipeline():
    """
    Full data pipeline: fetch → normalize → match → score → store
    Runs every 3 days.
    """

    run_id = str(uuid.uuid4())[:8]

    print(f"\n{'='*60}")
    print(f"Starting full pipeline run: {run_id}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    try:
        # Initialize database
        init_database()

        # Create sync log
        sync_log_id = create_sync_log(run_id)

        # Step 1: Fetch data from all sources
        print("📥 STEP 1: Fetching data from all sources...")

        print("  - Fetching from data.gov.sg...")
        datagov_raw = fetch_datagov_data(collection_id=2)
        print(f"    ✓ Got {len(datagov_raw)} records")

        print("  - Fetching from OpenStreetMap...")
        osm_raw = fetch_osm_shops()
        print(f"    ✓ Got {len(osm_raw)} records")

        print("  - Fetching from OneMap...")
        onemap_raw = fetch_onemap_shops()
        print(f"    ✓ Got {len(onemap_raw)} records")

        total_raw = len(datagov_raw) + len(osm_raw) + len(onemap_raw)
        print(f"\n  ✓ Total raw records: {total_raw}\n")

        # Step 2: Normalize data
        print("⚙️  STEP 2: Normalizing data to common schema...")

        datagov_clean = normalize_datagov(datagov_raw)
        print(f"  ✓ Normalized {len(datagov_clean)} data.gov records")

        # OSM and OneMap already in normalized format from fetchers
        all_clean = osm_raw + datagov_clean + onemap_raw
        print(f"  ✓ Total normalized records: {len(all_clean)}\n")

        # Step 3: Match shops across sources
        print("🔗 STEP 3: Matching shops across sources...")

        matched_groups = match_shops(all_clean, distance_threshold=0.05)
        print(f"  ✓ Found {len(matched_groups)} unique shops")
        print(f"    (containing {total_raw} raw records)\n")

        # Step 4: Calculate confidence scores
        print("⭐ STEP 4: Calculating confidence scores...")

        enriched_shops = []
        for group in matched_groups:
            merged = merge_shop_groups(group)
            confidence = calculate_confidence(merged)
            enriched = enrich_record(merged, confidence)
            enriched_shops.append(enriched)

        print(f"  ✓ Scored {len(enriched_shops)} records\n")

        # Step 5: Store in database
        print("💾 STEP 5: Storing in database...")

        stored_count = 0
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
                print(f"  ⚠ Error storing shop: {e}")

        print(f"  ✓ Stored {stored_count} records\n")

        # Step 6: Summary
        print(f"{'='*60}")
        print("✅ PIPELINE COMPLETE")
        print(f"{'='*60}")
        print(f"Timestamp:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Run ID:          {run_id}")
        print(f"Raw records:     {total_raw}")
        print(f"Matched shops:   {len(matched_groups)}")
        print(f"Stored:          {stored_count}")
        print(f"Total in DB:     {count_shops()}")
        print()

        # Update sync log
        complete_sync_log(run_id, "success", f"Processed {stored_count} shops from {total_raw} raw records")

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ PIPELINE FAILED: {error_msg}\n")
        complete_sync_log(run_id, "failed", error_msg)
        raise


def schedule_jobs():
    """Schedule periodic jobs."""
    
    # Run full pipeline every 3 days
    schedule.every(3).days.do(run_full_pipeline)
    
    print("✓ Scheduler initialized")
    print("  - Full pipeline scheduled: every 3 days")
    print()
    
    # Keep scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def run_once():
    """Run the pipeline once (for testing/manual runs)."""
    run_full_pipeline()
    print("\n✓ Single run completed")


if __name__ == "__main__":
    # For manual testing: python -m scheduler.jobs
    run_once()
