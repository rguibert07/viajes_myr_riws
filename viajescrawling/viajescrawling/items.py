# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class ViajescrawlingItem:
    titulo = scrapy.Field()
    descripcion = scrapy.Field()
    ciudad = scrapy.Field()
    region = scrapy.Field()
    pais = scrapy.Field()
    direccion = scrapy.Field()
    puntuacion = scrapy.Field()
    num_opiniones = scrapy.Field()
    imagen_url = scrapy.Field()
    tipo = scrapy.Field()
    url_origen = scrapy.Field()
    fuente = scrapy.Field()
