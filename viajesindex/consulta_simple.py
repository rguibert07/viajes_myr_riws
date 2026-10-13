from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

respuesta = es.search(
    index="viajes",
    query={"match": {"texto": "coruña"}},
    size=10
)
for hit in respuesta["hits"]["hits"]:
    doc = hit["_source"]
    print(hit["_id"], hit["_score"], doc["titulo"])
