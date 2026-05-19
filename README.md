# GeoShop Engine

GeoShop Engine is a scalable place intelligence platform designed to resolve inconsistencies across multiple POI (Points of Interest) data sources and generate a reliable representation of real-world businesses.

Built during the HERE Technologies Mumbai Hackathon, the project secured **2nd Runner-Up**.

---

## Features

- Multi-source POI aggregation
- Cross-source entity resolution
- Geospatial proximity matching
- Fuzzy similarity scoring
- Confidence-based decision system
- Automated sync pipelines
- Real-time dashboard visualization
- Detection of outdated or closed businesses
- Scalable backend architecture
- Interactive map analytics

---

## Problem Statement

Modern POI datasets often contain:
- duplicate records
- inconsistent naming
- outdated business information
- conflicting location data
- missing metadata

GeoShop Engine solves this problem by intelligently merging and validating entities across multiple data sources using similarity scoring and confidence evaluation.

---
##ScreenShot :


## Tech Stack

### Backend
- FastAPI
- Python
- MongoDB
- APScheduler

### Frontend
- React.js
- Vite
- Map Visualization Libraries
- Charting Libraries

### Core Intelligence
- Fuzzy Matching Algorithms
- Geospatial Distance Calculations
- Similarity Scoring Engine
- Confidence Evaluation System

---

## System Architecture

```text
External Sources
(OSM, OneMap, data.gov.sg)
            ↓
      Data Ingestion
            ↓
     Data Normalization
            ↓
   Entity Resolution Engine
   - Geospatial Matching
   - Fuzzy Matching
   - Similarity Scoring
            ↓
   Confidence Decision Layer
            ↓
 Insert / Update / Flag
            ↓
        MongoDB
            ↓
     FastAPI Services
            ↓
      React Dashboard
```

---

## How It Works

### Data Aggregation
The system collects POI data from multiple public and digital sources.

### Normalization
Incoming records are normalized into a common structure to reduce inconsistencies.

### Entity Resolution
Entities are matched using:
- geographic proximity
- fuzzy text similarity
- metadata comparison

### Confidence Scoring
A combined confidence score is generated based on:
- source consistency
- similarity score
- digital footprint signals

### Decision Engine
Based on the confidence score, the system:
- inserts new entities
- updates existing entities
- flags potentially closed businesses

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/geoshop-engine.git
cd geoshop-engine
```

If your folder name is `geoshop_engine`, use:

```bash
cd geoshop_engine
```

---

## Backend Setup

Create and activate a Python virtual environment.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / MacOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file in the project root:

```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=geoshop_engine

APP_HOST=0.0.0.0
APP_PORT=8000

MIN_CONFIDENCE_UPDATE=50

OSM_API_KEY=
DATAGOV_API_KEY=
ONEMAP_API_KEY=
ONEMAP_ACCESS_TOKEN=
```

> MongoDB is required for full database features.  
> If MongoDB is unavailable, some commands may run in offline/mock mode.

---

## Initialize Demo Data

```bash
python main.py demo
```

---

## Run Backend API

### Recommended

```bash
python run_api.py
```

### Alternative

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## Frontend Setup

Open a new terminal and go to the frontend folder:

```bash
cd frontend

npm install

npm run dev
```

Frontend will usually run at:

```text
http://localhost:5173
```

---

## Useful Commands

### Run Data Pipeline With Real APIs

```bash
python main.py run
```

### Run Demo Pipeline With Mock Data

```bash
python main.py demo
```

### Start Scheduler

```bash
python main.py schedule
```

Or:

```bash
python -m scheduler.jobs
```

### Verify Project Components

```bash
python verify.py
```

### Test MongoDB Connection

```bash
python test_mongodb.py
```

---

## API Endpoints

### Shops

| Method | Endpoint |
|--------|----------|
| GET | `/api/shops` |
| GET | `/api/shops/{id}` |
| GET | `/api/shops/stats` |

---

### Sync Operations

| Method | Endpoint |
|--------|----------|
| GET | `/api/sync/status` |
| GET | `/api/sync/changes` |
| POST | `/api/sync/trigger` |
| POST | `/api/update/realtime` |

---

### System

| Method | Endpoint |
|--------|----------|
| GET | `/api/health` |

---

## Project Structure

```text
geoshop_engine/
│
├── api/
│   └── main.py              # FastAPI application and API routes
│
├── config/                  # Configuration helpers
├── data_fetchers/           # OpenStreetMap, data.gov.sg, OneMap fetchers
├── db/                      # MongoDB connection, models, and CRUD logic
├── frontend/                # React + Vite dashboard
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── processors/              # Data normalization and matching logic
├── scheduler/               # Scheduled update jobs
├── signal_engine/           # Confidence scoring logic
├── utils/                   # Utility functions
│
├── .env                     # Environment variables
├── main.py                  # CLI entry point for pipeline/demo/scheduler
├── run_api.py               # Backend API server launcher
├── requirements.txt         # Python dependencies
├── verify.py                # Component verification script
└── README.md
```

---

## Challenges Faced

- Handling noisy and inconsistent POI datasets
- Preventing incorrect entity merges
- Managing conflicting source information
- Reducing false positives
- Designing scalable matching pipelines
- Optimizing confidence thresholds

---

## Key Learnings

- Clean data rarely exists in production systems
- Matching quality matters more than complex algorithms
- More data often creates more ambiguity
- Confidence scoring becomes essential in uncertain systems
- System design strongly impacts scalability and reliability
- Edge-case handling dominates real-world engineering

---

## Future Improvements

- ML-based entity resolution
- Real-time streaming architecture
- LLM-assisted semantic matching
- International dataset scaling
- Satellite imagery verification
- Kubernetes deployment
- Advanced anomaly detection

---

## Use Cases

- Smart city infrastructure
- Urban analytics
- Logistics optimization
- Business intelligence systems
- Mapping platforms
- POI verification systems
- Location intelligence products

---

## Contributing

Contributions are welcome.

### Steps to Contribute

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Add feature"
```

4. Push to your branch

```bash
git push origin feature-name
```

5. Open a Pull Request

---

## Contribution Guidelines

- Follow clean coding practices
- Keep commits meaningful
- Avoid unrelated large PRs
- Document major changes
- Do not commit sensitive credentials

---

## Reporting Issues

If you find a bug or want to request a feature:
- Open an issue
- Provide clear reproduction steps
- Include logs/screenshots if needed

---

## License

This project is licensed under the MIT License.

---

## Acknowledgements

Special thanks to:
- HERE Technologies
- COEP Technological University
- Hackathon organizers and mentors
- Open geospatial datasets and APIs

---

## Contact

### Rohit Chavan

- GitHub: https://github.com/RohitChavan16
- LinkedIn: https://linkedin.com/in/rohit-chavan16
