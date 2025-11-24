from django.core.management.base import BaseCommand
from catalog.models import Producto, Tienda, Oferta, PrecioHistorico
from django.core.mail import send_mail
from django.conf import settings
import requests
import json
import traceback
from thefuzz import fuzz, process

class Command(BaseCommand):
    help = 'Scanner JSON (Blindado): Descarga masiva + Alerta de Fallos (HU12)'

    def handle(self, *args, **kwargs):
        
        # --- BLOQUE DE SEGURIDAD (HU12) ---
        try:
            # --- 1. CONFIGURACIÓN DE TIENDAS (SOLO SHOPIFY COMPATIBLES) ---
            # Se agregaron las URLs nuevas compatibles con este motor JSON
            TIENDAS_SHOPIFY = [
                {'nombre': 'All Nutrition', 'url_json': 'https://allnutrition.cl/products.json?limit=250'},
                {'nombre': 'Mayorista WF', 'url_json': 'https://mayorista.thewildfoods.com/products.json?limit=250'},
                {'nombre': 'Wild Foods',   'url_json': 'https://thewildfoods.com/products.json?limit=250'}, # <-- Agregada del código nuevo
                {'nombre': 'Chile Be Free', 'url_json': 'https://chilebefree.com/products.json?limit=250'},
                {'nombre': 'Chile suplemento', 'url_json': 'https://www.chilesuplementos.cl/categoria/productos/vitaminas-y-wellness/.json?limit=250'},
            ]

            # NO DESCOMENTAR (Para pruebas de estrés)
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
                    response = requests.get(url, headers=HEADERS, timeout=20)
                    if response.status_code != 200:
                        self.stdout.write(self.style.ERROR(f"   Error conectando a {nombre_tienda} (Status {response.status_code})"))
                        continue
                    
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        self.stdout.write(self.style.ERROR(f"   Error: La respuesta de {nombre_tienda} no es un JSON válido."))
                        continue

                    # Validación específica para estructura Shopify
                    productos_externos = data.get('products', [])
                    if not productos_externos:
                        self.stdout.write(self.style.WARNING(f"   JSON válido pero sin productos en {nombre_tienda} (¿Cambió la estructura?)"))
                        continue

                    self.stdout.write(f"    Recibidos {len(productos_externos)} productos. Analizando...")

                    tienda_obj, _ = Tienda.objects.get_or_create(name=nombre_tienda)
                    matches_count = 0

                    for item in productos_externos:
                        titulo_externo = item['title']
                        # Fuzzy Matching
                        mejor_match, puntaje = process.extractOne(titulo_externo.lower(), lista_nombres_locales, scorer=fuzz.token_set_ratio)

                        if puntaje >= 85:
                            producto_local = mis_productos_map[mejor_match]
                            try:
                                # Lógica de extracción segura
                                variants = item.get('variants', [])
                                if not variants: continue
                                
                                variante = variants[0]
                                price_raw = variante.get('price', 0)
                                precio = int(float(price_raw))
                                
                                slug = item.get('handle', '')
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

                                    self.stdout.write(self.style.SUCCESS(f"    [MATCH {puntaje}%] {titulo_externo[:30]}... -> ${precio}"))
                                    matches_count += 1

                            except Exception as e_item:
                                # Error en un producto individual no detiene el loop
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
                    recipient_list=[settings.EMAIL_HOST_USER],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(">> Correo de alerta enviado con éxito."))
            except Exception as e_mail:
                self.stdout.write(self.style.ERROR(f">> No se pudo enviar el correo de alerta: {e_mail}"))