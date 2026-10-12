#!/usr/bin/env python3
"""Generate Facturapi resource clients from the public OpenAPI document.

The generator intentionally creates a small, stable SDK layer rather than a
large model tree. Request and response payloads remain ordinary mappings while
every documented operation gets an explicit, discoverable Python method.
"""

from __future__ import annotations

import argparse
import json
import keyword
import re
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

OPENAPI_URL = 'https://docs.facturapi.io/redocusaurus/api-en.yaml'
HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete'}

TAG_SERVICES = {
    'carta_porte_keys': ('carta_porte_catalogs', 'CartaPorteCatalogs'),
    'comercio_exterior_keys': (
        'comercio_exterior_catalogs',
        'ComercioExteriorCatalogs',
    ),
    'customer': ('customers', 'Customers'),
    'product': ('products', 'Products'),
    'invoice': ('invoices', 'Invoices'),
    'receipt': ('receipts', 'Receipts'),
    'retention': ('retentions', 'Retentions'),
    'organization': ('organizations', 'Organizations'),
    'organization_access': ('organizations', 'Organizations'),
    'webhooks': ('webhooks', 'Webhooks'),
    'tools': ('tools', 'Tools'),
    'sat_keys': ('catalogs', 'Catalogs'),
    'nomina_keys': ('nomina_catalogs', 'NominaCatalogs'),
}

FALLBACK_OPERATIONS = {
    ('GET', '/check'): ('tools', 'health_check'),
    ('GET', '/tools/tax_id_validation'): ('tools', 'validate_tax_id'),
    ('GET', '/catalogs/products'): ('catalogs', 'search_products'),
    ('GET', '/catalogs/units'): ('catalogs', 'search_units'),
}

QUERY_ARGUMENTS = {
    ('GET', '/tools/tax_id_validation'): ('tax_id',),
}

METHOD_OVERRIDES = {
    'uploadOrganizationFiel': 'upload_fiel',
    # Keep parity with the current Node SDK where the OpenAPI samples lag.
    'getSeriesGroup': 'list_series_group',
    'createSeriesGroup': 'create_series_group',
    'updateSeriesGroup': 'update_series_group',
    'deleteSeriesGroup': 'delete_series_group',
}

# A single OpenAPI operation accepts ``format``. These aliases provide the
# same convenient methods as facturapi-node while retaining a generic method.
FORMAT_ALIASES = {
    ('GET', '/invoices/{invoice_id}/{format}'): (
        'download',
        ('pdf', 'xml', 'zip'),
    ),
    ('GET', '/invoices/{invoice_id}/cancellation_receipt/{format}'): (
        'download_cancellation_receipt',
        ('pdf', 'xml'),
    ),
    ('GET', '/invoices/{invoice_id}/download-url/{format}'): (
        'download_url',
        ('pdf', 'xml', 'zip'),
    ),
    (
        'GET',
        '/invoices/{invoice_id}/cancellation_receipt/download-url/{format}',
    ): ('download_cancellation_receipt_url', ('pdf', 'xml')),
    ('GET', '/retentions/{retention_id}/{format}'): (
        'download',
        ('pdf', 'xml', 'zip'),
    ),
    ('GET', '/retentions/{retention_id}/download-url/{format}'): (
        'download_url',
        ('pdf', 'xml', 'zip'),
    ),
}


def camel_to_snake(value: str) -> str:
    value = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', value)
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
    return re.sub(r'[^a-zA-Z0-9_]+', '_', value).strip('_').lower()


def python_name(value: str) -> str:
    value = camel_to_snake(value)
    if keyword.iskeyword(value):
        value += '_'
    return value


def load_document(source: str) -> dict[str, Any]:
    if source.startswith(('http://', 'https://')):
        with urllib.request.urlopen(source) as response:  # noqa: S310
            raw = response.read().decode()
    else:
        raw = Path(source).read_text()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - developer guidance
            raise SystemExit(
                'PyYAML is required for YAML specs: pip install PyYAML'
            ) from exc
        return yaml.safe_load(raw)


def resolve(document: dict[str, Any], value: Any) -> Any:
    while isinstance(value, dict) and '$ref' in value:
        ref = value['$ref']
        if not ref.startswith('#/'):
            return value
        target: Any = document
        for part in ref[2:].split('/'):
            target = target[part.replace('~1', '/').replace('~0', '~')]
        value = target
    return value


