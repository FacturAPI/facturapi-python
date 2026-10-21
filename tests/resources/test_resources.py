import pytest

from facturapi.resources import base
from facturapi.resources.base import Queryable
from facturapi.resources.resources import retrieve_property


def test_retrieve_wrong_uri():
    with pytest.raises(ValueError):
        retrieve_property('wrong_uri')


class CursorResource(Queryable):
    _resource = 'resources'


def test_all_follows_cursor_pagination(monkeypatch):
    pages = iter(
        [
            {
                'data': [{'id': 'resource_1'}],
                'next_cursor': 'cursor/2',
            },
            {
                'data': [{'id': 'resource_2'}],
                'next_cursor': None,
            },
        ]
    )
    requested_uris = []

    def get(uri):
        requested_uris.append(uri)
        return next(pages)

    monkeypatch.setattr(base.client, 'get', get)

    resources = list(CursorResource.all(pagination='cursor', limit=1))

    assert [resource.id for resource in resources] == [
        'resource_1',
        'resource_2',
    ]
    assert requested_uris == [
        'resources?pagination=cursor&limit=1',
        'resources?pagination=cursor&limit=1&after=cursor%2F2',
    ]
