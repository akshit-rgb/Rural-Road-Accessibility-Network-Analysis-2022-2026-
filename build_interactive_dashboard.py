import json
import os
from pathlib import Path
import geopandas as gpd
import pandas as pd

base_dir = Path(__file__).resolve().parent

print("1. Preparing District GeoJSON with Master Analytics...")
cg = gpd.read_file(os.path.join(base_dir, "cg_districts_clean.gpkg"), layer="districts").to_crs(epsg=4326)
roads_df = pd.read_csv(os.path.join(base_dir, "district_road_density_2022_2026.csv"))
hab_df = pd.read_csv(os.path.join(base_dir, "district_habitation_accessibility.csv"))
agri_summary = pd.read_csv(os.path.join(base_dir, "agri_district_summary.csv"))

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
    agri_area_ha=('total_area_ha', 'sum'),
    agri_fields=('field_count', 'sum')
).reset_index()

# Merge all into cg
cg_master = cg.merge(roads_df, on='district_clean', how='left')
cg_master = cg_master.merge(hab_df[['district_clean', 'total_habitations', 'total_population', 
                                    'pct_hab_connected_2022', 'pct_hab_connected_2026', 'pct_hab_connected_comb',
                                    'pct_pop_connected_2022', 'pct_pop_connected_2026', 'pct_pop_connected_comb']], 
                            on='district_clean', how='left')
cg_master = cg_master.merge(agri_d28, left_on='district_clean', right_on='district_parent', how='left')

# Format fields for GeoJSON
for c in ['area_sqkm_x', 'area_sqkm_y']:
    if c in cg_master.columns:
        cg_master['area_sqkm'] = cg_master[c]

cg_master['density_2022'] = cg_master['density_2022_km_per_sqkm'].round(3)
cg_master['density_2026'] = cg_master['density_2026_km_per_sqkm'].round(3)
cg_master['growth_pct'] = cg_master['length_growth_pct'].round(1)
cg_master['hab_conn_pct'] = cg_master['pct_hab_connected_comb'].round(1)
cg_master['pop_conn_pct'] = cg_master['pct_pop_connected_comb'].round(1)
cg_master['agri_k_ha'] = (cg_master['agri_area_ha'] / 1000.0).round(1)

districts_json = cg_master[['district_clean', 'area_sqkm', 'roads_km_2022', 'roads_km_2026',
                            'density_2022', 'density_2026', 'growth_pct', 'total_habitations',
                            'total_population', 'hab_conn_pct', 'pop_conn_pct', 'agri_k_ha', 'agri_fields', 'geometry']].to_json()

print("2. Preparing PMGSY Schemes GeoJSON (simplified for web)...")
pmgsy = gpd.read_file(os.path.join(base_dir, "pmgsy_all_schemes.gpkg"), layer="pmgsy_roads").to_crs(epsg=4326)
pmgsy['geometry'] = pmgsy.geometry.simplify(0.001)
# Group or take representative subset to keep web performance silky smooth
pmgsy_web = pmgsy[['scheme', 'WORK_NAME', 'PROPOSED_L', 'calc_length_km', 'IMS_YEAR', 'geometry']].copy()
pmgsy_json = pmgsy_web.to_json()

print("3. Preparing Habitations sample GeoJSON...")
hab = gpd.read_file(os.path.join(base_dir, "habitations_accessibility.gpkg"), layer="habitations").to_crs(epsg=4326)
# Sample 2,000 habitations stratified by tier for smooth interactive rendering
hab_sample = hab.groupby('tier_comb', group_keys=False).apply(lambda x: x.sample(min(len(x), 600), random_state=42))
hab_web = hab_sample[['HAB_NAME', 'TOT_POPULA', 'district_clean', 'dist_combined_m', 'tier_comb', 'geometry']].copy()
hab_web['dist_m'] = hab_web['dist_combined_m'].round(0).astype(int)
hab_web['tier'] = hab_web['tier_comb'].astype(str)
hab_json = hab_web[['HAB_NAME', 'TOT_POPULA', 'district_clean', 'dist_m', 'tier', 'geometry']].to_json()

