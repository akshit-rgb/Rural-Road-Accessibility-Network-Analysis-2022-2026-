import os
from pathlib import Path
import time
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.strtree import STRtree

base_dir = Path(__file__).resolve().parent
TARGET_CRS = "EPSG:32644"  # UTM Zone 44N in meters

print("Loading Habitations...")
hab_zip = os.path.join(base_dir, "Habitation_Chhattisgarh.zip")
target_hab = f"zip://{hab_zip}!Habitation.shp"
hab = gpd.read_file(target_hab)
print(f"Raw habitations: {len(hab):,}")

# Filter out null or empty geometries
hab = hab[hab.geometry.notna() & ~hab.geometry.is_empty].copy().reset_index(drop=True)
print(f"Valid habitations: {len(hab):,}. Total recorded population: {hab['TOT_POPULA'].sum():,}")
hab_utm = hab.to_crs(TARGET_CRS)

print("Loading Clean Districts...")
cg = gpd.read_file(os.path.join(base_dir, "cg_districts_clean.gpkg"), layer="districts")

print("Spatial join Habitations with Districts using sjoin_nearest...")
hab_dist = gpd.sjoin_nearest(hab_utm, cg[['district_clean', 'geometry']], how='left')
hab_dist = hab_dist.drop_duplicates(subset=['HAB_ID', 'geometry']).reset_index(drop=True)

print("Loading Roads 2022...")
roads_2022 = gpd.read_file(os.path.join(base_dir, "CG2022.shp"))
roads_2022_utm = roads_2022.to_crs(TARGET_CRS)
roads_2022_utm = roads_2022_utm[roads_2022_utm.geometry.notna() & ~roads_2022_utm.geometry.is_empty].reset_index(drop=True)

print("Loading Roads 2026...")
roads_2026 = gpd.read_file(os.path.join(base_dir, "CG2026.shp"))
roads_2026_utm = roads_2026.to_crs(TARGET_CRS)
roads_2026_utm = roads_2026_utm[roads_2026_utm.geometry.notna() & ~roads_2026_utm.geometry.is_empty].reset_index(drop=True)

print("Loading PMGSY Roads...")
pmgsy = gpd.read_file(os.path.join(base_dir, "pmgsy_all_schemes.gpkg"), layer="pmgsy_roads")
pmgsy = pmgsy[pmgsy.geometry.notna() & ~pmgsy.geometry.is_empty].reset_index(drop=True)

print("Creating Combined 2026 + PMGSY Network...")
combined_geom = pd.concat([roads_2026_utm['geometry'], pmgsy['geometry']], ignore_index=True)
combined_geom = combined_geom[combined_geom.notna() & ~combined_geom.is_empty].reset_index(drop=True)

# Build spatial index trees
print("\nBuilding Spatial Index Trees (STRtree)...")
tree_2022 = STRtree(roads_2022_utm.geometry.values)
tree_2026 = STRtree(roads_2026_utm.geometry.values)
tree_pmgsy = STRtree(pmgsy.geometry.values)
tree_comb = STRtree(combined_geom.values)

hab_pts = hab_dist.geometry.values

print("Calculating distance to nearest 2022 road...")
t0 = time.time()
idx_2022 = tree_2022.nearest(hab_pts)
hab_dist['dist_road_2022_m'] = shapely.distance(hab_pts, roads_2022_utm.geometry.values[idx_2022])
print(f"2022 distances done in {time.time()-t0:.2f}s")

print("Calculating distance to nearest 2026 road...")
t0 = time.time()
idx_2026 = tree_2026.nearest(hab_pts)
hab_dist['dist_road_2026_m'] = shapely.distance(hab_pts, roads_2026_utm.geometry.values[idx_2026])
print(f"2026 distances done in {time.time()-t0:.2f}s")

print("Calculating distance to nearest PMGSY road...")
t0 = time.time()
idx_pm = tree_pmgsy.nearest(hab_pts)
hab_dist['dist_pmgsy_m'] = shapely.distance(hab_pts, pmgsy.geometry.values[idx_pm])
print(f"PMGSY distances done in {time.time()-t0:.2f}s")

print("Calculating distance to nearest Combined (2026 + PMGSY) road...")
t0 = time.time()
idx_cb = tree_comb.nearest(hab_pts)
hab_dist['dist_combined_m'] = shapely.distance(hab_pts, combined_geom.values[idx_cb])
print(f"Combined distances done in {time.time()-t0:.2f}s")

# Define accessibility tiers
bins = [-np.inf, 500, 1000, 2000, np.inf]
labels = ['<500m (High)', '500m-1km (Moderate)', '1km-2km (Low)', '>2km (Isolated)']

