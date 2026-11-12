from pathlib import Path
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

base_dir = Path(__file__).resolve().parent
figures_dir = base_dir / "figures"
figures_dir.mkdir(parents=True, exist_ok=True)

# Set global style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

print("Generating Graph 1: Road Length by Functional Class (2022 vs 2026)...")
df_classes = pd.read_csv(os.path.join(base_dir, "road_class_comparison_2022_2026.csv"), index_col=0)
top_classes = df_classes.head(8).copy()

fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
x = np.arange(len(top_classes))
width = 0.38

rects1 = ax.bar(x - width/2, top_classes['length_km_2022'], width, label='2022 OSM Network', color='#2b5c8f', edgecolor='black', linewidth=0.8)
rects2 = ax.bar(x + width/2, top_classes['length_km_2026'], width, label='2026 OSM Network', color='#00a86b', edgecolor='black', linewidth=0.8)

ax.set_ylabel('Total Road Length (Kilometers)', fontweight='bold')
ax.set_title('Chhattisgarh Road Network Expansion by Functional Class (2022 vs 2026)\nTotal Network: 58,947 km (2022) → 83,501 km (2026) [+41.7% Growth]', fontsize=14, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels([c.replace('_', ' ').capitalize() for c in top_classes.index], fontweight='bold')
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=11)

# Annotate growth percentage
for i, (idx, row) in enumerate(top_classes.iterrows()):
    growth_pct = row['length_growth_pct']
    h = row['length_km_2026']
    sign = '+' if growth_pct > 0 else ''
    ax.annotate(f"{sign}{growth_pct:.1f}%",
                xy=(x[i] + width/2, h), xytext=(0, 5),
                textcoords="offset points", ha='center', va='bottom',
                fontweight='bold', color='#006633', fontsize=10)

ax.set_ylim(0, top_classes['length_km_2026'].max() * 1.15)
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "graph_1_road_classes_2022_vs_2026.png"), dpi=300)
plt.close()
print("Saved graph_1_road_classes_2022_vs_2026.png")

print("Generating Graph 2: PMGSY & PM-JANMAN Scheme Breakdown...")
pm_df = pd.read_csv(os.path.join(base_dir, "pmgsy_phase_summary.csv"))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

palette = ['#e63946', '#457b9d', '#1d3557', '#2a9d8f', '#e76f51']
bars1 = ax1.bar(pm_df['scheme'], pm_df['total_calc_len_km'], color=palette, edgecolor='black', linewidth=0.8)
ax1.set_title('Total Length by Scheme Phase (km)', fontweight='bold', fontsize=13)
ax1.set_ylabel('Kilometers (km)', fontweight='bold')
for bar in bars1:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, yval + 100, f"{yval:,.0f} km", ha='center', va='bottom', fontweight='bold', fontsize=10)
ax1.set_ylim(0, pm_df['total_calc_len_km'].max() * 1.18)

bars2 = ax2.bar(pm_df['scheme'], pm_df['total_projects'], color=palette, edgecolor='black', linewidth=0.8)
ax2.set_title('Total Road Projects / Alignments by Phase', fontweight='bold', fontsize=13)
ax2.set_ylabel('Number of Projects', fontweight='bold')
for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, yval + 35, f"{yval:,}", ha='center', va='bottom', fontweight='bold', fontsize=10)
ax2.set_ylim(0, pm_df['total_projects'].max() * 1.18)

fig.suptitle('PMGSY & PM-JANMAN Rural Road Scheme Portfolio in Chhattisgarh\nTotal Portfolio: 19,816 km across 9,421 Segments / 6,144 Unique Projects', fontsize=15, fontweight='bold')
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "graph_2_pmgsy_schemes_breakdown.png"), dpi=300)
plt.close()
print("Saved graph_2_pmgsy_schemes_breakdown.png")

print("Generating Graph 3: Habitation Accessibility Shift (2022 vs 2026 vs Combined)...")
hab_summary = pd.read_csv(os.path.join(base_dir, "habitation_accessibility_summary.csv"))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5), dpi=300)

networks = ['2022 OSM', '2026 OSM', '2026 + PMGSY']
tiers = ['<500m (High)', '500m-1km (Moderate)', '1km-2km (Low)', '>2km (Isolated)']
colors = ['#2e7d32', '#fbc02d', '#f57c00', '#d32f2f']

# Prepare data for stacked bars
hab_pct_matrix = np.zeros((len(networks), len(tiers)))
pop_pct_matrix = np.zeros((len(networks), len(tiers)))

for i, net in enumerate(networks):
    for j, tier in enumerate(tiers):
        sub = hab_summary[(hab_summary['Network'] == net) & (hab_summary['Accessibility_Tier'] == tier)]
        if not sub.empty:
            hab_pct_matrix[i, j] = sub['Habitations_Pct'].values[0]
            pop_pct_matrix[i, j] = sub['Population_Pct'].values[0]

# Left: Habitations
bottom = np.zeros(len(networks))
for j, tier in enumerate(tiers):
    ax1.bar(networks, hab_pct_matrix[:, j], bottom=bottom, label=tier, color=colors[j], edgecolor='white', width=0.55)
    for i in range(len(networks)):
        val = hab_pct_matrix[i, j]
        if val > 5:
            ax1.text(i, bottom[i] + val/2, f"{val:.1f}%", ha='center', va='center', color='white' if j in [0, 3] else 'black', fontweight='bold', fontsize=10)
    bottom += hab_pct_matrix[:, j]

