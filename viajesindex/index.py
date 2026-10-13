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
    }
})
