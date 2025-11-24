from django.core.management.base import BaseCommand
from catalog.models import Producto, Tienda, Oferta, PrecioHistorico
import time
import re
from bs4 import BeautifulSoup
from thefuzz import fuzz, process

# --- SELENIUM ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Command(BaseCommand):
    help = 'Cazador de Ofertas: Busca precios en tiendas nuevas (FitMarket, Bull, MuscleFactory)'

    def handle(self, *args, **kwargs):
        
        # --- 1. CARGAR TU CATÁLOGO ---
        mis_productos = list(Producto.objects.all())
        if not mis_productos:
            self.stdout.write(self.style.ERROR("¡Error! BD vacía. Ejecuta 'python manage.py scaner' primero."))
            return

        mis_productos_map = {p.name.lower(): p for p in mis_productos}
        lista_nombres_locales = list(mis_productos_map.keys())
        
        self.stdout.write(self.style.SUCCESS(f"--- Buscando ofertas para {len(mis_productos)} productos ---"))

        # --- 2. LISTA NEGRA (ANTI-BASURA) ---
        PALABRAS_PROHIBIDAS = [
            'short', 'calza', 'top', 'polera', 'hoodie', 'camiseta', 'ropa', 'gorro', 
            'shaker', 'botella', 'toalla', 'mochila', 'jabon', 'crema', 'gift card', 
            'straps', 'muñequera', 'cinturon'
        ]

        # --- 3. NUEVAS TIENDAS CONFIGURADAS ---
        SITES = [
            
            {
                'nombre': 'Fit Market Chile',
                'tienda_db': 'Fit Market Chile',
                'url': 'https://fitmarketchile.cl/categoria-producto/proteinas/',
                'base_url': 'https://fitmarketchile.cl',
                'container': 'div.product-small', 
                'title': 'p.name a',
                'price': 'span.price',
                'link': 'p.name a'
            },
            {
                'nombre': 'Suplementos Bull',
                'tienda_db': 'Suplementos Bull',
                'url': 'https://www.suplementosbullchile.cl/proteinas',
                'base_url': 'https://www.suplementosbullchile.cl',
                'container': 'div.product-block', 
                'title': 'div.caption h4 a',
                'price': 'div.price',
                'link': 'div.caption h4 a'
            },
            {
                'nombre': 'Muscle Factory',
                'tienda_db': 'Muscle Factory',
                'url': 'https://www.musclefactory.cl/proteinas',
                'base_url': 'https://www.musclefactory.cl',
                'container': 'div.product-block',
                'title': 'div.caption h4 a',
                'price': 'div.price',
                'link': 'div.caption h4 a'
            }
        ]

        options = Options()
        options.add_argument("--headless=new") 
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080") 
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        def clean_price(text):
            if not text: return 0
            try:
                return int(re.sub(r'[^\d]', '', str(text)))
            except: return 0

        for site in SITES:
            print(f"\n>>> Visitando: {site['nombre']}...")
            tienda_obj, _ = Tienda.objects.get_or_create(name=site['tienda_db'])
            
            try:
                driver.get(site['url'])
                
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, site['container']))
                    )
                except:
                    self.stdout.write(self.style.WARNING(f"    Alerta: La página tardó en cargar. Intentando leer igual..."))
                
                total_height = int(driver.execute_script("return document.body.scrollHeight"))
                for i in range(1, total_height, 700):
                    driver.execute_script(f"window.scrollTo(0, {i});")
                    time.sleep(0.2)
                
                time.sleep(2) 

                soup = BeautifulSoup(driver.page_source, 'lxml')
                productos_html = soup.select(site['container'])
                
                if not productos_html:
                    self.stdout.write(self.style.ERROR(f"    0 productos encontrados. El diseño puede haber cambiado."))
                    continue

                count_match = 0
                count_ignored = 0

                for item in productos_html:
                    try:
                        # Extracción Segura
                        tag_title = item.select_one(site['title'])
                        if not tag_title: continue
                        nombre_web = tag_title.get_text(strip=True)
                        
                        # Filtro Rápido Anti-Basura
                        if any(x in nombre_web.lower() for x in PALABRAS_PROHIBIDAS):
                            continue

                        # Precio
                        tag_price = item.select_one(site['price'])
                        if not tag_price: continue
                        
                        precio_texto = tag_price.get_text(strip=True)
                        numeros = [int(s) for s in re.findall(r'\d+', precio_texto.replace('.', ''))]
                        
                        if not numeros: continue
                        precio = min([n for n in numeros if n > 2000]) 

                        
                        tag_link = item.select_one(site['link'])
                        url_compra = site['base_url']
                        if tag_link and tag_link.get('href'):
                            href = tag_link.get('href')
                            if href.startswith('http'): url_compra = href
                            else: url_compra = site['base_url'] + href

                        mejor_match, puntaje = process.extractOne(nombre_web.lower(), lista_nombres_locales, scorer=fuzz.token_set_ratio)
                        
                        if puntaje >= 85:
                            producto_db = mis_productos_map[mejor_match]
                            
                            Oferta.objects.update_or_create(
                                producto=producto_db,
                                tienda=tienda_obj,
                                defaults={'price': precio, 'url_compra': url_compra}
                            )
                            PrecioHistorico.objects.create(producto=producto_db, tienda=tienda_obj, price=precio)
                            
                            count_match += 1
                            self.stdout.write(f"    {nombre_web[:30]}... -> ${precio}")
                        else:
                            count_ignored += 1

                    except Exception:
                        continue
                
                self.stdout.write(self.style.SUCCESS(f"   Resumen: {count_match} Vinculados | {count_ignored} No estaban en tu BD"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    Error crítico: {e}"))

        driver.quit()
        self.stdout.write(self.style.SUCCESS("\n¡Búsqueda de ofertas terminada!"))