ax1.set_title('Habitations Accessibility Tier Distribution\n(Total: 29,831 Habitations)', fontweight='bold', fontsize=13)
ax1.set_ylabel('Percentage of Habitations (%)', fontweight='bold')
ax1.set_ylim(0, 100)

# Right: Population
bottom = np.zeros(len(networks))
for j, tier in enumerate(tiers):
    ax2.bar(networks, pop_pct_matrix[:, j], bottom=bottom, label=tier, color=colors[j], edgecolor='white', width=0.55)
    for i in range(len(networks)):
        val = pop_pct_matrix[i, j]
        if val > 5:
            ax2.text(i, bottom[i] + val/2, f"{val:.1f}%", ha='center', va='center', color='white' if j in [0, 3] else 'black', fontweight='bold', fontsize=10)
    bottom += pop_pct_matrix[:, j]

ax2.set_title('Rural Population Accessibility Tier Distribution\n(Total: 22.14 Million People)', fontweight='bold', fontsize=13)
ax2.set_ylabel('Percentage of Population (%)', fontweight='bold')
ax2.set_ylim(0, 100)
ax2.legend(title='Accessibility Tier (Dist to Road)', loc='lower right', frameon=True, facecolor='white', framealpha=0.95)

fig.suptitle('Impact of Road Expansion on Rural Connectivity in Chhattisgarh\nIsolated Habitations (>2km) fell from 29.2% to 4.6% with PMGSY Integration', fontsize=15, fontweight='bold')
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "graph_3_habitation_accessibility_shift.png"), dpi=300)
plt.close()
print("Saved graph_3_habitation_accessibility_shift.png")

print("Generating Graph 4: District Road Density Ranking & Growth...")
dist_roads = pd.read_csv(os.path.join(base_dir, "district_road_density_2022_2026.csv"))
dist_roads = dist_roads.sort_values(by='density_2026_km_per_sqkm', ascending=True)

fig, ax = plt.subplots(figsize=(10, 12), dpi=300)
y = np.arange(len(dist_roads))

# Draw connecting line
for i, (_, row) in enumerate(dist_roads.iterrows()):
    ax.plot([row['density_2022_km_per_sqkm'], row['density_2026_km_per_sqkm']], [i, i], color='#888888', linewidth=2, zorder=1)

# Draw points
ax.scatter(dist_roads['density_2022_km_per_sqkm'], y, color='#1f77b4', s=80, label='2022 Road Density', zorder=2, edgecolors='black')
ax.scatter(dist_roads['density_2026_km_per_sqkm'], y, color='#2ca02c', s=100, label='2026 Road Density', zorder=3, edgecolors='black')

ax.set_yticks(y)
ax.set_yticklabels(dist_roads['district_clean'], fontweight='bold', fontsize=10)
ax.set_xlabel('Road Density (km of road / sq. km area)', fontweight='bold', fontsize=12)
ax.set_title('District Road Density Growth (2022 vs 2026)\nDurg, Raipur, Bilaspur, Balod Lead in Network Density', fontsize=14, fontweight='bold', pad=15)
ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.95, fontsize=11)
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "graph_4_district_density_growth.png"), dpi=300)
plt.close()
print("Saved graph_4_district_density_growth.png")

print("Generating Graph 5: Agricultural Farm Area vs Road Density by District...")
agri_summary = pd.read_csv(os.path.join(base_dir, "agri_district_summary.csv"))
# Aggregate agri to 28 districts
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
agri_dist28 = agri_summary.groupby('district_parent').agg(
    total_area_ha=('total_area_ha', 'sum'),
    field_count=('field_count', 'sum')
).reset_index()

merged_dist = pd.merge(dist_roads, agri_dist28, left_on='district_clean', right_on='district_parent', how='inner')
merged_dist.to_csv(os.path.join(base_dir, "master_district_analytics.csv"), index=False)

fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
scatter = ax.scatter(merged_dist['density_2026_km_per_sqkm'], merged_dist['total_area_ha'] / 1000.0,
                     s=merged_dist['area_sqkm'] / 15.0, c=merged_dist['length_growth_pct'], 
                     cmap='viridis', alpha=0.85, edgecolors='black', linewidth=1.2)

cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Road Length Growth % (2022-2026)', fontweight='bold')

for _, row in merged_dist.iterrows():
    ax.annotate(row['district_clean'], 
                xy=(row['density_2026_km_per_sqkm'], row['total_area_ha'] / 1000.0),
                xytext=(5, 2), textcoords="offset points", fontsize=8.5, fontweight='bold')

ax.set_xlabel('2026 Road Density (km road / sq km)', fontweight='bold', fontsize=12)
ax.set_ylabel('Total Agricultural Area (Thousand Hectares)', fontweight='bold', fontsize=12)
ax.set_title('Agricultural Farmland vs Road Network Density by District\nBubble size represents District Land Area (sq km)', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
fig.savefig(os.path.join(figures_dir, "graph_5_agri_vs_road_density.png"), dpi=300)
plt.close()
print("Saved graph_5_agri_vs_road_density.png")

print("All graphs successfully generated in figures/ directory!")
