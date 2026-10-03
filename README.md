# Viajescrawling: crawling de Booking con Scrapy y Apache Nutch

Proyecto de la asignatura *Recuperación de Información y Web Semántica* (RISW), UDC. Dominio: **viajes**.

Este documento explica cómo instalar, configurar y ejecutar el crawler de Booking, cómo exportar los datos y cómo prepararlos para Elasticsearch. La estructura sigue el tutorial de crawling del curso (Scrapy y Apache Nutch).

---

## Avisos importantes sobre Booking

1. Revisad `https://www.booking.com/robots.txt` y las condiciones de uso antes de rastrear. Booking restringe el acceso automatizado, bloquea ciertas rutas (por ejemplo, resultados de búsqueda) y tiene protección anti-bots.
2. Uso exclusivamente académico, volumen pequeño (unos cientos de fichas), `ROBOTSTXT_OBEY` activado y pausas entre peticiones.
3. No se guardan **precios** (cambian según fechas) ni el **texto de las opiniones** de usuarios (contenido de terceros con datos personales). Solo puntuación y número de opiniones.
4. Si Booking bloquea el rastreo, no insistir: reducir el ritmo, revisar el alcance y apoyarse en la segunda fuente. Conservad siempre los datos ya descargados.

---

## Índice

- Parte 1. Crawling web con Scrapy (pasos 1 a 26)
- Parte 2. Apache Nutch (pasos 27 a 39)
- Resumen de entregables

---

## PARTE 1. Crawling web con Scrapy

### Paso 1. Conceptos: crawling y extracción de información

- **Crawling**: descubrir y descargar páginas siguiendo enlaces desde unas URLs semilla.
- **Scraping**: extraer campos concretos del contenido descargado.
- **Scrapy** integra ambos procesos en un framework Python con peticiones, respuestas, selectores y pipelines.
- Objetivo del proyecto: obtener documentos de **al menos dos sitios web** y prepararlos para Elasticsearch. Una fuente es Booking; la segunda se documenta en el paso 20.

### Paso 2. Qué ocurre durante un rastreo

1. El spider crea las peticiones iniciales.
2. Scrapy las planifica y descarga las respuestas.
3. Un callback (`parse`, `parse_alojamiento`) extrae datos y crea nuevas peticiones.
4. Los items pasan por los pipelines y se exportan.

Las descargas son **asíncronas**: `response.follow` agenda otra petición, no ejecuta una llamada recursiva directa a `parse`.

### Paso 3. Alcance de Scrapy

- Adecuado para colecciones con páginas enlazadas, fichas, listados y paginación.
- Incluye control de concurrencia, filtrado de peticiones duplicadas, reintentos y exportación.
- **No ejecuta JavaScript por sí solo**: procesa el HTML o los datos que devuelve la petición HTTP.
- Si Booking carga datos dinámicamente y no aparecen en el HTML descargado, hay que localizar la respuesta de datos o integrar un navegador (paso 22).

### Paso 4. Instalación

En la terminal de VS Code:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1

