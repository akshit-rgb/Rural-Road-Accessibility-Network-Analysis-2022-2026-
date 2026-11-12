import geopandas as gpd
import pyogrio
import pandas as pd
import os
import glob
import zipfile

base_dir = r"C:\Users\akshi\Downloads\geospatial_project\chhattisgaher_accisability_analysis"

cg = gpd.read_file(os.path.join(base_dir, "cg.shp"))
print("CG districts in cg.shp:")
print(sorted(cg['District'].tolist()))

# Check habitations
hab_zip = os.path.join(base_dir, "Habitation_Chhattisgarh.zip")
hab_df = pyogrio.read_dataframe(f"zip://{hab_zip}!Habitation.shp", max_features=10)
print("\nHabitation columns:", hab_df.columns.tolist())
print(hab_df.head())

# Check one PMGSY layer
pm_zip = os.path.join(base_dir, "Proposal_PMGSY-III_Chhattisgarh.zip")
pm_df = pyogrio.read_dataframe(f"zip://{pm_zip}!Proposal_PMGSY-III.shp", max_features=10)
print("\nPMGSY-III columns:", pm_df.columns.tolist())
print(pm_df.head())
