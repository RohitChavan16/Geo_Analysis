# GeoShop Engine - Deployment & Quick Start Guide

## Quick Start (5 minutes)

### 1. Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Edit .env with your MongoDB Atlas credentials
# (Already has placeholder values for testing)
```

### 3. Run Demo (Offline)

```bash
# Test pipeline with mock data (no APIs needed)
python main.py demo
```

Expected output:
```
============================================================
GeoShop Engine - Data Processing Pipeline
============================================================

📥 Fetching data from all sources...
   📝 Using mock data (APIs unavailable)
   ✓ data.gov.sg: 2 records
   ✓ OpenStreetMap: 2 records
   ✓ OneMap: 1 record
   ✓ Total: 5 records

⚙️  Normalizing data...
   ✓ Normalized 5 records

🔗 Matching shops across sources...
   ✓ Found 3 unique shops

⭐ Calculating confidence scores...
   ✓ Scored 3 records

💾 Storing in database...
   ⚠ Database not available - skipping storage
   ✓ Processed 3 records (not stored)

Sample output (first 3 records):

  📍 Toa Payoh Supermarket
     Address: Blk 75 Toa Payoh Lorong 5, Singapore 310075
     Sources: ['osm', 'data_gov']
     Confidence: 82.4% (HIGH)

  📍 Ang Mo Kio Market
     Address: AMK Hub, Ang Mo Kio, Singapore
     Sources: ['data_gov']
     Confidence: 68.8% (MEDIUM)
```

### 4. Start API Server

```bash
python run_api.py
```

Expected output:
```
🚀 Starting GeoShop Engine API Server
📍 Server will be available at: http://localhost:8000
📖 API documentation at: http://localhost:8000/docs

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Open Frontend

Option A - Direct file (simple):
```bash
# Windows
start frontend/index.html

# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html
```

Option B - Web server (recommended):
```bash
# Python built-in server
cd frontend
python -m http.server 5000

# Then open: http://localhost:5000
```

## Complete Workflow

### Terminal 1: Start API Server
```bash
python run_api.py
```

### Terminal 2: View Frontend (in browser)
```
http://localhost:8000 (if served by API)
or
http://localhost:5000 (if using web server)
```

### Terminal 3: Run Scheduler (Optional)
```bash
python -m scheduler.jobs
```

## MongoDB Atlas Setup

### 1. Create MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for free tier (M0 cluster)
3. Create a cluster with default settings

### 2. Get Connection String

1. In Atlas console → Database → Connect
2. Choose "Connect your application"
3. Copy the connection string
4. Replace `<password>` with your database user password

### 3. Update .env

```env
MONGODB_URL=mongodb+srv://username:password@cluster-name.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=geoshop_engine
```

### 4. Test Connection

```bash
python -c "from db.database import init_database; init_database()"
```

Expected output:
```
✅ Connected to MongoDB Atlas
✅ Database initialized successfully
```

## API Usage Examples

### Get All Shops
```bash
curl http://localhost:8000/api/shops
```

### Get High-Confidence Shops
```bash
curl "http://localhost:8000/api/shops?min_confidence=70"
```

### Search by Name
```bash
curl "http://localhost:8000/api/shops?name=supermarket"
```

### Search by Location
```bash
curl "http://localhost:8000/api/shops?lat=1.3305&lng=103.8533&radius=1"
```

### Get System Status
```bash
curl http://localhost:8000/api/sync/status
```

### Trigger Full Sync
```bash
curl -X POST http://localhost:8000/api/sync/trigger
```

### Trigger Real-time Update (≥50% confidence)
```bash
curl -X POST http://localhost:8000/api/update/realtime
```

### View Changes Since Last Sync
```bash
curl http://localhost:8000/api/sync/changes
```

### API Documentation
```
http://localhost:8000/docs (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

## Data Sources

### OpenStreetMap (OSM)
- **Free:** Yes
- **Rate Limit:** 1 request/second
- **Data:** Shop POIs with detailed tags
- **Example:** `/shops[@shop_type~"supermarket"]`

### data.gov.sg
- **Free:** Yes
- **Rate Limit:** API limits apply
- **Data:** Government datasets including business directory
- **Example:** Business licenses, permits

### OneMap
- **Free:** Yes (basic)
- **Rate Limit:** 250 requests/minute
- **Data:** Singapore address and POI data
- **Example:** HDB blocks, roads, buildings

## Environment Variables

```env
# Database
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=geoshop_engine

