# Official Flood Extent Source Files

Place official geospatial flood extent files in this folder before running cross-region validation.

Accepted files:

```text
pakistan_2022.geojson
pakistan_2022.zip
mozambique_2023.geojson
mozambique_2023.zip
```

Use either GeoJSON or a zipped ESRI shapefile. A zipped shapefile must include:

```text
.shp
.shx
.dbf
```

Only official UNOSAT, Copernicus EMS, or equivalent official disaster/flood mapping files should be used for publication metrics. Do not place NDWI self-labels, screenshots, news maps, or unofficial flood masks here.

After adding files, run from `backend`:

```text
python scripts\prepare_cross_region_ground_truth.py
python scripts\generate_cross_region_sentinel_predictions.py
python scripts\join_cross_region_scores.py
python scripts\run_cross_region_validation.py
```