python -m pip install scrapy
scrapy version -v
scrapy -h
```

Registrad la versión instalada para que los tres trabajéis con la misma:

> Versión de Scrapy: `______`

En VS Code, seleccionad el intérprete del entorno virtual (`Ctrl+Shift+P`, *Python: Select Interpreter*, elegir `.venv`).

Guardad las dependencias para que cualquiera pueda reproducir el entorno:

```bash
python -m pip freeze > requirements.txt
```

### Paso 5. Estructura del proyecto

Proyecto creado con:

```bash
scrapy startproject viajescrawling
cd viajescrawling
scrapy genspider booking www.booking.com
```

Estructura relevante:

- `viajescrawling/spiders/`: spiders y reglas de extracción (`booking.py`).
- `viajescrawling/items.py`: definición de los campos de los items.
- `viajescrawling/pipelines.py`: limpieza y validación de los datos extraídos.
- `viajescrawling/settings.py`: configuración.

**Ejecutad siempre los comandos de crawling desde la carpeta que contiene `scrapy.cfg`.**

### Paso 6. Qué se extrae de Booking

Cada ficha de alojamiento es un documento del corpus.

| Campo | Descripción |
|---|---|
| `id` | Identificador estable (se genera en el pipeline) |
| `titulo` | Nombre del alojamiento |
| `descripcion` | Texto descriptivo de la ficha |
| `ciudad`, `region`, `pais` | Localización |
| `direccion` | Dirección completa |
| `puntuacion` | Nota media de las opiniones |
| `num_opiniones` | Cantidad de opiniones |
| `imagen_url` | Imagen principal |
| `tipo` | Siempre `"alojamiento"` |
| `url_origen` | URL de la ficha |
| `fuente` | `"booking.com"` |

Los datos se leen preferentemente del bloque **JSON-LD** (`<script type="application/ld+json">`) de la ficha, más estable que los selectores CSS.

### Paso 7. Inspeccionar el HTML descargado

- Abrid una ficha de alojamiento y localizad el bloque JSON-LD y los elementos que queráis extraer (herramientas de desarrollador del navegador).
- **Comprobad los selectores sobre la respuesta que recibe Scrapy, no solo sobre el DOM del navegador**: el navegador ejecuta JavaScript y Scrapy no.

### Paso 8. Probar selectores con Scrapy shell

```bash
scrapy shell "URL_DE_UNA_FICHA"
```

Dentro de la shell:

```python
response.status
response.url
response.css('script[type="application/ld+json"]::text').getall()
# shelp() muestra los objetos y atajos disponibles.
```

Entrecomillad siempre las URLs para que la terminal no interprete caracteres como `&`. Salid con `exit()` o `Ctrl+D`.

### Paso 9. Selectores CSS: elementos y valores

```python
response.css("title::text").get()
response.css("a::attr(href)").getall()
```

- `.get()` devuelve la primera coincidencia o `None`; `.getall()` devuelve una lista.
- `::text` obtiene nodos de texto y `::attr(href)` el atributo de un enlace.

### Paso 10. XPath y texto anidado

```python
response.xpath("//title/text()").get()
# Texto de un elemento, incluidos sus descendientes:
response.xpath("string(//h2)").get()
```

- `.//` busca desde el nodo actual; `//` empieza desde la raíz del documento.
- `::text` puede omitir texto dentro de elementos hijos: comprobad siempre el HTML de la fuente.

### Paso 11. Expresiones regulares

```python
response.css("title::text").re(r"Hotel.*")
response.css("title::text").re_first(r"Hotel.*")
```

Aplicad regex solo sobre un texto **ya localizado**. Para navegar por la estructura del documento usad CSS o XPath, nunca regex sobre el HTML entero.

### Paso 12. Spider completo

`viajescrawling/spiders/booking.py`:

```python
import json
import scrapy
from viajescrawling.items import ViajescrawlingItem


class BookingSpider(scrapy.Spider):
    name = "booking"
    allowed_domains = ["www.booking.com"]
    start_urls = ["https://www.booking.com/"]  # sustituir por paginas de destino permitidas

    def parse(self, response):
        for href in response.css("a::attr(href)").getall():
            if "/hotel/" in href:
                yield response.follow(href, callback=self.parse_alojamiento)

    def parse_alojamiento(self, response):
        datos = {}
        for bloque in response.css('script[type="application/ld+json"]::text').getall():
            try:
                candidato = json.loads(bloque)
            except json.JSONDecodeError:
                continue
            if isinstance(candidato, dict) and candidato.get("@type") in ("Hotel", "LodgingBusiness", "Apartment"):
                datos = candidato
                break

        direccion = datos.get("address", {})
        valoracion = datos.get("aggregateRating", {})

        item = ViajescrawlingItem()
        item["titulo"] = datos.get("name", "")
        item["descripcion"] = datos.get("description", "")
        item["ciudad"] = direccion.get("addressLocality", "")
        item["region"] = direccion.get("addressRegion", "")
        item["pais"] = direccion.get("addressCountry", "")
        item["direccion"] = direccion.get("streetAddress", "")
        item["puntuacion"] = valoracion.get("ratingValue")
        item["num_opiniones"] = valoracion.get("reviewCount")
        item["imagen_url"] = datos.get("image", "")
        item["tipo"] = "alojamiento"
        item["url_origen"] = response.url
        item["fuente"] = "booking.com"
        yield item
```

Atención:

- `allowed_domains` debe ir como texto simple (`"www.booking.com"`), sin formato de enlace; si no, Scrapy filtra todas las peticiones.
- Los patrones de enlaces (por ejemplo `"/hotel/"`) y los campos exactos hay que ajustarlos tras inspeccionar la web real.