def node_method(operation: dict[str, Any]) -> tuple[str, str] | None:
    pattern = re.compile(
        r'facturapi\s*\.\s*([A-Za-z]\w*)\s*\.\s*' r'([A-Za-z]\w*)\s*\('
    )
    for sample in operation.get('x-codeSamples', []):
        lang = str(sample.get('lang', '')).lower()
        label = str(sample.get('label', '')).lower()
        if lang not in {'javascript', 'node.js'} and label != 'node.js':
            continue
        match = pattern.search(sample.get('source', ''))
        if match:
            service, method = match.groups()
            if method == 'del':
                method = 'delete'
            return camel_to_snake(service), camel_to_snake(method)
    return None


def fallback_method(operation_id: str, service: str) -> str:
    if operation_id in METHOD_OVERRIDES:
        return METHOD_OVERRIDES[operation_id]
    method = camel_to_snake(operation_id)
    tokens = service.rstrip('s').split('_')
    for token in tokens:
        method = re.sub(rf'(^|_){re.escape(token)}(?=_|$)', r'\1', method)
    return method.replace('__', '_').strip('_')


def path_parameters(path: str) -> list[str]:
    return [python_name(item) for item in re.findall(r'{([^}]+)}', path)]


def request_body(
    document: dict[str, Any], operation: dict[str, Any]
) -> tuple[bool, bool, bool]:
    body = operation.get('requestBody')
    if not body:
        return False, False, False
    body = resolve(document, body)
    content = body.get('content', {})
    multipart = 'multipart/form-data' in content
    return True, bool(body.get('required')), multipart


def has_query_parameters(
    document: dict[str, Any],
    path_item: dict[str, Any],
    operation: dict[str, Any],
) -> bool:
    parameters = [
        *path_item.get('parameters', []),
        *operation.get('parameters', []),
    ]
    return any(
        resolve(document, item).get('in') == 'query' for item in parameters
    )


def binary_response(
    document: dict[str, Any], operation: dict[str, Any]
) -> bool:
    for status, response in operation.get('responses', {}).items():
        if not str(status).startswith('2'):
            continue
        response = resolve(document, response)
        content_types = set(response.get('content', {}))
        if content_types and not any('json' in item for item in content_types):
            return True
    return False


def operation_name(
    method: str,
    path: str,
    operation: dict[str, Any],
    tag: str,
) -> tuple[str, str]:
    fallback = FALLBACK_OPERATIONS.get((method, path))
    if fallback:
        return fallback
    service, _ = TAG_SERVICES[tag]
    operation_id = operation.get('operationId')
    if operation_id in METHOD_OVERRIDES:
        return service, METHOD_OVERRIDES[operation_id]
    sample_name = node_method(operation)
    if sample_name:
        sample_service, sample_method = sample_name
        return sample_service, sample_method
    if not operation_id:
        raise ValueError(f'Missing operationId/name for {method} {path}')
    return service, fallback_method(operation_id, service)


def render_method(
    *,
    document: dict[str, Any],
    path_item: dict[str, Any],
    method: str,
    path: str,
    operation: dict[str, Any],
    name: str,
    fixed_format: str | None = None,
) -> list[str]:
    path_args = path_parameters(path)
    if fixed_format:
        path_args.remove('format')
    has_body, body_required, multipart = request_body(document, operation)
    has_query = has_query_parameters(document, path_item, operation)
    query_arguments = QUERY_ARGUMENTS.get((method, path), ())
    parameters = [f'{item}: str' for item in path_args]
    if multipart:
        parameters.append('files: Mapping[str, Any]')
        parameters.append('data: Mapping[str, Any] | None = None')
    elif has_body:
        default = '' if body_required else ' | None = None'
        parameters.append(f'data: Mapping[str, Any]{default}')
    parameters.extend(f'{item}: str' for item in query_arguments)
    if has_query and not query_arguments:
        parameters.append('params: QueryParams | None = None')

    signature = ', '.join(['self', *parameters])
    summary = operation.get('summary') or operation.get('operationId') or name
    operation_id = operation.get('operationId') or f'{method} {path}'
    values = ', '.join(f"'{item}': {item}" for item in path_args)
    if fixed_format:
        values = ', '.join(
            filter(None, [values, f"'format': '{fixed_format}'"])
        )
    args = [repr(method), repr(path)]
    if values:
        args.append(f'path_params={{{values}}}')
    if query_arguments:
        query_values = ', '.join(
            f"'{item}': {item}" for item in query_arguments
        )
        args.append(f'params={{{query_values}}}')
    elif has_query:
        args.append('params=params')
    if multipart:
        args.extend(['data=data', 'files=files'])
    elif has_body:
        args.append('data=data')
    if binary_response(document, operation):
        args.append("response_type='bytes'")

    return [
        f'    def {name}({signature}) -> Any:',
        f'        """{summary}.',
        '',
        f'        OpenAPI operation: ``{operation_id}``.',
        f'        Endpoint: ``{method} {path}``.',
        '        """',
        f"        return self._request({', '.join(args)})",
        '',
    ]


