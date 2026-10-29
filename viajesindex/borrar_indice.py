from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
es.indices.delete(index="viajes", ignore_unavailable=True)
print("Índice 'viajes' borrado (o no existía)")