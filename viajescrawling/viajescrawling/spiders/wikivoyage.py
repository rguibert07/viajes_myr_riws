import scrapy


class WikivoyageSpider(scrapy.Spider):
    name = "wikivoyage"
    allowed_domains = ["es.wikivoyage.org"]
    start_urls = ["https://es.wikivoyage.org/wiki/Espa%C3%B1a"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "ROBOTSTXT_OBEY": True,
        "DEPTH_LIMIT": 3,
        "CLOSESPIDER_ITEMCOUNT": 500,  # límite de páginas para no rastrear de más
    }

    def parse(self, response):
        titulo = response.css("h1 span.mw-page-title-main::text, h1::text").get(default="").strip()
        parrafos = response.css("#mw-content-text .mw-parser-output > p")
        descripcion = " ".join(
            " ".join(p.css("*::text").getall()).strip() for p in parrafos[:3]
        )
        secciones = [
            s.strip() for s in response.css("#mw-content-text h2 .mw-headline::text, #mw-content-text h2::text").getall()
            if s.strip()
        ]
        texto = " ".join(
            t.strip() for t in response.css("#mw-content-text .mw-parser-output p *::text, #mw-content-text li *::text").getall()
            if t.strip()
        )

        if titulo:
            yield {
                "titulo": titulo,
                "descripcion": descripcion,
                "texto": texto,
                "secciones": secciones,
                "tipo": "destino",
                "url_origen": response.url,
                "fuente": "es.wikivoyage.org",
            }

        # Seguir enlaces a otras guías (se evitan páginas especiales)
        for href in response.css("#mw-content-text a::attr(href)").getall():
            if href.startswith("/wiki/") and ":" not in href and "#" not in href:
                yield response.follow(href, callback=self.parse)