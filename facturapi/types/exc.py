from dataclasses import dataclass
from typing import Any


class FacturapiException(Exception):
    pass


class NoResultFound(FacturapiException):
    """No results where found"""


class MultipleResultsFound(FacturapiException):
    """One result was expected but multiple were returned"""


@dataclass
class FacturapiResponseException(FacturapiException):
    json: dict[str, Any]
    status_code: int
    headers: dict[str, str] | None = None

    @property
    def message(self) -> str:
        return str(self.json.get('message', 'Facturapi request failed'))

    @property
    def code(self) -> str | None:
        value = self.json.get('code')
        return str(value) if value is not None else None

    def __str__(self) -> str:
        return self.message
