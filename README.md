# Curvature API & Web Interface

A modern REST API and interactive web interface for [curvature](https://github.com/adamfranco/curvature) - the tool that finds the curviest, most twisty roads for motorcyclists and driving enthusiasts.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.14+-green)
![License](https://img.shields.io/badge/license-GPL%20v3-blue)

## 🏔️ What This Is

This project adds a modern API and web interface layer on top of curvature:

- **FastAPI Backend** - REST API for querying curvature road data
- **Interactive Google Maps Interface** - Visualize curvy roads with color-coded overlays
- **Secure API Key Management** - Backend-served configuration
- **msgpack 1.1+ Support** - Compatible with modern Python environments

## 🎯 How It Works

```
1. Process OSM data with curvature → .msgpack files
2. Load .msgpack files into this API
3. Query via REST endpoints or web interface
4. Visualize on interactive maps!
```

## 🚀 Quick Start

### Prerequisites

1. **Install curvature** (the data processing engine):
```bash
git clone https://github.com/adamfranco/curvature.git
cd curvature
pip install osmium msgpack
```

2. **Process some data** (example: Vermont):
```bash
# Download OSM data
wget http://download.geofabrik.de/north-america/us/vermont-latest.osm.pbf

# Process with curvature
./processing_chains/adams_default.sh -v vermont-latest.osm.pbf -t /tmp -r

# Output: /tmp/vermont-latest.msgpack
```

### Install curvature-api

```bash
# Clone this repository
git clone https://github.com/YOUR_USERNAME/curvature-api.git
cd curvature-api

# Install dependencies
pip install -r api/requirements.txt

# Set up configuration
cp api/config.example.py api/config.py
# Edit api/config.py and add your Google Maps API key

# Start the server
python api/server.py
```

### Open the web interface

Visit: http://localhost:8000/static/index.html

## 📖 Usage

### Web Interface

1. **Load Data**: Enter the path to your `.msgpack` file (e.g., `/tmp/vermont-latest.msgpack`)
2. **Search**: Adjust minimum curvature, surface type, and result limit
3. **Explore**: Click roads on the map or in the sidebar to see details!

**Road color coding:**
- 🟡 **Yellow** (300-600): Pleasant, flowing curves
- 🟠 **Orange** (600-1000): Fun, moderately twisty
- 🔴 **Red** (1000-2000): Very curvy, technical roads
- 🟣 **Purple** (2000+): Extremely twisty! Hairpin heaven!

### REST API

```bash
# Load data
curl -X POST "http://localhost:8000/data/load?filepath=/tmp/vermont-latest.msgpack"

# Search for curvy roads
curl "http://localhost:8000/roads?min_curvature=1000&limit=10"

# Get GeoJSON for mapping
curl "http://localhost:8000/roads/geojson?min_curvature=1500&surface=paved&limit=50"

# Interactive API docs
open http://localhost:8000/docs
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/config` | GET | Frontend configuration (includes API keys) |
| `/data/load` | POST | Load a .msgpack file |
| `/roads` | GET | Search roads (simple JSON) |
| `/roads/geojson` | GET | Search roads (GeoJSON for maps) |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API documentation |

See [API_README.md](API_README.md) for complete API documentation.

## 🔐 Security

API keys are stored securely and never committed to git:

- Keys in `api/config.py` (gitignored)
- Served via backend `/config` endpoint
- Frontend loads keys dynamically at runtime
- Template provided as `api/config.example.py`

For production deployment security considerations, see [SECURITY_ROADMAP.md](SECURITY_ROADMAP.md).

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (User)                        │
│  - Interactive map with Google Maps                      │
│  - Search and filter controls                            │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP
┌───────────────────────▼─────────────────────────────────┐
│              FastAPI Backend (api/server.py)             │
│  - Load .msgpack files                                   │
│  - Search/filter roads by curvature                      │
│  - Serve GeoJSON for mapping                             │
│  - Secure config endpoint                                │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│           Curvature Library (external)                   │
│  - OutputTools for road data processing                  │
│  - Curvature calculation utilities                       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                  Data Layer                              │
│  - .msgpack files (processed road collections)          │
│  - Original OSM data                                     │
└─────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
curvature-api/
├── api/
│   ├── server.py              # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── config.example.py      # Configuration template
│   ├── config.py              # Your actual config (gitignored!)
│   └── venv/                  # Virtual environment
├── web/
│   └── static/
│       ├── index.html         # Web interface
│       ├── app.js             # Google Maps integration
│       └── style.css          # Styling
├── README.md                  # This file
├── API_README.md              # Detailed API documentation
├── SECURITY_ROADMAP.md        # Security best practices
└── .gitignore                 # Git ignore rules
```

## 🔧 Configuration

### Google Maps API Key

1. Get a key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Maps JavaScript API"
3. Copy `api/config.example.py` to `api/config.py`
4. Add your key to `api/config.py`

### For Production

Set these restrictions in Google Cloud Console:
- **HTTP referrers**: Only your domain
- **API restrictions**: Only "Maps JavaScript API"
- **Quotas**: Set reasonable limits

## 🌍 Processing More Data

### Popular regions for curvy roads:

```bash
# New York (includes Catskills)
wget http://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf
curvature-collect new-york-latest.osm.pbf | [processing chain] > /tmp/new-york.msgpack

# North Carolina (Tail of the Dragon)
wget http://download.geofabrik.de/north-america/us/north-carolina-latest.osm.pbf

# Colorado (mountain passes)
wget http://download.geofabrik.de/north-america/us/colorado-latest.osm.pbf

# California (Pacific Coast Highway, Mulholland Drive)
wget http://download.geofabrik.de/north-america/us/california-latest.osm.pbf
```

See the [original curvature documentation](https://github.com/adamfranco/curvature) for processing instructions.

## 🚧 Roadmap

### Current Features (v1.0)
- ✅ FastAPI backend with road search
- ✅ Interactive Google Maps interface
- ✅ Secure API key management
- ✅ msgpack 1.1+ compatibility
- ✅ Filter by curvature, surface, length
- ✅ GeoJSON export

### Planned Features
- 🔲 Claude AI integration (natural language search)
- 🔲 MCP (Model Context Protocol) server
- 🔲 Elevation data integration
- 🔲 Street View previews
- 🔲 Multi-road route planning
- 🔲 User accounts and favorites
- 🔲 GPX export for GPS devices
- 🔲 Mobile app (React Native)

See [SECURITY_ROADMAP.md](SECURITY_ROADMAP.md) for production scaling plans.

## 🤝 Contributing

Contributions welcome! This project focuses on the API/web interface layer. For curvature core functionality, contribute to the [upstream project](https://github.com/adamfranco/curvature).

### Development Setup

```bash
# Install in development mode
cd curvature-api
python -m venv api/venv
source api/venv/bin/activate  # or `api/venv/bin/activate` on Windows
pip install -r api/requirements.txt

# Run with auto-reload
python api/server.py
```

## 🐛 Troubleshooting

### "No module named 'curvature'"

Install the curvature library separately or add it to your Python path.

### "Google Maps API key not configured"

Create `api/config.py` from `api/config.example.py` and add your API key.

### "FileNotFoundError: Data file not found"

Use absolute paths for .msgpack files (e.g., `/tmp/vermont-latest.msgpack`).

### Map shows gray box

Check browser console (F12) for API key errors. Verify your Google Maps API key is valid.

## 📝 License

GNU General Public License Version 3 or later - same as the original curvature project.

## 🙏 Credits

- **Original Curvature Project**: [Adam Franco](https://github.com/adamfranco/curvature)
- **API & Web Interface**: George Smith-Sweeper
- **Data**: [OpenStreetMap contributors](https://www.openstreetmap.org/)

## 🔗 Links

- [Curvature (original project)](https://github.com/adamfranco/curvature)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [Geofabrik (OSM data downloads)](http://download.geofabrik.de/)
- [Google Maps JavaScript API](https://developers.google.com/maps/documentation/javascript)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Find curvy roads. Drive them. Enjoy!** 🏍️🏔️