### Paso 13. Cómo funciona el spider

- `name` identifica el spider al ejecutarlo. `start_urls` define las páginas iniciales.
- `allowed_domains` delimita los sitios permitidos para las peticiones; además hay que decidir qué rutas seguir.
- `yield` puede entregar un **item** con datos o una **Request** que Scrapy descargará.
- `response.follow` resuelve enlaces relativos. Cuando llega la nueva respuesta, Scrapy invoca el callback.

### Paso 14. Items con estructura declarada

`viajescrawling/items.py`:

```python
import scrapy


class ViajescrawlingItem(scrapy.Item):
    id = scrapy.Field()
    titulo = scrapy.Field()
    descripcion = scrapy.Field()
    ciudad = scrapy.Field()
    region = scrapy.Field()
    pais = scrapy.Field()
    direccion = scrapy.Field()
    puntuacion = scrapy.Field()
    num_opiniones = scrapy.Field()
    imagen_url = scrapy.Field()
    tipo = scrapy.Field()
    url_origen = scrapy.Field()
    fuente = scrapy.Field()
```

El campo `id` debe estar declarado porque lo rellena el pipeline y un `Item` no admite campos no declarados. Un `Item` declara los campos, pero **no valida** automáticamente sus tipos ni que estén completos.

### Paso 15. Pipeline: limpieza e identificador

`viajescrawling/pipelines.py`:

```python
import hashlib
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class ViajescrawlingPipeline:
    def process_item(self, item, spider=None):
        a = ItemAdapter(item)
        a["descripcion"] = " ".join((a.get("descripcion") or "").split())

        # En JSON-LD, image a veces es una lista: nos quedamos con la primera
        imagen = a.get("imagen_url")
        if isinstance(imagen, list):
            a["imagen_url"] = imagen[0] if imagen else ""

        if not a.get("titulo") or not a.get("url_origen"):
            raise DropItem("Falta titulo o URL")

        a["id"] = hashlib.sha256(a["url_origen"].encode()).hexdigest()
        return item
```

El argumento opcional `spider` permite usar este ejemplo con firmas antiguas y recientes. En versiones recientes basta `process_item(self, item)`.

### Paso 16. Identificadores y duplicados

- Cada ficha de Booking tiene una URL propia estable, así que el `id` se genera a partir de `url_origen`. Al reindexar no se duplican documentos.
- Si la URL cambia, se generará otro ID: hay que decidir cómo actualizar o retirar documentos anteriores.
- El filtrado de **peticiones duplicadas** de Scrapy no elimina contenido repetido en distintas URLs; esa deduplicación pertenece al procesamiento de datos.

### Paso 17. Configurar `settings.py`

```python
ROBOTSTXT_OBEY = True
# Sustituir el contacto por el del grupo.
USER_AGENT = "RISW-Crawler/1.0 (+mailto:grupo@example.org)"
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 3
AUTOTHROTTLE_ENABLED = True
CLOSESPIDER_ITEMCOUNT = 300
FEED_EXPORT_ENCODING = "utf-8"
ITEM_PIPELINES = {
    "viajescrawling.pipelines.ViajescrawlingPipeline": 300,
}
```

- Las prioridades **menores** de los pipelines se ejecutan primero.
- `DOWNLOAD_DELAY` más alto de lo habitual y `CLOSESPIDER_ITEMCOUNT` para limitar el volumen en Booking.
- Respetad las reglas del sitio y controlad frecuencia y alcance. Evitad bucles, parámetros infinitos y páginas fuera del dominio temático.
- **No olvidéis sustituir el `USER_AGENT` por el contacto real del grupo.**

### Paso 18. Ejecutar el spider y exportar

Desde la carpeta que contiene `scrapy.cfg`:

```bash
scrapy crawl booking -O booking.jsonl
# Alternativa: un array JSON
scrapy crawl booking -O booking.json
```

- `-O` sobrescribe el archivo; `-o` añade contenido cuando el formato lo permite (cuidado con duplicar datos en ejecuciones sucesivas).
- **JSONL**: un objeto JSON por línea, útil para procesar el corpus por lotes.
- Usad *feed exports* para guardar archivos; el pipeline se ocupa de la transformación y validación.

### Paso 19. Comprobar la extracción

`check.py`:

