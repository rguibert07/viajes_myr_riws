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
