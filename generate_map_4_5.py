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

print("Loading base datasets...")
cg = gpd.read_file(os.path.join(base_dir, "cg_districts_clean.gpkg"), layer="districts")
roads_2026 = gpd.read_file(os.path.join(base_dir, "CG2026.shp")).to_crs(TARGET_CRS)
pmgsy = gpd.read_file(os.path.join(base_dir, "pmgsy_all_schemes.gpkg"), layer="pmgsy_roads")
dist_density = pd.read_csv(os.path.join(base_dir, "district_road_density_2022_2026.csv"))
agri_summary = pd.read_csv(os.path.join(base_dir, "agri_district_summary.csv"))

cg_density = cg.merge(dist_density, on='district_clean', how='left')
cg_density['repr_point'] = cg_density.geometry.representative_point()

def add_north_arrow(ax, x=0.07, y=0.92, size=25):
    ax.annotate('N', xy=(x, y), xytext=(x, y-0.06),
                xycoords='axes fraction', textcoords='axes fraction',
                ha='center', va='center', fontsize=13, fontweight='bold',
                arrowprops=dict(facecolor='black', edgecolor='black', width=2.5, headwidth=8))

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
cg_agri.plot(column='agri_area_k_ha', ax=ax, cmap='YlOrBr', edgecolor='#1e293b', linewidth=0.8,
             legend=True, legend_kwds={'label': 'Total Agricultural Land Area (Thousand Hectares)', 'orientation': 'horizontal', 'shrink': 0.6, 'pad': 0.03})

# Overlay major road network corridors
major_roads = roads_2026[roads_2026['fclass'].isin(['trunk', 'primary', 'secondary'])]
major_roads.plot(ax=ax, color='#b91c1c', linewidth=1.1, alpha=0.85, label='Arterial Transport Corridors (Trunk/Primary/Secondary)')

# Overlay PMGSY rural connectors
pmgsy.plot(ax=ax, color='#2563eb', linewidth=0.75, alpha=0.7, label='PMGSY Rural Feeder Corridors (Phases I-IV & JANMAN)')

for _, row in cg_agri.iterrows():
    pt = row['repr_point']
    ax.text(pt.x, pt.y, f"{row['district_clean']}\n{row['agri_area_k_ha']:.1f}k ha",
             fontsize=7.5, ha='center', va='center', weight='bold', color='#1e293b')

ax.set_axis_off()
add_north_arrow(ax)
ax.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.95, fontsize=10.5)
ax.set_title("CHHATTISGARH AGRICULTURAL FARMLAND & TRANSPORT CORRIDORS\nTotal Farmland Analyzed: 14.4 Million Fields across 1.48 Million Hectares", fontsize=15, fontweight='bold', pad=15)
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "map_5_agricultural_road_accessibility.png"), dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f"Saved map_5_agricultural_road_accessibility.png in {time.time()-t0:.1f}s")

# ==============================================================================
# MAP 6: Executive Master Summary Infographic Dashboard
# ==============================================================================
print("\nGenerating Map 6: Executive Master Summary Dashboard Map...")
t0 = time.time()
fig = plt.figure(figsize=(24, 16), dpi=300, facecolor='#f1f5f9')
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], width_ratios=[1, 1, 1], hspace=0.22, wspace=0.15)

# Subplot 1: 2026 Road Network + PMGSY
ax_net = fig.add_subplot(gs[0, 0])
cg.plot(ax=ax_net, color='#ffffff', edgecolor='#64748b', linewidth=0.7)
roads_2026.plot(ax=ax_net, color='#94a3b8', linewidth=0.3, alpha=0.6)
pmgsy.plot(ax=ax_net, color='#dc2626', linewidth=0.8, alpha=0.85)
ax_net.set_title("A. State Road Infrastructure (2026)\n83,501 km OSM + 19,816 km PMGSY", fontweight='bold', fontsize=12)
ax_net.set_axis_off()
add_north_arrow(ax_net, x=0.1, y=0.9)

# Subplot 2: PMGSY Schemes Footprint
ax_pm = fig.add_subplot(gs[0, 1])
cg.plot(ax=ax_pm, color='#ffffff', edgecolor='#64748b', linewidth=0.7)
pmgsy[pmgsy['scheme'] != 'PM-JANMAN'].plot(ax=ax_pm, color='#2563eb', linewidth=0.8, alpha=0.8, label='PMGSY I-IV (16,670 km)')
pmgsy[pmgsy['scheme'] == 'PM-JANMAN'].plot(ax=ax_pm, color='#e11d48', linewidth=1.1, alpha=0.9, label='PM-JANMAN Tribal (3,146 km)')
ax_pm.set_title("B. PMGSY & PM-JANMAN Scheme Reach\nPrioritizing Tribal & Remote Belts", fontweight='bold', fontsize=12)
ax_pm.legend(loc='lower left', fontsize=9, frameon=True, facecolor='white')
ax_pm.set_axis_off()
add_north_arrow(ax_pm, x=0.1, y=0.9)

