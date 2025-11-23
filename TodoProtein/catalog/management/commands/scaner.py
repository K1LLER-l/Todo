from django.core.management.base import BaseCommand
from catalog.models import Producto, Tienda, Oferta, PrecioHistorico
from django.core.mail import send_mail
from django.conf import settings
import requests
import json
import traceback # Para obtener el detalle del error
from thefuzz import fuzz, process

class Command(BaseCommand):
    help = 'Scanner JSON (Blindado): Descarga masiva + Alerta de Fallos (HU12)'

    def handle(self, *args, **kwargs):
        
        # --- BLOQUE DE SEGURIDAD (HU12) ---
        try:
            # --- 1. TIENDAS SHOPIFY ---
            TIENDAS_SHOPIFY = [
                {'nombre': 'All Nutrition', 'url_json': 'https://allnutrition.cl/products.json?limit=250'},
                {'nombre': 'Booz', 'url_json': 'https://www.booz.cl/products.json?limit=250'},
                {'nombre': 'Mayorista WF', 'url_json': 'https://mayorista.thewildfoods.com/products.json?limit=250'},
                {'nombre': 'Chile Be Free', 'url_json': 'https://chilebefree.com/products.json?limit=250'},
            ]

            # NO DESCOMENTAR 
            #raise Exception("¡Prueba de Alerta HU12! El scanner JSON colapsó.")

            mis_productos = list(Producto.objects.all())
            if not mis_productos:
                self.stdout.write(self.style.ERROR("No tienes productos en tu base de datos."))
                return

            mis_productos_map = {p.name.lower(): p for p in mis_productos}
            lista_nombres_locales = list(mis_productos_map.keys())

            HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

            self.stdout.write(f"--- Iniciando Escaneo JSON contra {len(mis_productos)} productos locales ---\n")

            for tienda_conf in TIENDAS_SHOPIFY:
                nombre_tienda = tienda_conf['nombre']
                url = tienda_conf['url_json']
                
                self.stdout.write(f">>> Descargando catálogo de: {nombre_tienda}...")

                try:
                    response = requests.get(url, headers=HEADERS, timeout=20) # Aumenté el timeout a 20s
                    if response.status_code != 200:
                        self.stdout.write(self.style.ERROR(f"   Error conectando a {nombre_tienda} (Status {response.status_code})"))
                        continue
                    
                    data = response.json()
                    productos_externos = data.get('products', [])
                    self.stdout.write(f"    Recibidos {len(productos_externos)} productos. Analizando...")

                    tienda_obj, _ = Tienda.objects.get_or_create(name=nombre_tienda)
                    matches_count = 0

                    for item in productos_externos:
                        titulo_externo = item['title']
                        mejor_match, puntaje = process.extractOne(titulo_externo.lower(), lista_nombres_locales, scorer=fuzz.token_set_ratio)

                        if puntaje >= 85:
                            producto_local = mis_productos_map[mejor_match]
                            try:
                                variante = item['variants'][0]
                                precio = int(float(variante['price']))
                                slug = item['handle']
                                domain = url.split('/products.json')[0]
                                url_final = f"{domain}/products/{slug}"

                                if precio > 0:
                                    Oferta.objects.update_or_create(
                                        producto=producto_local,
                                        tienda=tienda_obj,
                                        defaults={'price': precio, 'url_compra': url_final}
                                    )
                                    
                                    # Guardar Historial
                                    PrecioHistorico.objects.create(
                                        producto=producto_local,
                                        tienda=tienda_obj,
                                        price=precio
                                    )

                                    self.stdout.write(self.style.SUCCESS(f"    [MATCH {puntaje}%] {titulo_externo[:40]}... -> ${precio}"))
                                    matches_count += 1

                            except Exception:
                                continue
                    
                    if matches_count == 0:
                        self.stdout.write(self.style.WARNING(f"    No se encontraron coincidencias en {nombre_tienda}."))

                except Exception as e_tienda:
                    self.stdout.write(self.style.ERROR(f"    Error al procesar tienda {nombre_tienda}: {e_tienda}"))

            self.stdout.write(self.style.SUCCESS("\n--- Proceso JSON Finalizado ---"))

        # --- CAPTURA DE ERROR FATAL (HU12) ---
        except Exception as e:
            error_detalle = traceback.format_exc()
            self.stdout.write(self.style.ERROR(f"¡ERROR CRÍTICO! Enviando alerta al admin...\n{error_detalle}"))
            
            asunto = "🚨 ALERTA CRÍTICA: Scanner JSON Falló"
            mensaje = f"""
            El proceso de actualización masiva (JSON) ha fallado.
            
            Error: {str(e)}
            
            Detalles Técnicos:
            {error_detalle}
            """
            
            try:
                send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_HOST_USER], # Se envía a tu correo configurado
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(">> Correo de alerta enviado con éxito."))
            except Exception as e_mail:
                self.stdout.write(self.style.ERROR(f">> No se pudo enviar el correo de alerta: {e_mail}"))