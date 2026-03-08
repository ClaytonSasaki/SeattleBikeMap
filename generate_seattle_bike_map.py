"""
Seattle Bike Infrastructure Map Generator
==========================================
Produces an interactive HTML map styled after the official Seattle 2025 Bike Map.

Data sources (GeoJSON, downloaded from Seattle Open Data):
  - data/existing_bike_facilities.geojson
  - data/planned_bike_facilities.geojson

Usage:
    pip install folium branca
    python generate_seattle_bike_map.py

Output:
    seattle_bike_map.html  — open in any browser, or host as a static webpage.

To update the map when new data is released, simply replace the GeoJSON files
in the data/ directory and re-run this script.
"""

import json
import os
import folium
from folium.plugins import GroupedLayerControl

# ---------------------------------------------------------------------------
# CONFIG — edit colours / weights here without touching the rest of the script
# ---------------------------------------------------------------------------

# Paths to data files (relative to this script)
DATA_DIR = "data"
EXISTING_FILE = os.path.join(DATA_DIR, "existing_bike_facilities.geojson")
PLANNED_FILE  = os.path.join(DATA_DIR, "planned_bike_facilities.geojson")
TRAILS_FILE   = os.path.join(DATA_DIR, "multi-use_trails.geojson")

OUTPUT_FILE = "seattle_bike_map.html"

# Map centre and default zoom
MAP_CENTER = [47.606, -122.332]
MAP_ZOOM   = 12

# Tile layer — "CartoDB positron" gives a clean light-grey base similar to the
# printed map. Other good options: "CartoDB dark_matter", "OpenStreetMap".
TILE_LAYER = "CartoDB positron"

# ---------------------------------------------------------------------------
# Facility style definitions
# Each entry:  category_code → {label, color, weight, dash_array, opacity}
# dash_array=None means solid line; "6 4" means dashed.
# ---------------------------------------------------------------------------

FACILITY_STYLES = {
    # ---- Separated / high-comfort facilities --------------------------------
    "BKF-OFFST": {
        "label":      "Separated Pathway / Protected Lane / Multi-use Trail",
        "color":      "#2A7D4F",   # dark green — highest comfort
        "weight":     4,
        "dash_array": None,
        "opacity":    0.95,
    },
    "BKF-PBL": {
        "label":      "Separated Pathway / Protected Lane / Multi-use Trail",
        "color":      "#2A7D4F",   # same dark green family as official map
        "weight":     3,
        "dash_array": None,
        "opacity":    0.95,
    },
    # ---- On-street marked facilities ----------------------------------------
    "BKF-BL": {
        "label":      "Bike Lane",
        "color":      "#5BAD6F",   # medium green
        "weight":     2.5,
        "dash_array": None,
        "opacity":    0.9,
    },
    "BKF-BBL": {
        "label":      "Buffered Bike Lane",
        "color":      "#5BAD6F",
        "weight":     2.5,
        "dash_array": None,
        "opacity":    0.9,
    },
    "BKF-CLMB": {
        "label":      "Climbing Lane (uphill only)",
        "color":      "#5BAD6F",
        "weight":     2,
        "dash_array": "8 4",
        "opacity":    0.85,
    },
    # ---- Neighbourhood Greenways --------------------------------------------
    "BKF-NGW": {
        "label":      "Neighborhood Greenway",
        "color":      "#8CC63F",   # yellow-green
        "weight":     2,
        "dash_array": None,
        "opacity":    0.9,
    },
    # ---- Sharrows -----------------------------------------------------------
    "BKF-SHW": {
        "label":      "Sharrows / Shared Lane",
        "color":      "#C8A415",   # amber/gold
        "weight":     1.8,
        "dash_array": None,
        "opacity":    0.8,
    },
    # ---- Fallback for unknown categories ------------------------------------
    "_default": {
        "label":      "Other Bike Facility",
        "color":      "#888888",
        "weight":     1.5,
        "dash_array": None,
        "opacity":    0.7,
    },
}

