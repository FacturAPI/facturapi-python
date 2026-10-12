<p align="center">
    <a href="https://facturapi.io">
        <img alt="Facturapi Logo" src="./docs/images/facturapi-logo.svg" width="200" />
    </a>
</p>
<h1 align="center">
    FacturAPI – Librería de Python
</h1>

![test](https://github.com/FacturAPI/facturapi-python/actions/workflows/test.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/facturapi.svg)](https://badge.fury.io/py/facturapi)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

SDK oficial de Python para https://www.facturapi.io

FacturAPI facilita la creación de facturas válidas para desarrolladores en México (Facturas Electrónicas o CFDI).

Esta librería está basada en [`cuenca-python`](https://github.com/cuenca-mx/cuenca-python) 💙.

## 💻 Instalación

Fácil, únicamente utiliza `pip` para instalar la librería:

```bash
pip install facturapi
```

## 🚀 Primeros pasos

### Cliente recomendado
Asegurate de crear una cuenta gratis en [FacturAPI](https://www.facturapi.io) y tener acceso a tus llaves de test y live.

El cliente por instancia incluye todos los métodos de la referencia de API:

```python
from facturapi import Facturapi

facturapi = Facturapi("sk_test_...")
customer = facturapi.customers.create({
    "legal_name": "Frida Kahlo",
    "tax_id": "ABCD111111CBA",
    "tax_system": "601",
    "email": "frida@example.com",
    "address": {"zip": "01234", "country": "MEX"},
})
```

También puedes omitir la llave y usar la variable de entorno
`FACTURAPI_KEY`. La API anterior basada en `facturapi.Customer` y
`facturapi.Invoice` sigue disponible por compatibilidad.

Para más detalles en los datos necesarios para crear un Cliente y otros recursos, revisa la [documentación](http://docs.facturapi.io).

Puedes encontrar más ejemplos de código de cómo crear y usar recursos en el directorio de [examples](./examples/). 

## 📚 Documentación

Encuentra más información de Facturapi y sus recursos en sus [docs](http://docs.facturapi.io).

La capa de recursos se genera automáticamente desde el documento OpenAPI de
Facturapi. El workflow semanal propone un pull request cuando la API cambia.

## 💡 Contribuye
### ¿Encontraste un bug?
Crea un `issue` explicando el problema y cómo replicarlo.

### ¿Quieres contribuir?
Haz un `fork` del respositorio y crea tu PR, ¡toda la ayuda es bienvenida y apreciada!
No olvides mantener la cobertura del código arriba de 98%, nos encanta tener código testeado. 😋 

### Contactos:
- **Facturapi:** contacto@facturapi.io

---
Desarrollado y mantenido por [Facturapi](https://facturapi.io/).
