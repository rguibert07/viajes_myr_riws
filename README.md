# Buscador de viajes por España: crawling de spain.info y Wikivoyage

Memoria de la fase de crawling del proyecto de *Recuperación de Información y Web Semántica* (RISW), Máster Universitario en Ingeniería Informática, Universidade da Coruña.

Grupo: `______`, `______`, `______`

---

## 1. Dominio y alcance

**Dominio elegido: viajes por España.** El buscador integrará información de guías y portales de turismo para responder consultas sobre destinos, regiones, rutas y propuestas de viaje.

Consultas que queremos poder resolver:

- "qué ver en Santiago de Compostela"
- "rutas de naturaleza en Andalucía"
- "gastronomía y enoturismo en La Rioja"
- "playas de las Islas Baleares"

Delimitación:

- **Qué entra:** contenido editorial en español sobre destinos, regiones, rutas y temas de viaje.
- **Qué no entra:** precios, disponibilidad, reservas y reseñas de usuarios. Los precios cambian según las fechas y las reseñas son contenido de terceros con datos personales.
- **Unidad documental:** una página (un destino, una región, una ruta o un artículo). Más adelante, para la generación de respuestas con el LLM, podremos dividir el texto en fragmentos, conservando siempre el identificador y la URL de la página.

---

## 2. Fuentes elegidas

| Spider | Sitio | Tipo | Qué aporta |
|---|---|---|---|
| `spaininfo` | https://www.spain.info/ | Portal oficial de turismo de España (Turespaña) | Destinos, regiones, rutas y artículos temáticos |
| `wikivoyage` | https://es.wikivoyage.org/ | Guía de viajes colaborativa | Guías de destinos con secciones (ver, hacer, comer, dormir) y mucho texto |

### Por qué estas dos fuentes

1. **Son sitios distintos y complementarios.** Una fuente institucional y otra colaborativa, con estructuras HTML diferentes. Esto obliga a un spider por sitio y a unificar los datos en un esquema común.
2. **El contenido está en el HTML descargado.** En la prueba inicial con `scrapy shell` sobre spain.info obtuvimos respuesta 200, unos 196 KB de HTML, 156 enlaces con rutas a destinos, regiones y secciones temáticas, y encabezados con texto real (apartado 4). No hace falta renderizar JavaScript. Wikivoyage entrega HTML estático generado por MediaWiki.
3. **El banner de cookies de spain.info no afecta.** Se inyecta con JavaScript sobre la página y Scrapy no lo ejecuta, de modo que el contenido llega igualmente.
4. **Mucho texto y enlaces entre páginas.** Es lo que necesita un buscador y permite hacer crawling real, es decir, seguir enlaces entre destinos y secciones.
5. **Datos comparables.** Ambas fuentes ofrecen título, descripción, texto, URL y tipo de página, lo que permite un esquema común (apartado 3).
6. **Rastreo permitido.** Con `ROBOTSTXT_OBEY` activado, el `robots.txt` de spain.info se descarga sin problema y no impide acceder a la portada.

### Por qué no Booking ni Expedia

Las valoramos al principio por ser las webs de viajes más conocidas y las descartamos por estos motivos:

1. **Restricciones de acceso automatizado.** Sus condiciones de uso prohíben el scraping y limitan el acceso a rutas clave, como los resultados de búsqueda. El proyecto exige respetar las reglas de cada sitio.
2. **Protección anti-bots.** Responden a clientes como Scrapy con páginas de desafío, captchas o códigos 403/429. Superarlas exigiría proxies rotativos o suplantación de navegador, algo que no consideramos adecuado en un proyecto académico.
3. **Contenido que depende de JavaScript.** Las listas de alojamientos se cargan dinámicamente, así que habría que añadir un navegador automatizado (Playwright), con más dependencias, coste y fragilidad.
4. **Poco texto para un buscador.** Lo que se puede extraer legítimamente de una ficha (nombre, puntuación, número de opiniones) es corto y estructurado. Sin precios ni reseñas, el corpus quedaría pobre.
5. **Selectores inestables.** Los atributos de sus plantillas cambian con frecuencia, lo que dificulta reproducir el trabajo entre los miembros del grupo.

> Comprobación del grupo: `______` (resultado de probar `scrapy shell` sobre Booking y Expedia: código HTTP, si había página de desafío, si las fichas aparecían en `response.text`).

