# Chhattisgarh Rural Road Accessibility & Network Analysis (2022–2026)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GeoPandas](https://img.shields.io/badge/GeoPandas-Enabled-green.svg)](https://geopandas.org/)
[![Leaflet](https://img.shields.io/badge/WebGIS-Leaflet-199900.svg)](https://leafletjs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A multi-temporal geospatial accessibility and network analysis of Chhattisgarh State spanning **2022 to 2026**. By integrating high-resolution **OpenStreetMap (OSM) road networks**, **Pradhan Mantri Gram Sadak Yojana (PMGSY Phases I, II, III, IV)**, **PM-JANMAN (Pradhan Mantri Janjati Adivasi Nyaya Maha Abhiyan)**, **29,831 rural habitations** (housing 22.14 million residents), and **14,405,396 agricultural field parcels** (1.48 million hectares), this project evaluates rural connectivity shifts, infrastructure expansion, and farm-to-market transport linkages.

---

## 📌 Executive Master Infographic Dashboard

![Master Executive Dashboard](figures/map_6_chhattisgarh_accessibility_master_dashboard.png)

---

## 🚀 Key Analytical Findings

| Core Metric / Dimension | Baseline (2022) | Horizon (2026 / Integrated) | Net Impact / Change |
| :--- | :---: | :---: | :---: |
| **Total Road Network Length (OSM)** | 58,946.9 km | **83,500.6 km** | **+24,553.7 km (+41.65%)** |
| **Total Road Segments (OSM)** | 101,620 links | **142,825 links** | **+41,205 links (+40.55%)** |
| **Rural Collector Roads (`unclassified`)** | 14,481.2 km | **25,156.4 km** | **+10,675.2 km (+73.72%)** |
| **PMGSY Rural Scheme Portfolio** | - | **19,816.3 km** | **9,421 Segments / 6,144 Projects** |
| **PM-JANMAN Tribal PVTG Schemes** | - | **3,146.1 km** | **2,250 Segments (PVTG Priority)** |
| **Habitations with High Road Access (<500m)** | 12,552 (42.08%) | **22,065 (73.97%)** | **+9,513 Habitations (+31.89%)** |
| **Population with High Road Access (<500m)** | 12.62M (57.03%) | **17.98M (81.22%)** | **+5.36M People Connected** |
| **Isolated Rural Habitations (>2km from road)**| 8,710 (29.20%) | **1,365 (4.58%)** | **Plummeted by 84.3%** |
| **Agricultural Farmland Analyzed** | - | **14,405,396 Fields** | **1.48 Million Hectares** |

---

## 🗺️ Visual Cartography & Comparative Maps

### 1. Road Network Expansion (2022 vs 2026)
![Road Network Evolution](figures/map_1_road_network_evolution_2022_2026.png)

### 2. PMGSY Phases I–IV & PM-JANMAN Scheme Reach
![PMGSY Schemes Footprint](figures/map_2_pmgsy_schemes_chhattisgarh.png)

### 3. Habitation Accessibility & Proximity Classification
![Habitation Accessibility Classification](figures/map_3_habitation_accessibility.png)

### 4. District Road Density Choropleth (2022 vs 2026)
![District Road Density Choropleth](figures/map_4_district_road_density_choropleth.png)

### 5. Agricultural Farmland & Transport Corridors
![Agricultural Road Accessibility](figures/map_5_agricultural_road_accessibility.png)

---

## 📊 Comparative Statistical Graphs

<div align="center">
  <img src="figures/graph_1_road_classes_2022_vs_2026.png" width="48%" />
  <img src="figures/graph_2_pmgsy_schemes_breakdown.png" width="48%" />
</div>

<div align="center">
  <img src="figures/graph_3_habitation_accessibility_shift.png" width="48%" />
  <img src="figures/graph_4_district_density_growth.png" width="48%" />
</div>

<div align="center">
  <img src="figures/graph_5_agri_vs_road_density.png" width="70%" />
</div>

---

## 🌐 Interactive Web GIS Dashboard

The project includes an interactive, standalone Web GIS application built with Leaflet.js:
- **File**: `chhattisgarh_road_accessibility_dashboard.html`
- **Interactive Capabilities**:
  - Live hover & click inspection card displaying district area, road density, population, and agricultural hectarage.
  - Layer switcher for toggling between 2026 road networks, PMGSY scheme phases, and individual habitation points.
  - Dynamic accessibility color coding (<500m emerald green, 500m–1km yellow, 1–2km orange, >2km red).

---

## 📁 Repository Structure

```
├── figures/                                   # 300 DPI high-resolution figures & maps
│   ├── map_1_road_network_evolution_2022_2026.png
│   ├── map_2_pmgsy_schemes_chhattisgarh.png
│   ├── map_3_habitation_accessibility.png
│   ├── map_4_district_road_density_choropleth.png
│   ├── map_5_agricultural_road_accessibility.png
│   ├── map_6_chhattisgarh_accessibility_master_dashboard.png
│   ├── graph_1_road_classes_2022_vs_2026.png
│   ├── graph_2_pmgsy_schemes_breakdown.png
│   ├── graph_3_habitation_accessibility_shift.png
│   ├── graph_4_district_density_growth.png
│   └── graph_5_agri_vs_road_density.png
├── chhattisgarh_road_accessibility_dashboard.html # Interactive Web GIS Leaflet Dashboard
├── cg_districts_clean.gpkg                   # Standardized clean district boundaries (GeoPackage)
├── pmgsy_all_schemes.gpkg                    # Integrated PMGSY I-IV & PM-JANMAN roads (GeoPackage)
├── habitations_accessibility.gpkg            # 29,831 Habitations with distance metrics (GeoPackage)
├── master_district_analytics.csv             # District benchmarking dataset (28 districts)
├── road_class_comparison_2022_2026.csv       # Functional road classification growth metrics
├── pmgsy_phase_summary.csv                   # PMGSY scheme phase summary
├── pmgsy_district_scheme_summary.csv         # District allocation of PMGSY schemes
├── habitation_accessibility_summary.csv      # Population & habitation accessibility tiers
├── district_habitation_accessibility.csv     # District-level habitation connectivity
├── agri_district_summary.csv                 # District farm acreage & field count summary
├── process_roads.py                          # Script for processing OSM & PMGSY networks
├── process_habitation_accessibility.py       # Vectorized nearest-neighbor accessibility script
├── generate_graphs.py                        # Script for generating statistical charts
├── generate_maps.py                          # Cartographic map rendering script
├── generate_map_4_5.py                       # Choropleth & master dashboard script
├── build_interactive_dashboard.py            # Web GIS dashboard generator
├── requirements.txt                          # Python dependencies
└── README.md                                 # Project documentation
```

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/akshit-rgb/Rural-Road-Accessibility-Network-Analysis-2022-2026-.git
   cd Rural-Road-Accessibility-Network-Analysis-2022-2026-
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the full analysis pipeline**:
   ```bash
   python process_roads.py
   python process_habitation_accessibility.py
   python generate_graphs.py
   python generate_maps.py
   python build_interactive_dashboard.py
   ```

4. **Launch the interactive dashboard**:
   Simply open `chhattisgarh_road_accessibility_dashboard.html` in any modern web browser.

---

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
