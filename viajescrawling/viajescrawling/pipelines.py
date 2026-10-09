# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

MIN_TEXTO = 200  # caracteres mínimos para considerar útil una página

class ViajescrawlingPipeline:
    def process_item(self, item, spider=None):
        a = ItemAdapter(item)
        a["texto"] = " ".join(a.get("texto", "").split())
        if not a["texto"] or not a.get("url"):
            raise DropItem("Falta texto o URL")
        clave = a["url"] + "|" + a["texto"]
        a["id"] = hashlib.sha256(clave.encode()).hexdigest()
        return item
    
class LimpiezaPipeline:
    def process_item(self, item, spider=None):
        a = ItemAdapter(item)

        # Ruido: espacios y saltos de línea sobrantes
        for campo in ("titulo", "descripcion", "texto"):
            a[campo] = " ".join((a.get(campo) or "").split())

        # Campos ausentes: valores por defecto coherentes en las dos fuentes
        for campo in ("ciudad", "pais", "tipo", "fuente"):
            a[campo] = a.get(campo) or ""
        a["secciones"] = a.get("secciones") or []

        # Páginas sin contenido útil
        if not a["titulo"] or not a.get("url_origen"):
            raise DropItem("Falta titulo o URL")
        if len(a["texto"]) < MIN_TEXTO:
            raise DropItem("Texto demasiado corto")

        a["id"] = hashlib.sha256(a["url_origen"].encode()).hexdigest()
        return item


class DuplicadosPipeline:
    def __init__(self):
        self.ids = set()
        self.huellas = set()

    def process_item(self, item, spider=None):
        a = ItemAdapter(item)
        huella = hashlib.sha256(a["texto"].lower().encode()).hexdigest()
        if a["id"] in self.ids or huella in self.huellas:
            raise DropItem(f"Duplicado: {a['url_origen']}")
        self.ids.add(a["id"])
        self.huellas.add(huella)
        return item    
