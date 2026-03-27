# GeoShop Engine

A real-time geolocation-based shop intelligence platform that aggregates data from multiple sources (OpenStreetMap, data.gov.sg, OneMap) with confidence scoring and MongoDB Atlas storage.

## Features

- 🗺️ **Multi-source Data Aggregation**: Fetches shop data from OSM, data.gov.sg, and OneMap APIs
- 🎯 **Intelligent Matching**: Cross-references data across sources with fuzzy matching and geolocation
- 📊 **Confidence Scoring**: Calculates confidence levels based on data completeness and source reliability
- 💾 **MongoDB Atlas**: Scalable cloud database storage
- 🚀 **FastAPI Backend**: RESTful API with real-time update capabilities
- 🌐 **Web Frontend**: Interactive dashboard for monitoring shops and triggering updates
- ⏰ **Scheduled Updates**: Automatic data synchronization every 3 days
- 🔄 **Real-time Updates**: Frontend-triggered updates with confidence-based filtering

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │ -> │  Data Pipeline  │ -> │   MongoDB Atlas │
│                 │    │                 │    │                 │
│ • OpenStreetMap │    │ 1. Fetch        │    │ • Shop Records  │
│ • data.gov.sg   │    │ 2. Normalize    │    │ • Sync Logs     │
│ • OneMap        │    │ 3. Match        │    │ • Analytics     │
└─────────────────┘    │ 4. Score        │    └─────────────────┘
                       │ 5. Store        │
                       └─────────────────┘
                                ^
                                │
                       ┌─────────────────┐
                       │   FastAPI API   │
                       │                 │
                       │ • REST Endpoints│
                       │ • Real-time     │
                       │ • Background    │
                       └─────────────────┘
                                ^
                                │
                       ┌─────────────────┐
                       │   Web Frontend  │
                       │                 │
                       │ • Dashboard     │
                       │ • Controls      │
                       │ • Real-time     │
                       └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB Atlas account
- API keys for data sources (optional, can use mock data)

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd geoshop_engine
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB Atlas connection string
   ```

3. **Initialize database:**
   ```bash
   python main.py demo
   ```

### Running the System

1. **Start the API server:**
   ```bash
   python run_api.py
   ```

2. **Open the frontend:**
   - Open `frontend/index.html` in your browser
   - Or serve it with a web server

3. **Run scheduled jobs (optional):**
   ```bash
   python -m scheduler.jobs
   ```

## API Endpoints

### Shops
- `GET /api/shops` - List shops with filtering
- `GET /api/shops/{id}` - Get specific shop
- `GET /api/shops/stats` - Get shop statistics

### Sync Operations
- `GET /api/sync/status` - Get sync status
- `GET /api/sync/changes` - Get changes since last sync
- `POST /api/sync/trigger` - Trigger full sync
- `POST /api/update/realtime` - Trigger real-time update (confidence ≥ 50%)

### System
- `GET /api/health` - Health check

## Configuration

### Environment Variables (.env)

```env
# MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=geoshop_engine

# API Server
APP_PORT=8000
APP_HOST=0.0.0.0

# Data Pipeline
MIN_CONFIDENCE_UPDATE=50

# API Keys (optional)
OSM_API_KEY=your_key_here
DATAGOV_API_KEY=your_key_here
ONEMAP_API_KEY=your_key_here
```

### Data Sources

The system fetches data from:
- **OpenStreetMap**: Shop POIs via Overpass API
- **data.gov.sg**: Business directory data
- **OneMap**: Singapore address and POI data

## Usage Examples

### CLI Commands

```bash
# Run pipeline with real APIs
python main.py run

# Run demo with mock data
python main.py demo

# Start scheduler
python main.py schedule

# Test components
python verify.py
```

### API Usage

```python
import requests

# Get all shops
response = requests.get("http://localhost:8000/api/shops")
shops = response.json()

# Trigger real-time update
response = requests.post("http://localhost:8000/api/update/realtime")
result = response.json()
```

### Frontend Features

- **Dashboard**: Real-time statistics and sync status
- **Shop Browser**: Filter and search shops by name, location, confidence
- **Sync Controls**: Trigger manual syncs and real-time updates
- **Change Tracking**: View new and closed shops since last sync

## Data Pipeline

1. **Fetch**: Retrieve raw data from all configured sources
2. **Normalize**: Convert to common schema with standardized fields
3. **Match**: Group related records using fuzzy string matching and geolocation
4. **Score**: Calculate confidence based on data completeness and source reliability
5. **Store**: Save enriched records to MongoDB Atlas

### Confidence Scoring

Confidence scores (0-100%) are calculated based on:
- **Data Completeness**: Address, phone, coordinates, etc.
- **Source Reliability**: OSM > data.gov.sg > OneMap
- **Match Quality**: String similarity and location proximity
- **Multi-source Validation**: Higher confidence for cross-referenced data

## Development

### Project Structure

```
geoshop_engine/
├── api/                    # FastAPI backend
├── data_fetchers/          # External API clients
├── processors/             # Data processing pipeline
├── signal_engine/          # Confidence scoring
├── db/                     # Database models and CRUD
├── scheduler/              # Periodic job scheduling
├── frontend/               # Web interface
├── main.py                 # CLI entry point
├── run_api.py             # API server launcher
├── verify.py              # Testing utilities
└── requirements.txt       # Dependencies
```

### Testing

```bash
# Run component tests
python verify.py

# Test API endpoints
curl http://localhost:8000/api/health

# Test pipeline with mock data
python main.py demo
```

## Deployment

### Production Setup

1. **Database**: Set up MongoDB Atlas cluster
2. **Environment**: Configure production .env file
3. **Server**: Deploy FastAPI app with uvicorn/gunicorn
4. **Frontend**: Serve static files or deploy to CDN
5. **Scheduler**: Run periodic jobs with cron/systemd

### Docker (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_api.py"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details