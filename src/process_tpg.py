from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_TPG_PATH = PROJECT_ROOT / "data" / "raw" / "tpg"
PROCESSED_TPG_PATH = PROJECT_ROOT / "data" / "processed" / "tpg"


def get_raw_files():
    files = sorted(RAW_TPG_PATH.rglob("*.csv"))

    return files


def load_raw_data():
    files = get_raw_files()

    if not files:
        raise FileNotFoundError("No raw TPG CSV files found.")

    dataframes = []

    for file in files:
        print(f"Loading {file.name}...")

        df = pd.read_csv(
            file,
            encoding="utf-8-sig"
        )

        dataframes.append(df)

    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    return combined_df

def inspect_raw_data(df):
    print("\n    Data types    ")
    print(df.dtypes)

    print("\n    Missing values    ")
    print(df.isna().sum())

    print("\n    Exact duplicates    ")
    print(df.duplicated().sum())

    print("\n    Date range    ")
    print("Earliest:", df["date"].min())
    print("Latest:", df["date"].max())

    print("\n    Final vs non-final data    ")
    print(df["donnees_definitives"].value_counts(dropna=False))

def inspect_missing_lines(df):
    missing_lines = df[df["ligne"].isna()]

    print("\n--- MISSING LINE RECORDS ---")
    print("Total:", len(missing_lines))

    print("\nBy line type:")
    print(
        missing_lines["ligne_type_act"]
        .value_counts(dropna=False)
    )

    print("\nBy date:")
    print(
        missing_lines["date"]
        .value_counts()
        .sort_index()
        .tail(20)
    )

    print("\nMost common stops:")
    print(
        missing_lines["arret"]
        .value_counts()
        .head(20)
    )    

def clean_tpg_data(df):
    clean_df = df.copy()

    # Convert date to datetime
    clean_df["date"] = pd.to_datetime(clean_df["date"])

    # Preserve missing Noctambus Regional lines explicitly
    clean_df["ligne"] = clean_df["ligne"].astype("string")
    clean_df["ligne"] = clean_df["ligne"].fillna(
        "UNKNOWN_NOCTAMBUS_REGIONAL"
    )

    # Convert text columns to pandas string type
    string_columns = [
        "ligne_type_act",
        "jour_semaine",
        "horaire_type",
        "arret",
        "arret_code_long"
    ]

    for column in string_columns:
        clean_df[column] = clean_df[column].astype("string")

    # Split coordinates into latitude and longitude
    coordinates = clean_df["coordonnees"].str.split(
        ",",
        n=1,
        expand=True
    )

    clean_df["latitude"] = pd.to_numeric(
        coordinates[0].str.strip(),
        errors="coerce"
    )

    clean_df["longitude"] = pd.to_numeric(
        coordinates[1].str.strip(),
        errors="coerce"
    )

    return clean_df

if __name__ == "__main__":
    df = load_raw_data()

    clean_df = clean_tpg_data(df)

    print("\n--- CLEANED DATA ---")
    print(clean_df.dtypes)

    print("\nMissing values:")
    print(clean_df.isna().sum())

    print("\nShape:")
    print(clean_df.shape)

    print("\n--- COORDINATE CHECK ---")
    print(
        clean_df[
            ["coordonnees", "latitude", "longitude"]
        ].head()
    )

    print("\nMissing latitude/longitude:")
    print(
        clean_df[
            ["latitude", "longitude"]
        ].isna().sum()
    )

    invalid_coordinates = clean_df[
        ~clean_df["latitude"].between(-90, 90)
        | ~clean_df["longitude"].between(-180, 180)
    ]

    print("\nInvalid coordinates:")
    print(len(invalid_coordinates))