```python
import json

with open("booking.jsonl", encoding="utf-8") as f:
    docs = [json.loads(linea) for linea in f]
print("Documentos:", len(docs))
print("IDs distintos:", len({d["id"] for d in docs}))
print("Fuentes:", {d["fuente"] for d in docs})
print("Sin titulo:", sum(1 for d in docs if not d.get("titulo")))
print("Sin puntuacion:", sum(1 for d in docs if d.get("puntuacion") is None))
print(docs[:1])
```

Es una comprobación sobre una muestra pequeña. Revisad campos vacíos, duplicados, texto extraño y estadísticas del crawl. **No basta con que el proceso termine sin errores.**

### Paso 20. Segunda fuente (tarea obligatoria del proyecto)

- Crear **un spider por sitio** cuando tengan estructuras HTML diferentes (`scrapy genspider ...`).
- Extraer los datos con selectores específicos y **convertirlos al mismo conjunto de campos** que usa `booking.py`.
- Conservar `fuente` y `url_origen` para distinguir procedencia y permitir comprobaciones.
- Exportar cada fuente por separado y normalizar antes de combinar. No perder una fuente por sobrescribir el archivo.

```bash
scrapy crawl booking -O booking.jsonl
scrapy crawl segunda_fuente -O segunda_fuente.jsonl
```

> `segunda_fuente` es un nombre ilustrativo: sustituidlo por el spider real de la fuente que elijáis.

Segunda fuente elegida: `______`

### Paso 21. Preparación para Elasticsearch

- Cada archivo `.jsonl` debe usar el **esquema común** del proyecto, incluido el `id` generado por el pipeline.
- Crear un índice con tipos y analizador adecuados (analizador en español para `titulo` y `descripcion`, `keyword` para `pais`, `tipo` y `fuente`).
- Usar la carga por lotes (bulk) del tutorial de Elasticsearch y revisar los documentos rechazados.
- Conservar el corpus exportado permite reindexar sin repetir el crawling.
- Elasticsearch se ejecuta en local en cada equipo (sin Docker). Los datos (JSONL), el `mapping.json` y el script de indexación se comparten por el repositorio.

### Paso 22. Contenido dinámico y JavaScript

- Si los datos aparecen en el navegador pero faltan en `response.text`, inspeccionad las peticiones de red del sitio.
- Cuando exista una respuesta JSON accesible y permitida, Scrapy puede solicitarla y procesarla directamente.
- Si hace falta renderizar JavaScript, integrar un navegador como **Playwright**. Esto añade dependencias y coste.
- Para empezar, elegid páginas con HTML accesible. Una API aislada no demuestra por sí sola el crawling web requerido en el proyecto.

### Paso 23. Librerías complementarias (opcional)

- **Parsel / lxml**: selectores CSS y XPath (Scrapy ya los integra).
- **BeautifulSoup**: API alternativa para navegar y extraer contenido de HTML/XML.
- **Playwright / Selenium**: automatización del navegador cuando se necesita ejecutar JavaScript.
- **w3lib / urllib.parse**: utilidades para trabajar con URLs.

Ejemplo de BeautifulSoup dentro de un callback (ilustrativo; Scrapy sigue gestionando descargas y paginación):

```python
# Instalar antes: python -m pip install beautifulsoup4
from bs4 import BeautifulSoup

soup = BeautifulSoup(response.text, "html.parser")
titulo = soup.select_one("h2")
if titulo is not None:
    print(titulo.get_text(" ", strip=True))
```

### Paso 24. Diagnóstico del crawler

- **Cero items**: comprobar el estado HTTP, los selectores y el contenido real de la respuesta. Revisar también `allowed_domains`.
- **Solo la primera página**: revisar el patrón de enlaces y la creación de nuevas peticiones.
- **Datos repetidos o incompletos**: revisar contenedores, normalización e identificadores.
- **Bloqueos o demasiadas peticiones** (códigos 403 o 429, páginas de verificación): respetar las restricciones, reducir ritmo y revisar el alcance. Consultar los logs antes de ampliar el rastreo.

### Paso 25. Documentación de referencia

- Tutorial oficial de Scrapy
- Selectores y Scrapy shell
- Pipelines y exportación de datos
- Configuración y contenido dinámico

Consultad la documentación correspondiente a la versión de Scrapy registrada en el paso 4.

### Paso 26. Guardar el avance en GitHub