### Condiciones de uso

- Uso exclusivamente académico y con volumen pequeño.
- `ROBOTSTXT_OBEY = True`, pausa entre peticiones y concurrencia baja.
- `USER_AGENT` descriptivo con un contacto real del grupo.
- El contenido de Wikivoyage se publica con licencia CC BY-SA: conservamos `url_origen` y `fuente` para poder atribuirlo.
- Revisamos `https://www.spain.info/robots.txt` y el de Wikivoyage antes de ampliar el alcance.

---

## 3. Páginas que rastreamos y campos que extraemos

### Páginas de interés

| Fuente | Semilla | Enlaces que seguimos | Se ignoran |
|---|---|---|---|
| spain.info | `https://www.spain.info/es/` | Rutas que empiezan por `/es/destino/`, `/es/region/`, `/es/ciudades/`, `/es/arte-cultura/`, `/es/costas-playas/`, `/es/naturaleza/`, `/es/gastronomia-enoturismo/`, `/es/deporte-aventura/` y `/es/rutas/` | Información práctica (visados, tax free, folletos), enlaces externos, parámetros y fragmentos de URL |
| Wikivoyage | `https://es.wikivoyage.org/wiki/Espa%C3%B1a` | Enlaces `/wiki/...` | Páginas especiales o de otros espacios de nombres (con `:`) y anclas (`#`) |

### Esquema común

Ambos spiders producen los mismos campos:

| Campo | Descripción |
|---|---|
| `id` | Identificador estable: hash SHA-256 de `url_origen` (lo genera el pipeline) |
| `titulo` | Título de la página (`h1`) |
| `descripcion` | Resumen: meta description (spain.info) o primeros párrafos (Wikivoyage) |
| `texto` | Texto completo del contenido principal, sin menú, pie ni scripts |
| `secciones` | Encabezados de sección (solo Wikivoyage; lista vacía en spain.info) |
| `ciudad`, `pais` | Localización, cuando se puede deducir; cadena vacía si no |
| `tipo` | `destino`, `region`, `ruta` o `articulo` |
| `url_origen` | URL de la página |
| `fuente` | `spain.info` o `es.wikivoyage.org` |

Diferencias entre fuentes que normalizamos: `descripcion` se obtiene de forma distinta en cada sitio; `secciones` solo existe en Wikivoyage; `ciudad` y `pais` solo se rellenan en spain.info (en Wikivoyage las páginas cubren lugares de varios países, por lo que quedan vacíos de momento).

---

## 4. Muestra de comprobación inicial

Antes de escribir los spiders comprobamos con una muestra pequeña que cada fuente da datos suficientes y comparables.

| Comprobación | spain.info | Wikivoyage |
|---|---|---|
| Código HTTP de la portada | 200 | `______` |
| `robots.txt` descargado | Sí (200) | `______` |
| Tamaño del HTML | 196.503 caracteres | `______` |
| Enlaces en la portada | 156 | `______` |
| Enlaces a destinos y secciones | Sí (`/es/destino/madrid/`, `/es/region/islas-canarias/`, `/es/rutas/`...) | `______` |
| Encabezados con texto real | Sí | `______` |
| Contenido sin JavaScript | Sí | `______` |

Comprobación hecha con `scrapy shell` el 3 de octubre de 2026. Pendiente en ambas fuentes: abrir con `fetch(...)` una página interna de destino y verificar que el selector del texto principal no arrastra menú ni restos del aviso de cookies.

---

## 5. Crawling

### Configuración (`settings.py`)

```python
BOT_NAME = "viajescrawling"

ROBOTSTXT_OBEY = True
# Sustituir por el contacto real del grupo
USER_AGENT = "RISW-practica-UDC (contacto: correo_del_grupo@udc.es)"

CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 3
AUTOTHROTTLE_ENABLED = True
CLOSESPIDER_ITEMCOUNT = 300  # límite de items por ejecución, es decir, por fuente
FEED_EXPORT_ENCODING = "utf-8"

ITEM_PIPELINES = {
    "viajescrawling.pipelines.LimpiezaPipeline": 300,
    "viajescrawling.pipelines.DuplicadosPipeline": 400,
}
```

Límites del rastreo:

