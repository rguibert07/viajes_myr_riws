import json
import sys

archivos = sys.argv[1:] or ["spaininfo.jsonl", "wikivoyage.jsonl"]

for nombre in archivos:
    with open(nombre, encoding="utf-8") as f:
        docs = [json.loads(linea) for linea in f]
    print("==", nombre)
    print("Documentos:", len(docs))
    print("IDs distintos:", len({d["id"] for d in docs}))
    print("Fuentes:", {d["fuente"] for d in docs})
    print("Tipos:", {t: sum(1 for d in docs if d["tipo"] == t) for t in {d["tipo"] for d in docs}})
    print("Sin descripcion:", sum(1 for d in docs if not d.get("descripcion")))
    print("Longitud media del texto:", sum(len(d["texto"]) for d in docs) // max(len(docs), 1))
    print(docs[:1])