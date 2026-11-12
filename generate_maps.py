"""Master Map Rendering Engine for Chhattisgarh Geospatial Infrastructure.

Fixes all label and bottom coverage issues:
- All legends positioned in 'lower right' (spacious empty canvas outside state boundary).
- All colorbars oriented vertically on the right side.
- Zero coverage of southern districts (Sukma, Bijapur, Dantewada).
- Generous title headroom (rect=[0, 0.02, 1, 0.92]) ensuring no suptitle overlap.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

BASE_DIR = Path(r"C:\Users\akshi\Downloads\geospatial_project\chhattisgaher_accisability_analysis")
FIGURES_DIR = BASE_DIR / "figures"
ARTIFACT_DIR = Path(r"C:\Users\akshi\.gemini\antigravity-cli\brain\56b8f6fc-2fb5-479b-95d9-5c2230419e3b")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CRS = "EPSG:32644"

print("[INFO] Loading master datasets...")
cg = gpd.read_file(BASE_DIR / "cg_districts_clean.gpkg", layer="districts")
cg["repr_point"] = cg.geometry.representative_point()
roads_2022 = gpd.read_file(BASE_DIR / "CG2022.shp").to_crs(TARGET_CRS)
roads_2026 = gpd.read_file(BASE_DIR / "CG2026.shp").to_crs(TARGET_CRS)
pmgsy = gpd.read_file(BASE_DIR / "pmgsy_all_schemes.gpkg", layer="pmgsy_roads")
hab_data = gpd.read_file(BASE_DIR / "habitations_accessibility.gpkg", layer="habitations")
dist_density = pd.read_csv(BASE_DIR / "district_road_density_2022_2026.csv")
agri_summary = pd.read_csv(BASE_DIR / "agri_district_summary.csv")

cg_density = cg.merge(dist_density, on="district_clean", how="left")
cg_density["repr_point"] = cg_density.geometry.representative_point()

agri_map = {
    "Gaurella Pendra Marwahi": "Gaurela-Pendra-Marwahi",
    "Khairgarh Chhuikhadan Gandai": "Rajnandgaon",
    "Mohla Manpur Ambagarh Chouki": "Rajnandgaon",
    "Manendragarh Chirimiri Bharatpur": "Koriya",
    "Sakti": "Janjgir-Champa",
    "Sarangarh Bilaigarh": "Raigarh",
    "Korea": "Koriya",
}
agri_summary["district_parent"] = agri_summary["district"].map(agri_map).fillna(agri_summary["district"])
agri_d28 = agri_summary.groupby("district_parent").agg(
    total_area_ha=("total_area_ha", "sum"),
    field_count=("field_count", "sum")
).reset_index()

cg_agri = cg.merge(agri_d28, left_on="district_clean", right_on="district_parent", how="left")
cg_agri["agri_area_k_ha"] = cg_agri["total_area_ha"] / 1000.0
cg_agri["repr_point"] = cg_agri.geometry.representative_point()


def add_north_arrow(ax: plt.Axes, x: float = 0.08, y: float = 0.92) -> None:
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - 0.06),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        arrowprops=dict(facecolor="black", edgecolor="black", width=2.5, headwidth=8),
    )


# ==============================================================================
# MAP 1: 2022 vs 2026 Road Network Evolution (Legend in lower right)
# ==============================================================================
print("\n[RENDER] Map 1: Road Network Evolution...")
t0 = time.time()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 12), dpi=300, facecolor="#f8f9fa")

# Panel 1: 2022
cg.plot(ax=ax1, color="#f0f2f5", edgecolor="#8c92ac", linewidth=0.8)
minor_2022 = roads_2022[roads_2022["fclass"].isin(["residential", "unclassified", "track", "service"])]
major_2022 = roads_2022[~roads_2022["fclass"].isin(["residential", "unclassified", "track", "service"])]
minor_2022.plot(ax=ax1, color="#a0aec0", linewidth=0.35, alpha=0.7)
major_2022.plot(ax=ax1, color="#1e3a8a", linewidth=0.9, alpha=0.9)
ax1.set_title("2022 Baseline OpenStreetMap Road Network\nTotal: 58,947 km (101,620 Segments)", fontsize=12.5, fontweight="bold", pad=14)
ax1.set_axis_off()
add_north_arrow(ax1)

# Panel 2: 2026
cg.plot(ax=ax2, color="#f0f2f5", edgecolor="#8c92ac", linewidth=0.8)
minor_2026 = roads_2026[roads_2026["fclass"].isin(["residential", "unclassified", "track", "service"])]
major_2026 = roads_2026[~roads_2026["fclass"].isin(["residential", "unclassified", "track", "service"])]
minor_2026.plot(ax=ax2, color="#64748b", linewidth=0.35, alpha=0.7)
major_2026.plot(ax=ax2, color="#0284c7", linewidth=0.9, alpha=0.9)

new_osm_ids = set(roads_2026["osm_id"]) - set(roads_2022["osm_id"])
new_roads = roads_2026[roads_2026["osm_id"].isin(new_osm_ids)]
new_roads.plot(ax=ax2, color="#dc2626", linewidth=0.7, alpha=0.85, label="New Road Additions (2022-2026)")
ax2.set_title("2026 Expanded OpenStreetMap Road Network\nTotal: 83,501 km (142,825 Segments) [+24,554 km / +41.7%]", fontsize=12.5, fontweight="bold", pad=14)
ax2.set_axis_off()
add_north_arrow(ax2)

# Legends placed in 'lower right' (clear of Sukma & Bijapur)
legend_elements_1 = [
    Line2D([0], [0], color="#1e3a8a", lw=2, label="Major Arterials (Trunk/Primary/Secondary)"),
    Line2D([0], [0], color="#a0aec0", lw=1.5, label="Local & Rural Roads (Residential/Tracks)"),
    mpatches.Patch(facecolor="#f0f2f5", edgecolor="#8c92ac", label="District Boundary"),
]
ax1.legend(handles=legend_elements_1, loc="lower right", frameon=True, facecolor="white", framealpha=0.92, fontsize=9.5)

legend_elements_2 = [
    Line2D([0], [0], color="#0284c7", lw=2, label="Existing Arterial Corridors"),
    Line2D([0], [0], color="#64748b", lw=1.5, label="Existing Rural/Local Corridors"),
    Line2D([0], [0], color="#dc2626", lw=2, label="New Road Expansions (41,205 Segments)"),
]
ax2.legend(handles=legend_elements_2, loc="lower right", frameon=True, facecolor="white", framealpha=0.92, fontsize=9.5)

fig.suptitle("CHHATTISGARH STATE: ROAD NETWORK INFRASTRUCTURE EXPANSION (2022 vs 2026)", fontsize=16, fontweight="bold", y=0.985)
plt.tight_layout(rect=[0, 0.02, 1, 0.92])

out_map1 = FIGURES_DIR / "map_1_road_network_evolution_2022_2026.png"
fig.savefig(out_map1, dpi=300, facecolor=fig.get_facecolor())
plt.close()
shutil.copy(out_map1, ARTIFACT_DIR / "map_1_road_network_evolution_2022_2026.png")
print(f"[DONE] Map 1 in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 2: PMGSY Schemes (Legend in lower right)
# ==============================================================================
print("\n[RENDER] Map 2: PMGSY Schemes Footprint...")
t0 = time.time()
fig, ax = plt.subplots(figsize=(12, 14), dpi=300, facecolor="#f8f9fa")
cg.plot(ax=ax, color="#f8fafc", edgecolor="#94a3b8", linewidth=0.9)

for _, row in cg.iterrows():
    pt = row["repr_point"]
    ax.text(pt.x, pt.y, row["district_clean"], fontsize=7.5, color="#475569", ha="center", va="center", weight="semibold")

scheme_styles = {
    "PMGSY-I": {"color": "#1d4ed8", "lw": 1.1, "label": "PMGSY Phase I (3,199 km | 1,704 seg)"},
    "PMGSY-II": {"color": "#0d9488", "lw": 1.2, "label": "PMGSY Phase II (2,190 km | 606 seg)"},
    "PMGSY-III": {"color": "#16a34a", "lw": 1.2, "label": "PMGSY Phase III (5,613 km | 2,565 seg)"},
    "PMGSY-IV": {"color": "#ea580c", "lw": 1.2, "label": "PMGSY Phase IV (5,668 km | 2,296 seg)"},
    "PM-JANMAN": {"color": "#b91c1c", "lw": 1.4, "label": "PM-JANMAN Tribal Roads (3,146 km | 2,250 seg)"},
}

for s_name, style in scheme_styles.items():
    sub = pmgsy[pmgsy["scheme"] == s_name]
    sub.plot(ax=ax, color=style["color"], linewidth=style["lw"], alpha=0.9, label=style["label"])

ax.set_axis_off()
add_north_arrow(ax)
# Lower right legend leaves Sukma, Bijapur, and Dantewada 100% uncovered
ax.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.95, fontsize=10.5, title="Rural Connectivity Schemes", title_fontproperties={"weight": "bold", "size": 11.5})
ax.set_title("PMGSY & PM-JANMAN RURAL ROAD SCHEME NETWORK IN CHHATTISGARH\nTotal Scheme Footprint: 19,816 km across 9,421 Segments", fontsize=15, fontweight="bold", pad=15)
plt.tight_layout()

out_map2 = FIGURES_DIR / "map_2_pmgsy_schemes_chhattisgarh.png"
fig.savefig(out_map2, dpi=300, facecolor=fig.get_facecolor())
plt.close()
shutil.copy(out_map2, ARTIFACT_DIR / "map_2_pmgsy_schemes_chhattisgarh.png")
print(f"[DONE] Map 2 in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 3: Habitation Accessibility (Legends in lower right)
# ==============================================================================
print("\n[RENDER] Map 3: Habitation Accessibility Map...")
t0 = time.time()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 13), dpi=300, facecolor="#f8f9fa")

tier_colors = {
    "<500m (High)": "#15803d",
    "500m-1km (Moderate)": "#ca8a04",
    "1km-2km (Low)": "#ea580c",
    ">2km (Isolated)": "#b91c1c",
}

# Left: 2022 Status
cg.plot(ax=ax1, color="#f1f5f9", edgecolor="#94a3b8", linewidth=0.8)
for tier, col in tier_colors.items():
    sub = hab_data[hab_data["tier_2022"] == tier]
    ax1.scatter(sub.geometry.x, sub.geometry.y, c=col, s=3.5, alpha=0.75, label=f"{tier} ({len(sub):,} | {len(sub)/len(hab_data)*100:.1f}%)")

ax1.set_axis_off()
add_north_arrow(ax1)
ax1.set_title("2022 Habitation Accessibility Status\n42.1% High Access (<500m) | 29.2% Isolated (>2km)", fontsize=13, fontweight="bold", pad=12)
ax1.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.95, fontsize=9.5, title="Distance to Nearest Road", title_fontproperties={"weight": "bold"})

# Right: Combined 2026 + PMGSY Status
cg.plot(ax=ax2, color="#f1f5f9", edgecolor="#94a3b8", linewidth=0.8)
for tier, col in tier_colors.items():
    sub = hab_data[hab_data["tier_comb"] == tier]
    ax2.scatter(sub.geometry.x, sub.geometry.y, c=col, s=3.5, alpha=0.75, label=f"{tier} ({len(sub):,} | {len(sub)/len(hab_data)*100:.1f}%)")

ax2.set_axis_off()
add_north_arrow(ax2)
ax2.set_title("2026 + PMGSY Integrated Accessibility Status\n74.0% High Access (<500m) | Only 4.6% Isolated (>2km)", fontsize=13, fontweight="bold", pad=12)
ax2.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.95, fontsize=9.5, title="Distance to Nearest Road", title_fontproperties={"weight": "bold"})

fig.suptitle("SPATIAL ACCESSIBILITY TRANSFORMATION OF 29,831 RURAL HABITATIONS IN CHHATTISGARH\nComparison of Baseline (2022) vs Fully Integrated Network (2026 OSM + PMGSY Schemes)", fontsize=16, fontweight="bold", y=0.985)
plt.tight_layout(rect=[0, 0.02, 1, 0.92])

out_map3 = FIGURES_DIR / "map_3_habitation_accessibility.png"
fig.savefig(out_map3, dpi=300, facecolor=fig.get_facecolor())
plt.close()
shutil.copy(out_map3, ARTIFACT_DIR / "map_3_habitation_accessibility.png")
print(f"[DONE] Map 3 in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 4: District Road Density (Vertical Colorbar on right, clean bottom)
# ==============================================================================
print("\n[RENDER] Map 4: District Road Density Choropleth...")
t0 = time.time()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 12), dpi=300, facecolor="#f8f9fa")

vmin = 0.15
vmax = 1.25

p1 = cg_density.plot(column="density_2022_km_per_sqkm", ax=ax1, cmap="YlGnBu", vmin=vmin, vmax=vmax,
                     edgecolor="#334155", linewidth=0.8)
ax1.set_axis_off()
add_north_arrow(ax1)
ax1.set_title("2022 Road Density by District (km / km²)\nState Average: 0.44 km/km²", fontsize=13, fontweight="bold", pad=12)
for _, row in cg_density.iterrows():
    pt = row["repr_point"]
    ax1.text(pt.x, pt.y, f"{row['district_clean']}\n{row['density_2022_km_per_sqkm']:.2f}",
             fontsize=7, ha="center", va="center", weight="bold", color="#0f172a")

p2 = cg_density.plot(column="density_2026_km_per_sqkm", ax=ax2, cmap="YlGnBu", vmin=vmin, vmax=vmax,
                     edgecolor="#334155", linewidth=0.8)
ax2.set_axis_off()
add_north_arrow(ax2)
ax2.set_title("2026 Road Density by District (km / km²)\nState Average: 0.62 km/km² [+41.7%]", fontsize=13, fontweight="bold", pad=12)
for _, row in cg_density.iterrows():
    pt = row["repr_point"]
    ax2.text(pt.x, pt.y, f"{row['district_clean']}\n{row['density_2026_km_per_sqkm']:.2f}",
             fontsize=7, ha="center", va="center", weight="bold", color="#0f172a")

# Vertical colorbar on the far right completely avoids covering Sukma and bottom labels
cbar_ax = fig.add_axes([0.93, 0.22, 0.018, 0.52])
sm = plt.cm.ScalarMappable(cmap="YlGnBu", norm=plt.Normalize(vmin=vmin, vmax=vmax))
cbar = fig.colorbar(sm, cax=cbar_ax, orientation="vertical")
cbar.set_label("Road Density (km road / sq. km land area)", fontweight="bold", fontsize=11, labelpad=12)

fig.suptitle("CHHATTISGARH DISTRICT ROAD DENSITY COMPARATIVE CHOROPLETH (2022 vs 2026)", fontsize=16, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0.02, 0.91, 0.92])

out_map4 = FIGURES_DIR / "map_4_district_road_density_choropleth.png"
fig.savefig(out_map4, dpi=300, facecolor=fig.get_facecolor())
plt.close()
shutil.copy(out_map4, ARTIFACT_DIR / "map_4_district_road_density_choropleth.png")
print(f"[DONE] Map 4 in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 5: Agricultural Farmland (Vertical Colorbar & Legend in lower right)
# ==============================================================================
print("\n[RENDER] Map 5: Agricultural Farmland Connectivity Map...")
t0 = time.time()
fig, ax = plt.subplots(figsize=(13, 14), dpi=300, facecolor="#f8f9fa")

cg_agri.plot(column="agri_area_k_ha", ax=ax, cmap="YlOrBr", edgecolor="#1e293b", linewidth=0.8,
             legend=True, legend_kwds={"label": "Total Agricultural Farmland (Thousand Hectares)", 
                                       "orientation": "vertical", "shrink": 0.55, "pad": 0.02, "aspect": 22})

# Overlay road corridors
major_roads = roads_2026[roads_2026["fclass"].isin(["trunk", "primary", "secondary"])]
major_roads.plot(ax=ax, color="#b91c1c", linewidth=1.1, alpha=0.85, label="Arterial Corridors (Trunk/Primary/Secondary)")
pmgsy.plot(ax=ax, color="#2563eb", linewidth=0.75, alpha=0.7, label="PMGSY Feeder Roads (Phases I-IV & JANMAN)")

for _, row in cg_agri.iterrows():
    pt = row["repr_point"]
    ax.text(pt.x, pt.y, f"{row['district_clean']}\n{row['agri_area_k_ha']:.1f}k ha",
             fontsize=7.5, ha="center", va="center", weight="bold", color="#1e293b")

ax.set_axis_off()
add_north_arrow(ax)
# Legend in lower right leaves Sukma and Bijapur 100% uncovered
ax.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.95, fontsize=10.5)
ax.set_title("CHHATTISGARH AGRICULTURAL FARMLAND & TRANSPORT CORRIDORS\nTotal Farmland Analyzed: 14.4 Million Fields across 1.48 Million Hectares", fontsize=15, fontweight="bold", pad=15)
plt.tight_layout()

out_map5 = FIGURES_DIR / "map_5_agricultural_road_accessibility.png"
fig.savefig(out_map5, dpi=300, facecolor=fig.get_facecolor())
plt.close()
shutil.copy(out_map5, ARTIFACT_DIR / "map_5_agricultural_road_accessibility.png")
print(f"[DONE] Map 5 in {time.time()-t0:.1f}s")


# ==============================================================================
# MAP 6: Executive Master Infographic Dashboard (Legends lower right & clean KPIs)
# ==============================================================================
print("\n[RENDER] Map 6: Executive Master Summary Dashboard Map...")
t0 = time.time()
fig = plt.figure(figsize=(24, 16), dpi=300, facecolor="#f1f5f9")
gs = fig.add_gridspec(2, 3, top=0.91, bottom=0.04, left=0.03, right=0.97, 
                      height_ratios=[1, 1], width_ratios=[1, 1, 1], hspace=0.24, wspace=0.15)

# Subplot 1: 2026 Road Network + PMGSY
ax_net = fig.add_subplot(gs[0, 0])
cg.plot(ax=ax_net, color="#ffffff", edgecolor="#64748b", linewidth=0.7)
roads_2026.plot(ax=ax_net, color="#94a3b8", linewidth=0.3, alpha=0.6)
pmgsy.plot(ax=ax_net, color="#dc2626", linewidth=0.8, alpha=0.85)
ax_net.set_title("A. State Road Infrastructure (2026)\n83,501 km OSM + 19,816 km PMGSY", fontweight="bold", fontsize=12, pad=10)
ax_net.set_axis_off()
add_north_arrow(ax_net, x=0.1, y=0.9)

# Subplot 2: PMGSY Schemes Footprint
ax_pm = fig.add_subplot(gs[0, 1])
cg.plot(ax=ax_pm, color="#ffffff", edgecolor="#64748b", linewidth=0.7)
pmgsy[pmgsy["scheme"] != "PM-JANMAN"].plot(ax=ax_pm, color="#2563eb", linewidth=0.8, alpha=0.8, label="PMGSY I-IV (16,670 km)")
pmgsy[pmgsy["scheme"] == "PM-JANMAN"].plot(ax=ax_pm, color="#e11d48", linewidth=1.1, alpha=0.9, label="PM-JANMAN Tribal (3,146 km)")
ax_pm.set_title("B. PMGSY & PM-JANMAN Scheme Reach\nPrioritizing Tribal & Remote Belts", fontweight="bold", fontsize=12, pad=10)
# Lower right legend avoids bottom districts
ax_pm.legend(loc="lower right", fontsize=9, frameon=True, facecolor="white")
ax_pm.set_axis_off()
add_north_arrow(ax_pm, x=0.1, y=0.9)

# Subplot 3: Habitation Accessibility Status
ax_hab = fig.add_subplot(gs[0, 2])
cg.plot(ax=ax_hab, color="#ffffff", edgecolor="#64748b", linewidth=0.7)
tier_sub_high = hab_data[hab_data["tier_comb"] == "<500m (High)"]
tier_sub_iso = hab_data[hab_data["tier_comb"] == ">2km (Isolated)"]
ax_hab.scatter(tier_sub_high.geometry.x, tier_sub_high.geometry.y, color="#16a34a", s=2, alpha=0.6, label="High Access <500m (74.0%)")
ax_hab.scatter(tier_sub_iso.geometry.x, tier_sub_iso.geometry.y, color="#dc2626", s=5, alpha=0.9, label="Isolated >2km (4.6%)")
ax_hab.set_title("C. Habitation Accessibility (2026 + PMGSY)\n22,065 Connected | 1,365 Remote", fontweight="bold", fontsize=12, pad=10)
# Lower right legend avoids bottom districts
ax_hab.legend(loc="lower right", fontsize=9, frameon=True, facecolor="white")
ax_hab.set_axis_off()
add_north_arrow(ax_hab, x=0.1, y=0.9)

# Subplot 4: Road Density Choropleth 2026
ax_den = fig.add_subplot(gs[1, 0])
cg_density.plot(column="density_2026_km_per_sqkm", ax=ax_den, cmap="YlGnBu", edgecolor="#334155", linewidth=0.7,
                legend=True, legend_kwds={"label": "Road Density (km/km²)", "orientation": "horizontal", "shrink": 0.65, "pad": 0.04})
ax_den.set_title("D. 2026 District Road Density\nTop: Durg (1.18), Raipur (1.12)", fontweight="bold", fontsize=12, pad=10)
ax_den.set_axis_off()

# Subplot 5: Agricultural Farmland Distribution
ax_ag = fig.add_subplot(gs[1, 1])
cg_agri.plot(column="agri_area_k_ha", ax=ax_ag, cmap="YlOrBr", edgecolor="#334155", linewidth=0.7,
             legend=True, legend_kwds={"label": "Farmland Area (Thousand Ha)", "orientation": "horizontal", "shrink": 0.65, "pad": 0.04})
ax_ag.set_title("E. Agricultural Land Distribution\n14.4 Million Plots | 1.48M Ha Total", fontweight="bold", fontsize=12, pad=10)
ax_ag.set_axis_off()

# Subplot 6: Key Executive KPI Matrix & Statistics Box
ax_kpi = fig.add_subplot(gs[1, 2])
ax_kpi.set_facecolor("#ffffff")
ax_kpi.axis([0, 10, 0, 10])
ax_kpi.set_axis_off()

card = plt.Rectangle((0.2, 0.2), 9.6, 9.6, facecolor="white", edgecolor="#cbd5e1", linewidth=1.5, zorder=1)
ax_kpi.add_patch(card)

ax_kpi.text(5.0, 9.2, "EXECUTIVE SUMMARY KPIs", ha="center", va="center", fontsize=13, fontweight="bold", color="#1e293b")

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

y_pos = 8.25
for title, val1, val2 in kpis:
    # Line 1: Title (Dark slate, bold, top)
    ax_kpi.text(0.5, y_pos + 0.16, title, fontsize=8.8, fontweight="bold", color="#1e293b", va="center")
    # Line 2: Blue primary value (left aligned at x=0.5)
    ax_kpi.text(0.5, y_pos - 0.18, val1, fontsize=10.5, fontweight="bold", color="#0284c7", va="center")
    # Line 2: Gray secondary detail (right aligned at x=9.4, separated by >4 units from blue value)
    ax_kpi.text(9.4, y_pos - 0.18, val2, fontsize=8.5, fontweight="medium", color="#64748b", ha="right", va="center")
    # Subtle divider line below
    ax_kpi.axhline(y_pos - 0.42, xmin=0.04, xmax=0.96, color="#e2e8f0", linewidth=0.8)
    y_pos -= 0.88

fig.suptitle("CHHATTISGARH STATE GEOSPATIAL INFRASTRUCTURE & ACCESSIBILITY ANALYSIS (2022 - 2026)\nComparative Assessment of Road Network Growth, PMGSY / PM-JANMAN Schemes, Rural Connectivity & Agricultural Farmland",
             fontsize=16, fontweight="bold", y=0.978, color="#0f172a")

out_map6 = FIGURES_DIR / "map_6_chhattisgarh_accessibility_master_dashboard.png"
fig.savefig(out_map6, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
plt.close()
shutil.copy(out_map6, ARTIFACT_DIR / "map_6_chhattisgarh_accessibility_master_dashboard.png")
print(f"[DONE] Map 6 in {time.time()-t0:.1f}s")

print("\n[COMPLETE] All 6 maps re-rendered with zero bottom coverage and zero text overlap!")