- `CLOSESPIDER_ITEMCOUNT = 300` por ejecución.
- `DEPTH_LIMIT = 3` desde la semilla (configurado en cada spider).
- `allowed_domains` restringe cada spider a su sitio.
- Se mantiene el filtro de duplicados de peticiones que trae Scrapy por defecto. Es imprescindible: los menús enlazan a las mismas páginas desde todas partes y, sin él, se agotaría el límite de items con páginas repetidas.

### Spider `spaininfo`

`viajescrawling/spiders/spaininfo.py`:

```python
import re

import scrapy

from viajescrawling.items import ViajescrawlingItem


class SpainInfoSpider(scrapy.Spider):
    name = "spaininfo"
    allowed_domains = ["www.spain.info"]
    start_urls = ["https://www.spain.info/es/"]

    custom_settings = {"DEPTH_LIMIT": 3}

    PATRON = re.compile(
        r"^/es/(destino|region|ciudades|arte-cultura|costas-playas|naturaleza|"
        r"gastronomia-enoturismo|deporte-aventura|rutas)/"
    )

    def parse(self, response):
        titulo = " ".join(
            t.strip() for t in response.css("h1 *::text, h1::text").getall() if t.strip()
        )

        descripcion = (
            response.css('meta[name="description"]::attr(content)').get()
            or response.css('meta[property="og:description"]::attr(content)').get()
            or ""
        ).strip()

        # Texto del contenido principal, sin scripts, estilos, menu ni pie
        excluir = (
            "not(ancestor::script or ancestor::style or ancestor::nav "
            "or ancestor::footer or ancestor::noscript)"
        )
        fragmentos = response.xpath(f"//main//text()[{excluir}]").getall()
        if not fragmentos:
            fragmentos = response.xpath(f"//body//text()[{excluir}]").getall()
        texto = re.sub(r"\s+", " ", " ".join(fragmentos)).strip()

        ruta = response.url.split("spain.info", 1)[-1]
        if "/destino/" in ruta:
            tipo = "destino"
        elif "/region/" in ruta:
            tipo = "region"
        elif "/rutas/" in ruta:
            tipo = "ruta"
        else:
            tipo = "articulo"

        if titulo and texto:
            item = ViajescrawlingItem()
            item["titulo"] = titulo
            item["descripcion"] = descripcion
            item["texto"] = texto
            item["secciones"] = []
            item["ciudad"] = titulo if tipo == "destino" else ""
            item["pais"] = "España"
            item["tipo"] = tipo
            item["url_origen"] = response.url
            item["fuente"] = "spain.info"
            yield item

        for href in response.css("a::attr(href)").getall():
            href = href.split("#")[0].split("?")[0]
            if self.PATRON.match(href):
                yield response.follow(href, callback=self.parse)
```

### Spider `wikivoyage`

`viajescrawling/spiders/wikivoyage.py`:

```python
import re

import scrapy

from viajescrawling.items import ViajescrawlingItem


class WikivoyageSpider(scrapy.Spider):
    name = "wikivoyage"
    allowed_domains = ["es.wikivoyage.org"]
    start_urls = ["https://es.wikivoyage.org/wiki/Espa%C3%B1a"]

    custom_settings = {"DEPTH_LIMIT": 3}

    def parse(self, response):
        titulo = response.css("h1 span.mw-page-title-main::text, h1::text").get(default="").strip()

        parrafos = response.css("#mw-content-text .mw-parser-output > p")
        descripcion = " ".join(
            " ".join(p.css("*::text").getall()).strip() for p in parrafos[:3]
        )
        descripcion = re.sub(r"\s+", " ", descripcion).strip()

        secciones = [
            s.strip()
            for s in response.css(
                "#mw-content-text h2 .mw-headline::text, #mw-content-text h2::text"
            ).getall()
            if s.strip()
        ]

        texto = " ".join(
            t.strip()
            for t in response.css(
                "#mw-content-text .mw-parser-output p *::text, #mw-content-text li *::text"
            ).getall()
            if t.strip()
        )

        if titulo and texto:
            item = ViajescrawlingItem()
            item["titulo"] = titulo
            item["descripcion"] = descripcion
            item["texto"] = texto
            item["secciones"] = secciones
            item["ciudad"] = ""
            item["pais"] = ""
            item["tipo"] = "destino"
            item["url_origen"] = response.url
            item["fuente"] = "es.wikivoyage.org"
            yield item

        for href in response.css("#mw-content-text a::attr(href)").getall():
            if href.startswith("/wiki/") and ":" not in href and "#" not in href:
                yield response.follow(href, callback=self.parse)
```

