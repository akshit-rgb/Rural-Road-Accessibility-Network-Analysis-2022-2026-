"""Typing schema and protocol definitions for Chhattisgarh Accessibility Analysis.

Implements modern Python typing standards including Protocol, TypedDict,
and Literal for strict-mode type checking under Pyright and Ruff.
"""

from __future__ import annotations

from typing import (
    Any,
    Literal,
    Protocol,
    TypedDict,
    runtime_checkable,
)

# Literal Type Definitions
AccessibilityTier = Literal[
    "<500m (High)",
    "500m-1km (Moderate)",
    "1km-2km (Low)",
    ">2km (Isolated)",
]

PMGSYScheme = Literal[
    "PMGSY-I",
    "PMGSY-II",
    "PMGSY-III",
    "PMGSY-IV",
    "PM-JANMAN",
]

RoadFunctionalClass = Literal[
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "unclassified",
    "residential",
    "service",
    "track",
    "living_street",
    "path",
    "footway",
    "steps",
    "unknown",
]

CoordinateReferenceSystem = Literal[
    "EPSG:4326",
    "EPSG:32644",
]


# TypedDict Structure Definitions
class HabitationFeatureRecord(TypedDict):
    """Schema for a rural settlement habitation record."""

    HAB_ID: int
    STATE_ID: int
    DISTRICT_I: int
    BLOCK_ID: int
    HAB_NAME: str
    TOT_POPULA: int
    district_clean: str
    dist_road_2022_m: float
    dist_road_2026_m: float
    dist_pmgsy_m: float
    dist_combined_m: float
    tier_2022: AccessibilityTier
    tier_2026: AccessibilityTier
    tier_comb: AccessibilityTier


class DistrictSummaryRecord(TypedDict):
    """Schema for aggregated district infrastructure analytics."""

    district_clean: str
    area_sqkm: float
    population: int
    roads_km_2022: float
    roads_km_2026: float
    density_2022_km_per_sqkm: float
    density_2026_km_per_sqkm: float
    density_growth: float
    length_growth_km: float
    length_growth_pct: float
    pct_hab_connected_2022: float
    pct_hab_connected_2026: float
    pct_hab_connected_comb: float
    total_agri_area_ha: float
    total_agri_fields: int


class SchemePortfolioRecord(TypedDict):
    """Schema for PMGSY & PM-JANMAN scheme phase summaries."""

    scheme: PMGSYScheme
    total_projects: int
    total_segments: int
    total_proposed_len_km: float
    total_calc_len_km: float
    avg_project_len_km: float


class RoadClassGrowthRecord(TypedDict):
    """Schema for functional road class temporal growth analysis."""

    fclass: RoadFunctionalClass
    segments_2022: int
    length_km_2022: float
    segments_2026: int
    length_km_2026: float
    length_growth_km: float
    length_growth_pct: float
    segment_growth: int


# Structural Subtyping Protocols
@runtime_checkable
class SpatialIndexTree(Protocol):
    """Protocol defining the spatial indexing contract for STRtree nearest-neighbor queries."""

    def nearest(self, geometries: Any) -> Any:
        """Find the nearest geometry indices in the spatial index."""
        ...


@runtime_checkable
class NetworkMetricCalculator(Protocol):
    """Protocol defining network length and density computation engine."""

    def calculate_length_km(self, crs: CoordinateReferenceSystem) -> float:
        """Calculate total road network length projected in target CRS."""
        ...

    def compute_density(self, area_sqkm: float) -> float:
        """Calculate road network density in km/km²."""
        ...
