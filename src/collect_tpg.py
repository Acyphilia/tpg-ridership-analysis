from pathlib import Path
import requests
import pandas as pd

RECORDS_URL = (
    "https://opendata.tpg.ch/api/explore/v2.1/catalog/datasets/"
    "montees-par-arret-par-ligne/records"
)

EXPORT_URL = (
    "https://opendata.tpg.ch/api/explore/v2.1/catalog/datasets/"
    "montees-par-arret-par-ligne/exports/csv"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_TPG_PATH = PROJECT_ROOT / "data" / "raw" / "tpg"

def get_latest_date():
    params = {
        "select": "max(date) as max_date",
        "limit": 1
    }

    response = requests.get(
        RECORDS_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    latest_date = data["results"][0]["max_date"]

    return latest_date


def get_earliest_date():
    params = {
        "select": "min(date) as min_date",
        "limit": 1
    }

    response = requests.get(
        RECORDS_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    earliest_date = data["results"][0]["min_date"]

    return earliest_date


def get_available_months():
    earliest_date = pd.Timestamp(get_earliest_date()).tz_localize(None)
    latest_date = pd.Timestamp(get_latest_date()).tz_localize(None)
    earliest_month = earliest_date.to_period("M")
    latest_month = latest_date.to_period("M")

    months = pd.period_range(
        start=earliest_month,
        end=latest_month,
        freq="M"
    )

    return months


def get_month_bounds(month):
    period = pd.Period(month, freq="M")

    start_date = period.start_time.strftime("%Y-%m-%d")
    next_month = (period + 1).start_time.strftime("%Y-%m-%d")

    return start_date, next_month

def get_month_record_count(month):
    start_date, next_month = get_month_bounds(month)

    params = {
        "where": (
            f"date >= date'{start_date}' "
            f"AND date < date'{next_month}'"
        ),
        "limit": 1
    }

    response = requests.get(
        RECORDS_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data["total_count"]

print(get_month_record_count("2026-08"))