# Planned facilities are drawn dashed and slightly transparent over the base style
PLANNED_DASH   = "8 5"
PLANNED_OPACITY_SCALE = 0.7   # multiply base opacity by this


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_geojson(path: str) -> dict:
    """Load a GeoJSON file and return the parsed dict."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def facility_style(category: str, planned: bool = False) -> dict:
    """Return a Folium-compatible style dict for a given category code."""
    base = FACILITY_STYLES.get(category) or FACILITY_STYLES["_default"]
    dash = PLANNED_DASH if planned else base["dash_array"]
    opacity = base["opacity"] * (PLANNED_OPACITY_SCALE if planned else 1.0)
    return {
        "color":     base["color"],
        "weight":    base["weight"],
        "opacity":   opacity,
        "dashArray": dash,
    }


def feature_popup(props: dict, planned: bool) -> str:
    """Build a compact HTML popup string from feature properties."""
    cat   = props.get("CATEGORY") or "Unknown"
    style = FACILITY_STYLES.get(cat, FACILITY_STYLES["_default"])
    desc  = props.get("UNITDESC", "").title()
    status_label = "Planned" if planned else "Existing"
    install = (props.get("INSTALL_DATE") or "")[:11] if not planned else "–"
    html = (
        f"<b style='color:{style['color']}'>{style['label']}</b><br>"
        f"<small><b>Status:</b> {status_label}<br>"
        f"<b>Description:</b> {desc}<br>"
        f"<b>Code:</b> {cat}<br>"
        f"<b>Installed:</b> {install}</small>"
    )
    return html


# ---------------------------------------------------------------------------
# Build layer groups — one FeatureGroup per facility type per status
# ---------------------------------------------------------------------------

def build_layer_groups(existing_data: dict, planned_data: dict, trails_data: dict) -> dict:
    """
    Returns a dict:
      { (category, planned_bool): folium.FeatureGroup }
    Populated with GeoJSON lines.

    Multi-use trails are merged into the ("BKF-OFFST", False) group so they
    share the "Separated Pathway / Protected Lane / Multi-use Trail" legend entry.
    """
    groups: dict = {}

    def add_features(geojson_data: dict, planned: bool):
        for feature in geojson_data["features"]:
            props = feature.get("properties", {})
            cat   = props.get("CATEGORY") or "_default"
            key   = (cat, planned)

            if key not in groups:
                style_info = FACILITY_STYLES.get(cat, FACILITY_STYLES["_default"])
                suffix = " (Planned)" if planned else ""
                groups[key] = folium.FeatureGroup(
                    name=style_info["label"] + suffix,
                    show=True,
                )

            style = facility_style(cat, planned)
            popup_html = feature_popup(props, planned)

            folium.GeoJson(
                feature,
                style_function=lambda _f, s=style: s,
                tooltip=folium.Tooltip(
                    props.get("UNITDESC", "").title() or "Bike Facility",
                    sticky=False,
                ),
                popup=folium.Popup(popup_html, max_width=280),
            ).add_to(groups[key])

    def add_trails(geojson_data: dict):
        """Add multi-use trails into the BKF-OFFST (existing) layer group."""
        key = ("BKF-OFFST", False)
        style_info = FACILITY_STYLES["BKF-OFFST"]

        # Create the group if it hasn't been created yet by add_features
        if key not in groups:
            groups[key] = folium.FeatureGroup(
                name=style_info["label"],
                show=True,
            )

        style = facility_style("BKF-OFFST", planned=False)

        for feature in geojson_data["features"]:
            props = feature.get("properties", {})
            name  = props.get("ORD_STNAME_CONCAT", "").title() or "Multi-use Trail"
            popup_html = (
                f"<b style='color:{style_info['color']}'>Multi-use Trail</b><br>"
                f"<small><b>Name:</b> {name}</small>"
            )
            folium.GeoJson(
                feature,
                style_function=lambda _f, s=style: s,
                tooltip=folium.Tooltip(name, sticky=False),
                popup=folium.Popup(popup_html, max_width=280),
            ).add_to(groups[key])

    add_features(existing_data, planned=False)
    add_features(planned_data,  planned=True)
    add_trails(trails_data)
    return groups


# ---------------------------------------------------------------------------
# Legend HTML
# ---------------------------------------------------------------------------

LEGEND_HTML = """
<div style="
    position: fixed; bottom: 30px; left: 15px; z-index: 1000;
    background: rgba(255,255,255,0.93); border-radius: 8px;
    padding: 12px 16px; font-family: Arial, sans-serif; font-size: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25); max-width: 210px;
