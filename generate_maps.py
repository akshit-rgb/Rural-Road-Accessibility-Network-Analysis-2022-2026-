import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import os
import time

base_dir = r"C:\Users\akshi\Downloads\geospatial_project\chhattisgaher_accisability_analysis"
figures_dir = os.path.join(base_dir, "figures")
os.makedirs(figures_dir, exist_ok=True)

TARGET_CRS = "EPSG:32644"

print("1. Loading base datasets for mapping...")
cg = gpd.read_file(os.path.join(base_dir, "cg_districts_clean.gpkg"), layer="districts")
roads_2022 = gpd.read_file(os.path.join(base_dir, "CG2022.shp")).to_crs(TARGET_CRS)
roads_2026 = gpd.read_file(os.path.join(base_dir, "CG2026.shp")).to_crs(TARGET_CRS)
pmgsy = gpd.read_file(os.path.join(base_dir, "pmgsy_all_schemes.gpkg"), layer="pmgsy_roads")
hab = gpd.read_file(os.path.join(base_dir, "habitations_accessibility.gpkg"), layer="habitations")
dist_density = pd.read_csv(os.path.join(base_dir, "district_road_density_2022_2026.csv"))
agri_summary = pd.read_csv(os.path.join(base_dir, "agri_district_summary.csv"))

# Merge density into cg for choropleth
cg_density = cg.merge(dist_density, on='district_clean', how='left')
cg_density['repr_point'] = cg_density.geometry.representative_point()

# Major district centroids for labeling
cg['repr_point'] = cg.geometry.representative_point()
major_cities = ['Raipur', 'Bilaspur', 'Durg', 'Bastar', 'Surguja', 'Rajnandgaon', 'Korba', 'Raigarh']

# Helper function to add scalebar & north arrow
def add_north_arrow(ax, x=0.07, y=0.92, size=25):
    ax.annotate('N', xy=(x, y), xytext=(x, y-0.06),
                xycoords='axes fraction', textcoords='axes fraction',
                ha='center', va='center', fontsize=13, fontweight='bold',
                arrowprops=dict(facecolor='black', edgecolor='black', width=2.5, headwidth=8))

# ==============================================================================
# MAP 1: Comparative Road Network Evolution (2022 vs 2026)
# ==============================================================================
map1_path = os.path.join(figures_dir, "map_1_road_network_evolution_2022_2026.png")
if not os.path.exists(map1_path):
    print("\nGenerating Map 1: Chhattisgarh Road Network Evolution (2022 vs 2026)...")
    t0 = time.time()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 12), dpi=300, facecolor='#f8f9fa')

# Panel 1: 2022
cg.plot(ax=ax1, color='#f0f2f5', edgecolor='#8c92ac', linewidth=0.8)
# Plot minor roads
minor_2022 = roads_2022[roads_2022['fclass'].isin(['residential', 'unclassified', 'track', 'service'])]
major_2022 = roads_2022[~roads_2022['fclass'].isin(['residential', 'unclassified', 'track', 'service'])]
minor_2022.plot(ax=ax1, color='#a0aec0', linewidth=0.35, alpha=0.7)
major_2022.plot(ax=ax1, color='#1e3a8a', linewidth=0.9, alpha=0.9)

ax1.set_title("2022 OpenStreetMap Road Network\nTotal: 58,947 km (101,620 Segments)", fontsize=13, fontweight='bold', pad=10)
ax1.set_axis_off()
add_north_arrow(ax1)

# Panel 2: 2026
cg.plot(ax=ax2, color='#f0f2f5', edgecolor='#8c92ac', linewidth=0.8)
minor_2026 = roads_2026[roads_2026['fclass'].isin(['residential', 'unclassified', 'track', 'service'])]
major_2026 = roads_2026[~roads_2026['fclass'].isin(['residential', 'unclassified', 'track', 'service'])]
minor_2026.plot(ax=ax2, color='#64748b', linewidth=0.35, alpha=0.7)
major_2026.plot(ax=ax2, color='#0284c7', linewidth=0.9, alpha=0.9)