def generate(document: dict[str, Any]) -> str:
    services: dict[str, dict[str, Any]] = defaultdict(dict)
    operations: list[tuple[Any, ...]] = []

    for path, path_item in document['paths'].items():
        for verb, operation in path_item.items():
            if verb.lower() not in HTTP_METHODS:
                continue
            method = verb.upper()
            tag = operation.get('tags', ['tools'])[0]
            service, class_name = TAG_SERVICES[tag]
            resolved_service, name = operation_name(
                method, path, operation, tag
            )
            if resolved_service != service:
                service = resolved_service
                class_name = next(
                    item[1]
                    for item in TAG_SERVICES.values()
                    if item[0] == service
                )
            record = (document, path_item, method, path, operation)

            format_alias = FORMAT_ALIASES.get((method, path))
            if format_alias:
                generic_name, formats = format_alias
                services[class_name][generic_name] = (
                    *record,
                    generic_name,
                    None,
                )
                for value in formats:
                    alias = f'{generic_name}_{value}'
                    if generic_name.endswith('_url'):
                        alias = f'{generic_name[:-4]}_{value}_url'
                    services[class_name][alias] = (*record, alias, value)
            else:
                if name in services[class_name]:
                    raise ValueError(
                        f'Duplicate generated method {class_name}.{name}'
                    )
                services[class_name][name] = (*record, name, None)
            operations.append((method, path, operation.get('operationId')))

    class_order = [
        'Customers',
        'Products',
        'Invoices',
        'Receipts',
        'Retentions',
        'Organizations',
        'Webhooks',
        'Tools',
        'Catalogs',
        'NominaCatalogs',
        'CartaPorteCatalogs',
        'ComercioExteriorCatalogs',
    ]
    output = [
        '# This file is generated by scripts/generate_openapi.py.',
        '# Do not edit it by hand.',
        '',
        'from collections.abc import Mapping',
        'from typing import Any',
        'from urllib.parse import quote',
        '',
        'from .http.client import Client, QueryParams',
        '',
        f"OPENAPI_VERSION = {document['info']['version']!r}",
        f'OPENAPI_OPERATION_COUNT = {len(operations)}',
        '',
        '',
        'class _Service:',
        '    def __init__(self, client: Client) -> None:',
        '        self._client = client',
        '',
        '    def _request(',
        '        self,',
        '        method: str,',
        '        path: str,',
        '        *,',
        '        path_params: Mapping[str, Any] | None = None,',
        '        params: QueryParams | None = None,',
        '        data: Mapping[str, Any] | None = None,',
        '        files: Mapping[str, Any] | None = None,',
        "        response_type: str = 'auto',",
        '    ) -> Any:',
        '        for key, value in (path_params or {}).items():',
        "            encoded = quote(str(value), safe='')",
        "            path = path.replace('{' + key + '}', encoded)",
        '        return self._client.request(',
        '            method,',
        '            path,',
        '            params=params,',
        '            data=data,',
        '            files=files,',
        '            response_type=response_type,',
        '        )',
        '',
        '',
    ]
    for class_name in class_order:
        output.extend([f'class {class_name}(_Service):'])
        methods = services.get(class_name, {})
        if not methods:
            output.extend(['    pass', '', ''])
            continue
        for record in methods.values():
            doc, path_item, method, path, operation, name, fixed_format = (
                record
            )
            output.extend(
                render_method(
                    document=doc,
                    path_item=path_item,
                    method=method,
                    path=path,
                    operation=operation,
                    name=name,
                    fixed_format=fixed_format,
                )
            )
        output.append('')
    rendered = '\n'.join(output).rstrip() + '\n'
    try:
        import black
    except ImportError:
        return rendered
    return black.format_str(
        rendered,
        mode=black.Mode(line_length=79, string_normalization=False),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=OPENAPI_URL)
    parser.add_argument('--output', default='facturapi/_generated.py')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    rendered = generate(load_document(args.input))
    output = Path(args.output)
    if args.check:
        if not output.exists() or output.read_text() != rendered:
            raise SystemExit(
                f'{output} is stale; run scripts/generate_openapi.py'
            )
        return
    output.write_text(rendered)
    print(f'Generated {output}')


if __name__ == '__main__':
    main()
