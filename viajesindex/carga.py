import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk

es = Elasticsearch("http://localhost:9200")

def acciones(ruta):
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            doc = json.loads(linea)
            yield {"_index": "viajes", "_id": doc["id"],
                   "_source": doc}

for ok, resultado in streaming_bulk(
        es, acciones("index.jsonl"), chunk_size=200,
        raise_on_error=False):
    if not ok:
        print("Documento rechazado:", resultado)
es.indices.refresh(index="viajes")
print(es.count(index="recursos")["count"])
