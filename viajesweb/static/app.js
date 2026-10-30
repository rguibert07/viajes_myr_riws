const formulario = document.querySelector("#formulario-busqueda");
const consulta = document.querySelector("#consulta");
const tipo = document.querySelector("#tipo");
const fuente = document.querySelector("#fuente");
const ciudad = document.querySelector("#ciudad");
const frase = document.querySelector("#frase");

const botonBuscar = document.querySelector("#boton-buscar");
const zonaRespuestas = document.querySelector("#zona-respuestas");
const estado = document.querySelector("#estado");
const contenedorResultados = document.querySelector("#resultados");


function cambiarEstado(mensaje, tipoEstado) {
    estado.textContent = mensaje;

    estado.className = `estado estado--${tipoEstado}`;
}


function crearMetadato(texto) {
    if (!texto) {
        return null;
    }

    const elemento = document.createElement("span");
    elemento.textContent = texto;

    return elemento;
}


function crearResultado(resultado) {
    const articulo = document.createElement("article");
    articulo.className = "resultado";

    const cabecera = document.createElement("div");
    cabecera.className = "resultado__cabecera";

    const titulo = document.createElement("h2");
    const enlace = document.createElement("a");

    enlace.textContent = resultado.titulo || "Sin título";

    if (resultado.url) {
        enlace.href = resultado.url;
        enlace.target = "_blank";
        enlace.rel = "noopener noreferrer";
    } else {
        enlace.removeAttribute("href");
    }

    titulo.appendChild(enlace);
    cabecera.appendChild(titulo);

    if (resultado.tipo) {
        const etiquetaTipo = document.createElement("span");
        etiquetaTipo.className = "resultado__tipo";
        etiquetaTipo.textContent = resultado.tipo;

        cabecera.appendChild(etiquetaTipo);
    }

    const fragmento = document.createElement("p");
    fragmento.className = "resultado__fragmento";
    fragmento.textContent =
        resultado.fragmento || "No hay descripción disponible.";

    const metadatos = document.createElement("p");
    metadatos.className = "resultado__metadatos";

    const datos = [
        crearMetadato(resultado.fuente),
        crearMetadato(resultado.ciudad),
        crearMetadato(resultado.pais),
    ];

    for (const dato of datos) {
        if (dato) {
            metadatos.appendChild(dato);
        }
    }

    articulo.appendChild(cabecera);
    articulo.appendChild(fragmento);

    if (metadatos.childElementCount > 0) {
        articulo.appendChild(metadatos);
    }

    return articulo;
}


formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const texto = consulta.value.trim();

    contenedorResultados.replaceChildren();

    cambiarEstado("Buscando destinos...", "carga");

    zonaRespuestas.setAttribute("aria-busy", "true");
    botonBuscar.disabled = true;
    botonBuscar.textContent = "Buscando...";

    const parametros = new URLSearchParams();

    if (texto) {
        parametros.set("q", texto);
    }

    if (tipo.value) {
        parametros.set("tipo", tipo.value);
    }

    if (fuente.value) {
        parametros.set("fuente", fuente.value);
    }

    if (ciudad.value.trim()) {
        parametros.set("ciudad", ciudad.value.trim());
    }

    if (frase.checked) {
        parametros.set("frase", "true");
    }

    try {
        const respuesta = await fetch(
            `/api/buscar?${parametros.toString()}`
        );

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                datos.error || "No se pudo realizar la búsqueda."
            );
        }

        if (!datos.resultados || datos.resultados.length === 0) {
            cambiarEstado(
                "No se encontraron resultados. Prueba con otros términos o elimina algún filtro.",
                "vacio"
            );

            return;
        }

        const textoResultado =
            datos.total === 1
                ? "Se encontró 1 resultado."
                : `Se encontraron ${datos.total} resultados.`;

        cambiarEstado(textoResultado, "exito");

        for (const resultado of datos.resultados) {
            const tarjeta = crearResultado(resultado);
            contenedorResultados.appendChild(tarjeta);
        }
    } catch (error) {
        cambiarEstado(
            error.message ||
                "Se produjo un error inesperado durante la búsqueda.",
            "error"
        );
    } finally {
        zonaRespuestas.setAttribute("aria-busy", "false");
        botonBuscar.disabled = false;
        botonBuscar.textContent = "Buscar";
    }
});