```bash
git add viajescrawling/ requirements.txt check.py README.md
git commit -m "Scrapy: spider booking + items + pipeline + export JSONL"
git push
```

Los datos exportados (`*.jsonl`) se pueden subir si pesan poco (comprimidos si hace falta). Si pesan mucho, compartid un enlace de descarga y anotadlo aquí. Añadid al `.gitignore` la carpeta `.venv/`.

---

## PARTE 2. Apache Nutch

> Esta parte sigue el tutorial del curso sobre un dominio propio. **No uséis Booking con Nutch** (restricciones de acceso): elegid un dominio que permita el rastreo y anotadlo en el paso 35.

### Paso 27. Qué es Apache Nutch

- *Web crawler* extensible y escalable.
- Proporciona, entre otras cosas: web crawling, WebGraph y LinkRank, detección de formatos de documento y parsing, detección de lenguaje y codificación, mecanismo de extensión mediante plugins y soporte de múltiples *backends* de persistencia.
- Originalmente, Hadoop nació como parte de Nutch.

### Paso 28. Elegir versión de Nutch

- **Nutch 1.x**: versión madura. Usa estructuras de datos de Hadoop (HDFS).
- **Nutch 2.x**: versión más moderna. Emplea **Apache Gora** para gestionar la persistencia. Nutch 2.4 usa Gora 0.8, con varios backends soportados (entre ellos MongoDB, HBase, Cassandra y Solr).

Esta guía sigue **Nutch 2.4 con MongoDB** como backend.

### Paso 29. Instalar Nutch 2.4 (I): descarga y agent name

```bash
wget https://downloads.apache.org/nutch/2.4/apache-nutch-2.4-src
```

Configurad Nutch en `conf/nutch-site.xml` (los valores por defecto están en `conf/nutch-default.xml`). Como mínimo hay que establecer el *agent name*:

```xml
<property>
  <name>http.agent.name</name>
  <value>My RISW Spider 1.0</value>
</property>
```

### Paso 30. Instalar Nutch 2.4 (II): MongoDB como backend

1. Añadid el backend en `conf/nutch-site.xml`:

```xml
<property>
  <name>storage.data.store.class</name>
  <value>org.apache.gora.mongodb.store.MongoStore</value>
  <description>Class for storing data</description>
</property>
```

2. Descomentad el backend en `ivy/ivy.xml` y ajustad su versión:

```xml
<dependency org="org.apache.gora" name="gora-mongodb" rev="0.8" conf="*->default" />
```

3. Añadid el backend en `conf/gora.properties`:

```
gora.mongodb.override_hadoop_configuration=false
gora.mongodb.mapping.file=/gora-mongodb-mapping.xml
gora.mongodb.servers=localhost:27017
gora.mongodb.db=nutch-risw
```

4. Compilad el código:

```bash
ant runtime
```

### Paso 31. Instalar Nutch 2.4 (III): dependencias que fallan

Si falla la compilación porque no encuentra unas dependencias, añadid un repositorio en `ivy/ivysettings.xml`:

```xml
<property name="repo.restlet"
  value="https://maven.restlet.talend.com/"
  override="false"/>
...
<resolvers>
  <ibiblio name="restlet"
    root="${repo.restlet}"
    pattern="${maven2.pattern.ext}"
    m2compatible="true"
  />
  ...
  <chain name="default" dual="true">
    <resolver ref="local"/>
    <resolver ref="maven2"/>
    <resolver ref="sonatype"/>
    <resolver ref="apache-snapshot"/>
    <resolver ref="spring-plugins"/>
    <resolver ref="restlet"/>
  </chain>
  ...
```

### Paso 32. Instalar y arrancar MongoDB 3.4.7

```bash
wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu1604-3.4.7.tgz
tar xzvf mongodb-linux-x86_64-ubuntu1604-3.4.7.tgz

mkdir data logs

./mongodb-linux-x86_64-ubuntu1604-3.4.7/bin/mongod --dbpath data/ \
  --logpath logs/mongo-risw.log
```

Dejad este proceso corriendo en una terminal de VS Code mientras trabajáis con Nutch.

### Paso 33. Usar Nutch 2.4 (I): esquema de Solr

```bash
rm solr-8.4.1/server/solr/nutch-risw/conf/managed-schema
cp apache-nutch-2.4/conf/schema.xml \
   solr-8.4.1/server/solr/nutch-risw/conf/
```

