import json

import scrapy


class BookingSpider(scrapy.Spider):
    name = "booking"
    allowed_domains = ["www.booking.com"]
    start_urls = [
        "https://www.booking.com/searchresults.es.html?ss=Madrid%2C+Espa%C3%B1a&efdco=1&label=es-es-booking-desktop-onknyt5TBrS8m9RnGd*6fgS652829001115%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi%3Atikwd-65526620%3Alp1005479%3Ali%3Adec%3Adm&aid=2311236&lang=es&sb=1&src_elem=sb&src=index&dest_id=-390625&dest_type=city&group_adults=2&no_rooms=1&group_children=0"
    ]

    def parse(self, response):
        # enlaces a fichas de alojamiento (ajustar el patrón tras inspeccionar la web)
        for href in response.css("a::attr(href)").getall():
            if "/hotel/" in href:
                yield response.follow(href, callback=self.parse_alojamiento)

    def parse_alojamiento(self, response):
        datos = {}
        for bloque in response.css('script[type="application/ld+json"]::text').getall():
            try:
                candidato = json.loads(bloque)
            except json.JSONDecodeError:
                continue
            if isinstance(candidato, dict) and candidato.get("@type") in ("Hotel", "LodgingBusiness", "Apartment"):
                datos = candidato
                break

        direccion = datos.get("address", {})
        valoracion = datos.get("aggregateRating", {})

        yield {
            "titulo": datos.get("name", ""),
            "descripcion": datos.get("description", ""),
            "ciudad": direccion.get("addressLocality", ""),
            "region": direccion.get("addressRegion", ""),
            "pais": direccion.get("addressCountry", ""),
            "direccion": direccion.get("streetAddress", ""),
            "puntuacion": valoracion.get("ratingValue"),
            "num_opiniones": valoracion.get("reviewCount"),
            "imagen_url": datos.get("image", ""),
            "tipo": "alojamiento",
            "url_origen": response.url,
            "fuente": "booking.com",
        }
