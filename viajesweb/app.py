from flask import Flask, jsonify, render_template, request


app = Flask(__name__)


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/api/buscar")
def buscar():
    texto = request.args.get("q", "").strip()

    resultados_prueba = [
        {
            "titulo": "Santiago de Compostela",
            "fragmento": (
                "Resultado ficticio para comprobar cómo se visualizan "
                "el título, el fragmento y el enlace."
            ),
            "url": "https://www.spain.info/es/destino/santiago-de-compostela/",
            "tipo": "destino",
            "fuente": "spain.info",
            "ciudad": "Santiago de Compostela",
            "pais": "España",
            "puntuacion": 10.5,
        },
        {
            "titulo": "Galicia",
            "fragmento": (
                "Segundo resultado de prueba para verificar el diseño "
                "de la lista de resultados."
            ),
            "url": "https://es.wikivoyage.org/wiki/Galicia",
            "tipo": "region",
            "fuente": "es.wikivoyage.org",
            "ciudad": "",
            "pais": "España",
            "puntuacion": 8.2,
        },
    ]

    if texto.lower() == "sin resultados":
        resultados_prueba = []

    return jsonify(
        {
            "total": len(resultados_prueba),
            "resultados": resultados_prueba,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)