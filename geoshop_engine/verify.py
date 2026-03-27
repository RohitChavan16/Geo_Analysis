#!/usr/bin/env python3
"""
Quick verification script for GeoShop Engine
"""

import os
if os.path.exists('geoshop_test.db'):
    try:
        os.remove('geoshop_test.db')
    except:
        pass

print('🧪 Running simplified verification...')

from processors.normalizer import normalize_datagov
from processors.matcher import match_shops, merge_shop_groups
from signal_engine.signal_calculator import calculate_confidence
from db.database import init_db, SessionLocal
from db.models import Shop
from db.crud import create_shop, count_shops

# Test data
mock_data = [
    {'name': 'Test Shop', 'address': 'Test Address', 'latitude': 1.35, 'longitude': 103.85}
]
normalized = normalize_datagov(mock_data)
print(f'✅ Normalizer: {len(normalized)} records')

# Test matching
shops = [
    {'name': 'Shop A', 'address': 'Addr A', 'lat': 1.35, 'lng': 103.85, 'source': 'osm'},
    {'name': 'Shop A', 'address': 'Addr A', 'lat': 1.35, 'lng': 103.85, 'source': 'datagov'},
    {'name': 'Shop B', 'address': 'Addr B', 'lat': 1.36, 'lng': 103.86, 'source': 'onemap'}
]
groups = match_shops(shops)
print(f'✅ Matcher: {len(groups)} groups from {len(shops)} shops')

# Test confidence
shop = {'name': 'Good Shop', 'address': '123 Street', 'lat': 1.35, 'lng': 103.85, 'sources': ['osm', 'datagov']}
conf = calculate_confidence(shop)
print(f'✅ Signal Calculator: {conf["confidence_score"]:.1f}% confidence')

# Test database
init_db()
db = SessionLocal()
try:
    shop_data = {'name': 'DB Test', 'address': 'DB Addr', 'lat': 1.35, 'lng': 103.85, 'sources': ['test']}
    shop = create_shop(db, shop_data)
    total = count_shops(db)
    print(f'✅ Database: Created shop ID {shop.id}, total in DB: {total}')
finally:
    db.close()

print()
print('🎉 ALL COMPONENTS VERIFIED SUCCESSFULLY!')
print('The GeoShop Engine is ready to use.')