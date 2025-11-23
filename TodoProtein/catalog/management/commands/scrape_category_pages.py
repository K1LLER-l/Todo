from django.core.management.base import BaseCommand
# Importamos los 3 modelos de la nueva arquitectura
from catalog.models import Producto, Categoria, Tienda, Oferta 
import requests
from bs4 import BeautifulSoup
import re

class Command(BaseCommand):
    help = 'Descubre productos y crea las Ofertas iniciales (Arquitectura Solotodo)'

    def handle(self, *args, **kwargs):
        
        # --- 1. REGLAS DE PALABRAS CLAVE ---
        KEYWORD_RULES = {
            'Barritas Proteicas': ['barra', 'barrita', 'bar'],
            'Cereales y Desayuno': ['cereal', 'granola', 'avena'],
            'Proteínas en Polvo': ['whey', 'protein', 'proteína'],
            'Chocolates y Dulces': ['chocolate', 'bombón', 'cacao', 'dulce'],
            'Mermeladas y Untables': ['mermelada', 'manjar', 'spread', 'untable'],
        }
        DEFAULT_CATEGORY = "Otros Productos"

        # --- 2. CONFIGURACIÓN DE SITIOS ---
        EEL_SELECTORS = {
            'container_tag': 'article',
            'container_class': 'product-miniature',
            'title_selector': 'h2.product-title a',
            'price_selector': 'div.product-price-and-shipping span.product-price',
            'img_selector': 'div.thumbnail-container img'
        }

        SITES = [
            {
                'nombre_sitio': 'Wild Foods - General',
                'tienda_name': 'Wild Foods', # Nombre exacto para la BD
                'url': 'https://thewildfoods.com/collections/all',
                'base_url': 'https://thewildfoods.com',
                'marca_default': 'Wild Foods',
                'categoria_fija': None,
                'container_tag': 'div',
                'container_class': 'product-item',
                'title_selector': 'a.product-item__title',
                'price_selector': 'div.product-item__price',
                'img_selector': 'div.product-item__image-wrapper img, div.product-item img'
            },
            {
                'nombre_sitio': 'Estas En Línea - Cereales',
                'tienda_name': 'Estas En Línea', # Nombre exacto para la BD
                'url': 'https://tienda.estasenlinea.cl/14-cereales',
                'base_url': '', 
                'marca_default': 'En Línea',
                'categoria_fija': 'Cereales y Desayuno',
                **EEL_SELECTORS
            },
            {
                'nombre_sitio': 'Estas En Línea - Chocolates',
                'tienda_name': 'Estas En Línea',
                'url': 'https://tienda.estasenlinea.cl/87-chocolates-dulces',
                'base_url': '', 
                'marca_default': 'En Línea',
                'categoria_fija': 'Chocolates y Dulces',
                **EEL_SELECTORS
            },
            {
                'nombre_sitio': 'Estas En Línea - Mermeladas',
                'tienda_name': 'Estas En Línea',
                'url': 'https://tienda.estasenlinea.cl/11-MERMELADAS',
                'base_url': '', 
                'marca_default': 'En Línea',
                'categoria_fija': 'Mermeladas y Untables',
                **EEL_SELECTORS
            },
            {
                'nombre_sitio': 'Estas En Línea - Otros',
                'tienda_name': 'Estas En Línea',
                'url': 'https://tienda.estasenlinea.cl/89-otros-productos',
                'base_url': '', 
                'marca_default': 'En Línea',
                'categoria_fija': 'Despensa y Otros',
                **EEL_SELECTORS
            }
        ]

        # --- Funciones Auxiliares ---
        def clean_price(price_text):
            if not price_text: return 0
            match = re.search(r'[\d\.]+', str(price_text))
            if match:
                cleaned = re.sub(r'[^\d]', '', match.group())
                try:
                    val = int(cleaned)
                    return val if val < 100000000 else 0
                except ValueError: return 0
            return 0

        def detect_category(product_name, fixed_cat=None):
            if fixed_cat: return fixed_cat
            name_lower = product_name.lower()
            for cat_name, keywords in KEYWORD_RULES.items():
                for keyword in keywords:
                    if keyword in name_lower: return cat_name
            return DEFAULT_CATEGORY

        # --- BUCLE PRINCIPAL ---
        HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        category_cache = {}

        for site in SITES:
            self.stdout.write(self.style.WARNING(f"\n--- Procesando: {site['nombre_sitio']} ---"))
            
            # Buscamos o creamos la TIENDA en la BD
            tienda_obj, _ = Tienda.objects.get_or_create(name=site['tienda_name'])
            
            try:
                response = requests.get(site['url'], headers=HEADERS)
                soup = BeautifulSoup(response.text, 'lxml')
                productos = soup.find_all(site['container_tag'], class_=site['container_class'])
                
                count_nuevos = 0
                
                for prod in productos:
                    try:
                        # 1. Título, 3. URL, 4. Precio, 5. Imagen (extracción normal)
                        tag_titulo = prod.select_one(site['title_selector'])
                        if not tag_titulo: continue
                        nombre = tag_titulo.text.strip()
                        
                        href = tag_titulo.get('href', '')
                        if href.startswith('//'): url_prod = 'https:' + href
                        elif href.startswith('http'): url_prod = href
                        else: url_prod = site['base_url'] + href

                        tag_precio = prod.select_one(site['price_selector'])
                        precio_final = 0
                        if tag_precio:
                            precio_attr = tag_precio.get('content')
                            if precio_attr: precio_final = int(float(precio_attr))
                            else: precio_final = clean_price(tag_precio.text.strip())

                        tag_img = prod.select_one(site['img_selector'])
                        image_src = "https://via.placeholder.com/300"
                        if tag_img:
                            raw_src = tag_img.get('data-src') or tag_img.get('src')
                            if raw_src:
                                raw_src = raw_src.strip()
                                if raw_src.startswith('//'): image_src = "https:" + raw_src
                                elif raw_src.startswith('http'): image_src = raw_src
                                else: image_src = site['base_url'] + raw_src
                        
                        # 2. Categoría (extracción normal)
                        nombre_cat = detect_category(nombre, site.get('categoria_fija'))
                        if nombre_cat not in category_cache:
                            cat_obj, _ = Categoria.objects.get_or_create(name=nombre_cat)
                            category_cache[nombre_cat] = cat_obj
                        categoria_final = category_cache[nombre_cat]

                        # --- 6. GUARDADO (Arquitectura Solotodo) ---
                        
                        # A. Crear/Actualizar el PRODUCTO (Ficha maestra)
                        producto_obj, created = Producto.objects.update_or_create(
                            name=nombre, 
                            defaults={
                                'brand': site['marca_default'],
                                'categoria': categoria_final,
                                'image_url': image_src,
                                'protein_grams': 0, # Lo llenaremos después
                            }
                        )
                        
                        # B. Crear/Actualizar la OFERTA (Precio y Tienda)
                        Oferta.objects.update_or_create(
                            producto=producto_obj,
                            tienda=tienda_obj,
                            defaults={
                                'price': precio_final,
                                'url_compra': url_prod
                            }
                        )

                        if created: count_nuevos += 1

                    except Exception as e_inner: 
                        self.stdout.write(f"Error en producto: {e_inner}")
                        continue
                
                self.stdout.write(self.style.SUCCESS(f"Finalizado. Productos nuevos/actualizados: {count_nuevos}"))

            except Exception as e_outer:
                self.stdout.write(self.style.ERROR(f"Error en {site['nombre_sitio']}: {e_outer}"))

        self.stdout.write(self.style.SUCCESS("Listo!"))
        return