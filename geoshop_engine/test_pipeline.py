"""
Comprehensive test of the GeoShop Engine pipeline components.
Uses mock data instead of real API calls.
"""

from processors.normalizer import normalize_datagov
from processors.matcher import match_shops, merge_shop_groups, calculate_distance, string_similarity
from signal_engine.signal_calculator import calculate_confidence
from db.database import init_db, SessionLocal
from db.models import Shop, SyncLog
from db.crud import create_shop, get_all_active_shops, count_shops
import os


def test_normalizer():
    """Test data normalization."""
    print("\n🧪 TEST 1: Normalizer")
    
    mock_datagov_data = [
        {
            "name": "Toa Payoh Supermarket",
            "business_name": "TPS",
            "address": "Blk 75 Toa Payoh Lorong 5, Singapore 310075",
            "latitude": 1.3305,
            "longitude": 103.8533,
        },
        {
            "name": "Ang Mo Kio Market",
            "address": "AMK Hub, Ang Mo Kio, Singapore",
            "latitude": 1.3741,
            "longitude": 103.8449,
        }
    ]
    
    normalized = normalize_datagov(mock_datagov_data)
    
    assert len(normalized) == 2
    assert normalized[0]["source"] == "data_gov"
    assert normalized[0]["name"] == "Toa Payoh Supermarket"
    assert normalized[1]["lat"] == 1.3741
    
    print("   ✅ Normalization works correctly")
    return normalized


def test_matcher(sample_shops):
    """Test shop matching logic."""
    print("\n🧪 TEST 2: Matcher")
    
    # Exact match test
    osm_shop = {
        "name": "Toa Payoh Supermarket",
        "address": "Blk 75 Toa Payoh Lorong 5",
        "lat": 1.3305,
        "lng": 103.8533,
        "source": "osm",
    }
    
    # Same shop from different source (slightly different data)
    datagov_shop = {
        "name": "Toa Payoh Supermarket",
        "address": "Blk 75 Toa Payoh Lorong 5, Singapore 310075",
        "lat": 1.3305,
        "lng": 103.8533,
        "source": "data_gov",
    }
    
    # Different shop
    other_shop = {
        "name": "Ang Mo Kio Market",
        "address": "AMK Hub, Ang Mo Kio",
        "lat": 1.3741,
        "lng": 103.8449,
        "source": "onemap",
    }
    
    # Test distance calculation
    dist = calculate_distance(1.3305, 103.8533, 1.3305, 103.8533)
    assert dist < 0.001, "Same location should have ~0 distance"
    print("   ✅ Distance calculation correct")
    
    # Test string similarity
    sim = string_similarity("Toa Payoh Supermarket", "Toa Payoh Supermarket")
    assert sim == 1.0, "Identical strings should have 1.0 similarity"
    print("   ✅ String similarity correct")
    
    # Test matching
    all_shops = [osm_shop, datagov_shop, other_shop]
    groups = match_shops(all_shops, distance_threshold=0.1)
    
    assert len(groups) == 2, f"Expected 2 groups, got {len(groups)}"
    print("   ✅ Shop matching works correctly")
    
    return groups


def test_signal_calculator():
    """Test confidence scoring."""
    print("\n🧪 TEST 3: Signal Calculator")
    
    # High confidence shop (multiple sources, complete data)
    shop_high = {
        "name": "Good Shop Name",
        "address": "123 Singapore Street, Singapore 123456",
        "lat": 1.35,
        "lng": 103.85,
        "sources": ["osm", "datagov", "onemap"],
        "phone": "+65 6123 4567",
        "website": "www.goodshop.sg",
        "shop_type": "retail",
        "postal_code": "123456",
    }
    
    # Low confidence shop (single source, minimal data)
    shop_low = {
        "name": "Unknown Shop",
        "address": "Unknown Address",
        "lat": 1.35,
        "lng": 103.85,
        "sources": ["osm"],
    }
    
    conf_high = calculate_confidence(shop_high)
    conf_low = calculate_confidence(shop_low)
    
    assert conf_high["confidence_score"] > conf_low["confidence_score"], \
        "High-quality shop should have higher confidence"
    assert conf_high["confidence_level"] in ["VERY HIGH", "HIGH", "MEDIUM", "LOW", "VERY LOW"]
    
    print(f"   ✅ High confidence shop: {conf_high['confidence_score']:.1f}% ({conf_high['confidence_level']})")
    print(f"   ✅ Low confidence shop: {conf_low['confidence_score']:.1f}% ({conf_low['confidence_level']})")
    
    return conf_high, conf_low


