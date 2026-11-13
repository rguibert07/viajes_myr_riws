from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")


def validar_keys(filtros: dict) -> bool:
    keys_permitidas = ("id", "ciudad", "pais", "tipo", "fuente", "url_origen", "titulo", "descripcion", "texto", "secciones")
    return set(filtros.keys()).issubset(keys_permitidas)

def consulta_filtrada(filtros: dict) -> list:
    if not validar_keys(filtros):
        raise Exception("Los filtros solicitados no son válidos!")
    #filtros = list(map(lambda filtro: {"term": {f"{filtro[0]}.keyword": filtro[1]}}, filtros.items()))
    filtros = list(map(lambda filtro: {"match_phrase": {filtro[0]: filtro[1]}}, filtros.items()))
    consulta = {"bool": {"filter": filtros}}
    respuesta = es.search(index="viajes", query=consulta, size=10)

    hits = respuesta["hits"]["hits"]
    return list(map(lambda x: x["_source"], hits))

if __name__ == '__main__':
    filtros = {"ciudad": "A Coruña"}
    print(consulta_filtrada(filtros))