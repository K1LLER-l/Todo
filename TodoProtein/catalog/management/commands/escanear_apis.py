from django.core.management.base import BaseCommand
from catalog.models import Producto, Categoria, Tienda, Oferta
import requests
import time
import re
import random

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class Command(BaseCommand):
    help = 'Carga masiva inteligente: Usa API JSON donde es posible y Selenium donde no.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Iniciando Carga Masiva Híbrida...")

        # --- FILTROS ---
        self.PALABRAS_PERMITIDAS = [
            'proteina', 'proteína', 'protein', 'whey', 'isolate', 'caseina', 'caseína',
            'creatina', 'creatine', 'amino', 'bcaa', 'glutamina',
            'pre-entreno', 'pre entreno', 'pre-workout', 'pre workout',
            'barra', 'barrita', 'snack', 'cookie', 'galleta',
            'vitamina', 'multivitaminico', 'omega', 'zma', 'colageno', 'colágeno'
        ]
        self.PALABRAS_PROHIBIDAS = [
            'polera', 'shaker', 'botella', 'tazón', 'tazon', 'gorro', 'jockey', 
            'mochila', 'bolso', 'toalla', 'gift card', 'pack degustación'
        ]

        # --- TIENDAS API (Rápidas) ---
        TIENDAS_API = [
            {
                'nombre': 'Wild Foods',
                'tipo': 'shopify',
                'url_base': 'https://thewildfoods.com',
                'marca_default': 'Wild Foods'
            },
            {
                'nombre': 'Suplementos Al Mayor',
                'tipo': 'woocommerce',
                'url_base': 'https://suplementosalmayor.cl',
                'marca_default': 'MultiMarca'
            }
        ]

        # --- TIENDAS SELENIUM (Lentas pero necesarias) ---
        TIENDAS_SELENIUM = [
            {
                'nombre': 'Estas En Línea',
                'url': 'https://tienda.estasenlinea.cl/14-cereales',
                'marca_default': 'En Línea',
                'categoria_fija': 'Cereales y Desayuno',
                # Selectores específicos para esta tienda
                'container_tag': 'article',
                'container_class': 'product-miniature',
                'title_selector': 'h2.product-title a',
                'price_selector': 'div.product-price-and-shipping span.product-price',
                'img_selector': 'div.thumbnail-container img',
                'base_url': ''
            },
             {
                'nombre': 'One Nutrition',
                'url': 'https://onenutrition.cl/tienda/proteinas',
                'marca_default': 'One Nutrition',
                'categoria_fija': 'Proteínas en Polvo',
                'container_tag': 'div',
                'container_class': 'uael-woo-product-wrapper', 
                'title_selector': 'h2.uael-loop-product__title a',
                'price_selector': 'span.woocommerce-Price-amount',
                'img_selector': 'img.attachment-woocommerce_thumbnail',
                'base_url': ''
            }
        ]

        HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        # 1. EJECUTAR CARGA RÁPIDA (API)
        self.stdout.write("\n⚡ FASE 1: Carga Rápida (APIs)...")
        for tienda_conf in TIENDAS_API:
            self.stdout.write(f"--- Procesando {tienda_conf['nombre']} via API ---")
            tienda_obj, _ = Tienda.objects.get_or_create(name=tienda_conf['nombre'])
            
            if tienda_conf['tipo'] == 'shopify':
                self.procesar_shopify(tienda_conf, tienda_obj, HEADERS)
            elif tienda_conf['tipo'] == 'woocommerce':
                self.procesar_woocommerce(tienda_conf, tienda_obj, HEADERS)

        # 2. EJECUTAR CARGA LENTA (SELENIUM)
        self.stdout.write("\n🐢 FASE 2: Carga Lenta (Selenium)...")
        self.procesar_selenium(TIENDAS_SELENIUM)

        self.stdout.write(self.style.SUCCESS("\n✨ ¡Carga Masiva Híbrida Finalizada!"))

    # --- LÓGICA API (Igual que antes, optimizada) ---
    def procesar_shopify(self, conf, tienda_obj, headers):
        # ... (Copia aquí el método procesar_shopify del archivo anterior) ...
        # Para ahorrar espacio, asumo que usarás el mismo lógica que ya te funcionó.
        # Asegúrate de incluir la llamada a self.es_producto_relevante(nombre)
        base_url = conf['url_base']
        page = 1
        total_filtrados = 0
        while True:
            url = f"{base_url}/products.json?limit=250&page={page}"
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code != 200: break
                data = r.json()
                products = data.get('products', [])
                if not products: break
                self.stdout.write(f"   -> Pág {page}: {len(products)} items.")
                for item in products:
                    if self.es_producto_relevante(item['title']):
                        self.guardar_producto(item['title'], item.get('vendor') or conf['marca_default'], item.get('product_type') or "Otros", int(float(item['variants'][0]['price'])), item['images'][0]['src'] if item.get('images') else None, f"{base_url}/products/{item['handle']}", tienda_obj)
                        total_filtrados += 1
                page += 1
            except: break
        self.stdout.write(f"   -> Guardados: {total_filtrados}")

    def procesar_woocommerce(self, conf, tienda_obj, headers):
        # ... (Copia aquí el método procesar_woocommerce corregido) ...
        base_url = conf['url_base']
        page = 1
        total_filtrados = 0
        endpoints = ["/wp-json/wc/store/products", "/wp-json/wp/v2/product"]
        endpoint_activo = None
        for ep in endpoints:
            try:
                if requests.get(f"{base_url}{ep}", headers=headers, timeout=5).status_code == 200:
                    endpoint_activo = ep; break
            except: pass
        
        if not endpoint_activo: return

        while True:
            url = f"{base_url}{endpoint_activo}?page={page}&per_page=50"
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code != 200: break
                data = r.json()
                if not data: break
                self.stdout.write(f"   -> Pág {page}: {len(data)} items.")
                for item in data:
                    nombre = item.get('name') or item.get('title', {}).get('rendered')
                    if nombre and self.es_producto_relevante(nombre):
                        precio = int(item['prices']['price']) if 'prices' in item else int(float(item['price'])) if 'price' in item and item['price'] else 0
                        # Ajuste para precios en centavos si es necesario, pero probamos directo primero
                        if precio > 0:
                             img = item['images'][0].get('src') if 'images' in item and item['images'] else None
                             link = item.get('permalink') or item.get('link')
                             self.guardar_producto(nombre, conf['marca_default'], "Suplementos", precio, img, link, tienda_obj)
                             total_filtrados += 1
                page += 1
            except: break
        self.stdout.write(f"   -> Guardados: {total_filtrados}")

    # --- LÓGICA SELENIUM ---
    def procesar_selenium(self, tiendas):
        chrome_options = Options()
        chrome_options.add_argument("--headless") # Ejecutar en modo silencioso
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        for site in tiendas:
            self.stdout.write(f"--- Selenium: {site['nombre']} ---")
            tienda_obj, _ = Tienda.objects.get_or_create(name=site['nombre'])
            try:
                driver.get(site['url'])
                time.sleep(5)
                soup = BeautifulSoup(driver.page_source, 'lxml')
                productos = soup.find_all(site['container_tag'], class_=re.compile(site['container_class']))
                
                count = 0
                for prod in productos:
                    try:
                        tag_titulo = prod.select_one(site['title_selector'])
                        if not tag_titulo: continue
                        nombre = tag_titulo.text.strip()
                        
                        if not self.es_producto_relevante(nombre): continue

                        # Precio
                        tag_precio = prod.select_one(site['price_selector'])
                        precio = 0
                        if tag_precio:
                            precio = int(re.sub(r'[^\d]', '', tag_precio.text.strip()))

                        # Imagen y Link (Lógica simplificada)
                        href = tag_titulo.get('href')
                        link = site['base_url'] + href if href and not href.startswith('http') else href
                        
                        tag_img = prod.select_one(site['img_selector'])
                        img = tag_img.get('src') if tag_img else None

                        if precio > 0:
                            self.guardar_producto(nombre, site['marca_default'], site['categoria_fija'], precio, img, link, tienda_obj)
                            count += 1
                    except: continue
                self.stdout.write(f"   -> Guardados: {count}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error Selenium en {site['nombre']}: {e}"))
        
        driver.quit()

    def es_producto_relevante(self, nombre):
        nombre_lower = nombre.lower()
        for prohibida in self.PALABRAS_PROHIBIDAS:
            if prohibida in nombre_lower: return False
        for permitida in self.PALABRAS_PERMITIDAS:
            if permitida in nombre_lower: return True
        return False

    def guardar_producto(self, nombre, marca, categoria_nombre, precio, imagen, url_compra, tienda_obj):
        if not nombre or precio <= 0: return
        cat_obj, _ = Categoria.objects.get_or_create(name=categoria_nombre)
        prod_obj, _ = Producto.objects.update_or_create(
            name=nombre,
            defaults={'brand': marca, 'categoria': cat_obj, 'image_url': imagen or "https://via.placeholder.com/300"}
        )
        Oferta.objects.update_or_create(
            producto=prod_obj,
            tienda=tienda_obj,
            defaults={'price': precio, 'url_compra': url_compra}
        )