# Multi-Cloud GPU Pricing Catalog

A Python ingestion prototype for building normalized GPU price catalogs from AWS and Azure public pricing endpoints.

## Build catalogs

~~~bash
python -m pip install -r requirements.txt
python -m src.ingestion.build_aws_catalog
python -m src.ingestion.build_azure_catalog
~~~

Review the [AWS builder](src/ingestion/build_aws_catalog.py) and [Azure builder](src/ingestion/build_azure_catalog.py). Both write raw and normalized outputs to **data/processed/**. Catalog contents and prices can change between runs.

This snapshot implements ingestion and cleaning. Workload placement and measured savings are outside the demonstrated scope.