# API Server
APP_PORT=8000
APP_HOST=0.0.0.0

# Pipeline
MIN_CONFIDENCE_UPDATE=50

# Optional: API Keys
OSM_API_KEY=your_key_here
DATAGOV_API_KEY=your_key_here
ONEMAP_API_KEY=your_key_here
```

## Running in Production

### Using Gunicorn (Production ASGI Server)

```bash
# Install
pip install gunicorn

# Run
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app
```

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t geoshop-engine .
docker run -p 8000:8000 --env-file .env geoshop-engine
```

### Using Systemd Service

Create `/etc/systemd/system/geoshop-engine.service`:

```ini
[Unit]
Description=GeoShop Engine API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/geoshop-engine
Environment="PATH=/opt/geoshop-engine/venv/bin"
ExecStart=/opt/geoshop-engine/venv/bin/python run_api.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl start geoshop-engine
sudo systemctl enable geoshop-engine
```

## Scheduling Automatic Syncs

### Using APScheduler in Background

```bash
# The scheduler runs automatically with the API
# It will sync data every 3 days by default
```

### Using Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add this line to run sync every 3 days
0 0 */3 * * cd /path/to/geoshop_engine && python main.py run
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily (repeat every 3 days)
4. Set action: `python main.py run`
5. Set location: `E:\test\geoshop_engine`

## Monitoring

### View Sync Logs

```bash
# Get recent syncs
curl http://localhost:8000/api/sync/logs
```

### Check Database Status

```python
from db.database import get_database
from db.crud import count_shops, get_sync_status

db = get_database()
status = get_sync_status()
print(f"Total shops: {count_shops()}")
print(f"Last sync: {status['last_sync']}")
```

### View API Logs

```bash
# Check logs in API server terminal or:
tail -f /var/log/geoshop-engine.log
```

## Troubleshooting

### MongoDB Connection Failed

```
❌ MongoDB connection failed: bad auth
```

Solution:
1. Check `.env` file has correct credentials
2. Verify MongoDB Atlas whitelist includes your IP
3. Test connection: `python -c "from db.database import init_database; init_database()"`

### API Server Won't Start

```
Address already in use
```

Solution:
```bash
# Change port in .env
APP_PORT=8001

# Or kill existing process on port 8000
# Windows: netstat -ano | findstr :8000
# Linux: lsof -i :8000 | grep LISTEN
```

### Data Fetching Returns 0 Records

```
✓ data.gov.sg: 0 records
✓ OpenStreetMap: 0 records
```

Solution:
1. Use mock data: `python main.py demo`
2. Check API rate limits
3. Verify internet connection
4. Check data source status

### Frontend Shows "Cannot connect to API"

Solution:
1. Ensure API server is running: `python run_api.py`
2. Check frontend URL matches API port
3. Verify CORS is enabled in API
4. Check browser console for errors

## Performance Tuning

### Increase Matching Accuracy
Edit `processors/matcher.py` - adjust `distance_threshold` and `similarity_threshold`

### Faster Data Processing
Edit `main.py` - reduce mock data sample or implement pagination

### Database Optimization
Create compound indexes:
```javascript
db.shops.createIndex({ "confidence_score": -1, "is_active": 1 })
db.shops.createIndex({ "sources": 1, "created_at": -1 })
```

## Backup & Recovery

### Backup MongoDB

```bash
# Using mongodump
mongodump --uri="mongodb+srv://..." --out=./backup

# Restore
mongorestore --uri="mongodb+srv://..." ./backup
```

### Export to CSV

```bash
mongoexport --uri="mongodb+srv://..." --collection=shops --out=shops.csv --type=csv
```

## Getting Help

1. **API Documentation:** `http://localhost:8000/docs`
2. **Project README:** See [README.md](README.md)
3. **Code Comments:** Check source code for inline documentation
4. **Issues:** Review error messages in terminal/logs

## Support

For issues or questions:
1. Check logs and error messages
2. Review the README.md
3. Test components individually
4. Run test suite: `python test_e2e.py`