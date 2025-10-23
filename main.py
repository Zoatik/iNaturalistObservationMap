#!/usr/bin/env python3
"""
make_observation_map.py — Clustered map with clickable iNaturalist links 💙
"""

import argparse
import html
import pandas as pd
import folium
from folium.plugins import MarkerCluster

def parse_args():
    p = argparse.ArgumentParser(description="Clustered map with popups for observation points.")
    p.add_argument("--csv", required=True, help="Input CSV (needs latitude, longitude; optional: observation_uuid, taxon_id, quality_grade, observed_on, observer_id, positional_accuracy)")
    p.add_argument("--out", default="observations_clustered_popups.html", help="Output HTML map path")
    p.add_argument("--max-points", type=int, default=30000, help="Max points to render (sampling keeps HTML small)")
    p.add_argument("--zoom", type=int, default=7, help="Initial zoom level")
    p.add_argument("--lat-col", default="latitude")
    p.add_argument("--lon-col", default="longitude")
    p.add_argument("--no-sample", action="store_true", help="Disable sampling (not recommended for huge files)")
    return p.parse_args()

def gv(row, col, default="—"):
    try:
        val = row[col]
        if pd.isna(val):
            return default
        return val
    except Exception:
        return default

def main():
    args = parse_args()

    df = pd.read_csv(args.csv)
    df = df.rename(columns={c: c.strip() for c in df.columns})

    lat_col, lon_col = args.lat_col, args.lon_col
    if lat_col not in df.columns or lon_col not in df.columns:
        raise SystemExit(f"CSV must contain '{lat_col}' and '{lon_col}' columns.")

    df = df.dropna(subset=[lat_col, lon_col])
    df = df[(df[lat_col].between(-90, 90)) & (df[lon_col].between(-180, 180))]

    total_points = len(df)
    if total_points == 0:
        raise SystemExit("No valid coordinates found after filtering.")

    if not args.no_sample and total_points > args.max_points:
        df = df.sample(args.max_points, random_state=39).reset_index(drop=True)
    used_points = len(df)

    center_lat = float(df[lat_col].mean())
    center_lon = float(df[lon_col].mean())

    m = folium.Map(location=[center_lat, center_lon], zoom_start=args.zoom, tiles="OpenStreetMap")
    cluster = MarkerCluster(name="Observations").add_to(m)

    for _, row in df.iterrows():
        try:
            lat = float(row[lat_col])
            lon = float(row[lon_col])
        except Exception:
            continue

        # fetch values (escaped for safety)
        quality     = html.escape(str(gv(row, "quality_grade")))
        taxon_id    = gv(row, "taxon_id")
        observed_on = html.escape(str(gv(row, "observed_on")))
        obs_id      = html.escape(str(gv(row, "observation_uuid")))
        acc         = html.escape(str(gv(row, "positional_accuracy")))
        observer    = html.escape(str(gv(row, "observer_id")))

        # show the raw taxon_id as text (escaped), but build a clickable link if present
        taxon_id_txt = html.escape("" if taxon_id == "—" else str(taxon_id))
        taxon_link_html = ""
        if taxon_id not in (None, "—", ""):
            # don’t over-validate; just link it
            taxon_link_html = f'<br><a href="https://www.inaturalist.org/taxa/{int(taxon_id)}" target="_blank" rel="noopener">View on iNaturalist</a>'

        popup_html = (
            f"<b>Observation:</b> {obs_id or '—'}<br>"
            f"Taxon ID: {taxon_id_txt}{taxon_link_html}<br>"
            f"Quality: {quality or '—'}<br>"
            f"Observed on: {observed_on or '—'}<br>"
            f"Observer ID: {observer or '—'}<br>"
            f"Positional accuracy: {acc or '—'} m<br>"
            f"Lat, Lon: {lat:.5f}, {lon:.5f}"
        )

        iframe = folium.IFrame(html=popup_html, width=320, height=170)
        popup = folium.Popup(iframe, max_width=340)

        folium.Marker(
            location=[lat, lon],
            popup=popup,
            tooltip=f"Taxon {taxon_id_txt or '—'} • {quality or '—'}",
            icon=folium.Icon(icon="info-sign")
        ).add_to(cluster)

    m.save(args.out)
    print(f"🌸 Map saved: {args.out}")
    print(f"   Points in CSV: {total_points:,}")
    print(f"   Points rendered: {used_points:,} (sampling={'OFF' if args.no_sample else 'ON'})")

if __name__ == "__main__":
    main()
