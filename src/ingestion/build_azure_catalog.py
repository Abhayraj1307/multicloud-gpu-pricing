import pandas as pd

from src.ingestion.azure_pricing import fetch_azure_gpu_prices, SCHEMA
from src.utils.io import save_dataframe
from src.config import PROCESSED_DIR


RAW_OUTPUT = PROCESSED_DIR / "azure_gpu_catalog_raw.parquet"
CLEAN_OUTPUT_PARQUET = PROCESSED_DIR / "azure_gpu_catalog_clean.parquet"
CLEAN_OUTPUT_CSV = PROCESSED_DIR / "azure_gpu_catalog_clean.csv"


def ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    safe_df = df.copy()

    for col in SCHEMA:
        if col not in safe_df.columns:
            safe_df[col] = None

    return safe_df[SCHEMA]


def clean_azure_gpu_catalog(df: pd.DataFrame) -> pd.DataFrame:
    clean_df = ensure_schema(df)

    if clean_df.empty:
        return clean_df

    clean_df = clean_df.dropna(subset=["sku", "region", "price_per_hour_usd"])

    text_cols = [
        "provider",
        "region",
        "sku",
        "instance_family",
        "gpu_model",
        "currency",
        "os",
        "tenancy",
    ]

    for col in text_cols:
        clean_df[col] = clean_df[col].astype("string").str.strip()

    numeric_cols = ["vcpu", "memory_gb", "gpu_count", "price_per_hour_usd"]
    for col in numeric_cols:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    clean_df = clean_df.sort_values(
        by=["sku", "region", "price_per_hour_usd"],
        ascending=[True, True, True],
    )

    clean_df = clean_df.drop_duplicates(
        subset=["provider", "region", "sku", "os"],
        keep="first",
    )

    clean_df = clean_df.sort_values(
        by=["region", "instance_family", "sku", "price_per_hour_usd"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)

    return clean_df


def main() -> None:
    print("Fetching raw Azure GPU catalog...")
    raw_df = fetch_azure_gpu_prices()
    raw_df = ensure_schema(raw_df)
    print(f"Raw rows: {len(raw_df)}")

    print("Saving raw catalog...")
    save_dataframe(raw_df, RAW_OUTPUT)

    print("Cleaning catalog...")
    clean_df = clean_azure_gpu_catalog(raw_df)
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