# Highlight new segments (roads present in 2026 that were not in 2022)
new_osm_ids = set(roads_2026['osm_id']) - set(roads_2022['osm_id'])
new_roads = roads_2026[roads_2026['osm_id'].isin(new_osm_ids)]
new_roads.plot(ax=ax2, color='#dc2626', linewidth=0.7, alpha=0.85, label='New Road Additions (2022-2026)')

ax2.set_title(f"2026 OpenStreetMap Road Network\nTotal: 83,501 km (142,825 Segments) [+24,554 km / +41.7%]", fontsize=13, fontweight='bold', pad=10)
ax2.set_axis_off()
add_north_arrow(ax2)

# Legends
legend_elements_1 = [
    Line2D([0], [0], color='#1e3a8a', lw=2, label='Major Arterials (Trunk/Primary/Secondary/Tertiary)'),
    Line2D([0], [0], color='#a0aec0', lw=1.5, label='Local & Rural Roads (Residential/Unclassified/Tracks)'),
    mpatches.Patch(facecolor='#f0f2f5', edgecolor='#8c92ac', label='District Boundary')
]
ax1.legend(handles=legend_elements_1, loc='lower left', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)

legend_elements_2 = [
    Line2D([0], [0], color='#0284c7', lw=2, label='Existing Arterial Corridors'),
    Line2D([0], [0], color='#64748b', lw=1.5, label='Existing Rural/Local Corridors'),
    Line2D([0], [0], color='#dc2626', lw=2, label='New Road Expansions (41,205 Segments)'),
]
ax2.legend(handles=legend_elements_2, loc='lower left', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)

fig.suptitle("CHHATTISGARH STATE: ROAD NETWORK INFRASTRUCTURE EXPANSION (2022 vs 2026)", fontsize=16, fontweight='bold', y=0.97)
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "map_1_road_network_evolution_2022_2026.png"), dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved map_1_road_network_evolution_2022_2026.png in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 2: PMGSY & PM-JANMAN Schemes Spatial Footprint
# ==============================================================================
print("\nGenerating Map 2: PMGSY Schemes Footprint...")
t0 = time.time()
fig, ax = plt.subplots(figsize=(12, 14), dpi=300, facecolor='#f8f9fa')
cg.plot(ax=ax, color='#f8fafc', edgecolor='#94a3b8', linewidth=0.9)

# Plot district labels
for _, row in cg.iterrows():
    pt = row['repr_point']
    ax.text(pt.x, pt.y, row['district_clean'], fontsize=7.5, color='#475569', ha='center', va='center', weight='semibold')

scheme_styles = {
    'PMGSY-I': {'color': '#1d4ed8', 'lw': 1.1, 'label': 'PMGSY Phase I (3,199 km | 1,704 seg)'},
    'PMGSY-II': {'color': '#0d9488', 'lw': 1.2, 'label': 'PMGSY Phase II (2,190 km | 606 seg)'},
    'PMGSY-III': {'color': '#16a34a', 'lw': 1.2, 'label': 'PMGSY Phase III (5,613 km | 2,565 seg)'},
    'PMGSY-IV': {'color': '#ea580c', 'lw': 1.2, 'label': 'PMGSY Phase IV (5,668 km | 2,296 seg)'},
    'PM-JANMAN': {'color': '#b91c1c', 'lw': 1.4, 'label': 'PM-JANMAN Tribal Roads (3,146 km | 2,250 seg)'},
}

for s_name, style in scheme_styles.items():
    sub = pmgsy[pmgsy['scheme'] == s_name]
    sub.plot(ax=ax, color=style['color'], linewidth=style['lw'], alpha=0.9, label=style['label'])

ax.set_axis_off()
add_north_arrow(ax)
ax.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.95, fontsize=10.5, title='Rural Connectivity Schemes', title_fontproperties={'weight': 'bold', 'size': 11.5})
ax.set_title("PMGSY & PM-JANMAN RURAL ROAD SCHEME NETWORK IN CHHATTISGARH\nTotal Scheme Footprint: 19,816 km across 9,421 Segments", fontsize=15, fontweight='bold', pad=15)
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "map_2_pmgsy_schemes_chhattisgarh.png"), dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved map_2_pmgsy_schemes_chhattisgarh.png in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 3: Habitation Accessibility & Connectivity Classification
# ==============================================================================
print("\nGenerating Map 3: Habitation Accessibility Map...")
t0 = time.time()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 13), dpi=300, facecolor='#f8f9fa')

