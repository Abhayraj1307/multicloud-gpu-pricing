import pandas as pd

from src.ingestion.aws_pricing import fetch_aws_gpu_prices
from src.utils.io import save_dataframe
from src.config import PROCESSED_DIR


RAW_OUTPUT = PROCESSED_DIR / "aws_gpu_catalog_raw.parquet"
CLEAN_OUTPUT_PARQUET = PROCESSED_DIR / "aws_gpu_catalog_clean.parquet"
CLEAN_OUTPUT_CSV = PROCESSED_DIR / "aws_gpu_catalog_clean.csv"


def clean_aws_gpu_catalog(df: pd.DataFrame) -> pd.DataFrame:
    clean_df = df.copy()

    # Remove rows with missing key values
    clean_df = clean_df.dropna(subset=["sku", "region", "price_per_hour_usd"])

    # Keep only Linux/NA rows already filtered, but enforce again
    clean_df = clean_df[clean_df["os"].isin(["Linux", "NA"])]

    # Normalize text fields
    text_cols = ["provider", "region", "sku", "instance_family", "gpu_model", "currency", "os", "tenancy"]
    for col in text_cols:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].astype("string").str.strip()

    # Numeric conversions
    numeric_cols = ["vcpu", "memory_gb", "gpu_count", "price_per_hour_usd"]
    for col in numeric_cols:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    # Deduplicate:
    # keep the lowest price per unique infra shape
    clean_df = clean_df.sort_values(
        by=["sku", "region", "price_per_hour_usd"],
        ascending=[True, True, True]
    )

    clean_df = clean_df.drop_duplicates(
        subset=["provider", "region", "sku", "vcpu", "memory_gb", "gpu_count", "os", "tenancy"],
        keep="first"
    )

    # Final sort for readability
    clean_df = clean_df.sort_values(
        by=["region", "instance_family", "sku", "price_per_hour_usd"],
        ascending=[True, True, True, True]
    ).reset_index(drop=True)

    return clean_df


def main() -> None:
    print("Fetching raw AWS GPU catalog...")
    raw_df = fetch_aws_gpu_prices()
    print(f"Raw rows: {len(raw_df)}")

    print("Saving raw catalog...")
    save_dataframe(raw_df, RAW_OUTPUT)

    print("Cleaning catalog...")
    clean_df = clean_aws_gpu_catalog(raw_df)
    print(f"Clean rows: {len(clean_df)}")

    print("Saving cleaned catalog...")
    save_dataframe(clean_df, CLEAN_OUTPUT_PARQUET)
    save_dataframe(clean_df, CLEAN_OUTPUT_CSV)

    print("\nSaved files:")
    print(RAW_OUTPUT)
    print(CLEAN_OUTPUT_PARQUET)
    print(CLEAN_OUTPUT_CSV)

    print("\nPreview:")
    print(clean_df.head(10))

    print("\nShape:")
    print(clean_df.shape)


if __name__ == "__main__":
    main()