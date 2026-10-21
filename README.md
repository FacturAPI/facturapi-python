<p align="center">
  <a href="https://facturapi.io">
    <img alt="Facturapi Logo" src="./docs/images/facturapi-logo.svg" width="200" />
  </a>
</p>

# Facturapi Python SDK

[![tests](https://github.com/FacturAPI/facturapi-python/actions/workflows/test.yml/badge.svg)](https://github.com/FacturAPI/facturapi-python/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/facturapi.svg)](https://pypi.org/project/facturapi/)
[![Python](https://img.shields.io/pypi/pyversions/facturapi.svg)](https://pypi.org/project/facturapi/)

The official synchronous Python client for the
[Facturapi API](https://docs.facturapi.io/en/api/). It supports every operation
in the public OpenAPI document while keeping the original `Customer` and
`Invoice` class API backwards compatible.

[Español](./README.es-MX.md)

## Install

```bash
pip install facturapi
```

Python 3.10 or newer is required.

## Quick start

```python
import os

from facturapi import Facturapi

facturapi = Facturapi(os.environ["FACTURAPI_KEY"])

customer = facturapi.customers.create(
    {
        "legal_name": "Dunder Mifflin",
        "tax_id": "ABC101010111",
        "tax_system": "601",
        "email": "accounting@example.com",
        "address": {"zip": "01234", "country": "MEX"},
    }
)

invoice = facturapi.invoices.create(
    {
        "customer": customer["id"],
        "payment_form": "03",
        "items": [
            {
                "quantity": 1,
                "product": {
                    "description": "Consulting",
                    "product_key": "80101500",
                    "price": 1000,
                },
            }
        ],
    }
)

pdf = facturapi.invoices.download_pdf(invoice["id"])
```

If the key is omitted, `Facturapi()` reads `FACTURAPI_KEY`. The timeout can be
set per client or through `FACTURAPI_TIMEOUT`.

```python
with Facturapi("sk_test_...", timeout=30) as facturapi:
    result = facturapi.invoices.list(
        {
            "status": ["valid", "canceled"],
            "date": {"gte": "2026-01-01T00:00:00Z"},
        }
    )
```

## API resources

The instance client follows the same resource layout as `facturapi-node`:

- `customers`
- `products`
- `invoices`
- `receipts`
- `retentions`
- `organizations`, including users, roles, API keys, certificates, and series
- `webhooks`
- `tools`
- `catalogs`
- `nomina_catalogs`
- `carta_porte_catalogs`
- `comercio_exterior_catalogs`

Methods use `snake_case`, accept normal Python dictionaries, and return decoded
JSON. Download methods return `bytes`. Multipart organization methods accept an
`httpx`-compatible `files` mapping.

```python
files = {
    "cer": ("certificate.cer", open("certificate.cer", "rb")),
    "key": ("certificate.key", open("certificate.key", "rb")),
}
facturapi.organizations.upload_certificate(
    "org_123",
    files,
    {"password": "certificate-password"},
)
```

For parameter and payload details, use the
[Facturapi API reference](https://docs.facturapi.io/en/api/). Each generated
method includes its OpenAPI operation and endpoint in its docstring.

## Backwards compatibility

The original class API still works:

```python
import facturapi
from facturapi.resources.customers import CustomerRequest

facturapi.configure(api_key="sk_test_...")
customer = facturapi.Customer.create(
    CustomerRequest(
        legal_name="Dunder Mifflin",
        tax_id="ABC101010111",
        tax_system="601",
        email="accounting@example.com",
        address={"zip": "01234", "country": "MEX"},
    )
)
```

## OpenAPI updates

The resource layer is generated from Facturapi's public OpenAPI document:

```bash
make generate
make generate-check
```

The `update-openapi-client` GitHub Actions workflow checks the current document
weekly and opens a pull request when generated methods change. Generated code
lives in `facturapi/_generated.py`; edit the generator instead of that file.

## Development and releases

```bash
make venv
make test
make build
```

Publishing uses PyPI Trusted Publishing. Maintainers publish a GitHub release;
the release workflow builds, verifies, and uploads the wheel and source archive
without a long-lived PyPI token. The PyPI project must trust the
`FacturAPI/facturapi-python` repository, the `release.yml` workflow, and the
`pypi` environment.

## License

[MIT](./LICENSE)
