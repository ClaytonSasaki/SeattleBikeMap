# Seattle Bike Infrastructure Map

An interactive map of Seattle's bike infrastructure, styled after the official [Seattle 2025 Bike Map](https://www.seattle.gov/documents/Departments/SDOT/BikeProgram/2025_BikeMap_Brochure.pdf), but includes planned bike facilities. Built with Python and [Folium](https://python-visualization.github.io/folium/), it outputs a single self-contained HTML file that can be opened in any browser or hosted as a static webpage.

## Overview

- Each bike facility type is rendered with a distinct color
- Planned facilities are shown as dashed, semi-transparent overlays
- Multi-use trails are merged into the separated pathway layer
- Hover tooltips are included for quick identification with clickable popups for extra detail
- All layers are toggleable layers and two base maps (CartoDB light and OpenStreetMap) are included (CartoDB requires a free API key; see Usage)

## Facility Types

| Category code | Description | Colour |
|---|---|---|
| `BKF-OFFST` | Separated Pathway / Trail | Dark green |
| `BKF-PBL` | Protected Bike Lane | Dark green |
| `BKF-BL` | Bike Lane | Medium green |
| `BKF-BBL` | Buffered Bike Lane | Medium green |
| `BKF-CLMB` | Climbing Lane (uphill only) | Medium green, dashed |
| `BKF-NGW` | Neighborhood Greenway | Yellow-green |
| `BKF-SHW` | Sharrows / Shared Lane | Amber |
| *(trails file)* | Multi-use Trail | Dark green |

Planned versions of each facility are rendered with the same colour but as dashed, semi-transparent lines.

## Project Structure

```
SeattleBikeMap/
├── .github/workflows/deploy.yml
├── fetch_data.py
├── generate_seattle_bike_map.py
├── requirements.txt
├── README.md
├── LICENSE
└── data/
    ├── existing_bike_facilities.geojson
    ├── planned_bike_facilities.geojson
    └── multi-use_trails.geojson
```

## Setup (to run locally)

**Requirements:** Python 3.8+ (limited by the `folium` dependency, not the script itself)

1. Clone the repository to your local machine and navigate to the base directory 

```bash
git clone https://github.com/ClaytonSasaki/SeattleBikeMap.git
cd SeattleBikeMap
```

2. Create and activate a virtual environment (Optional):

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python generate_seattle_bike_map.py
```

This produces `seattle_bike_map.html` in the project root. To view it, serve it locally rather than opening the file directly — OpenStreetMap's tile servers block pages opened from disk (`file://`), because they send no `Referer` header:

```bash
python -m http.server 8765
# then open http://localhost:8765/seattle_bike_map.html
```

CARTO basemaps require an API key ([get a free one here](https://carto.com/basemaps/apikey)). Set it before generating the map to use the CartoDB light base map as the default:

```bash
CARTO_API_KEY=your_key python generate_seattle_bike_map.py
```

Without a key, OpenStreetMap is used as the default (and only) base map. Note that the key is embedded in the generated HTML, so restrict it to your site's domain in the CARTO dashboard if you host the map publicly. A domain-restricted key won't load tiles in a local preview unless you also allow `localhost`.

## Updating the Map

The hosted map updates itself: a [GitHub Actions workflow](.github/workflows/deploy.yml) downloads the latest data, regenerates the map and deploys it to GitHub Pages on the 1st of every month, on every push to `main`, and on demand (Actions tab → *Build and deploy map* → *Run workflow*). It reads the CARTO key from the `CARTO_API_KEY` repository secret.

To update the map locally:

1. Download the latest data into `data/`:

```bash
python fetch_data.py
```

   Or download the GeoJSON files manually from [Seattle Open Data](https://data-seattlecitygis.opendata.arcgis.com):
   - [Existing bike facilities](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::sdot-bike-facilities/explore?layer=2)
   - [Planned bike facilities](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::sdot-bike-facilities/explore?layer=3)
   - [Multi-use trails](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::sdot-bike-facilities/explore?layer=1)
2. Re-run `python generate_seattle_bike_map.py`

No code changes are needed unless SDOT changes the underlying data schema.

## Data Sources

- Bike facilities: [Seattle Open Data — SDOT Bike Facilities](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::sdot-bike-facilities)
- Reference map: [Seattle SDOT 2025 Bike Map](https://www.seattle.gov/documents/Departments/SDOT/BikeProgram/2025_BikeMap_Brochure.pdf)
