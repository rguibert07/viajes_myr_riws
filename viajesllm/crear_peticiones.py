import json
import numpy as np

def get_json():
    records = []
    with open('../viajesindex/index.jsonl', 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def build_overview_petition(document):
    text = document.get("texto")
    cut_text = ' '.join(text.split(".")[:3]) #:3
    custom_id = document.get("id")
    destination = document.get("titulo")

    return json.dumps({"custom_id": custom_id, "method": "POST", "url": "/v1/chat/completions", "body": {"messages": [{"role": "Actúa como un sistema que genera un breve texto introductorio de menos de 20 palabras sobre el destino turistico " + destination + " , sin generar conversación, utilizando el texto dado si es de utilidad.", "content": cut_text}], "max_tokens": 100}})

def build_completion_petition(document):
    custom_id = document.get("id")
    destination = document.get("titulo")

    return json.dumps({"custom_id": custom_id, "method": "POST", "url": "/v1/chat/completions", "body": {"messages": [{"role": "Actúa como un sistema que devuelve la ciudad y país de una localidad dada, siguiendo exactamente el modelo: ciudad: <CIUDAD>, país: <PAÍS>. En caso de que algún campo no aplique, o la información dada no sea una localidad, deja vacío. No generes conversación en ningún caso.", "content": destination}], "max_tokens": 100, "temperature": 0}})

def build_completion_petitions(documents):
    incomplete_documents = list(filter(lambda x: "wikivoyage" in x.get("fuente"), documents))
    return list(map(build_completion_petition, incomplete_documents))


def write_file(petitions, partition_number, tag):
    with open (f'input/{tag}/{partition_number}.jsonl', 'w') as file:
        for petition in petitions:
            print(petition, file = file)

def write_input(petitions, partition_count, tag):
    partitions = np.array_split(petitions, partition_count)
    for count, partition in enumerate(partitions, 0):
        write_file(partition, count, tag)
    print(f'Escritos {len(partitions)} particiones en la carpeta ./input')

if __name__ == '__main__':
    documents = get_json()
    print(f'Cargados {len(documents)} documentos')
    petitions = list(map(build_overview_petition, documents))
    write_input(petitions, 10, "overview")
    #petitions = build_completion_petitions(documents)
    #write_input(petitions, 5, "completion")

