__all__ = [
    '__version__',
    'Customer',
    'FacturAPI',
    'Facturapi',
    'Invoice',
    'configure',
]

from .client import FacturAPI, Facturapi
from .http import client
from .resources import Customer, Invoice
from .version import __version__

configure = client.configure