Después, en el `schema.xml` copiado al core de Solr:

- Eliminad las ocurrencias de `enablePositionIncrements="true"`.
- Eliminad `<solrQueryParser defaultOperator="OR"/>` y `<defaultSearchField>text</defaultSearchField>`.
- Comentad el bloque `<updateProcessor class="solr.AddSchemaFieldUpdateProcessorFactory" name="add-schema-fields">...` en `solr-8.4.1/server/solr/nutch-risw/conf/solrconfig.xml`, y eliminad `add-schema-field` de la chain `"add-unknown-fields-to-the-schema"`.

### Paso 34. Usar Nutch 2.4 (II): arrancar Solr y añadir plugins

Arrancad Solr y comprobad en el navegador `http://localhost:8983/solr`.

Añadid el plugin `indexer-solr` mediante la propiedad `plugin.includes` en `runtime/local/conf/nutch-site.xml`:

```xml
<property>
  <name>plugin.includes</name>
  <value>protocol-http|urlfilter-regex|parse-(html|tika)|index-(basic|anchor)|urlnormalizer-(pass|regex|basic)|scoring-opic|indexer-solr</value>
</property>
```

### Paso 35. Usar Nutch 2.4 (III): alcance y lanzamiento

1. Restringid el crawling al dominio deseado en `runtime/local/conf/regex-urlfilter.txt` (cambiad la última línea):

```
+^https://DOMINIO_ELEGIDO
```

Dominio elegido para Nutch: `______`

2. Añadid las URLs semilla:

```bash
mkdir runtime/local/urls
echo "https://DOMINIO_ELEGIDO/" > runtime/local/urls/seed.txt
```

3. Iniciad el crawling:

```bash
cd runtime/local
bin/nutch inject urls
bin/nutch generate -topN 25
bin/nutch fetch -all
bin/nutch parse -all
bin/nutch updatedb -all
```

### Paso 36. Usar Nutch 2.4 (IV): indexar en Solr y consultar

- Podéis repetir los últimos cuatro comandos del paso 35 para profundizar en el crawling.
- Para pasar los datos de Gora a Solr:

```bash
bin/nutch solrindex http://localhost:8983/solr/nutch-risw -all
```

- Para consultar los datos importados: `http://localhost:8983/solr/#/nutch-risw/query`
- Para definir nuevos campos o reglas de parsing, crear un **plugin**. Para indexar nuevos campos en Solr, editar el `schema.xml`. Tutorial de referencia (metatags): `http://wiki.apache.org/nutch/IndexMetatags`
- Clase de referencia: `src/plugin/index-metadata/src/java/org/apache/nutch/indexer/metadata/MetadataIndexer.java`

### Paso 37. Documentación de referencia de Nutch

- Wiki de Nutch: https://wiki.apache.org/nutch
- Tutorial de Nutch 2: http://wiki.apache.org/nutch/Nutch2Tutorial
- Interfaz web autocontenida: https://issues.apache.org/jira/browse/NUTCH-841
- API REST: https://wiki.apache.org/nutch/NutchRESTAPI

### Paso 38. Debugging

- Ante cualquier problema, consultad los **logs** (todos los proyectos Apache tienen una carpeta `logs`).
- Si Nutch da problemas, comprobad que el *backend* de almacenamiento (MongoDB) está funcionando.
- Si no conseguís rastrear un sitio, comprobad la conexión y que la web no esté bloqueando el rastreo.

### Paso 39. Guardar el avance de Nutch en GitHub

```bash
git add nutch-config-notes.md
git commit -m "Nutch 2.4 + MongoDB: configuracion, crawling y volcado a Solr"
git push
```

No subáis al repositorio los binarios descargados (Nutch, MongoDB, Solr) ni las carpetas `data/` y `logs/`. Añadidlos al `.gitignore`.

---

## Resumen de entregables

1. Spider Scrapy `booking` funcionando.
2. **Un segundo spider Scrapy** para una fuente real distinta, con el mismo esquema de campos.
3. Pipeline de limpieza y generación de `id` aplicado a ambas fuentes.
4. Exportación en JSONL de cada fuente, revisada con el script de comprobación.
5. Corpus preparado con el esquema común, listo para indexar en Elasticsearch.
6. Configuración y ejecución de un crawling con Apache Nutch 2.4 (o la rama que elijáis) sobre un dominio propio, con volcado a Solr.