print("4. Writing interactive HTML dashboard...")
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chhattisgarh Road Network & Accessibility Interactive Dashboard (2022-2026)</title>
    <!-- Leaflet CSS & JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }}
        body {{ display: flex; flex-direction: column; height: 100vh; background-color: #0f172a; color: #f8fafc; overflow: hidden; }}
        header {{
            background: linear-gradient(135deg, #1e293b, #0f172a);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #334155;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        .header-title h1 {{ font-size: 1.25rem; font-weight: 700; color: #38bdf8; }}
        .header-title p {{ font-size: 0.8rem; color: #94a3b8; }}
        .stats-strip {{
            display: flex;
            gap: 16px;
            background: #1e293b;
            padding: 10px 24px;
            border-bottom: 1px solid #334155;
            overflow-x: auto;
        }}
        .stat-card {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 8px 16px;
            min-width: 170px;
            display: flex;
            flex-direction: column;
        }}
        .stat-label {{ font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }}
        .stat-val {{ font-size: 1.15rem; font-weight: 700; color: #38bdf8; margin-top: 2px; }}
        .stat-sub {{ font-size: 0.72rem; color: #10b981; font-weight: 600; }}
        #main-container {{ display: flex; flex: 1; position: relative; }}
        #map {{ flex: 1; height: 100%; z-index: 10; background: #1e293b; }}
        #sidebar {{
            width: 380px;
            background: #1e293b;
            border-left: 1px solid #334155;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            z-index: 20;
        }}
        .panel-box {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
        }}
        .panel-box h3 {{ font-size: 0.95rem; font-weight: 700; color: #38bdf8; margin-bottom: 12px; border-bottom: 1px solid #334155; padding-bottom: 6px; }}
        .info-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.85rem; }}
        .info-label {{ color: #94a3b8; }}
        .info-value {{ font-weight: 600; color: #f8fafc; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 0.8rem; margin-bottom: 6px; }}
        .legend-color {{ width: 14px; height: 14px; border-radius: 3px; display: inline-block; }}
        .legend-circle {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
        .btn {{
            background: #0284c7;
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            text-decoration: none;
            display: inline-block;
        }}
        .btn:hover {{ background: #0369a1; }}
    </style>
</head>
<body>
    <header>
        <div class="header-title">
            <h1>Chhattisgarh Road Infrastructure & Accessibility Analysis (2022 - 2026)</h1>
            <p>Comprehensive GIS Assessment of OSM Road Expansion, PMGSY Schemes I-IV & PM-JANMAN, Rural Habitations & Farmland</p>
        </div>
    </header>

    <div class="stats-strip">
        <div class="stat-card">
            <span class="stat-label">2022 OSM Roads</span>
            <span class="stat-val">58,947 km</span>
            <span class="stat-sub">101,620 Segments</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">2026 OSM Roads</span>
            <span class="stat-val">83,501 km</span>
            <span class="stat-sub">+24,554 km (+41.7%)</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">PMGSY Total Portfolio</span>
            <span class="stat-val">19,816 km</span>
            <span class="stat-sub">9,421 Segments / 6,144 Projects</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">PM-JANMAN Tribal Scheme</span>
            <span class="stat-val">3,146 km</span>
            <span class="stat-sub">2,250 Segments (PVTG)</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Habitation Connectivity</span>
            <span class="stat-val">74.0% (&lt;500m)</span>
            <span class="stat-sub">Up from 42.1% in 2022</span>
        </div>
        <div class="stat-card">
            <span class="stat-label">Agricultural Farmland</span>
            <span class="stat-val">14.4M Plots</span>
            <span class="stat-sub">1.48 Million Hectares</span>
        </div>
    </div>

    <div id="main-container">
        <div id="map"></div>
        <div id="sidebar">
            <div class="panel-box" id="district-info">
                <h3>District Analytics</h3>
                <p style="font-size: 0.85rem; color: #94a3b8; font-style: italic;">Click or hover over any district polygon on the map to inspect granular connectivity and farmland statistics.</p>
            </div>

            <div class="panel-box">
                <h3>Map Layers & Legends</h3>
                <div style="font-weight: 600; font-size: 0.8rem; margin-bottom: 6px; color: #cbd5e1;">PMGSY Schemes</div>
                <div class="legend-item"><span class="legend-color" style="background: #1d4ed8;"></span> PMGSY Phase I (3,199 km)</div>
                <div class="legend-item"><span class="legend-color" style="background: #0d9488;"></span> PMGSY Phase II (2,190 km)</div>
                <div class="legend-item"><span class="legend-color" style="background: #16a34a;"></span> PMGSY Phase III (5,613 km)</div>
                <div class="legend-item"><span class="legend-color" style="background: #ea580c;"></span> PMGSY Phase IV (5,668 km)</div>
                <div class="legend-item"><span class="legend-color" style="background: #dc2626;"></span> PM-JANMAN Tribal Roads (3,146 km)</div>

                <div style="font-weight: 600; font-size: 0.8rem; margin: 12px 0 6px; color: #cbd5e1;">Habitation Distance to Road</div>
                <div class="legend-item"><span class="legend-circle" style="background: #16a34a;"></span> &lt;500m (High Accessibility - 74.0%)</div>
                <div class="legend-item"><span class="legend-circle" style="background: #ca8a04;"></span> 500m - 1km (Moderate - 11.0%)</div>
                <div class="legend-item"><span class="legend-circle" style="background: #ea580c;"></span> 1km - 2km (Low - 10.5%)</div>
                <div class="legend-item"><span class="legend-circle" style="background: #dc2626;"></span> &gt;2km (Isolated - 4.6%)</div>
            </div>

            <div class="panel-box">
                <h3>High-Resolution Map Figures</h3>
                <p style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 10px;">Generated publication-ready 300 DPI analytical figures available in figures/ directory:</p>
                <div style="display: flex; flex-direction: column; gap: 6px;">
                    <a href="figures/map_1_road_network_evolution_2022_2026.png" target="_blank" class="btn">View Road Network Evolution Map</a>
                    <a href="figures/map_2_pmgsy_schemes_chhattisgarh.png" target="_blank" class="btn">View PMGSY Schemes Map</a>
                    <a href="figures/map_3_habitation_accessibility.png" target="_blank" class="btn">View Habitation Accessibility Map</a>
                    <a href="figures/map_4_district_road_density_choropleth.png" target="_blank" class="btn">View Road Density Choropleth</a>
                    <a href="figures/map_5_agricultural_road_accessibility.png" target="_blank" class="btn">View Agricultural Farmland Map</a>
                    <a href="figures/map_6_chhattisgarh_accessibility_master_dashboard.png" target="_blank" class="btn" style="background: #059669;">View Master Executive Dashboard</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        const districtsData = {districts_json};
        const pmgsyData = {pmgsy_json};
        const habData = {hab_json};

        const map = L.map('map', {{
            center: [21.2787, 81.8661],
            zoom: 7,
            zoomControl: true
        }});

        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }}).addTo(map);

        function getDensityColor(d) {{
            return d > 1.0  ? '#08519c' :
                   d > 0.8  ? '#3182bd' :
                   d > 0.6  ? '#6baed6' :
                   d > 0.4  ? '#9ecae1' :
                              '#c6dbef';
        }}

        function styleDistricts(feature) {{
            return {{
                fillColor: getDensityColor(feature.properties.density_2026),
                weight: 1.5,
                opacity: 1,
                color: '#64748b',
                fillOpacity: 0.55
            }};
        }}

        function highlightFeature(e) {{
            const layer = e.target;
            layer.setStyle({{
                weight: 3,
                color: '#38bdf8',
                fillOpacity: 0.75
            }});
            layer.bringToFront();
            updateSidebar(layer.feature.properties);
        }}

        function resetHighlight(e) {{
            districtsLayer.resetStyle(e.target);
        }}

        function updateSidebar(props) {{
            const side = document.getElementById('district-info');
            side.innerHTML = `
                <h3>${{props.district_clean}} District</h3>
                <div class="info-row"><span class="info-label">District Area:</span><span class="info-value">${{Math.round(props.area_sqkm).toLocaleString()}} sq km</span></div>
                <div class="info-row"><span class="info-label">Population:</span><span class="info-value">${{props.total_population ? props.total_population.toLocaleString() : 'N/A'}}</span></div>
                <div class="info-row"><span class="info-label">Road Length (2022):</span><span class="info-value">${{Math.round(props.roads_km_2022).toLocaleString()}} km</span></div>
                <div class="info-row"><span class="info-label">Road Length (2026):</span><span class="info-value" style="color: #38bdf8;">${{Math.round(props.roads_km_2026).toLocaleString()}} km</span></div>
                <div class="info-row"><span class="info-label">Network Growth:</span><span class="info-value" style="color: #10b981;">+${{props.growth_pct}}%</span></div>
                <div class="info-row"><span class="info-label">Road Density (2026):</span><span class="info-value">${{props.density_2026}} km/km²</span></div>
                <div class="info-row"><span class="info-label">Habitations (&lt;500m):</span><span class="info-value" style="color: #10b981;">${{props.hab_conn_pct}}%</span></div>
                <div class="info-row"><span class="info-label">Farmland Area:</span><span class="info-value">${{props.agri_k_ha ? props.agri_k_ha + 'k Ha' : 'N/A'}}</span></div>
                <div class="info-row"><span class="info-label">Agricultural Plots:</span><span class="info-value">${{props.agri_fields ? props.agri_fields.toLocaleString() : 'N/A'}}</span></div>
            `;
        }}

        const districtsLayer = L.geoJson(districtsData, {{
            style: styleDistricts,
            onEachFeature: function(feature, layer) {{
                layer.on({{
                    mouseover: highlightFeature,
                    mouseout: resetHighlight,
                    click: highlightFeature
                }});
            }}
        }}).addTo(map);

        function getSchemeColor(scheme) {{
            switch(scheme) {{
                case 'PMGSY-I': return '#1d4ed8';
                case 'PMGSY-II': return '#0d9488';
                case 'PMGSY-III': return '#16a34a';
                case 'PMGSY-IV': return '#ea580c';
                case 'PM-JANMAN': return '#dc2626';
                default: return '#fbbf24';
            }}
        }}

        const pmgsyLayer = L.geoJson(pmgsyData, {{
            style: function(feature) {{
                return {{
                    color: getSchemeColor(feature.properties.scheme),
                    weight: 2.2,
                    opacity: 0.85
                }};
            }},
            onEachFeature: function(feature, layer) {{
                layer.bindPopup(`
                    <div style="color: #0f172a; font-family: 'Inter', sans-serif;">
                        <b style="color: #0284c7;">${{feature.properties.scheme}}</b><br>
                        <b>Work:</b> ${{feature.properties.WORK_NAME || 'Road Alignment'}}<br>
                        <b>Length:</b> ${{Number(feature.properties.calc_length_km).toFixed(2)}} km<br>
                        <b>IMS Year:</b> ${{feature.properties.IMS_YEAR || 'N/A'}}
                    </div>
                `);
            }}
        }}).addTo(map);

        function getTierColor(tier) {{
            if (tier.includes('<500m')) return '#16a34a';
            if (tier.includes('500m-1km')) return '#ca8a04';
            if (tier.includes('1km-2km')) return '#ea580c';
            return '#dc2626';
        }}

        const habLayer = L.geoJson(habData, {{
            pointToLayer: function(feature, latlng) {{
                return L.circleMarker(latlng, {{
                    radius: 4,
                    fillColor: getTierColor(feature.properties.tier),
                    color: '#ffffff',
                    weight: 0.5,
                    opacity: 0.9,
                    fillOpacity: 0.85
                }});
            }},
            onEachFeature: function(feature, layer) {{
                layer.bindPopup(`
                    <div style="color: #0f172a; font-family: 'Inter', sans-serif;">
                        <b style="color: #0284c7;">${{feature.properties.HAB_NAME}}</b> (${{feature.properties.district_clean}})<br>
                        <b>Population:</b> ${{feature.properties.TOT_POPULA.toLocaleString()}}<br>
                        <b>Distance to Road:</b> ${{feature.properties.dist_m.toLocaleString()}} meters<br>
                        <b>Accessibility Tier:</b> ${{feature.properties.tier}}
                    </div>
                `);
            }}
        }}).addTo(map);

        const overlayMaps = {{
            "District Boundaries & Density": districtsLayer,
            "PMGSY Schemes (I-IV & JANMAN)": pmgsyLayer,
            "Rural Habitations (Sampled)": habLayer
        }};

        L.control.layers(null, overlayMaps, {{ collapsed: false, position: 'topright' }}).addTo(map);
    </script>
</body>
</html>
"""

output_html = os.path.join(base_dir, "chhattisgarh_road_accessibility_dashboard.html")
with open(output_html, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Interactive dashboard successfully generated at: {output_html}")