---

## 6. Preparación de los datos

### Items

`viajescrawling/items.py`:

```python
import scrapy


class ViajescrawlingItem(scrapy.Item):
    id = scrapy.Field()
    titulo = scrapy.Field()
    descripcion = scrapy.Field()
    texto = scrapy.Field()
    secciones = scrapy.Field()
    ciudad = scrapy.Field()
    pais = scrapy.Field()
    tipo = scrapy.Field()
    url_origen = scrapy.Field()
    fuente = scrapy.Field()
```

### Pipelines: ruido, campos ausentes y duplicados

`viajescrawling/pipelines.py`:

```python
import hashlib

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

MIN_TEXTO = 200  # caracteres mínimos para considerar útil una página


class LimpiezaPipeline:
    def process_item(self, item, spider=None):
        a = ItemAdapter(item)

        # Ruido: espacios y saltos de línea sobrantes
        for campo in ("titulo", "descripcion", "texto"):
            a[campo] = " ".join((a.get(campo) or "").split())

        # Campos ausentes: valores por defecto coherentes en las dos fuentes
        for campo in ("ciudad", "pais", "tipo", "fuente"):
            a[campo] = a.get(campo) or ""
        a["secciones"] = a.get("secciones") or []

        # Páginas sin contenido útil
        if not a["titulo"] or not a.get("url_origen"):
            raise DropItem("Falta titulo o URL")
        if len(a["texto"]) < MIN_TEXTO:
            raise DropItem("Texto demasiado corto")

        a["id"] = hashlib.sha256(a["url_origen"].encode()).hexdigest()
        return item


class DuplicadosPipeline:
    def __init__(self):
        self.ids = set()
        self.huellas = set()

    def process_item(self, item, spider=None):
        a = ItemAdapter(item)
        huella = hashlib.sha256(a["texto"].lower().encode()).hexdigest()
        if a["id"] in self.ids or huella in self.huellas:
            raise DropItem(f"Duplicado: {a['url_origen']}")
        self.ids.add(a["id"])
        self.huellas.add(huella)
        return item
```

Decisiones de preparación:

- **Ruido:** el texto se extrae solo del contenido principal (`main` o, si no existe, `body`), excluyendo `script`, `style`, `nav`, `footer` y `noscript`, y se normalizan los espacios.
- **Duplicados:** se descartan por identificador (misma URL) y por contenido idéntico (misma huella del texto bajo URLs distintas).
- **Campos ausentes:** los textos vacíos se rellenan con cadena vacía y `secciones` con lista vacía, para que el esquema sea idéntico en las dos fuentes. Las páginas sin título, sin URL o con menos de 200 caracteres de texto se descartan.
- **Identificador estable:** el `id` se calcula a partir de la URL, de modo que al reindexar no se crean documentos duplicados.
- **Procedencia:** `fuente` y `url_origen` se conservan siempre.

---

## 7. Puesta en marcha

Entorno de desarrollo: Python 3.13 en Windows 10. Versión de Scrapy: `______`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install scrapy
python -m pip freeze > requirements.txt
```

Desde la raíz del repositorio, activa el entorno virtual como arriba y cambia a la carpeta que contiene `scrapy.cfg`. Ejecuta los crawlers desde ahí:

```powershell
Set-Location .\viajescrawling
python -m scrapy crawl spaininfo -O spaininfo.jsonl
python -m scrapy crawl wikivoyage -O wikivoyage.jsonl
python .\viajescrawling\check.py
```

Script de comprobación (`check.py`):

```python
import json
import sys

archivos = sys.argv[1:] or ["spaininfo.jsonl", "wikivoyage.jsonl"]

