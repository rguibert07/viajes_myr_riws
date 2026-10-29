"""Estrategia de busqueda adaptada al dominio de viajes.

Combina:
  - varios campos con pesos distintos (titulo > secciones = descripcion > texto)
  - busqueda de frases (match_phrase) con mas peso que la busqueda por terminos
  - filtros exactos por tipo, fuente, ciudad y pais (no afectan a la puntuacion)
  - fragmento resaltado del texto para mostrar en la interfaz

Requiere el indice creado con index_mejora.py, donde `secciones` es de tipo text
y los campos usan el analizador spanish.
"""
import argparse

from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

INDICE = "viajes"

# Pesos por campo. descripcion esta vacia en Wikivoyage, asi que solo ayuda en spain.info.
CAMPOS = ["titulo^4", "secciones^2", "descripcion^2", "texto"]

FILTROS_VALIDOS = ("tipo", "fuente", "ciudad", "pais")

# None = basta con que case un termino de la consulta.
# "100%" = deben casar todos los terminos (mas preciso, menos cobertura).
MINIMO_COINCIDENCIA = None


def construir_consulta(texto: str, filtros: dict | None = None) -> dict:
    filtros = filtros or {}
    no_validos = set(filtros) - set(FILTROS_VALIDOS)
    if no_validos:
        raise ValueError(f"Filtros no validos: {sorted(no_validos)}")

    por_terminos = {
        "query": texto,
        "fields": CAMPOS,
        "type": "best_fields",
        "tie_breaker": 0.3,
    }
    if MINIMO_COINCIDENCIA:
        por_terminos["minimum_should_match"] = MINIMO_COINCIDENCIA

    return {
        "bool": {
            "should": [
                # Frase completa: sube los documentos que contienen la expresion tal cual
                {
                    "multi_match": {
                        "query": texto,
                        "fields": CAMPOS,
                        "type": "phrase",
                        "boost": 3,
                    }
                },
                # Terminos sueltos repartidos por los campos
                {"multi_match": por_terminos},
            ],
            "minimum_should_match": 1,
            "filter": [{"term": {campo: valor}} for campo, valor in filtros.items()],
        }
    }


def buscar(
    texto: str,
    tipo: str | None = None,
    fuente: str | None = None,
    ciudad: str | None = None,
    pais: str | None = None,
    size: int = 10,
) -> list:
    if not texto or not texto.strip():
        raise ValueError("El texto de busqueda no puede estar vacio")

    filtros = {
        campo: valor
        for campo, valor in (
            ("tipo", tipo),
            ("fuente", fuente),
            ("ciudad", ciudad),
            ("pais", pais),
        )
        if valor
    }

    respuesta = es.search(
        index=INDICE,
        query=construir_consulta(texto.strip(), filtros),
        size=size,
        highlight={
            "fields": {"texto": {"fragment_size": 200, "number_of_fragments": 1}},
        },
    )

    resultados = []
    for hit in respuesta["hits"]["hits"]:
        doc = hit["_source"]
        fragmento = (hit.get("highlight", {}).get("texto") or [""])[0]
        if not fragmento:
            fragmento = (doc.get("descripcion") or doc.get("texto", ""))[:200]
        resultados.append(
            {
                "titulo": doc["titulo"],
                "tipo": doc["tipo"],
                "fuente": doc["fuente"],
                "ciudad": doc.get("ciudad", ""),
                "url_origen": doc["url_origen"],
                "puntuacion": round(hit["_score"], 2),
                "fragmento": fragmento,
            }
        )
    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Busqueda de viajes")
    parser.add_argument("texto", nargs="?", default="qué ver en Santiago de Compostela")
    parser.add_argument("--tipo")
    parser.add_argument("--fuente")
    parser.add_argument("--ciudad")
    parser.add_argument("--pais")
    parser.add_argument("--size", type=int, default=5)
    args = parser.parse_args()

    for i, r in enumerate(
        buscar(args.texto, args.tipo, args.fuente, args.ciudad, args.pais, args.size), 1
    ):
        print(f"{i}. {r['titulo']} [{r['fuente']} | {r['tipo']}] puntuacion {r['puntuacion']}")
        print(f"   {r['url_origen']}")
        print(f"   {r['fragmento']}")