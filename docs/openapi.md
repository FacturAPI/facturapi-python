# Generated API client

`Facturapi` exposes every operation in the public Facturapi OpenAPI document.
Create an instance with an API key and use one of its resource clients:

```python
from facturapi import Facturapi

api = Facturapi("sk_test_...")
products = api.products.list({"page": 1, "limit": 50})
```

| Attribute | Coverage |
| --- | --- |
| `customers` | Customer CRUD, edit links, tax validation |
| `products` | Product CRUD |
| `invoices` | CRUD, drafts, cancellation, email, previews, downloads, ZIP requests |
| `receipts` | CRUD, invoice conversion, previews, email, downloads |
| `retentions` | CRUD, drafts, cancellation, email, downloads |
| `organizations` | Legal data, files, keys, domains, series, team access, roles |
| `webhooks` | CRUD and signature validation |
| `tools` | Health and RFC validation |
| `catalogs` | SAT product and unit catalogs |
| `nomina_catalogs` | Payroll deduction and perception catalogs |
| `carta_porte_catalogs` | Carta Porte 3.1 catalogs |
| `comercio_exterior_catalogs` | Foreign trade tariff fractions |

Python method names use `snake_case`. Request bodies and query parameters are
passed as dictionaries. Download operations return `bytes`.

::: facturapi.client.Facturapi
    options:
        show_source: false

## Customers

::: facturapi._generated.Customers
    options:
        show_source: false

## Products

::: facturapi._generated.Products
    options:
        show_source: false

## Invoices

::: facturapi._generated.Invoices
    options:
        show_source: false

## E-Receipts

::: facturapi._generated.Receipts
    options:
        show_source: false

## Retentions

::: facturapi._generated.Retentions
    options:
        show_source: false

## Organizations

::: facturapi._generated.Organizations
    options:
        show_source: false

## Webhooks

::: facturapi._generated.Webhooks
    options:
        show_source: false

## Tools

::: facturapi._generated.Tools
    options:
        show_source: false

## SAT catalogs

::: facturapi._generated.Catalogs
    options:
        show_source: false

## Payroll catalogs

::: facturapi._generated.NominaCatalogs
    options:
        show_source: false

## Carta Porte catalogs

::: facturapi._generated.CartaPorteCatalogs
    options:
        show_source: false

## Foreign-trade catalogs

::: facturapi._generated.ComercioExteriorCatalogs
    options:
        show_source: false
