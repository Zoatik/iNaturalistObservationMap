# 🗺️ Observation Map (Tiled Viewer)

This project displays all **622,133 Swiss observations** from `observations_swiss.csv`  
on an interactive map, *without* loading a massive 1 GB HTML file.

Instead of embedding every point, the data is split into **compressed GeoJSON tiles**  
that load dynamically as you pan and zoom — just like Google Maps 🌸

---

Run this once to generate the map tiles:

```bash
python build_point_tiles.py --csv observations_swiss.csv --out tiles --min-zoom 5 --max-zoom 12
```

✅ This creates a folder structure like:
```
tiles/
 ├─ 5/
 │   ├─ 16/
 │   │   ├─ 10.geojson.gz
 │   │   └─ 11.geojson.gz
 ├─ 6/
 │   └─ ...
 └─ 12/
```

Each file contains the observations inside that map tile, compressed with gzip.

---

## 🗺️ Step 2 — Run the viewer

Start a local web server in the project directory:
```bash
python -m http.server 8000
```

Then open in your browser:
👉 [http://localhost:8000/viewer.html](http://localhost:8000/viewer.html)

### Folder layout
```
PythonProject10/
├── build_point_tiles.py
├── viewer.html
├── observations_swiss.csv
└── tiles/
```
