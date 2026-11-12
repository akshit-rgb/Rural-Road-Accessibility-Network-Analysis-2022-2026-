"""Agricultural Farmland Summary & District Aggregation Engine.

Processes 14.4 million agricultural parcel records to extract district-level
acreage, field counts, and average plot sizes for accessibility benchmarking.
Supports fallback to precomputed datasets when raw shapefiles are not present.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Final, TypedDict

import pandas as pd
import pyogrio

# Standard district mapping from 33 newly formed districts to 28 parent administrative units
DISTRICT_33_TO_28_MAP: Final[dict[str, str]] = {
    "Gaurella Pendra Marwahi": "Gaurela-Pendra-Marwahi",
    "Khairgarh Chhuikhadan Gandai": "Rajnandgaon",
    "Mohla Manpur Ambagarh Chouki": "Rajnandgaon",
    "Manendragarh Chirimiri Bharatpur": "Koriya",
    "Sakti": "Janjgir-Champa",
    "Sarangarh Bilaigarh": "Raigarh",
    "Korea": "Koriya",
}


class AgriSummaryRow(TypedDict):
    """Schema for agricultural parcel summary rows."""

    district: str
    field_count: int
    total_area_ha: float
    mean_area_ha: float


def get_default_paths() -> tuple[Path, Path]:
    """Resolve default input shapefile and output CSV paths dynamically."""
    base_dir = Path(__file__).resolve().parent
    shp_path = base_dir / "agriculture_field.shp"
    out_csv = base_dir / "agri_district_summary.csv"
    return shp_path, out_csv


def summarize_agricultural_data(shp_path: Path, out_csv: Path) -> pd.DataFrame:
    """Summarize agricultural fields by district with fallback support."""
    t0 = time.time()

    if not shp_path.exists():
        print(f"[INFO] Raw shapefile not found at: {shp_path}")
        if out_csv.exists():
            print(f"[INFO] Loading precomputed summary from: {out_csv}")
            summary = pd.read_csv(out_csv)
            print("\nLoaded existing agricultural district summary:")
            print(summary.to_string(index=False))
            return summary
        else:
            raise FileNotFoundError(
                f"Neither raw shapefile ({shp_path}) nor precomputed summary ({out_csv}) could be found."
            )

    print(f"[INFO] Reading district and area_ha from: {shp_path}")
    df = pyogrio.read_dataframe(str(shp_path), columns=["district", "area_ha"], read_geometry=False)
    load_time = time.time() - t0
    print(f"[SUCCESS] Loaded {len(df):,} agricultural records in {load_time:.1f}s")

    # Aggregate by 33 administrative districts
    summary_33 = (
        df.groupby("district")["area_ha"]
        .agg(field_count="count", total_area_ha="sum", mean_area_ha="mean")
        .reset_index()
    )

    # Save 33-district summary
    summary_33.to_csv(out_csv, index=False)
    print(f"[SUCCESS] Saved 33-district summary to: {out_csv}")

    # Aggregate to 28 standard parent districts for GIS choropleth mapping
    df["district_28"] = df["district"].map(DISTRICT_33_TO_28_MAP).fillna(df["district"])
    summary_28 = (
        df.groupby("district_28")["area_ha"]
        .agg(field_count="count", total_area_ha="sum", mean_area_ha="mean")
        .reset_index()
    )
    summary_28.rename(columns={"district_28": "district"}, inplace=True)

    out_csv_28 = out_csv.parent / "agri_district_summary_28.csv"
    summary_28.to_csv(out_csv_28, index=False)
    print(f"[SUCCESS] Saved 28-parent-district summary to: {out_csv_28}")

    print("\n=== AGRICULTURAL SUMMARY BY DISTRICT (FIRST 10 DISTRICTS) ===")
    print(summary_33.head(10).to_string(index=False))

    return summary_33


def main() -> None:
    """CLI entry point for agricultural field summarization."""
    default_shp, default_out = get_default_paths()

    parser = argparse.ArgumentParser(
        description="Summarize Chhattisgarh agricultural parcel acreage and field counts by district."
    )
    parser.add_argument(
        "--shapefile",
        "-s",
        type=Path,
        default=default_shp,
        help="Path to agriculture_field.shp input file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=default_out,
        help="Path to save output agri_district_summary.csv.",
    )

    args = parser.parse_args()

    try:
        summarize_agricultural_data(args.shapefile, args.output)
    except Exception as exc:
        print(f"[ERROR] Failed to summarize agricultural data: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
