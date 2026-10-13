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
