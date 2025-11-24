from django.core.management.base import BaseCommand
import requests
import time

class Command(BaseCommand):
    help = 'Verifica si las tiendas tienen "puerta trasera" JSON (Shopify/WooCommerce)'

    def handle(self, *args, **kwargs):
        self.stdout.write("🕵️‍♂️ Investigando librerías JSON en las tiendas...")

        # Lista actualizada con tus tiendas
        SITES = [
            {'nombre': 'Wild Foods', 'url_base': 'https://thewildfoods.com'},
            {'nombre': 'Estas En Línea', 'url_base': 'https://tienda.estasenlinea.cl'},
            {'nombre': 'Chile Suplementos', 'url_base': 'https://www.chilesuplementos.cl'},
            {'nombre': 'One Nutrition', 'url_base': 'https://onenutrition.cl'},
            {'nombre': 'Suplementos Al Mayor', 'url_base': 'https://suplementosalmayor.cl'},
            {'nombre': 'My Protein Chile', 'url_base': 'https://www.supletech.cl'},
            


        ]

        HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        for site in SITES:
            nombre = site['nombre']
            base = site['url_base']
            
            self.stdout.write(f"\n--- Analizando: {nombre} ---")
            
            # 1. PRUEBA SHOPIFY (/products.json)
            # Si funciona, devuelve TODOS los productos de una vez.
            url_shopify = f"{base}/products.json"
            try:
                resp = requests.get(url_shopify, headers=HEADERS, timeout=5)
                if resp.status_code == 200 and 'products' in resp.json():
                    self.stdout.write(self.style.SUCCESS(f"✅ {nombre} es SHOPIFY. Tiene librería JSON abierta."))
                    self.stdout.write(f"   -> Estrategia: Usar carga masiva JSON (Súper Rápido)")
                    continue 
            except:
                pass

            # 2. PRUEBA WOOCOMMERCE API (/wp-json/...)
            # Común en Chile Suplementos y Suplementos Al Mayor
            url_woo = f"{base}/wp-json/wp/v2/product"
            try:
                resp = requests.get(url_woo, headers=HEADERS, timeout=5)
                # Si devuelve una lista [], es un endpoint válido de WordPress
                if resp.status_code == 200 and isinstance(resp.json(), list):
                    self.stdout.write(self.style.SUCCESS(f"✅ {nombre} tiene API WOOCOMMERCE abierta."))
                    self.stdout.write(f"   -> Estrategia: Leer API JSON (Rápido y seguro)")
                    continue
            except:
                pass
            
            # 3. Si falla todo
            self.stdout.write(self.style.ERROR(f"❌ {nombre} no tiene JSON público fácil."))
            self.stdout.write(f"   -> Estrategia: Usar Selenium (Lento pero efectivo)")
            
        self.stdout.write("\n--- Fin del Diagnóstico ---")