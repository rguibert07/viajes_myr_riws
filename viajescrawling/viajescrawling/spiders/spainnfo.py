import re

import scrapy


class SpainInfoSpider(scrapy.Spider):
    name = "spaininfo"
    allowed_domains = ["www.spain.info"]
    start_urls = ["https://www.spain.info/es/"]

    custom_settings = {
        "DEPTH_LIMIT": 3,
    }

    # Secciones de contenido que merece la pena seguir
    PATRON = re.compile(
        r"^/es/(destino|region|ciudades|arte-cultura|costas-playas|naturaleza|"
        r"gastronomia-enoturismo|deporte-aventura|rutas)/"
    )

    def parse(self, response):
        titulo = " ".join(t.strip() for t in response.css("h1 *::text, h1::text").getall() if t.strip())

        descripcion = (
            response.css('meta[name="description"]::attr(content)').get()
            or response.css('meta[property="og:description"]::attr(content)').get()
            or ""
        ).strip()

        # Texto del contenido principal, sin scripts, estilos, menú ni pie
        fragmentos = response.xpath(
            "//main//text()[not(ancestor::script or ancestor::style or ancestor::nav "
            "or ancestor::footer or ancestor::noscript)]"
        ).getall()
        if not fragmentos:
            fragmentos = response.xpath(
                "//body//text()[not(ancestor::script or ancestor::style or ancestor::nav "
                "or ancestor::footer or ancestor::noscript)]"
            ).getall()
        texto = re.sub(r"\s+", " ", " ".join(fragmentos)).strip()

        ruta = response.url.split("spain.info", 1)[-1]
        if "/destino/" in ruta:
            tipo = "destino"
        elif "/region/" in ruta:
            tipo = "region"
        elif "/rutas/" in ruta:
            tipo = "ruta"
        else:
            tipo = "articulo"

        if titulo and texto:
            yield {
                "titulo": titulo,
                "descripcion": descripcion,
                "texto": texto,
                "ciudad": titulo if tipo == "destino" else "",
                "pais": "España",
                "tipo": tipo,
                "url_origen": response.url,
                "fuente": "spain.info",
            }

        for href in response.css("a::attr(href)").getall():
            href = href.split("#")[0].split("?")[0]
            if self.PATRON.match(href):
                yield response.follow(href, callback=self.parse)