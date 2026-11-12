import pyogrio
import pandas as pd
import time

path = r"C:\Users\akshi\Downloads\geospatial_project\chhattisgaher_accisability_analysis\agriculture_field.shp"

t0 = time.time()
print("Reading district and area_ha from agriculture_field.shp...")
df = pyogrio.read_dataframe(path, columns=['district', 'area_ha'], read_geometry=False)
print(f"Loaded {len(df):,} records in {time.time()-t0:.1f} s")

summary = df.groupby('district')['area_ha'].agg(
    field_count='count',
    total_area_ha='sum',
    mean_area_ha='mean'
).reset_index()

print("\nAgriculture summary by district:")
print(summary.to_string())

# Save summary to csv for quick reference
summary.to_csv(r"C:\Users\akshi\Downloads\geospatial_project\chhattisgaher_accisability_analysis\agri_district_summary.csv", index=False)
print("\nSaved agri_district_summary.csv")
