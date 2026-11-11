from datetime import datetime, timezone
from typing import List, Dict, Any
import requests
import pandas as pd

AZURE_API_URL = "https://prices.azure.com/api/retail/prices"

# Curated GPU VM SKUs for v1.
# These are common Azure GPU families and are good enough for a serious prototype.
AZURE_GPU_SKUS = [
    "Standard_NC4as_T4_v3",
    "Standard_NC8as_T4_v3",
    "Standard_NC16as_T4_v3",
    "Standard_NC64as_T4_v3",
    "Standard_NC24ads_A100_v4",
    "Standard_NC48ads_A100_v4",
    "Standard_NC96ads_A100_v4",
    "Standard_ND40rs_v2",
    "Standard_ND96asr_v4",
    "Standard_NV6",
    "Standard_NV12",
    "Standard_NV24",
]

# Start with a focused region set for v1.
AZURE_REGIONS = [
    "eastus",
    "eastus2",
    "southcentralus",
    "westus2",
    "westeurope",
]

SCHEMA = [
    "provider",
    "region",
    "sku",
    "instance_family",
    "vcpu",
    "memory_gb",
    "gpu_count",
    "gpu_model",
    "price_per_hour_usd",
    "currency",
    "os",
    "tenancy",
    "raw_source",
    "ingested_at",
]


def empty_azure_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=SCHEMA)


def build_query_url(region: str, sku: str) -> str:
    # Azure docs support filtering by serviceName, armRegionName, armSkuName, and priceType.
    # We query only the exact SKU + region + consumption price.
    return (
        f"{AZURE_API_URL}"
        f"?$filter=serviceName eq 'Virtual Machines'"
        f" and armRegionName eq '{region}'"
        f" and armSkuName eq '{sku}'"
        f" and priceType eq 'Consumption'"
    )


def extract_rows_from_items(items: List[Dict[str, Any]], ingested_at: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for item in items:
        retail_price = item.get("retailPrice")
        if retail_price is None:
            continue

        sku = item.get("armSkuName") or item.get("skuName")
        if not sku:
            continue

        rows.append(
            {
                "provider": "azure",
                "region": item.get("armRegionName") or item.get("location"),
                "sku": sku,
                "instance_family": sku.split("_")[1] if "_" in sku else sku,
                "vcpu": None,
                "memory_gb": None,
                "gpu_count": None,
                "gpu_model": None,
                "price_per_hour_usd": retail_price,
                "currency": item.get("currencyCode"),
                "os": item.get("productName"),
                "tenancy": None,
                "raw_source": AZURE_API_URL,
                "ingested_at": ingested_at,
            }
        )

    return rows


def fetch_azure_gpu_prices() -> pd.DataFrame:
    print("Requesting Azure GPU pricing with targeted SKU-region queries...")

    ingested_at = datetime.now(timezone.utc).isoformat()
    rows: List[Dict[str, Any]] = []

    total_queries = len(AZURE_GPU_SKUS) * len(AZURE_REGIONS)
    query_num = 0

    for region in AZURE_REGIONS:
        for sku in AZURE_GPU_SKUS:
            query_num += 1
            url = build_query_url(region=region, sku=sku)
            print(f"Query {query_num}/{total_queries}: region={region}, sku={sku}")

            response = requests.get(url, timeout=120)
            response.raise_for_status()

            payload = response.json()
            items = payload.get("Items", [])

            extracted = extract_rows_from_items(items, ingested_at=ingested_at)
            rows.extend(extracted)

    if not rows:
        print("Azure GPU rows fetched: 0")
        return empty_azure_dataframe()

    df = pd.DataFrame(rows, columns=SCHEMA)
    print(f"Azure GPU rows fetched: {len(df)}")
    return df