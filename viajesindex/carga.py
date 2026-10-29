import json
from pathlib import Path
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk

es = Elasticsearch("http://localhost:9200", request_timeout=120, max_retries=3, retry_on_timeout=True)

def acciones(ruta):
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            doc = json.loads(linea)
            yield {"_index": "viajes", "_id": doc["id"],
                   "_source": doc}

for ok, resultado in streaming_bulk(
        es, acciones(Path(__file__).resolve().with_name("index.jsonl")),
        chunk_size=25, 
        max_chunk_bytes=5*1024*1024,
        raise_on_error=False, 
        max_retries=3,
          ):

    if not ok:
        print("Documento rechazado:", resultado)
es.indices.refresh(index="viajes")
print(es.count(index="viajes")["count"])