for nombre in archivos:
    with open(nombre, encoding="utf-8") as f:
        docs = [json.loads(linea) for linea in f]
    print("==", nombre)
    print("Documentos:", len(docs))
    print("IDs distintos:", len({d["id"] for d in docs}))
    print("Fuentes:", {d["fuente"] for d in docs})
    print("Tipos:", {t: sum(1 for d in docs if d["tipo"] == t) for t in {d["tipo"] for d in docs}})
    print("Sin descripcion:", sum(1 for d in docs if not d.get("descripcion")))
    print("Longitud media del texto:", sum(len(d["texto"]) for d in docs) // max(len(docs), 1))
    print(docs[:1])
```

---

## 8. Resultados y limitaciones

### Resultados del crawling

| | spain.info | Wikivoyage |
|---|---|---|
| Documentos obtenidos | `316` | `512` |
| IDs distintos | `316` | `512` |
| Reparto por tipo | `destino: 220, región 61, artículo: 34, ruta: 1` | `destino:512` |
| Sin descripción | `0` | `512` |
| Longitud media del texto | `3.687 caracteres` | `38.593 caracteres` |
| Descartados por duplicado o texto corto | `No registrado` | `No registrado` |

### Limitaciones conocidas

- Los selectores del contenido de spain.info son genéricos (`main`, `h1`, meta description). Hay que verificar sobre páginas reales que `texto` no incluye menú ni restos del aviso de cookies y, si los incluye, acotar el selector al contenedor del artículo.
- En Wikivoyage, el rastreo desde la página de España puede llegar a guías de otros países y a páginas que no son de destinos. `DEPTH_LIMIT` y `CLOSESPIDER_ITEMCOUNT` acotan el volumen, pero la cobertura queda condicionada por los enlaces que se siguen.
- `ciudad` y `pais` solo se informan en spain.info. Para filtrar por localización en ambas fuentes habrá que deducirlos más adelante, por ejemplo con ayuda del LLM durante la indexación.
- Las diferencias de longitud y estilo entre una web institucional y una colaborativa pueden afectar al ranking. Lo revisaremos en la fase de búsqueda.
- Si una web empieza a devolver 403 o 429, reduciremos el ritmo y conservaremos los datos ya descargados en lugar de insistir.
- En el conjunto de Wikivoyage, los 512 documentos exportados no tienen contenido en el campo `descripcion`. La recuperación deberá apoyarse inicialmente en `titulo`, `texto` y `secciones`, o deberá definirse posteriormente una estrategia para generar o extraer descripciones.
- La longitud media del texto es considerablemente mayor en Wikivoyage (38.593 caracteres) que en spain.info (3.687 caracteres). Antes de la indexación habrá que comprobar si esta diferencia procede únicamente de la extensión de las guías o si también se está extrayendo navegación, contenido repetido u otros elementos no relevantes.
- El script `check.py` valida los documentos exportados, pero no proporciona el número de elementos descartados por duplicado o texto corto. Por este motivo, ese dato no quedó registrado de forma separada en los resultados disponibles.

## 9. Indexación con Elasticsearch
### 9.1. Configuración del índice
La unidad documental es la página, con mappings con analizador en español para `titulo`,`descripcion`, `texto` y `secciones`, así como `keyword` para `ciudad`, `pais`, `tipo`, `fuente` y `url_origen`.
El índice se define como `strict` para rechazar campos no declarados.

`viajesindex/index.py`
```python
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

es.indices.create(index="viajes", settings={
    "number_of_shards": 1, "number_of_replicas": 0
}, mappings ={
    "dynamic": "strict",
    "properties": {
        "id": {"type": "keyword"},
        "ciudad": {"type": "keyword"},
        "pais": {"type": "keyword"},
        "tipo": {"type": "keyword"},
        "fuente": {"type": "keyword"},
        "url_origen": {"type": "keyword"},
        "titulo": {"type": "text", "analyzer": "spanish"},
        "descripcion": {"type": "text", "analyzer": "spanish"},
        "texto": {"type": "text", "analyzer": "spanish"},
        "secciones": {"type": "keyword"},
    }
})
```

### 9.2. Carga de documentos al índice
Los documentos (cada página web) se carga al índice mediante carga en lotes. Los `jsonl` disponibles ya siguen un mismo esquema (ver apartados 5 & 6).

`viajesindex/carga.py`
```python
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk

es = Elasticsearch("http://localhost:9200")

def acciones(ruta):
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            doc = json.loads(linea)
            yield {"_index": "viajes", "_id": doc["id"],
                   "_source": doc}

for ok, resultado in streaming_bulk(
        es, acciones("index.jsonl"), chunk_size=200,
        raise_on_error=False):
    if not ok:
        print("Documento rechazado:", resultado)
es.indices.refresh(index="viajes")
print(es.count(index="recursos")["count"])
```

### 9.3. Funciones de búsqueda
Se proporcionan tres posibilidades para realizar consultas sobre el índice.

Una primera consulta simple, que utiliza el texto como punto de comparación:
`viajesindex/consulta_simple.py`
```python
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

def consulta_simple (texto: str) -> list:
    respuesta = es.search(
        index="viajes",
        query={"match": {"texto": texto}},
        size=10
    )

    hits = respuesta["hits"]["hits"]
    return list(map(lambda x: x["_source"], hits))

if __name__ == '__main__':
    print(consulta_simple ("Coruña"))
```

Una consulta multi campo, más adaptada al dominio que utiliza el texto y el título como punto de comparación, dando más peso a este último:
`viajesindex/consulta_multi_campo.py`
```python
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

def consulta_multi_campo (texto: str) -> list:
    consulta = {"multi_match": {
        "query": "coruña",
        "fields": ["titulo^2", "texto"],
        "type": "best_fields"
    }}
    respuesta = es.search(index="viajes", query=consulta, size=10)

    hits = respuesta["hits"]["hits"]
    return list(map(lambda x: x["_source"], hits))

if __name__ == '__main__':
    print(consulta_multi_campo("Coruña"))
```

Y una tercera consulta filtrada que permite filtrar el índice según cualquiera de los campos definidos en índice (ver apartado 9.1).
`viajesindex/consulta_filtrada.py`
```python
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

def validar_keys(filtros: dict) -> bool:
    keys_permitidas = ( "id", "ciudad", "pais", "tipo", "fuente", "url_origen", "titulo", "descripcion", "texto", "secciones")
    return set(filtros.keys()).issubset(keys_permitidas)

def consulta_filtrada (filtros: dict) -> list:
    if not validar_keys(filtros):
        raise Exception("Los filtros solicitados no son válidos!")
    filtros = list(map(lambda filtro: {"term": {filtro[0]: filtro[1]}}, filtros.items()))
    consulta = {"bool": { "filter": filtros }}
    respuesta = es.search(index="viajes", query=consulta, size=10)

    hits = respuesta["hits"]["hits"]
    return list(map(lambda x: x["_source"], hits))

if __name__ == '__main__':
    filtros = {"ciudad": "A Coruña"}
    print(consulta_filtrada(filtros))
```

TODO:
- [] *Cambiar lectura de viajesindex/index.jsonl a los dos jsonl de viajescrawler*
- [] *Relacionado con las limitaciones conocidas (8. Resultados y limitaciones), revisar más adelante los campos que son distintos entre ambas fuentes (vid. `ciudad` y `país`)*
- [] *Posible revisión de las funciones de búsqueda, por el momento tienen sentido, mas no debería ser mucho problema modificarlas/expandirlas si fuese de interés*
- [] *Revisión de funciones y extracción de ejemplos (las tres funciones son ejecutables con `python consulta_<TIPO>.py`, con `Coruña` como ejemplo)*


## 10. Siguientes fases
Plan según los requisitos de la asignatura. Las decisiones concretas se irán documentando aquí conforme se tomen.

2. **Estrategia de búsqueda.** Búsqueda inicial sobre el texto como punto de comparación, y después una estrategia adaptada al dominio (combinar campos, más peso al título, filtros por `tipo`, `fuente` y `ciudad`, búsqueda de frases), justificada con consultas de ejemplo y análisis de aciertos y fallos.
3. **Interfaz web.** Consulta, resultados con título, fragmento y enlace a la fuente, filtros, y estados de carga, error y sin resultados.
4. **Integración del LLM.** Una única vía a elegir (enriquecer documentos durante la indexación o postprocesar resultados, por ejemplo con RAG), con control del presupuesto de tokens, caché de resultados y búsqueda básica siempre disponible. Decisión: `______`

---

## 10. Organización del proyecto

| Miembro | Responsabilidad |
|---|---|
| `______` | `______` |
| `______` | `______` |
| `______` | `______` |

Estructura del repositorio:

```
README.md
requirements.txt
viajescrawling/
  scrapy.cfg
  viajescrawling/
    spiders/spaininfo.py
    spiders/wikivoyage.py
    items.py
    pipelines.py
    settings.py
    check.py
```

Los datos exportados (`*.jsonl`) se suben al repositorio si pesan poco; si no, se comparte un enlace de descarga. El `.gitignore` incluye `.venv/`. No se suben credenciales.
