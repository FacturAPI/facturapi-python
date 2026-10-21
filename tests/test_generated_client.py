from typing import Any

from facturapi import Facturapi
from facturapi._generated import OPENAPI_OPERATION_COUNT


class RecordingClient:
    def __init__(self) -> None:
        self.host = 'https://example.test/v2/'
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.closed = False

    def request(self, method: str, path: str, **kwargs: Any) -> dict:
        self.calls.append((method, path, kwargs))
        return {'ok': True}

    def close(self) -> None:
        self.closed = True


def test_generated_client_has_openapi_operations():
    assert OPENAPI_OPERATION_COUNT > 0


def test_resource_clients_are_exposed():
    http = RecordingClient()
    api = Facturapi(http_client=http)  # type: ignore[arg-type]

    assert api.customers
    assert api.products
    assert api.invoices
    assert api.receipts
    assert api.retentions
    assert api.organizations
    assert api.webhooks
    assert api.tools
    assert api.catalogs
    assert api.nomina_catalogs
    assert api.carta_porte_catalogs
    assert api.comercio_exterior_catalogs
    assert api.base_url == 'https://example.test/v2/'
    api.base_url = 'https://api.example.test/custom'
    assert http.host == 'https://api.example.test/custom/'


def test_generated_method_builds_path_body_and_query():
    http = RecordingClient()
    api = Facturapi(http_client=http)  # type: ignore[arg-type]

    api.customers.update(
        'cus/with spaces',
        {'email': 'test@example.com'},
        {'createEditLink': True},
    )

    assert http.calls == [
        (
            'PUT',
            '/customers/cus%2Fwith%20spaces',
            {
                'params': {'createEditLink': True},
                'data': {'email': 'test@example.com'},
                'files': None,
                'response_type': 'auto',
            },
        )
    ]


def test_format_convenience_methods_match_node_sdk():
    http = RecordingClient()
    api = Facturapi(http_client=http)  # type: ignore[arg-type]

    api.invoices.download_pdf('inv_123')
    api.invoices.download_xml_url('inv_123')
    api.retentions.download_zip('ret_123')

    assert [call[:2] for call in http.calls] == [
        ('GET', '/invoices/inv_123/pdf'),
        ('GET', '/invoices/inv_123/download-url/xml'),
        ('GET', '/retentions/ret_123/zip'),
    ]
    assert http.calls[0][2]['response_type'] == 'bytes'
    assert http.calls[1][2]['response_type'] == 'auto'


def test_multipart_operation_is_generated():
    http = RecordingClient()
    api = Facturapi(http_client=http)  # type: ignore[arg-type]
    files = {'file': ('logo.png', b'png', 'image/png')}

    api.organizations.upload_logo('org_123', files)

    _, path, kwargs = http.calls[0]
    assert path == '/organizations/org_123/logo'
    assert kwargs['files'] == files


def test_tool_method_matches_node_sdk_signature():
    http = RecordingClient()
    api = Facturapi(http_client=http)  # type: ignore[arg-type]

    api.tools.validate_tax_id('ABC101010111')

    assert http.calls[0][1] == '/tools/tax_id_validation'
    assert http.calls[0][2]['params'] == {'tax_id': 'ABC101010111'}


def test_nomina_catalog_methods_are_exposed():
    http = RecordingClient()
    api = Facturapi(http_client=http)  # type: ignore[arg-type]

    api.nomina_catalogs.search_deductions({'q': '001', 'limit': 10})
    api.nomina_catalogs.search_perceptions({'q': '001', 'limit': 10})

    assert [call[:2] for call in http.calls] == [
        ('GET', '/catalogs/deductions'),
        ('GET', '/catalogs/perceptions'),
    ]
    assert http.calls[0][2]['params'] == {'q': '001', 'limit': 10}


def test_context_manager_closes_http_client():
    http = RecordingClient()
    with Facturapi(http_client=http):  # type: ignore[arg-type]
        pass
    assert http.closed
