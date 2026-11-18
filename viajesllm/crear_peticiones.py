import json

def get_json():
    records = []
    with open('../viajesindex/index.jsonl', 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def build_petition(document):
    text = document.get("texto")
    cut_text = ' '.join(text.split(".")[:3]) #:3
    custom_id = document.get("custom_id")
    destination = document.get("titulo")

    return json.dumps({"custom_id": custom_id, "method": "POST", "url": "/v1/chat/completions", "body": {"messages": [{"role": "Actúa como un sistema que genera un breve texto introductorio de menos de 20 palabras sobre el destino turistico " + destination + " , sin generar conversación, utilizando el texto dado si es de utilidad.", "content": cut_text}], "max_tokens": 100}})

def write_input(petitions):
    with open ('input.jsonl', 'w') as file:
        for petition in petitions:
            print(petition, file = file)

if __name__ == '__main__':
    records = get_json()
    print(f'Loaded {len(records)} records')
    petitions = list(map(build_petition, records))
    write_input(petitions)

