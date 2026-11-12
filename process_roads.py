import os
from pathlib import Path
import time
import zipfile
import geopandas as gpd
import numpy as np
import pandas as pd

base_dir = Path(__file__).resolve().parent
TARGET_CRS = "EPSG:32644"  # UTM Zone 44N, in meters

DISTRICT_NAME_MAP = {
    'B>LOD': 'Balod',
    'BALODA B>Z>R': 'Baloda Bazar',
    'BALR>MPUR': 'Balrampur',
    'BASTAR': 'Bastar',
    'BEMET>RA': 'Bemetara',
    'B|J>PUR': 'Bijapur',
    'BIL>SPUR': 'Bilaspur',
    'DAKSHIN BASTAR DANTEW>DA': 'Dantewada',
    'DHAMTARI': 'Dhamtari',
    'DURG': 'Durg',
    'GARIY>BAND': 'Gariaband',
    'GAURELA-PENDRA-MARWAHI': 'Gaurela-Pendra-Marwahi',
    'J>NJG|R - CH>MPA': 'Janjgir-Champa',
    'JASHPUR': 'Jashpur',
    'KAB|RDH>M': 'Kabirdham',
    'KONDAGAON': 'Kondagaon',
    'KORBA': 'Korba',
    'KOREA': 'Koriya',
    'MAH>SAMUND': 'Mahasamund',
    'MUNGELI': 'Mungeli',
    'N>R>INPUR': 'Narayanpur',
    'R>J NANDGAON': 'Rajnandgaon',
    'RAIGARH': 'Raigarh',
    'RAIPUR': 'Raipur',
    'S@RAJPUR': 'Surajpur',
    'SUKMA': 'Sukma',
    'SURGUJA': 'Surguja',
    'UTTAR BASTAR K>NKER': 'Kanker',
}

print("1. Loading districts (cg.shp)...")
cg = gpd.read_file(os.path.join(base_dir, "cg.shp"))
cg['district_clean'] = cg['District'].map(DISTRICT_NAME_MAP).fillna(cg['District'])
cg_utm = cg.to_crs(TARGET_CRS)
cg_utm['area_sqkm'] = cg_utm.geometry.area / 1e6
print(f"Loaded {len(cg_utm)} districts. Total area: {cg_utm['area_sqkm'].sum():,.2f} sq km")

# Save cleaned districts
cg_clean = cg_utm[['district_clean', 'State_LGD', 'DISTRICT_L', 'area_sqkm', 'geometry']].copy()
cg_clean.to_file(os.path.join(base_dir, "cg_districts_clean.gpkg"), layer="districts", driver="GPKG")

print("\n2. Processing 2022 OSM Roads...")
t0 = time.time()
roads_2022 = gpd.read_file(os.path.join(base_dir, "CG2022.shp"))
roads_2022 = roads_2022.to_crs(TARGET_CRS)
roads_2022['length_km'] = roads_2022.geometry.length / 1000.0
print(f"2022 roads: {len(roads_2022):,} segments, total length: {roads_2022['length_km'].sum():,.2f} km in {time.time()-t0:.1f}s")

print("\n3. Processing 2026 OSM Roads...")
t0 = time.time()
roads_2026 = gpd.read_file(os.path.join(base_dir, "CG2026.shp"))
roads_2026 = roads_2026.to_crs(TARGET_CRS)
roads_2026['length_km'] = roads_2026.geometry.length / 1000.0
print(f"2026 roads: {len(roads_2026):,} segments, total length: {roads_2026['length_km'].sum():,.2f} km in {time.time()-t0:.1f}s")

# Compare road classes
summary_2022 = roads_2022.groupby('fclass').agg(
    segments_2022=('osm_id', 'count'),
    length_km_2022=('length_km', 'sum')
)
summary_2026 = roads_2026.groupby('fclass').agg(
    segments_2026=('osm_id', 'count'),
    length_km_2026=('length_km', 'sum')
)

class_comp = pd.merge(summary_2022, summary_2026, left_index=True, right_index=True, how='outer').fillna(0)
class_comp['length_growth_km'] = class_comp['length_km_2026'] - class_comp['length_km_2022']
class_comp['length_growth_pct'] = (class_comp['length_growth_km'] / class_comp['length_km_2022'].replace(0, np.nan)) * 100
class_comp['segment_growth'] = class_comp['segments_2026'] - class_comp['segments_2022']
class_comp = class_comp.sort_values(by='length_km_2026', ascending=False)
class_comp.to_csv(os.path.join(base_dir, "road_class_comparison_2022_2026.csv"))
print("\nTop 10 Road Classes Comparison (km):")
print(class_comp[['length_km_2022', 'length_km_2026', 'length_growth_km', 'length_growth_pct']].head(10).round(2))

print("\n4. District-level Road Aggregation (Spatial Join)...")
# Spatial overlay to find road length by district
roads_2022_dist = gpd.sjoin(roads_2022[['osm_id', 'fclass', 'length_km', 'geometry']], 
                            cg_clean[['district_clean', 'area_sqkm', 'geometry']], 
                            how='inner', predicate='intersects')
