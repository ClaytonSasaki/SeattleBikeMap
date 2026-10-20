"""
Download the latest Seattle bike facility data
==============================================
Fetches the SDOT Bike Facilities layers from Seattle's ArcGIS feature service
and writes them to the data/ directory as GeoJSON, in the same format as the
files downloaded from Seattle Open Data.

Usage:
    python fetch_data.py
"""

import json
import os
import urllib.parse
import urllib.request
from email.utils import formatdate

SERVICE_URL = (
    "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/"
    "SDOT_Bike_Facilities/FeatureServer"
)

DATA_DIR = "data"

# Feature service layer id → output file
LAYERS = {
    1: "multi-use_trails.geojson",
    2: "existing_bike_facilities.geojson",
    3: "planned_bike_facilities.geojson",
}

PAGE_SIZE = 2000   # the service's maxRecordCount


def get_json(url: str, params: dict) -> dict:
    """GET a URL with query parameters and return the parsed JSON response."""
    full_url = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full_url, timeout=120) as resp:
        data = json.load(resp)
    if "error" in data:
        raise RuntimeError(f"ArcGIS error from {url}: {data['error']}")
    return data


def fetch_layer(layer_id: int) -> dict:
    """Download every feature in a layer as a GeoJSON FeatureCollection."""
    layer_url = f"{SERVICE_URL}/{layer_id}"

    # The REST API returns dates as epoch milliseconds; the Open Data downloads
    # use RFC 2822 strings, which generate_seattle_bike_map.py expects.
    info = get_json(layer_url, {"f": "json"})
    date_fields = [f["name"] for f in info["fields"] if f["type"] == "esriFieldTypeDate"]

    expected = get_json(f"{layer_url}/query", {
        "where": "1=1", "returnCountOnly": "true", "f": "json",
    })["count"]

    features = []
    while True:
        page = get_json(f"{layer_url}/query", {
            "where":             "1=1",
            "outFields":         "*",
            "outSR":             4326,
            "orderByFields":     "OBJECTID",
            "resultOffset":      len(features),
            "resultRecordCount": PAGE_SIZE,
            "f":                 "geojson",
        })
        features.extend(page["features"])
        if not page["features"] or not page.get("properties", {}).get("exceededTransferLimit"):
            break

    # Refuse to write a partial download — better to keep the old data
    if not features or len(features) != expected:
        raise RuntimeError(
            f"Layer {layer_id} ({info['name']}): got {len(features)} features, expected {expected}"
        )

    # Strip values that change on every refresh, so month-to-month git diffs
    # only show real changes: OBJECTIDs are reassigned each time, and the
    # refresh timestamp (identical on every feature) is kept once per file.
    last_updated = None
    for feature in features:
        feature.pop("id", None)
        props = feature.get("properties") or {}
        props.pop("OBJECTID", None)
        for name in date_fields:
            if isinstance(props.get(name), (int, float)):
                props[name] = formatdate(props[name] / 1000, usegmt=True)
        last_updated = props.pop("DATE_MVW_LAST_UPDATED", None) or last_updated

    # Sort on stable IDs (geometry breaks the few ties) so rows keep their order
    features.sort(key=lambda f: (
        f["properties"].get("COMPKEY") or 0,
        f["properties"].get("SND_ID") or 0,
        json.dumps(f["geometry"]),
    ))

    collection = {"type": "FeatureCollection", "features": features}
    if last_updated:
        collection["properties"] = {"DATE_MVW_LAST_UPDATED": last_updated}
    return collection


def write_geojson(path: str, collection: dict):
    """Write GeoJSON with one feature per line, so git diffs show which segments changed."""
    header = {k: v for k, v in collection.items() if k != "features"}
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(header)[:-1] + ', "features": [\n')
        fh.write(",\n".join(json.dumps(f) for f in collection["features"]))
        fh.write("\n]}\n")


def main():
    for layer_id, filename in LAYERS.items():
        path = os.path.join(DATA_DIR, filename)
        print(f"Fetching layer {layer_id} → {path} …")
        collection = fetch_layer(layer_id)
        write_geojson(path, collection)
        print(f"  → {len(collection['features'])} features")


if __name__ == "__main__":
    main()
