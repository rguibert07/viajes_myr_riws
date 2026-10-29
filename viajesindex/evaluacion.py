"""Compara la busqueda simple, la multi campo y la estrategia final sobre consultas de ejemplo.

Uso (desde la carpeta viajesindex, con Elasticsearch en marcha y el indice cargado):
    python evaluacion.py

Imprime los 5 primeros resultados de cada estrategia y guarda lo mismo en
resultados_evaluacion.txt para poder analizar aciertos y fallos.
"""
from pathlib import Path

from elasticsearch import Elasticsearch

from busqueda import buscar

es = Elasticsearch("http://localhost:9200")
TOP = 5

# (consulta, filtros). Las cuatro primeras son las del apartado 1 del README.
CASOS = [
    ("qué ver en Santiago de Compostela", {}),
    ("rutas de naturaleza en Andalucía", {}),
    ("gastronomía y enoturismo en La Rioja", {}),
    ("playas de las Islas Baleares", {}),
    ("gastronomía y enoturismo en La Rioja", {"fuente": "spain.info"}),
    ("qué ver en Santiago de Compostela", {"fuente": "es.wikivoyage.org", "tipo": "destino"}),
]


def filas(respuesta) -> list:
    return [
        (h["_source"]["titulo"], h["_source"]["fuente"], h["_source"]["tipo"], h["_score"])
        for h in respuesta["hits"]["hits"]
    ]


def simple(texto: str) -> list:
    return filas(es.search(index="viajes", query={"match": {"texto": texto}}, size=TOP))


def multi_campo(texto: str) -> list:
    consulta = {
        "multi_match": {"query": texto, "fields": ["titulo^2", "texto"], "type": "best_fields"}
    }
    return filas(es.search(index="viajes", query=consulta, size=TOP))


def final(texto: str, filtros: dict) -> list:
    return [
        (r["titulo"], r["fuente"], r["tipo"], r["puntuacion"])
        for r in buscar(texto, size=TOP, **filtros)
    ]


def formatear(nombre: str, resultados: list) -> list:
    lineas = [f"  {nombre}"]
    if not resultados:
        lineas.append("    (sin resultados)")
    for i, (titulo, fuente, tipo, puntuacion) in enumerate(resultados, 1):
        lineas.append(f"    {i}. {titulo} | {fuente} | {tipo} | {puntuacion:.2f}")
    return lineas


def main():
    salida = []
    for texto, filtros in CASOS:
        cabecera = f"CONSULTA: {texto}"
        if filtros:
            cabecera += f"  FILTROS: {filtros}"
        salida.append(cabecera)
        if not filtros:
            salida += formatear("Simple (match sobre texto)", simple(texto))
            salida += formatear("Multi campo (titulo^2, texto)", multi_campo(texto))
        salida += formatear("Estrategia final", final(texto, filtros))
        salida.append("")

    texto_salida = "\n".join(salida)
    print(texto_salida)
    ruta = Path(__file__).resolve().with_name("resultados_evaluacion.txt")
    ruta.write_text(texto_salida, encoding="utf-8")
    print(f"Guardado en {ruta}")


if __name__ == "__main__":
    main()
