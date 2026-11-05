import html
import os

from elasticsearch import (
    ApiError,
    ConnectionError as ESConnectionError,
    ConnectionTimeout,
    Elasticsearch,
)
from flask import Flask, jsonify, render_template, request

from viajesindex.busqueda import CAMPOS, construir_consulta

ES_URL = os.environ.get("ES_URL", "http://localhost:9200")
INDICE = "viajes"
TAMANO = 10

# Filtros de coincidencia exacta (campos keyword). La ciudad se trata aparte.
FILTROS_EXACTOS = ("tipo", "fuente", "pais")

# encoder html: escapa el HTML del texto indexado y deja solo nuestras etiquetas mark
RESALTADO = {
    "fields": {"texto": {"fragment_size": 200, "number_of_fragments": 1}},
    "pre_tags": ["<mark>"],
    "post_tags": ["</mark>"],
    "encoder": "html",
}

app = Flask(__name__)
es = Elasticsearch(ES_URL, request_timeout=5)


def filtro_ciudad(texto):
    """Ciudad contiene el texto, sin distinguir mayusculas (ciudad es keyword)."""
    for caracter in ("\\", "*", "?"):
        texto = texto.replace(caracter, "\\" + caracter)
    return {"wildcard": {"ciudad": {"value": f"*{texto}*", "case_insensitive": True}}}


def consulta_frase(texto, filtros):
    """Opcion 'Buscar la frase completa': solo documentos que contienen la frase exacta."""
    return {"bool": {
        "must": [{"multi_match": {"query": texto, "fields": CAMPOS, "type": "phrase"}}],
        "filter": [{"term": {c: v}} for c, v in filtros.items()],
    }}


def fragmento(hit):
    resaltado = hit.get("highlight", {}).get("texto")
    if resaltado:
        return resaltado[0]
    fuente = hit["_source"]
    base = fuente.get("descripcion") or fuente.get("texto") or ""
    return html.escape(base[:200])


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/api/estado")
def estado():
    try:
        return jsonify(elasticsearch=es.ping(), documentos=es.count(index=INDICE)["count"])
    except (ESConnectionError, ConnectionTimeout):
        return jsonify(elasticsearch=False, documentos=0), 503
    except ApiError as e:
        return jsonify(elasticsearch=True, error=str(e.message)), 500


@app.get("/api/buscar")
def buscar():
    texto = request.args.get("q", "").strip()
    if not texto:
        return jsonify(error="La consulta está vacía."), 400

    filtros = {
        c: request.args[c].strip()
        for c in FILTROS_EXACTOS
        if request.args.get(c, "").strip()
    }
    ciudad = request.args.get("ciudad", "").strip()
    frase = request.args.get("frase", "").lower() in ("1", "true", "on")

    if frase:
        consulta = consulta_frase(texto, filtros)
    else:
        consulta = construir_consulta(texto, filtros)
    if ciudad:
        consulta["bool"]["filter"].append(filtro_ciudad(ciudad))

    try:
        r = es.search(index=INDICE, query=consulta, highlight=RESALTADO, size=TAMANO)
    except (ESConnectionError, ConnectionTimeout):
        return jsonify(error="No se pudo conectar con Elasticsearch. Comprueba que está en marcha."), 503
    except ApiError as e:
        if e.status_code == 404:
            return jsonify(error="El índice 'viajes' no existe. Ejecuta index_mejora.py y carga.py."), 500
        return jsonify(error=f"Error de Elasticsearch: {e.message}"), 500

    resultados = []
    for hit in r["hits"]["hits"]:
        s = hit["_source"]
        resultados.append({
            "titulo": s.get("titulo", ""),
            "fragmento": fragmento(hit),
            "url": s.get("url_origen", ""),
            "tipo": s.get("tipo", ""),
            "fuente": s.get("fuente", ""),
            "ciudad": s.get("ciudad", ""),
            "pais": s.get("pais", ""),
            "puntuacion": round(hit["_score"] or 0, 2),
        })

    return jsonify({"total": r["hits"]["total"]["value"], "resultados": resultados})


if __name__ == "__main__":
    app.run(debug=True)