hab_dist['tier_2022'] = pd.cut(hab_dist['dist_road_2022_m'], bins=bins, labels=labels)
hab_dist['tier_2026'] = pd.cut(hab_dist['dist_road_2026_m'], bins=bins, labels=labels)
hab_dist['tier_comb'] = pd.cut(hab_dist['dist_combined_m'], bins=bins, labels=labels)

# Save processed habitations
cols_to_save = ['HAB_ID', 'HAB_NAME', 'TOT_POPULA', 'district_clean', 
                'dist_road_2022_m', 'dist_road_2026_m', 'dist_pmgsy_m', 'dist_combined_m',
                'tier_2022', 'tier_2026', 'tier_comb', 'geometry']
hab_dist_clean = hab_dist[cols_to_save].copy()
hab_dist_clean.to_file(os.path.join(base_dir, "habitations_accessibility.gpkg"), layer="habitations", driver="GPKG")

# Summary comparisons
print("\n=== HABITATION ACCESSIBILITY BREAKDOWN (COUNTS & POPULATION) ===")
summary_rows = []
total_habs = len(hab_dist)
total_pop = hab_dist['TOT_POPULA'].sum()

for col_name, label_title in [('tier_2022', '2022 OSM'), ('tier_2026', '2026 OSM'), ('tier_comb', '2026 + PMGSY')]:
    cnt = hab_dist.groupby(col_name, observed=False)['HAB_ID'].count()
    cnt_pct = (cnt / total_habs) * 100
    pop = hab_dist.groupby(col_name, observed=False)['TOT_POPULA'].sum()
    pop_pct = (pop / total_pop) * 100
    for tier in labels:
        summary_rows.append({
            'Network': label_title,
            'Accessibility_Tier': tier,
            'Habitations_Count': int(cnt[tier]),
            'Habitations_Pct': round(float(cnt_pct[tier]), 2),
            'Population': int(pop[tier]),
            'Population_Pct': round(float(pop_pct[tier]), 2)
        })

hab_summary_df = pd.DataFrame(summary_rows)
hab_summary_df.to_csv(os.path.join(base_dir, "habitation_accessibility_summary.csv"), index=False)
print(hab_summary_df.to_string())

# District level accessibility summary
dist_hab = hab_dist.groupby('district_clean').agg(
    total_habitations=('HAB_ID', 'count'),
    total_population=('TOT_POPULA', 'sum'),
    hab_under_500m_2022=('dist_road_2022_m', lambda s: (s <= 500).sum()),
    hab_under_500m_2026=('dist_road_2026_m', lambda s: (s <= 500).sum()),
    hab_under_500m_comb=('dist_combined_m', lambda s: (s <= 500).sum()),
    mean_dist_2022_m=('dist_road_2022_m', 'mean'),
    mean_dist_2026_m=('dist_road_2026_m', 'mean'),
    mean_dist_comb_m=('dist_combined_m', 'mean')
).reset_index()

# District population under 500m
for d in dist_hab['district_clean']:
    sub = hab_dist[hab_dist['district_clean'] == d]
    dist_hab.loc[dist_hab['district_clean'] == d, 'pop_under_500m_2022'] = sub.loc[sub['dist_road_2022_m'] <= 500, 'TOT_POPULA'].sum()
    dist_hab.loc[dist_hab['district_clean'] == d, 'pop_under_500m_2026'] = sub.loc[sub['dist_road_2026_m'] <= 500, 'TOT_POPULA'].sum()
    dist_hab.loc[dist_hab['district_clean'] == d, 'pop_under_500m_comb'] = sub.loc[sub['dist_combined_m'] <= 500, 'TOT_POPULA'].sum()

dist_hab['pct_hab_connected_2022'] = (dist_hab['hab_under_500m_2022'] / dist_hab['total_habitations']) * 100
dist_hab['pct_hab_connected_2026'] = (dist_hab['hab_under_500m_2026'] / dist_hab['total_habitations']) * 100
dist_hab['pct_hab_connected_comb'] = (dist_hab['hab_under_500m_comb'] / dist_hab['total_habitations']) * 100
dist_hab['pct_pop_connected_2022'] = (dist_hab['pop_under_500m_2022'] / dist_hab['total_population']) * 100
dist_hab['pct_pop_connected_2026'] = (dist_hab['pop_under_500m_2026'] / dist_hab['total_population']) * 100
dist_hab['pct_pop_connected_comb'] = (dist_hab['pop_under_500m_comb'] / dist_hab['total_population']) * 100

dist_hab.to_csv(os.path.join(base_dir, "district_habitation_accessibility.csv"), index=False)
print("\nSaved habitations_accessibility.gpkg & district_habitation_accessibility.csv successfully!")
