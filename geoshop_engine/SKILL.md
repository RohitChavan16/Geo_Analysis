---
name: layered-data-pipeline
description: Multi-stage pipeline architecture for data ingestion, transformation, and intelligence scoring
applies_to: Python projects involving multiple data sources
---

# Layered Data Pipeline Architecture

A reusable pattern for building scalable data ingestion systems with multiple sources, transformations, and confidence scoring.

## Problem This Solves

- **Scattered logic**: Data fetching, cleaning, and analysis mixed together
- **Hard to extend**: Adding a new data source requires changes everywhere
- **Low testability**: Tightly coupled components make unit testing difficult
- **Unclear flow**: No clear separation of concerns

## The Pattern

```
FETCHERS → PROCESSORS → SIGNALS → STORAGE
   ↓           ↓            ↓        ↓
(Raw Data) (Normalized) (Scored) (Output)
```

### 1. **FETCHERS** (Data Ingestion Layer)
Each data source gets its own fetcher module:
- `osm_fetcher.py` - Fetch from Overpass API
- `datagov_fetcher.py` - Fetch from data.gov.sg
- `onemap_fetcher.py` - Fetch from OneMap API

**Key properties**:
- Returns raw data in original format
- Handles pagination/API limits
- No business logic

**Example**:
```python
def fetch_datagov_data(collection_id):
    # Paginate through API
    # Return all_data as list of dicts
    return all_data
```

### 2. **PROCESSORS** (Transformation Layer)
Three sub-components:

#### a) **Normalizer** - Convert to common format
```python
def normalize_datagov(records):
    clean = []
    for r in records:
        place = {
            "name": r.get("name"),
            "address": r.get("address"),
            "lat": r.get("latitude"),
            "lng": r.get("longitude"),
            "source": "data_gov"
        }
        clean.append(place)
    return clean
```

#### b) **Matcher** - Detect duplicates across sources
```python
def match_shops(osm_data, datagov_data):
    # Compare name, location, etc.
    # Return pairs of matching records
    return matched_pairs
```

#### c) **Result Formatter** - Final output shape
```python
def format_output(enriched_data):
    # Shape data for database/API
    # Add metadata, validation
    return formatted_result
```

### 3. **SIGNALS** (Intelligence Layer)
Confidence scoring and enrichment:
```python
def calculate_confidence(record):
    # Multiple sources = higher confidence
    # Name match quality
    # Distance between coordinates
    return {"confidence": 0.95, "reasoning": [...]}
```

### 4. **STORAGE** (Output Layer)
- Database models (ORM)
- CRUD operations
- Connection management

## Folder Structure Template

```
project_name/
├── main.py                 # Entry point: orchestrates pipeline
├── config/
│   └── settings.py        # URLs, API keys, constants
├── data_fetchers/         # One module per source
│   ├── source_a_fetcher.py
│   ├── source_b_fetcher.py
│   └── source_c_fetcher.py
├── processors/
│   ├── normalizer.py      # Convert to common schema
│   ├── matcher.py         # Match/deduplicate
│   └── result_formatter.py # Final shape
├── signal_engine/
│   └── signal_calculator.py # Scoring logic
├── db/
│   ├── database.py
│   ├── models.py
│   └── crud.py
├── scheduler/
│   └── jobs.py            # Cron/periodic runs
├── utils/
│   └── helpers.py
└── requirements.txt
```

## Data Flow Example

```python
# main.py orchestrates the pipeline
def run():
    # Step 1: Fetch from all sources
    osm_data = fetch_osm_data()
    datagov_data = fetch_datagov_data(collection_id=2)
    onemap_data = fetch_onemap_data()
    
    # Step 2: Normalize each to common schema
    osm_clean = normalize_osm(osm_data)
    datagov_clean = normalize_datagov(datagov_data)
    onemap_clean = normalize_onemap(onemap_data)
    
    # Step 3: Combine and match
    all_data = osm_clean + datagov_clean + onemap_clean
    matched = match_shops(all_data)
    
    # Step 4: Score confidence
    scored = [calculate_confidence(record) for record in matched]
    
    # Step 5: Store or output
    save_to_database(scored)
```

## When to Add a New Data Source

1. **Create fetcher**: `data_fetchers/newsource_fetcher.py`
   ```python
   def fetch_newsource_data():
       # Implement API calls
       return raw_data
   ```

2. **Add normalizer**: Add case to `processors/normalizer.py`
   ```python
   def normalize_newsource(records):
       clean = []
       for r in records:
           place = {
               "name": r.get("field_x"),
               # ... map to schema
               "source": "newsource"
           }
           clean.append(place)
       return clean
   ```

3. **Update main.py**: Add new source to pipeline
   ```python
   newsource_data = fetch_newsource_data()
   newsource_clean = normalize_newsource(newsource_data)
   all_data += newsource_clean
   ```

## Key Principles

| Principle | Benefit |
|-----------|---------|
| **One fetcher per source** | Easy to add, remove, or debug sources independently |
| **Normalize to schema** | Matcher and signals work on consistent format |
| **Matcher is optional** | Single source? Skip matching, go straight to signals |
| **Signals are pluggable** | Add/remove scoring rules without changing data flow |
| **main.py orchestrates** | Clear entry point, shows full pipeline at a glance |

## Extension Points

- **Add caching**: Store raw data locally between runs
- **Add validation**: Schema checks in normalizer
- **Add deduplication**: Enhance matcher with fuzzy name matching
- **Add scheduling**: Run every N days via scheduler/jobs.py
- **Add database**: Store results with CRUD operations

## Anti-Patterns to Avoid

❌ **Mixing fetching and normalizing**: Keep layers separate  
❌ **Multiple normalizers**: One schema per format  
❌ **Hardcoding API logic**: Use config/settings.py  
❌ **Skipping signal calculation**: Even one source benefits from validation  
❌ **main.py doing too much**: Use fetchers/processors/signals modules  

## When This Pattern Works Best

✅ Multiple data sources (2+)  
✅ Complex transformation rules  
✅ Need for confidence/quality scoring  
✅ Data needs to be refreshed periodically  
✅ Team that values modularity  

## Example Prompts to Try

- "Add caching layer to geoshop_engine data fetchers"
- "Implement fuzzy name matching in matcher.py"
- "Add PostgreSQL models for normalized shop data"
- "Create scheduler to run pipeline every 3 days"
- "Add validation signals (address format, coordinate bounds)"

## Related Skills/Customizations

- **Signal calculation patterns** — How to design confidence scores
- **Database layer abstraction** — ORM models and migrations
- **API client patterns** — Building resilient fetchers with retry logic
