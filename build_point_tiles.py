#!/usr/bin/env python3
"""
build_point_tiles.py — cut a big CSV of points into slippy-map tiles (GeoJSON, gzip).
Keeps maps tiny & fast by loading only visible tiles on demand.

Usage:
  python build_point_tiles.py --csv observations_swiss.csv --out tiles --min-zoom 5 --max-zoom 12
"""

import argparse
import csv
import gzip
import json
import math
import os
from collections import defaultdict

def lonlat_to_tile(lon, lat, z):
    """Convert lon/lat to tile x,y at zoom z (Web Mercator)."""
    lat = max(min(lat, 85.05112878), -85.05112878)
    x = int((lon + 180.0) / 360.0 * (1 << z))
    s = math.sin(math.radians(lat))
    y = int((1.0 - math.log((1.0 + s) / (1.0 - s)) / math.pi) / 2.0 * (1 << z))
    return x, y

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default="tiles")
    ap.add_argument("--lat-col", default="latitude")
    ap.add_argument("--lon-col", default="longitude")
    ap.add_argument("--min-zoom", type=int, default=5)
    ap.add_argument("--max-zoom", type=int, default=12)
    ap.add_argument("--keep-cols", default="observation_uuid,taxon_id,quality_grade,observed_on,observer_id,positional_accuracy")
    ap.add_argument("--batch", type=int, default=200000, help="rows per write batch (avoid huge RAM)")
    args = ap.parse_args()

    keep_cols = [c.strip() for c in args.keep_cols.split(",") if c.strip()]

    os.makedirs(args.out, exist_ok=True)

    # We'll stream rows and bucket them per (z, x, y) in memory, flushing per batches.
    # To minimize RAM, we rotate batches across zooms.
    def flush_buckets(buckets):
        for (z, x, y), feats in buckets.items():
            if not feats:
                continue
            folder = os.path.join(args.out, str(z), str(x))
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"{y}.geojson.gz")

            # Append mode: read existing, extend, write back (still small per tile)
            if os.path.exists(path):
                with gzip.open(path, "rt", encoding="utf-8") as f:
                    data = json.load(f)
                data["features"].extend(feats)
            else:
                data = {"type": "FeatureCollection", "features": feats}

            # Write compressed
            with gzip.open(path, "wt", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))  # compact JSON
        buckets.clear()

    buckets = defaultdict(list)
    rows_seen = 0

    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # normalize headers
        headers = {h: h.strip() for h in reader.fieldnames or []}
        lat_key = args.lat_col
        lon_key = args.lon_col

        for row in reader:
            rows_seen += 1
            try:
                lat = float(row[lat_key])
                lon = float(row[lon_key])
            except Exception:
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue

            # build properties (only keep useful columns)
            props = {}
            for k in keep_cols:
                v = row.get(k, "")
                if v is None:
                    v = ""
                props[k] = v

            # feature shared for all zooms (point feature)
            geom = {"type": "Point", "coordinates": [lon, lat]}
            feature = {"type": "Feature", "geometry": geom, "properties": props}

            # assign to all zoom buckets (min..max) so every zoom has points
            for z in range(args.min_zoom, args.max_zoom + 1):
                x, y = lonlat_to_tile(lon, lat, z)
                buckets[(z, x, y)].append(feature)

            # flush periodically to keep RAM bounded
            if rows_seen % args.batch == 0:
                flush_buckets(buckets)

    # final flush
    flush_buckets(buckets)
    print(f"✅ Tiled {rows_seen:,} rows into {args.out} (z {args.min_zoom}..{args.max_zoom})")

if __name__ == "__main__":
    main()