">
  <b style="font-size:13px;">Seattle Bike Facilities</b>
  <hr style="margin:6px 0; border-color:#ddd">

  <b style="font-size:11px; color:#555; text-transform:uppercase; letter-spacing:.5px;">
    Existing
  </b><br>

  <svg width="30" height="8"><line x1="0" y1="4" x2="30" y2="4"
    style="stroke:#2A7D4F;stroke-width:4"/></svg>
  Separated Pathway / Protected Lane / Multi-use Trail<br>

  <svg width="30" height="8"><line x1="0" y1="4" x2="30" y2="4"
    style="stroke:#5BAD6F;stroke-width:2.5"/></svg>
  Bike Lane / Buffered Lane<br>

  <svg width="30" height="8"><line x1="0" y1="4" x2="30" y2="4"
    style="stroke:#8CC63F;stroke-width:2"/></svg>
  Neighborhood Greenway<br>

  <svg width="30" height="8"><line x1="0" y1="4" x2="30" y2="4"
    style="stroke:#C8A415;stroke-width:1.8"/></svg>
  Sharrows / Shared Lane<br>

  <br>
  <b style="font-size:11px; color:#555; text-transform:uppercase; letter-spacing:.5px;">
    Planned (dashed)
  </b><br>

  <svg width="30" height="8"><line x1="0" y1="4" x2="30" y2="4"
    style="stroke:#2A7D4F;stroke-width:3;stroke-dasharray:8,5;opacity:0.7"/></svg>
  Separated / Protected<br>

  <svg width="30" height="8"><line x1="0" y1="4" x2="30" y2="4"
    style="stroke:#5BAD6F;stroke-width:2.5;stroke-dasharray:8,5;opacity:0.7"/></svg>
  Bike Lane (Planned)<br>

  <svg width="30" height="8"><line x1="0" y1="4" x2="30" y2="4"
    style="stroke:#8CC63F;stroke-width:2;stroke-dasharray:8,5;opacity:0.7"/></svg>
  Greenway (Planned)<br>

  <svg width="30" height="8"><line x1="0" y1="4" x2="30" y2="4"
    style="stroke:#C8A415;stroke-width:1.8;stroke-dasharray:8,5;opacity:0.7"/></svg>
  Sharrows (Planned)<br>

  <hr style="margin:6px 0; border-color:#ddd">
  <small style="color:#888">
    Data: Seattle Open Data<br>
    Generated: {date}
  </small>
</div>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    from datetime import date

    print(f"Loading {EXISTING_FILE} …")
    existing = load_geojson(EXISTING_FILE)
    print(f"  → {len(existing['features'])} features")

    print(f"Loading {PLANNED_FILE} …")
    planned = load_geojson(PLANNED_FILE)
    print(f"  → {len(planned['features'])} features")

    print(f"Loading {TRAILS_FILE} …")
    trails = load_geojson(TRAILS_FILE)
    print(f"  → {len(trails['features'])} features")

    # Create base map
    m = folium.Map(
        location=MAP_CENTER,
        zoom_start=MAP_ZOOM,
        tiles=TILE_LAYER,
        attr="© CartoDB © OpenStreetMap contributors | Bike data © City of Seattle",
        prefer_canvas=True,   # faster rendering for many lines
    )

    # Add a secondary tile choice so users can switch to a satellite/street view
    folium.TileLayer(
        "OpenStreetMap", name="OpenStreetMap", attr="© OpenStreetMap contributors"
    ).add_to(m)

    # Build and attach layer groups
    print("Building layers …")
    groups = build_layer_groups(existing, planned, trails)

    # Add layers to map in a sensible Z-order (least visible on bottom)
    priority_order = [
        ("BKF-SHW", False), ("BKF-SHW", True),
        ("BKF-NGW", False), ("BKF-NGW", True),
        ("BKF-CLMB", False),
        ("BKF-BL",  False), ("BKF-BL",  True),
        ("BKF-BBL", False),
        ("BKF-PBL", False), ("BKF-PBL", True),
        ("BKF-OFFST", False),
        ("_default", False), ("_default", True),
    ]
    added_keys = set()
    for key in priority_order:
        if key in groups:
            groups[key].add_to(m)
            added_keys.add(key)
    for key, grp in groups.items():
        if key not in added_keys:
            grp.add_to(m)

    # Layer control
    folium.LayerControl(collapsed=True).add_to(m)

    # Legend
    legend = LEGEND_HTML.format(date=date.today().strftime("%B %d, %Y"))
    m.get_root().html.add_child(folium.Element(legend))

    # Title bar
    title_html = """
    <div style="
        position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
        z-index: 1000; background: rgba(255,255,255,0.92);
        padding: 8px 20px; border-radius: 6px;
        font-family: Arial, sans-serif; font-size: 16px; font-weight: bold;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2); white-space: nowrap;
    ">
        🚲 Seattle Bike Infrastructure Map
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # Save
    m.save(OUTPUT_FILE)
    print(f"\n✅  Saved → {OUTPUT_FILE}")
    print("Open it in any browser. To update, replace the GeoJSON files and re-run.")


if __name__ == "__main__":
    main()
