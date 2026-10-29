from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
resultado = es.indices.analyze(
    index="viajes", field="texto", text="qué ver en Santiago de Compostela"
)
print([t["token"] for t in resultado["tokens"]])