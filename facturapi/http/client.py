import os
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from enum import Enum
from typing import Any
from urllib.parse import urljoin

import httpx
from httpx import Response

from ..types.exc import FacturapiResponseException
from ..version import CLIENT_VERSION

API_HOST = 'https://www.facturapi.io/v2/'
FACTURAPI_TIMEOUT = float(os.getenv('FACTURAPI_TIMEOUT', 10.0))

QueryParams = Mapping[str, Any] | Sequence[tuple[str, Any]]


class Client:
    """Client to perform http requests to Facturapi.

    By default it inits and uses an `API_KEY` configured as
    an environment variable `FACTURAPI_KEY`, if the key
    is going to be set latter, the method `configure()`
    can be used.

    Attributes:
        host (str): Base URL to perform requests.
        client (httpx.Client): The httpx client used
            to perform requests.
        api_key (str): API KEY for Facturapi

    """

    host: str = API_HOST
    client: httpx.Client

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = API_HOST,
        timeout: float = FACTURAPI_TIMEOUT,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.host = base_url.rstrip('/') + '/'
        self.client = httpx.Client(timeout=timeout)
        self.client.headers.update(
            {
                'User-Agent': f'facturapi-python/{CLIENT_VERSION}',
                'Accept': 'application/json',
            }
        )
        if headers:
            self.client.headers.update(headers)

        # Auth
        self.api_key = api_key or os.getenv('FACTURAPI_KEY', '')
        self._set_auth()

    def configure(self, api_key: str) -> None:
        """Configure the http client.

        Import the client and configure it passing the `API_KEY`
        instead of configuring it as an environment variable.

        Args:
            api_key: Facturapi `API_KEY`

        """
        self.api_key = api_key
        self._set_auth()

    def _set_auth(self) -> None:
        """Set the current Bearer token without leaking it to other clients."""
        if self.api_key:
            self.client.headers['Authorization'] = f'Bearer {self.api_key}'
        else:
            self.client.headers.pop('Authorization', None)

    def get(
        self,
        endpoint: str,
        params: QueryParams | None = None,
        **kwargs: Any,
    ) -> Any:
        """Performs GET request to Facturapi."""
        return self.request('get', endpoint, params=params, **kwargs)

    def post(
        self,
        endpoint: str,
        data: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Performs POST request to Facturapi."""
        return self.request('post', endpoint, data=data, **kwargs)

    def put(
        self,
        endpoint: str,
        data: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Performs PUT request to Facturapi."""
        return self.request('put', endpoint, data=data, **kwargs)

    def delete(
        self,
        endpoint: str,
        params: QueryParams | None = None,
        **kwargs: Any,
    ) -> Any:
        """Performs DELETE request to Facturapi."""
        return self.request('delete', endpoint, params=params, **kwargs)

    def request(
        self,
        method: str,
        endpoint: str,
        params: QueryParams | None = None,
        data: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        response_type: str = 'auto',
        **kwargs: Any,
    ) -> Any:
        """Performs a request to Facturapi.

        Given a `method` and `endpoint`, perform a request to
        Facturapi.

        Args:
            method: HTTP method of the request.
            endpoint: Endpoint to make the request to.
            params: URL encoded parameters. Defaults to `None`.
            data: JSON data to be sent. Defaults to `None`.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            dict[str, Any]: JSON of the request's response.

        Raises:
            FacturapiResponseException: If response is not
                successful.

        """
        request_kwargs: dict[str, Any] = dict(kwargs)
        if files is not None:
            request_kwargs['files'] = files
            request_kwargs['data'] = dict(data or {})
        elif data is not None:
            request_kwargs['json'] = self._serialize(data)

        response = self.client.request(
            method=method,
            url=urljoin(self.host, endpoint.lstrip('/')),
            params=(
                httpx.QueryParams(self._query_items(params))
                if params is not None
                else None
            ),
            **request_kwargs,
        )
        self._check_response(response)
        if response_type == 'bytes':
            return response.content
        if response_type == 'text':
            return response.text

        content_type = response.headers.get('content-type', '').lower()
        if 'json' in content_type:
            return response.json()
        if response_type == 'json':
            return response.json()
        if content_type.startswith('text/'):
            return response.text
        return response.content

    def download_request(
        self,
        endpoint: str,
        **kwargs,
    ) -> bytes:
        """Performs a GET request handling a file download.

        Args:
            endpoint: Endpoint to make the request to.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bytes: Bytes of the requested file.

        Raises:
            FacturapiResponseException: If response is not
                successful.

        """
        return self.request('GET', endpoint, response_type='bytes', **kwargs)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self.client.close()

    def __enter__(self) -> 'Client':
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    @classmethod
    def _serialize(cls, value: Any) -> Any:
        if hasattr(value, 'model_dump'):
            return cls._serialize(
                value.model_dump(exclude_none=True, exclude_unset=True)
            )
        if isinstance(value, Mapping):
            return {key: cls._serialize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._serialize(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Enum):
            return value.value
        return value

    @classmethod
    def _query_items(
        cls, params: QueryParams | None
    ) -> list[tuple[str, str | int | float | bool | None]] | None:
        """Encode deep objects and arrays according to the OpenAPI contract."""
        if params is None:
            return None
        source = params.items() if isinstance(params, Mapping) else params
        items: list[tuple[str, str | int | float | bool | None]] = []

        def append(key: str, value: Any) -> None:
            if value is None:
                return
            if isinstance(value, Mapping):
                for child_key, child_value in value.items():
                    append(f'{key}[{child_key}]', child_value)
                return
            if isinstance(value, (list, tuple, set)):
                for child_value in value:
                    append(key, child_value)
                return
            value = cls._serialize(value)
            if isinstance(value, bool):
                rendered = str(value).lower()
            else:
                rendered = str(value)
            items.append((key, rendered))

        for key, value in source:
            append(str(key), value)
        return items

    @staticmethod
    def _check_response(response: Response) -> None:
        if not response.is_success:
            try:
                parsed = response.json()
                body = (
                    parsed
                    if isinstance(parsed, dict)
                    else {'message': str(parsed)}
                )
            except ValueError:
                body = {'message': response.text or response.reason_phrase}
            raise FacturapiResponseException(
                json=body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
