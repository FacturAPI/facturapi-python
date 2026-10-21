import datetime as dt

import httpx
import pytest

from facturapi.http.client import Client
from facturapi.types import BaseQuery
from facturapi.types.exc import FacturapiResponseException


def test_auth_without_env():
    client = Client()
    assert not client.api_key


def test_auth_configure():
    client = Client()
    client.configure('some_api_key')
    assert client.api_key == 'some_api_key'


@pytest.mark.vcr
def test_invalid_auth():
    client = Client()
    with pytest.raises(FacturapiResponseException) as e:
        client.get('/invoices')
    assert e.value.status_code == 401
    assert str(e.value)


@pytest.mark.usefixtures('facturapi_creds')
def test_env_auth():
    client = Client()
    assert client.api_key == 'some_api_key'


@pytest.mark.usefixtures('facturapi_creds')
def test_override_with_configure():
    client = Client()
    client.configure('some_api_key2')
    assert client.api_key == 'some_api_key2'


def test_query_params_use_openapi_deep_object_encoding():
    request = None

    def handler(value: httpx.Request) -> httpx.Response:
        nonlocal request
        request = value
        return httpx.Response(
            200,
            json={'ok': True},
            headers={'Content-Type': 'application/json'},
        )

    client = Client('test_key')
    headers = dict(client.client.headers)
    client.client.close()
    client.client = httpx.Client(
        transport=httpx.MockTransport(handler), headers=headers
    )
    client.get(
        '/invoices',
        params={
            'date': {'gte': dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)},
            'status': ['valid', 'canceled'],
            'draft': False,
            'empty': None,
        },
    )

    assert request is not None
    assert request.headers['authorization'] == 'Bearer test_key'
    assert request.url.params.multi_items() == [
        ('date[gte]', '2026-01-01T00:00:00+00:00'),
        ('status', 'valid'),
        ('status', 'canceled'),
        ('draft', 'false'),
    ]


def test_binary_response_is_returned_as_bytes():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b'%PDF',
            headers={'Content-Type': 'application/pdf'},
        )

    client = Client('test_key')
    headers = dict(client.client.headers)
    client.client.close()
    client.client = httpx.Client(
        transport=httpx.MockTransport(handler), headers=headers
    )

    assert client.get('/invoices/inv_123/pdf') == b'%PDF'


def test_non_json_error_response():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text='temporarily unavailable')

    client = Client('test_key')
    headers = dict(client.client.headers)
    client.client.close()
    client.client = httpx.Client(
        transport=httpx.MockTransport(handler), headers=headers
    )

    with pytest.raises(FacturapiResponseException) as exc_info:
        client.get('/check')

    assert exc_info.value.status_code == 503
    assert str(exc_info.value) == 'temporarily unavailable'


@pytest.mark.parametrize('body', ['gateway unavailable', ['bad gateway']])
def test_non_object_json_error_response(body):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(502, json=body)

    client = Client('test_key')
    headers = dict(client.client.headers)
    client.client.close()
    client.client = httpx.Client(
        transport=httpx.MockTransport(handler), headers=headers
    )

    with pytest.raises(FacturapiResponseException) as exc_info:
        client.get('/check')

    assert exc_info.value.status_code == 502
    assert str(exc_info.value) == str(body)


def test_response_modes_and_multipart_request():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith('/explicit-json'):
            return httpx.Response(200, content=b'{"ok": true}', headers={})
        return httpx.Response(
            200,
            text='plain response',
            headers={'Content-Type': 'text/plain'},
        )

    client = Client('test_key', headers={'X-Test': 'true'})
    headers = dict(client.client.headers)
    client.client.close()
    client.client = httpx.Client(
        transport=httpx.MockTransport(handler), headers=headers
    )

    assert client.get('/text', response_type='text') == 'plain response'
    assert client.get('/text') == 'plain response'
    assert client.get('/explicit-json', response_type='json') == {'ok': True}
    client.post(
        '/upload',
        {'password': 'secret'},
        files={'file': ('file.txt', b'content', 'text/plain')},
    )

    content_type = requests[-1].headers['content-type']
    assert content_type.startswith('multipart/form-data')
    assert requests[-1].headers['x-test'] == 'true'


def test_client_helpers_and_context_manager():
    assert Client._serialize(BaseQuery(q='test')) == {'q': 'test'}
    assert Client._query_items(None) is None

    with Client('test_key') as client:
        assert client.__enter__() is client


def test_response_exception_code():
    error = FacturapiResponseException(
        json={'message': 'bad request', 'code': 123}, status_code=400
    )
    assert error.code == '123'