dist_2022 = roads_2022_dist.groupby('district_clean').agg(
    roads_km_2022=('length_km', 'sum'),
    roads_count_2022=('osm_id', 'count')
).reset_index()

roads_2026_dist = gpd.sjoin(roads_2026[['osm_id', 'fclass', 'length_km', 'geometry']], 
                            cg_clean[['district_clean', 'area_sqkm', 'geometry']], 
                            how='inner', predicate='intersects')
dist_2026 = roads_2026_dist.groupby('district_clean').agg(
    roads_km_2026=('length_km', 'sum'),
    roads_count_2026=('osm_id', 'count')
).reset_index()

dist_roads = cg_clean[['district_clean', 'area_sqkm']].copy()
dist_roads = dist_roads.merge(dist_2022, on='district_clean', how='left').merge(dist_2026, on='district_clean', how='left')
dist_roads['density_2022_km_per_sqkm'] = dist_roads['roads_km_2022'] / dist_roads['area_sqkm']
dist_roads['density_2026_km_per_sqkm'] = dist_roads['roads_km_2026'] / dist_roads['area_sqkm']
dist_roads['density_growth'] = dist_roads['density_2026_km_per_sqkm'] - dist_roads['density_2022_km_per_sqkm']
dist_roads['length_growth_km'] = dist_roads['roads_km_2026'] - dist_roads['roads_km_2022']
dist_roads['length_growth_pct'] = (dist_roads['length_growth_km'] / dist_roads['roads_km_2022']) * 100

dist_roads = dist_roads.sort_values(by='density_2026_km_per_sqkm', ascending=False)
dist_roads.to_csv(os.path.join(base_dir, "district_road_density_2022_2026.csv"), index=False)
print("Saved district_road_density_2022_2026.csv")

print("\n5. Processing PMGSY & PM-JANMAN Schemes...")
pmgsy_schemes = [
    ("PMGSY-I", "Proposal_PMGSY-I_Chhattisgarh.zip", "Proposal_PMGSY-I.shp"),
    ("PMGSY-II", "Proposal_PMGSY-II_Chhattisgarh.zip", "Proposal_PMGSY-II.shp"),
    ("PMGSY-III", "Proposal_PMGSY-III_Chhattisgarh.zip", "Proposal_PMGSY-III.shp"),
    ("PMGSY-IV", "Proposal_PMGSY-IV_Chhattisgarh.zip", "Proposal_PMGSY-IV.shp"),
    ("PM-JANMAN", "Proposal_PM-JANMAN_Chhattisgarh.zip", "Proposal_PM-JANMAN.shp"),
]

all_pmgsy_list = []
for scheme_name, zip_file, shp_name in pmgsy_schemes:
    zpath = os.path.join(base_dir, zip_file)
    target = f"zip://{zpath}!{shp_name}"
    gdf = gpd.read_file(target)
    gdf['scheme'] = scheme_name
    gdf = gdf.to_crs(TARGET_CRS)
    gdf['calc_length_km'] = gdf.geometry.length / 1000.0
    if 'PROPOSED_L' in gdf.columns:
        gdf['PROPOSED_L'] = pd.to_numeric(gdf['PROPOSED_L'], errors='coerce')
    all_pmgsy_list.append(gdf)
    print(f"  {scheme_name}: {len(gdf)} segments, total calc length: {gdf['calc_length_km'].sum():.2f} km")

all_pmgsy = gpd.GeoDataFrame(pd.concat(all_pmgsy_list, ignore_index=True), crs=TARGET_CRS)
all_pmgsy.to_file(os.path.join(base_dir, "pmgsy_all_schemes.gpkg"), layer="pmgsy_roads", driver="GPKG")

# Summary by scheme
pmgsy_summary = all_pmgsy.groupby('scheme').agg(
    total_projects=('MRL_ID', 'nunique'),
    total_segments=('MRL_ID', 'count'),
    total_proposed_len_km=('PROPOSED_L', 'sum'),
    total_calc_len_km=('calc_length_km', 'sum'),
    avg_project_len_km=('calc_length_km', 'mean')
).reset_index()
pmgsy_summary.to_csv(os.path.join(base_dir, "pmgsy_phase_summary.csv"), index=False)
print("\nPMGSY Summary by Phase:")
print(pmgsy_summary.to_string())

# Spatial join PMGSY with districts
pmgsy_dist = gpd.sjoin(all_pmgsy, cg_clean[['district_clean', 'geometry']], how='inner', predicate='intersects')
pmgsy_dist_summary = pmgsy_dist.groupby(['district_clean', 'scheme']).agg(
    projects=('MRL_ID', 'nunique'),
    calc_len_km=('calc_length_km', 'sum')
).reset_index()
pmgsy_dist_summary.to_csv(os.path.join(base_dir, "pmgsy_district_scheme_summary.csv"), index=False)

print("\nProcess roads complete!")
