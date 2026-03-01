"""Demographics data for all supported regions."""

from .turkey import TURKEY_DEMOGRAPHICS
from .usa import USA_DEMOGRAPHICS
from .europe import EUROPE_DEMOGRAPHICS
from .mena import MENA_DEMOGRAPHICS


def get_demographics(region: str) -> dict:
    demographics_map = {
        "TR": TURKEY_DEMOGRAPHICS,
        "US": USA_DEMOGRAPHICS,
        "EU": EUROPE_DEMOGRAPHICS,
        "MENA": MENA_DEMOGRAPHICS,
    }
    if region not in demographics_map:
        raise ValueError(f"Desteklenmeyen bölge: {region}")
    return demographics_map[region]
