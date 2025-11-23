import time
import re
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Producto, Categoria

# Importaciones de Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

def clean_price(price_text):
    """Limpia el precio, quita $ y ."""
    return int(''.join(filter(str.isdigit, price_text)))

def scrape_lider_page(lider_product_url, django_category):
    """
    Abre UNA página de producto de Lider usando el perfil de usuario de Chrome
    para evitar el CAPTCHA y extrae los datos.
    """
    
    service = Service(ChromeDriverManager().install())
    
    # --- CONFIGURACIÓN DE PERFIL DE USUARIO ---
    options = webdriver.ChromeOptions()
    user_profile_path = os.environ.get('LOCALAPPDATA')
    
    if not user_profile_path:
        print("[ERROR] No se pudo encontrar la ruta LOCALAPPDATA. Abortando.")
        return False
        
    chrome_user_data_dir = os.path.join(user_profile_path, r"Google\Chrome\User Data")
    
    options.add_argument(f"user-data-dir={chrome_user_data_dir}")
    options.add_argument("profile-directory=Default")
    options.add_argument("start-maximized")
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36')
    # options.add_argument('--headless') # No usar headless, Lider lo detecta

    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"[ERROR AL INICIAR CHROME] {e}")
        print("-> Asegúrate de CERRAR TODAS las ventanas de Chrome antes de ejecutar.")
        return False

    print(f"  -> [Lider] Abriendo navegador con tu perfil...")
    driver.get(lider_product_url)
    
    try:
        # --- 1. Esperar a que la página cargue ---
        # Esperamos por el NOMBRE del producto, que tiene un data-testid
        print("    -> Esperando que la página del producto cargue...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='product-name']"))
        )
        print("    -> ¡Página cargada! Extrayendo datos...")
        time.sleep(2) # Pausa por si acaso

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # --- 2. Extraer Datos ---
        
        # SKU (Lo sacamos de la URL que nos dio el usuario)
        sku_match = re.search(r'/([\d]{12,})$', lider_product_url)
        if not sku_match:
             print(f"    [ERROR] No se pudo extraer SKU de la URL: {lider_product_url}")
             driver.quit()
             return False
        sku_lider = sku_match.group(1)

        # Nombre
        name_tag = soup.find('div', {'data-testid': 'product-name'})
        nombre = name_tag.get_text(strip=True) if name_tag else None

        # Marca
        brand_tag = soup.find('div', {'data-testid': 'product-brand'})
        marca = brand_tag.get_text(strip=True) if brand_tag else "Sin Marca"

        # Precio
        price_tag = soup.find('span', {'data-testid': 'product-price'})
        precio_texto = price_tag.get_text(strip=True) if price_tag else "0"
        precio = clean_price(precio_texto)
        
        # Proteína (No está en un tag fácil, la dejamos N/A por ahora)
        gramos_proteina = "N/A" # El usuario puede editarlo en el Admin

        if not all([nombre, marca, precio > 0]):
            print(f"    [ERROR] No se pudieron extraer todos los datos (Nombre, Marca o Precio).")
            driver.quit()
            return False

        # --- 3. Guardar en Base de Datos ---
        defaults = {
            'name': nombre,
            'brand': marca,
            'categoria': django_category,
            'price': precio, 
            'protein_grams': gramos_proteina,
            'image_url': f"https://www.lider.cl/catalogo/images/catalogo_xl/{sku_lider}.jpg",
            'price_lider': precio,
            'url_lider': lider_product_url,
            'price_jumbo': 0, 
            'price_acuenta': 0,
            'price_unimarc': 0,
        }

        with transaction.atomic():
            producto, created = Producto.objects.update_or_create(
                sku_lider=sku_lider,
                defaults=defaults
            )
        
        if created:
            print(f"    [CREADO] {producto.brand} - {producto.name} (${producto.price})")
        else:
            print(f"    [ACTUALIZADO] {producto.brand} - {producto.name} (${producto.price})")

        driver.quit()
        return True

    except TimeoutException:
        print(f"    [ERROR] CAPTCHA DETECTADO O PÁGINA NO CARGÓ.")
        print(f"    -> Asegúrate de 'calentar' tu perfil de Chrome (Paso 1) e inténtalo de nuevo.")
        driver.quit()
        return False
    except Exception as e:
        print(f"    [ERROR INESPERADO] {e}")
        driver.quit()
        return False


class Command(BaseCommand):
    help = 'Agrega o actualiza UN producto de Lider.cl usando su URL.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Asistente para Scrapear por Link ---'))
        self.stdout.write("Asegúrate de haber 'calentado' tu perfil de Chrome primero.")
        self.stdout.write(self.style.WARNING("Cierra TODAS las ventanas de Chrome antes de continuar."))
        input(self.style.NOTICE("Presiona ENTER cuando estés listo..."))

        while True:
            # 1. Pedir URL
            url_lider = input(self.style.NOTICE("\nPega la URL del producto (o 'salir'): ")).strip()
            if url_lider == 'salir' or not url_lider:
                break
            
            # 2. Pedir Categoría
            categoria_nombre = input(self.style.NOTICE("Categoría en tu BD (ej. Suplementos): ")).strip()
            if categoria_nombre == 'salir' or not categoria_nombre:
                break
                
            categoria_obj, cat_created = Categoria.objects.get_or_create(name=categoria_nombre)
            if cat_created:
                self.stdout.write(f"  -> Se creó la categoría '{categoria_nombre}' en la BD.")

            # 3. Ejecutar Scraper
            success = scrape_lider_page(url_lider, categoria_obj)
            
            if success:
                self.stdout.write(self.style.SUCCESS("--- Producto procesado ---"))
            else:
                self.stdout.write(self.style.ERROR("--- Falló el procesamiento del producto ---"))
        
        self.stdout.write(self.style.SUCCESS('--- Asistente finalizado ---'))