tier_colors = {
    '<500m (High)': '#15803d',
    '500m-1km (Moderate)': '#ca8a04',
    '1km-2km (Low)': '#ea580c',
    '>2km (Isolated)': '#b91c1c'
}

# Left: 2022 Status
cg.plot(ax=ax1, color='#f1f5f9', edgecolor='#94a3b8', linewidth=0.8)
for tier, col in tier_colors.items():
    sub = hab[hab['tier_2022'] == tier]
    ax1.scatter(sub.geometry.x, sub.geometry.y, c=col, s=3.5, alpha=0.75, label=f"{tier} ({len(sub):,} habs | {len(sub)/len(hab)*100:.1f}%)")

ax1.set_axis_off()
add_north_arrow(ax1)
ax1.set_title("2022 Habitation Accessibility Status\n42.1% High Access (<500m) | 29.2% Isolated (>2km)", fontsize=13, fontweight='bold', pad=10)
ax1.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.95, fontsize=9.5, title='Distance to Nearest Road', title_fontproperties={'weight': 'bold'})

# Right: Combined 2026 + PMGSY Status
cg.plot(ax=ax2, color='#f1f5f9', edgecolor='#94a3b8', linewidth=0.8)
for tier, col in tier_colors.items():
    sub = hab[hab['tier_comb'] == tier]
    ax2.scatter(sub.geometry.x, sub.geometry.y, c=col, s=3.5, alpha=0.75, label=f"{tier} ({len(sub):,} habs | {len(sub)/len(hab)*100:.1f}%)")

ax2.set_axis_off()
add_north_arrow(ax2)
ax2.set_title("2026 + PMGSY Integrated Accessibility Status\n74.0% High Access (<500m) | Only 4.6% Isolated (>2km)", fontsize=13, fontweight='bold', pad=10)
ax2.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.95, fontsize=9.5, title='Distance to Nearest Road', title_fontproperties={'weight': 'bold'})

fig.suptitle("SPATIAL ACCESSIBILITY TRANSFORMATION OF 29,831 RURAL HABITATIONS IN CHHATTISGARH\nComparison of Baseline (2022) vs Fully Integrated Network (2026 OSM + PMGSY Schemes)", fontsize=16, fontweight='bold', y=0.97)
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "map_3_habitation_accessibility.png"), dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved map_3_habitation_accessibility.png in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 4: District Road Density Choropleth (2022 vs 2026)
# ==============================================================================
print("\nGenerating Map 4: District Road Density Choropleth...")
t0 = time.time()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 12), dpi=300, facecolor='#f8f9fa')

vmin = 0.15
vmax = 1.25

p1 = cg_density.plot(column='density_2022_km_per_sqkm', ax=ax1, cmap='YlGnBu', vmin=vmin, vmax=vmax,
                     edgecolor='#334155', linewidth=0.8)
ax1.set_axis_off()
add_north_arrow(ax1)
ax1.set_title("2022 Road Density by District (km / km²)\nState Average: 0.44 km/km²", fontsize=13, fontweight='bold', pad=10)
for _, row in cg_density.iterrows():
    pt = row['repr_point']
    ax1.text(pt.x, pt.y, f"{row['district_clean']}\n{row['density_2022_km_per_sqkm']:.2f}",
             fontsize=7, ha='center', va='center', weight='bold', color='#0f172a')

p2 = cg_density.plot(column='density_2026_km_per_sqkm', ax=ax2, cmap='YlGnBu', vmin=vmin, vmax=vmax,
                     edgecolor='#334155', linewidth=0.8)
ax2.set_axis_off()
add_north_arrow(ax2)
ax2.set_title("2026 Road Density by District (km / km²)\nState Average: 0.62 km/km² [+41.7%]", fontsize=13, fontweight='bold', pad=10)
for _, row in cg_density.iterrows():
    pt = row['repr_point']
    ax2.text(pt.x, pt.y, f"{row['district_clean']}\n{row['density_2026_km_per_sqkm']:.2f}",
             fontsize=7, ha='center', va='center', weight='bold', color='#0f172a')

