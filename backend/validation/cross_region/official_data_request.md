# Official Data Request Template

Use this message to request the missing official geospatial flood extent files from UNOSAT, Copernicus EMS, OCHA/HDX, or another official source custodian.

```text
Hello,

I am working on an academic flood detection validation study and need official geospatial flood extent data for patch-level validation.

Could you please provide downloadable GIS data, preferably GeoJSON or ESRI shapefile, for:

1. Pakistan 2022 floods:
   "Satellite detected water extents between 03 and 23 August 2022 over Pakistan"

2. Mozambique Cyclone Freddy 2023 floods:
   "Satellite detected water extent over Sofala and Zambezia Provinces, Mozambique as of 13 Mar. 2023"

The data will be used only for academic validation against model predictions, with attribution to the official source.

Thank you.
```

Requested formats:

- GeoJSON
- ESRI shapefile zipped with `.shp`, `.shx`, and `.dbf`

Expected local filenames after receipt:

```text
backend/validation/cross_region/official_sources/pakistan_2022.geojson
backend/validation/cross_region/official_sources/pakistan_2022.zip
backend/validation/cross_region/official_sources/mozambique_2023.geojson
backend/validation/cross_region/official_sources/mozambique_2023.zip
```
