import geopandas as gpd
import pyogrio
import os
import glob
import zipfile

base_dir = r"C:\Users\akshi\Downloads\geospatial_project\chhattisgaher_accisability_analysis"

def inspect_layer(name, path, is_zip=False, zip_inner=""):
    print(f"\n==========================================")
    print(f"=== {name} ===")
    try:
        if is_zip:
            target = f"zip://{path}!{zip_inner}"
        else:
            target = path
        
        info = pyogrio.read_info(target)
        print(f"Feature count: {info['features']}")
        print(f"Geometry type: {info['geometry_type']}")
        print(f"CRS: {info['crs']}")
        print(f"Fields: {info['fields']}")
        
        # Read 2 rows
        gdf = gpd.read_file(target, rows=2)
        cols_no_geom = [c for c in gdf.columns if c != "geometry"]
        print("Sample data (first 2 rows):")
        for idx, row in gdf.head(2).iterrows():
            print(f" Row {idx}: " + ", ".join([f"{c}={row[c]}" for c in cols_no_geom[:10]]))
    except Exception as e:
        print(f"Error reading {name}: {e}")

inspect_layer("cg.shp", os.path.join(base_dir, "cg.shp"))
inspect_layer("CG2022.shp", os.path.join(base_dir, "CG2022.shp"))
inspect_layer("CG2026.shp", os.path.join(base_dir, "CG2026.shp"))
inspect_layer("agriculture_field.shp", os.path.join(base_dir, "agriculture_field.shp"))

# Inspect zip files
zip_files = glob.glob(os.path.join(base_dir, "*.zip"))
for z in sorted(zip_files):
    z_name = os.path.basename(z)
    with zipfile.ZipFile(z, 'r') as zf:
        shp_members = [m for m in zf.namelist() if m.endswith('.shp')]
        for sm in shp_members:
            inspect_layer(f"{z_name} -> {sm}", z, is_zip=True, zip_inner=sm)
