from src.ingestion.aws_pricing import fetch_aws_gpu_prices


def main():
    print("Starting AWS GPU pricing ingestion test...\n")

    df = fetch_aws_gpu_prices()

    print("\nPreview of data:")
    print(df.head())

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())


if __name__ == "__main__":
    main()