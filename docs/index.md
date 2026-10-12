<p align="center">
  <a href="https://facturapi.io">
    <img alt="Facturapi Logo" src="./images/facturapi-logo.svg" width="200" />
  </a>
</p>

# Facturapi Python SDK

The official synchronous Python client for Facturapi. The generated instance
client covers every operation in the public OpenAPI document, and the original
`Customer` and `Invoice` classes remain available for compatibility.

## Installation

```bash
pip install facturapi
```

## Getting started

```python
from facturapi import Facturapi

api = Facturapi("sk_test_...")
customer = api.customers.create(
    {
        "legal_name": "Dunder Mifflin",
        "tax_id": "ABC101010111",
        "tax_system": "601",
        "email": "accounting@example.com",
        "address": {"zip": "01234", "country": "MEX"},
    }
)
```

If the API key is omitted, the client reads `FACTURAPI_KEY`. See the
[generated API client](./openapi.md) for resource coverage and the
[Facturapi API reference](https://docs.facturapi.io/en/api/) for request and
response fields.
