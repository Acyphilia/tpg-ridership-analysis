from pathlib import Path
import requests
import pandas as pd
#my imports needed

#information about the api
RECORDS_URL = (
    "https://opendata.tpg.ch/api/explore/v2.1/catalog/datasets/"
    "montees-par-arret-par-ligne/records"
)

#get the data set
exports_url = (
    "https://opendata.tpg.ch/api/explore/v2.1/catalog/datasets/"
    "montees-par-arret-par-ligne/exports/csv"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent 

RAW_TPG_PATH = PROJECT_ROOT / "data" / "raw" / "tpg"
##change later to tpg data

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


def download_month(month, overwrite=False):
    start_date, next_month = get_month_bounds(month)

    # Create folder for the year
    year = month[:4]

    year_folder = RAW_TPG_PATH / year
    year_folder.mkdir(parents=True, exist_ok=True)

    # Final file location
    file_path = year_folder / f"{month}.csv"

    # Don't download again unless we explicitly ask
    if file_path.exists() and not overwrite:
        print(f"{month}: file already exists — skipped")
        return file_path

    # Expected number of rows according to the API
    expected_rows = get_month_record_count(month)

    # Filter TPG export to this month
    params = {
        "where": (
            f"date >= date'{start_date}' "
            f"AND date < date'{next_month}'"
        ),
        "delimiter": ","
    }

    print(f"Downloading {month}...")

    response = requests.get(
        exports_url,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    # Save exact API response
    with open(file_path, "wb") as file:
        file.write(response.content)

    # Verify downloaded data
    downloaded_df = pd.read_csv(
        file_path,
        encoding="utf-8-sig"
    )

    downloaded_rows = len(downloaded_df)

    if downloaded_rows == expected_rows:
        print(
            f" {month}: {downloaded_rows:,} rows downloaded successfully"
        )
    else:
        print(
            f" {month}: expected {expected_rows:,} rows, "
            f"but downloaded {downloaded_rows:,}"
        )

    return file_path


#when i rebuild everything i want to backfill all months
def backfill_all_months():
    months = get_available_months()
    total_months = len(months)

    for index, month in enumerate(months, start=1):
        month_str = str(month)

        print(f"\n[{index}/{total_months}] Processing {month_str}")

        download_month(month_str)

#day to day or month to month updates,
def update_data():
    months = get_available_months()

    if len(months) == 0:
        print("No TPG data available.")
        return

    latest_month = str(months[-1])

    previous_month = None

    if len(months) >= 2:
        previous_month = str(months[-2])

    print(f"Latest TPG month: {latest_month}")

    for month in months:
        month_str = str(month)

        if month_str in {latest_month, previous_month}:
            print(f"\nRefreshing {month_str}")

            download_month(
                month_str,
                overwrite=True
            )

        else:
            download_month(month_str)

if __name__ == "__main__":
    update_data()