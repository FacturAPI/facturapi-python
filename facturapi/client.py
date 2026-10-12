"""Modern, instance-based Facturapi client.

The resource classes imported here are generated from Facturapi's OpenAPI
document.  The legacy ``facturapi.Customer`` and ``facturapi.Invoice`` APIs
remain available for backwards compatibility.
"""

from collections.abc import Mapping
from typing import Any

from ._generated import (
    CartaPorteCatalogs,
    Catalogs,
    ComercioExteriorCatalogs,
    Customers,
    Invoices,
    NominaCatalogs,
    Organizations,
    Products,
    Receipts,
    Retentions,
    Tools,
    Webhooks,
)
from .http.client import API_HOST, FACTURAPI_TIMEOUT, Client


class Facturapi:
    """Synchronous client for every operation in the Facturapi API.

    Args:
        api_key: Test, Live, or User API key. If omitted, ``FACTURAPI_KEY`` is
            read from the environment.
        base_url: API base URL. Override this for tests or compatible proxies.
        timeout: Request timeout in seconds.
        headers: Extra default request headers.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = API_HOST,
        timeout: float = FACTURAPI_TIMEOUT,
        headers: Mapping[str, str] | None = None,
        http_client: Client | None = None,
    ) -> None:
        self.http = http_client or Client(
            api_key,
            base_url=base_url,
            timeout=timeout,
            headers=headers,
        )
        self.customers = Customers(self.http)
        self.products = Products(self.http)
        self.invoices = Invoices(self.http)
        self.receipts = Receipts(self.http)
        self.retentions = Retentions(self.http)
        self.organizations = Organizations(self.http)
        self.webhooks = Webhooks(self.http)
        self.tools = Tools(self.http)
        self.catalogs = Catalogs(self.http)
        self.nomina_catalogs = NominaCatalogs(self.http)
        self.carta_porte_catalogs = CartaPorteCatalogs(self.http)
        self.comercio_exterior_catalogs = ComercioExteriorCatalogs(self.http)

    @property
    def base_url(self) -> str:
        return self.http.host

    @base_url.setter
    def base_url(self, value: str) -> None:
        self.http.host = value.rstrip('/') + '/'

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> 'Facturapi':
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


FacturAPI = Facturapi