cbar_ax = fig.add_axes([0.3, 0.05, 0.4, 0.025])
sm = plt.cm.ScalarMappable(cmap='YlGnBu', norm=plt.Normalize(vmin=vmin, vmax=vmax))
cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal')
cbar.set_label('Road Density (Kilometers of Road per Square Kilometer of Land Area)', fontweight='bold', fontsize=11)

fig.suptitle("CHHATTISGARH DISTRICT ROAD DENSITY COMPARATIVE CHOROPLETH (2022 vs 2026)", fontsize=16, fontweight='bold', y=0.97)
plt.tight_layout(rect=[0, 0.08, 1, 0.95])
fig.savefig(os.path.join(figures_dir, "map_4_district_road_density_choropleth.png"), dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved map_4_district_road_density_choropleth.png in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 5: Agricultural Farmland & Transport Connectivity Map
# ==============================================================================
print("\nGenerating Map 5: Agricultural Farmland Connectivity Map...")
t0 = time.time()
# Aggregated agri into cg
agri_map = {
    'Gaurella Pendra Marwahi': 'Gaurela-Pendra-Marwahi',
    'Khairgarh Chhuikhadan Gandai': 'Rajnandgaon',
    'Mohla Manpur Ambagarh Chouki': 'Rajnandgaon',
    'Manendragarh Chirimiri Bharatpur': 'Koriya',
    'Sakti': 'Janjgir-Champa',
    'Sarangarh Bilaigarh': 'Raigarh',
    'Korea': 'Koriya'
}
agri_summary['district_parent'] = agri_summary['district'].map(agri_map).fillna(agri_summary['district'])
agri_d28 = agri_summary.groupby('district_parent').agg(
    total_area_ha=('total_area_ha', 'sum'),
    field_count=('field_count', 'sum')
).reset_index()

cg_agri = cg.merge(agri_d28, left_on='district_clean', right_on='district_parent', how='left')
cg_agri['agri_area_k_ha'] = cg_agri['total_area_ha'] / 1000.0
cg_agri['repr_point'] = cg_agri.geometry.representative_point()

fig, ax = plt.subplots(figsize=(13, 14), dpi=300, facecolor='#f8f9fa')
cg_agri.plot(column='agri_area_k_ha', ax=ax, cmap='Greens', edgecolor='#1e293b', linewidth=0.8,
             legend=True, legend_kwds={'label': 'Total Agricultural Land Area (Thousand Hectares)', 'orientation': 'horizontal', 'shrink': 0.6, 'pad': 0.03})

# Overlay major road network corridors
major_roads = roads_2026[roads_2026['fclass'].isin(['trunk', 'primary', 'secondary'])]
major_roads.plot(ax=ax, color='#b91c1c', linewidth=1.1, alpha=0.8, label='Arterial Transport Corridors')

# Overlay PMGSY rural connectors
pmgsy.plot(ax=ax, color='#2563eb', linewidth=0.7, alpha=0.6, label='PMGSY Farm-to-Market Feeder Roads')

for _, row in cg_agri.iterrows():
    pt = row['repr_point']
    ax.text(pt.x, pt.y, f"{row['district_clean']}\n{row['agri_area_k_ha']:.1f}k ha",
             fontsize=7.5, ha='center', va='center', weight='bold', color='#022c22')

ax.set_axis_off()
add_north_arrow(ax)
ax.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.95, fontsize=10.5)
ax.set_title("CHHATTISGARH AGRICULTURAL LAND & FARM-TO-MARKET ROAD CORRIDORS\nTotal Farmland Analyzed: 14.4 Million Fields across 1.48 Million Hectares", fontsize=15, fontweight='bold', pad=15)
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "map_5_agricultural_road_accessibility.png"), dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved map_5_agricultural_road_accessibility.png in {time.time()-t0:.1f}s")

print("All 5 high-resolution maps successfully generated!")