def test_database():
    """Test database operations."""
    print("\n🧪 TEST 4: Database Layer")
    
    # Clean up old database if exists
    if os.path.exists("geoshop_test.db"):
        os.remove("geoshop_test.db")
    
    # Create test database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from db.database import Base
    
    engine = create_engine("sqlite:///geoshop_test.db")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    
    db = TestSession()
    
    try:
        # Create a shop record
        shop_data = {
            "name": "Test Shop",
            "address": "Test Address",
            "lat": 1.35,
            "lng": 103.85,
            "sources": ["osm", "datagov"],
            "phone": "+65 1234567",
            "confidence_score": 85.5,
            "confidence_level": "HIGH",
            "all_records": [{"source": "osm"}, {"source": "datagov"}],
        }
        
        shop = create_shop(db, shop_data)
        assert shop.id is not None
        print(f"   ✅ Shop created with ID: {shop.id}")
        
        # Query shops
        all_shops = db.query(Shop).all()
        assert len(all_shops) == 1
        print(f"   ✅ Query works, found {len(all_shops)} shop(s)")
        
        # Test counts
        from db.crud import count_shops as count_active
        count = count_active(db)
        assert count == 1
        print(f"   ✅ Database count: {count}")
        
    finally:
        db.close()
        os.remove("geoshop_test.db")


def test_pipeline_flow():
    """Test complete pipeline flow with mock data."""
    print("\n🧪 TEST 5: Complete Pipeline Flow")
    
    # Test data from all sources
    osm_shops = [
        {"name": "OSM Shop", "address": "OSM Address", "lat": 1.35, "lng": 103.85, "source": "osm"},
    ]
    
    datagov_shops = [
        {"name": "DataGov Shop", "address": "DataGov Address", "lat": 1.36, "lng": 103.86, "source": "data_gov"},
    ]
    
    onemap_shops = [
        {"name": "OneMap Shop", "address": "OneMap Address", "lat": 1.34, "lng": 103.84, "source": "onemap"},
    ]
    
    # Combine
    all_shops = osm_shops + datagov_shops + onemap_shops
    print(f"   ✓ Combined: {len(all_shops)} raw records from 3 sources")
    
    # Match
    groups = match_shops(all_shops)
    print(f"   ✓ Matched into {len(groups)} groups")
    
    # Merge and score
    final_records = []
    for group in groups:
        merged = merge_shop_groups(group)
        confidence = calculate_confidence(merged)
        final_record = {**merged, **confidence}
        final_records.append(final_record)
    
    print(f"   ✓ Generated {len(final_records)} final records with confidence scores")
    
    assert len(final_records) > 0
    assert all("confidence_score" in r for r in final_records)
    
    print("   ✅ Complete pipeline flow successful")


def main():
    print("\n" + "="*60)
    print("GeoShop Engine - Component Test Suite")
    print("="*60)
    
    try:
        # Run tests
        normalized = test_normalizer()
        groups = test_matcher(normalized)
        conf_high, conf_low = test_signal_calculator()
        test_database()
        test_pipeline_flow()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nThe project is ready to use!")
        print("Run commands:")
        print("  python main.py run      - Run pipeline once")
        print("  python main.py schedule - Run every 3 days")
        print("  python main.py test     - Run single execution")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