# Subplot 3: Habitation Accessibility Status
ax_hab = fig.add_subplot(gs[0, 2])
cg.plot(ax=ax_hab, color='#ffffff', edgecolor='#64748b', linewidth=0.7)
hab_data = gpd.read_file(os.path.join(base_dir, "habitations_accessibility.gpkg"), layer="habitations")
tier_sub_high = hab_data[hab_data['tier_comb'] == '<500m (High)']
tier_sub_iso = hab_data[hab_data['tier_comb'] == '>2km (Isolated)']
ax_hab.scatter(tier_sub_high.geometry.x, tier_sub_high.geometry.y, color='#16a34a', s=2, alpha=0.6, label='High Access <500m (74.0%)')
ax_hab.scatter(tier_sub_iso.geometry.x, tier_sub_iso.geometry.y, color='#dc2626', s=5, alpha=0.9, label='Isolated >2km (4.6%)')
ax_hab.set_title("C. Habitation Accessibility (2026 + PMGSY)\n22,065 Connected | 1,365 Remote", fontweight='bold', fontsize=12)
ax_hab.legend(loc='lower left', fontsize=9, frameon=True, facecolor='white')
ax_hab.set_axis_off()
add_north_arrow(ax_hab, x=0.1, y=0.9)

# Subplot 4: Road Density Choropleth 2026
ax_den = fig.add_subplot(gs[1, 0])
cg_density.plot(column='density_2026_km_per_sqkm', ax=ax_den, cmap='YlGnBu', edgecolor='#334155', linewidth=0.7,
                legend=True, legend_kwds={'label': 'Road Density (km/km²)', 'orientation': 'horizontal', 'shrink': 0.7, 'pad': 0.05})
ax_den.set_title("D. 2026 District Road Density\nTop: Durg (1.18), Raipur (1.12)", fontweight='bold', fontsize=12)
ax_den.set_axis_off()

# Subplot 5: Agricultural Farmland Distribution
ax_ag = fig.add_subplot(gs[1, 1])
cg_agri.plot(column='agri_area_k_ha', ax=ax_ag, cmap='YlOrBr', edgecolor='#334155', linewidth=0.7,
             legend=True, legend_kwds={'label': 'Farmland Area (Thousand Ha)', 'orientation': 'horizontal', 'shrink': 0.7, 'pad': 0.05})
ax_ag.set_title("E. Agricultural Land Distribution\n14.4 Million Plots | 1.48M Ha Total", fontweight='bold', fontsize=12)
ax_ag.set_axis_off()

# Subplot 6: Key Executive KPI Matrix & Statistics Box
ax_kpi = fig.add_subplot(gs[1, 2])
ax_kpi.set_facecolor('#ffffff')
ax_kpi.axis([0, 10, 0, 10])
ax_kpi.set_axis_off()

card = plt.Rectangle((0.2, 0.2), 9.6, 9.6, facecolor='white', edgecolor='#cbd5e1', linewidth=1.5, zorder=1)
ax_kpi.add_patch(card)

ax_kpi.text(5.0, 9.1, "EXECUTIVE SUMMARY KPIs", ha='center', va='center', fontsize=13, fontweight='bold', color='#1e293b')

kpis = [
    ("OSM Road Network (2022)", "58,947 km", "101,620 Segments"),
    ("OSM Road Network (2026)", "83,501 km", "+24,554 km (+41.7%)"),
    ("PMGSY Total Portfolio", "19,816 km", "9,421 Segments / 6,144 Projects"),
    ("PMGSY Phases I, II, III, IV", "16,670 km", "Connectivity & Upgradation"),
    ("PM-JANMAN Tribal Scheme", "3,146 km", "PVTG Habitations (2,250 Segments)"),
    ("Total Rural Habitations", "29,831", "22.14 Million Population"),
    ("Habitations Connected (<500m)", "42.1% (2022)", "→ 74.0% (2026 + PMGSY)"),
    ("Isolated Habitations (>2km)", "29.2% (2022)", "→ 4.6% (2026 + PMGSY)"),
    ("Agricultural Fields Analyzed", "14,405,396", "1.48 Million Hectares"),
]

y_pos = 8.1
for title, val1, val2 in kpis:
    ax_kpi.text(0.6, y_pos, title, fontsize=9.5, fontweight='bold', color='#334155', va='center')
    ax_kpi.text(6.0, y_pos, val1, fontsize=9.5, fontweight='bold', color='#0284c7', va='center')
    ax_kpi.text(9.5, y_pos, val2, fontsize=8.5, color='#64748b', ha='right', va='center')
    ax_kpi.axhline(y_pos - 0.4, xmin=0.06, xmax=0.96, color='#f1f5f9', linewidth=1)
    y_pos -= 0.85

fig.suptitle("CHHATTISGARH STATE GEOSPATIAL INFRASTRUCTURE & ACCESSIBILITY ANALYSIS (2022 - 2026)\nComparative Assessment of Road Network Growth, PMGSY / PM-JANMAN Schemes, Rural Connectivity & Agricultural Farmland",
             fontsize=17, fontweight='bold', y=0.98, color='#0f172a')

fig.savefig(os.path.join(figures_dir, "map_6_chhattisgarh_accessibility_master_dashboard.png"), dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
plt.close()
print(f"Saved map_6_chhattisgarh_accessibility_master_dashboard.png in {time.time()-t0:.1f}s")
print("All maps generated successfully!")
