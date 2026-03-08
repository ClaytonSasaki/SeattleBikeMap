# Seattle Bike Infrastructure Map

An interactive map of Seattle's bike infrastructure, styled after the official [Seattle 2025 Bike Map](https://www.seattle.gov/documents/Departments/SDOT/BikeProgram/2025_BikeMap_Brochure.pdf), but includes planned bike facilities. Built with Python and [Folium](https://python-visualization.github.io/folium/), it outputs a single self-contained HTML file that can be opened in any browser or hosted as a static webpage.

## Overview

- Each bike facility type is rendered with a distinct color
- Planned facilities are shown as dashed, semi-transparent overlays
- Multi-use trails are merged into the separated pathway layer
- Hover tooltips are included for quick identification with clickable popups for extra detail
- All layers are toggleable layers and two base maps (CartoDB light and OpenStreetMap) are included

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
├── generate_seattle_bike_map.py
├── requirements.txt
├── README.md
├── LICENSE
└── data/
    ├── existing_bike_facilities.geojson
    ├── planned_bike_facilities.geojson
    └── multi-use_trails.geojson
```

## Setup

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

This produces `seattle_bike_map.html` in the project root. Open it in any browser.

## Updating the Map

The map is designed to be easy to keep current as Seattle's bike network changes.

1. Download updated GeoJSON files from [Seattle Open Data](https://data-seattlecitygis.opendata.arcgis.com):
   - [Existing bike facilities](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::sdot-bike-facilities/explore?layer=2)
   - [Planned bike facilities](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::sdot-bike-facilities/explore?layer=2)
   - [Multi-use trails](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::sdot-bike-facilities/explore?layer=1)
2. Replace the files in the `data/` directory
3. Re-run `python generate_seattle_bike_map.py`

No code changes are needed unless SDOT changes the underlying data schema.

## Data Sources

- Bike facilities: [Seattle Open Data — SDOT Bike Facilities](https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::sdot-bike-facilities)
- Reference map: [Seattle SDOT 2025 Bike Map](https://www.seattle.gov/documents/Departments/SDOT/BikeProgram/2025_BikeMap_Brochure.pdf)
