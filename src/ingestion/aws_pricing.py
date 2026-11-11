from datetime import datetime, timezone
import requests
import pandas as pd

# Use regional AWS pricing file to avoid huge global JSON
AWS_EC2_PRICE_URL = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.json"

# GPU instance prefixes
GPU_PREFIXES = ("g4", "g5", "g6", "p2", "p3", "p4", "p5", "trn", "inf")


def is_gpu_instance(instance_type: str) -> bool:
    if not instance_type:
        return False
    return instance_type.lower().startswith(GPU_PREFIXES)


def fetch_aws_gpu_prices() -> pd.DataFrame:
    print("Requesting AWS EC2 regional pricing JSON...")

    response = requests.get(AWS_EC2_PRICE_URL, timeout=120)
    response.raise_for_status()

    print("Parsing AWS JSON...")
    payload = response.json()

    products = payload.get("products", {})
    terms = payload.get("terms", {}).get("OnDemand", {})

    ingested_at = datetime.now(timezone.utc).isoformat()

    rows = []

    for sku, product in products.items():

        attrs = product.get("attributes", {})
        instance_type = attrs.get("instanceType")

        # skip non GPU instances
        if not is_gpu_instance(instance_type):
            continue

        os_name = attrs.get("operatingSystem")
        if os_name not in {"Linux", "NA"}:
            continue

        price_per_hour = None
        sku_terms = terms.get(sku, {})

        for _, offer_term in sku_terms.items():
            for _, dim in offer_term.get("priceDimensions", {}).items():
                if dim.get("unit") == "Hrs":
                    usd = dim.get("pricePerUnit", {}).get("USD")
                    if usd:
                        price_per_hour = float(usd)
                        break
            if price_per_hour is not None:
                break

        memory = attrs.get("memory")
        memory_gb = None
        if memory and " GiB" in memory:
            memory_gb = float(memory.replace(" GiB", ""))

        gpu_count = attrs.get("gpu")

        rows.append({
            "provider": "aws",
            "region": attrs.get("location"),
            "sku": instance_type,
            "instance_family": instance_type.split(".")[0] if instance_type else None,
            "vcpu": float(attrs["vcpu"]) if attrs.get("vcpu") else None,
            "memory_gb": memory_gb,
            "gpu_count": float(gpu_count) if gpu_count else None,
            "gpu_model": attrs.get("physicalProcessor"),
            "price_per_hour_usd": price_per_hour,
            "currency": "USD",
            "os": os_name,
            "tenancy": attrs.get("tenancy"),
            "raw_source": AWS_EC2_PRICE_URL,
            "ingested_at": ingested_at,
        })

    df = pd.DataFrame(rows)

    print(f"AWS GPU rows fetched: {len(df)}")

    return df