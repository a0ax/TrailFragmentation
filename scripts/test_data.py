import geopandas as gpd
import pandas as pd

# Load the data
gdf = gpd.read_file('data/boundaries/ALL_SwissReserve.shp')

# 1. Filter to only polygon geometries (skip points/lines)
gdf = gdf[gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])].copy()
print(f"After filtering polygons: {len(gdf)} features")

# 2. Reproject to a Swiss projected CRS (LV95 - EPSG:2056) for accurate area calculations
gdf = gdf.to_crs('EPSG:2056')
print(f"Reprojected to EPSG:2056 (LV95)")

# 3. Check for meaningful protected area categories
print("\nProtected area types (Res_Type):")
print(gdf['Res_Type'].value_counts())