from django.core.management.base import BaseCommand
from catalog.models import Producto, Tienda, Oferta, PrecioHistorico, Categoria
from django.core.mail import send_mail
from django.conf import settings
import requests
import json
import traceback
from thefuzz import fuzz, process

class Command(BaseCommand):
    help = 'Scanner JSON Definitivo: Crea productos nuevos y compara precios (Modo Solotodo) con Alerta de Error'

    def handle(self, *args, **kwargs):
        try:
            #FALLO
            raise Exception("¡PRUEBA DE FALLO! Esto es una simulación de error crítico para probar las alertas.")

            mis_productos = list(Producto.objects.all())
            mis_productos_map = {p.name.lower(): p for p in mis_productos}
            lista_nombres_locales = list(mis_productos_map.keys())
            

            cat_cache = {}
            
            self.stdout.write(f"--- Base de Datos Inicial: {len(mis_productos)} productos ---")

            
            TIENDAS_SHOPIFY = [
                {'nombre': 'All Nutrition', 'url_json': 'https://allnutrition.cl/products.json?limit=250'},
                {'nombre': 'Mayorista WF', 'url_json': 'https://mayorista.thewildfoods.com/products.json?limit=250'},
                {'nombre': 'Chile Be Free', 'url_json': 'https://chilebefree.com/products.json?limit=250'},
                {'nombre': 'VC Suplementos', 'url_json': 'https://vcsuplementos.cl/products.json?limit=250'},
                {'nombre': 'Hopkins', 'url_json': 'https://hopkins.cl/products.json?limit=250'},
                {'nombre': 'The Fuel Place', 'url_json': 'https://thefuelplace.com/products.json?limit=250'},
                {'nombre': 'Global Nutrition', 'url_json': 'https://globalnutrition.cl/products.json?limit=250'},
                {'nombre': 'TBH Suplementos', 'url_json': 'https://tbhsuplementos.cl/products.json?limit=250'},
                {'nombre': 'MixGreen', 'url_json': 'https://www.mixgreen.cl/products.json?limit=250'},
                
                {'nombre': 'Sportika', 'url_json': 'https://sportika.cl/products.json?limit=250'},
                {'nombre': 'Suples', 'url_json': 'https://www2.suples.cl/products.json?limit=250'},
                {'nombre': 'Biogymstore', 'url_json': 'https://biogymstore.cl/products.json?limit=250'},
                {'nombre': 'Wild Foods', 'url_json': 'https://thewildfoods.com/products.json?limit=250'},
                {'nombre': 'Wild Foods USA', 'url_json': 'https://thewildfoods.com/products.json?limit=250'},
                {'nombre': 'Swolverine', 'url_json': 'https://swolverine.com/products.json?limit=250'},
                {'nombre': 'Legion Athletics', 'url_json': 'https://legionathletics.com/products.json?limit=250'},
                {'nombre': 'Transparent Labs', 'url_json': 'https://www.transparentlabs.com/products.json?limit=250'},
                {'nombre': 'NutraBio', 'url_json': 'https://nutrabio.com/products.json?limit=250'},
                {'nombre': 'Kaged', 'url_json': 'https://www.kagedmuscle.com/products.json?limit=250'},
                
                {'nombre': 'Supplements Canada', 'url_json': 'https://www.supplementscanada.com/products.json?limit=250'},
            ]

            HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

            PALABRAS_PROHIBIDAS = [
                
                'short', 'calza', 'top', 'tank', 'hoodie', 'poleron', 'polera', 'camiseta', 
                'leggins', 'vestuario', 'ropa', 'gorro', 'jockey', 'calcetines', 'straps', 
                'muñequera', 'cinturon', 'bolso', 'mochila', 'toalla', 'guantes',
                
                'shaker', 'mezclador', 'botella', 'vaso', 'pastillero', 'bandas elasticas',
                'colchoneta', 'mat', 'yoga mat', 'pesas', 'mancuerna', 'disco',
                
                'jabon', 'jabón', 'locion', 'loción', 'crema', 'shampoo', 'acondicionador', 'gel',
                'gift card', 'tarjeta de regalo', 'servicio', 'flete', 'envio', 'despacho',
                'dr. teal', 'dr teals', 'salsa', 'aderezo', 'sirope', 'mantequilla',
                'cereal', 'granola', 'chocolate', 'dulce', 'caramelo', 'chicle',
            ]

            def detectar_categoria(nombre):
                nombre = nombre.lower()
                if any(x in nombre for x in ['whey', 'protein', 'proteína', 'aislada', 'isolate', 'beef', 'vegan', 'vegetal', 'caseina', 'casein']): 
                    return 'Proteínas en Polvo'
                if any(x in nombre for x in ['barra', 'barrita', 'snack', 'cookie', 'galleta', 'brownie', 'alfajor']): 
                    return 'Barritas Proteicas'
                if any(x in nombre for x in ['creatina', 'creatine']): 
                    return 'Creatina'
                if any(x in nombre for x in ['pre-workout', 'pre entreno', 'pre-entreno', 'preentreno', 'beta alanina', 'citrulina']): 
                    return 'Pre-Entrenos'
                if any(x in nombre for x in ['vitamin', 'multivitaminico', 'omega', 'zinc', 'magnesio', 'colageno', 'colágeno', 'biotina', 'calcio']): 
                    return 'Vitaminas y Salud'
                if any(x in nombre for x in ['quemador', 'fat burner', 'l-carnitina', 'cla', 'cafeina', 'termogenico', 'termogénico']):
                    return 'Quemadores'
                if any(x in nombre for x in ['bcaa', 'aminoacido', 'aminoácido', 'glutamina', 'eaa', 'hmb']):
                    return 'Aminoácidos'
                if any(x in nombre for x in ['mass gainer', 'ganador', 'hipercalorico', 'hipercalórico']):
                    return 'Ganadores de Masa'
                return None 

            total_nuevos = 0
            total_match = 0
            total_filtrados = 0
            tiendas_exitosas = 0
            tiendas_fallidas = 0

            for tienda_conf in TIENDAS_SHOPIFY:
                nombre_tienda = tienda_conf['nombre']
                url = tienda_conf['url_json']
                
                self.stdout.write(f"\n>>> Conectando a: {nombre_tienda}...")

                try:
                    response = requests.get(url, headers=HEADERS, timeout=20)
                    if response.status_code != 200:
                        self.stdout.write(self.style.WARNING(f"   ⚠ Saltando {nombre_tienda} (Status {response.status_code})"))
                        tiendas_fallidas += 1
                        continue
                    
                    data = response.json()
                    productos_externos = data.get('products', [])
                    
                    if not productos_externos:
                        self.stdout.write(self.style.WARNING(f"   ⚠ Sin productos en {nombre_tienda}"))
                        tiendas_fallidas += 1
                        continue
                    
                    tienda_obj, _ = Tienda.objects.get_or_create(name=nombre_tienda)
                    tiendas_exitosas += 1
                    
                    count_nuevos = 0
                    count_match = 0
                    count_filtrados = 0

                    for item in productos_externos:
                        titulo_externo = item['title']
                        titulo_lower = titulo_externo.lower()

                        if any(banned in titulo_lower for banned in PALABRAS_PROHIBIDAS):
                            count_filtrados += 1
                            continue 

                        cat_nombre = detectar_categoria(titulo_externo)
                        
                        if not cat_nombre:
                            count_filtrados += 1
                            continue

                        producto_final = None
                        if lista_nombres_locales:
                            mejor_match, puntaje = process.extractOne(titulo_lower, lista_nombres_locales, scorer=fuzz.token_set_ratio)
                            if puntaje >= 89:
                                producto_final = mis_productos_map[mejor_match]
                                count_match += 1
                        
                        if not producto_final:
                            if cat_nombre not in cat_cache:
                                c_obj, _ = Categoria.objects.get_or_create(name=cat_nombre)
                                cat_cache[cat_nombre] = c_obj
                            
                            img = "https://via.placeholder.com/300"
                            if item.get('images') and len(item['images']) > 0:
                                img = item['images'][0]['src']

                            producto_final = Producto.objects.create(
                                name=titulo_externo,
                                brand=item.get('vendor', 'Generico'),
                                categoria=cat_cache[cat_nombre],
                                image_url=img
                            )
                            mis_productos_map[titulo_lower] = producto_final
                            lista_nombres_locales.append(titulo_lower)
                            count_nuevos += 1

                        try:
                            variante = item['variants'][0]
                            precio = int(float(variante['price']))
                            
                            if precio > 2000:
                                slug = item['handle']
                                domain = url.split('/products.json')[0]
                                url_final = f"{domain}/products/{slug}"

                                Oferta.objects.update_or_create(
                                    producto=producto_final,
                                    tienda=tienda_obj,
                                    defaults={'price': precio, 'url_compra': url_final}
                                )
                                PrecioHistorico.objects.create(producto=producto_final, tienda=tienda_obj, price=precio)

                        except Exception:
                            continue
                    
                    total_nuevos += count_nuevos
                    total_match += count_match
                    total_filtrados += count_filtrados
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"   ✓ {count_nuevos} Nuevos | {count_match} Matches | {count_filtrados} Ignorados"
                    ))

                except requests.exceptions.Timeout:
                    self.stdout.write(self.style.ERROR(f"   ✗ Timeout conectando a {nombre_tienda}"))
                    tiendas_fallidas += 1
                except requests.exceptions.ConnectionError:
                    self.stdout.write(self.style.ERROR(f"   ✗ Error de conexión con {nombre_tienda}"))
                    tiendas_fallidas += 1
                except Exception as e_tienda:
                    self.stdout.write(self.style.ERROR(f"   ✗ Error: {str(e_tienda)[:100]}"))
                    tiendas_fallidas += 1

            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.SUCCESS("--- ESCANEO COMPLETO FINALIZADO ---"))
            self.stdout.write(f"Tiendas procesadas exitosamente: {tiendas_exitosas}/{len(TIENDAS_SHOPIFY)}")
            self.stdout.write(f"Tiendas con error: {tiendas_fallidas}")
            self.stdout.write(f"Total productos nuevos agregados: {total_nuevos}")
            self.stdout.write(f"Total matches encontrados: {total_match}")
            self.stdout.write(f"Total productos filtrados: {total_filtrados}")
            self.stdout.write("="*60 + "\n")

        except Exception as e:
            error_detalle = traceback.format_exc()
            self.stdout.write(self.style.ERROR(f"¡ERROR CRÍTICO DETECTADO!\n{error_detalle}"))
            
            asunto = "🚨 ALERTA: El Scanner de Precios Falló (Todo Protein)"
            mensaje = f"""
            Hola Admin,

            El proceso automático de escaneo de precios (scaner.py) ha fallado inesperadamente.
            
            --------------------------------------------------
            ERROR PRINCIPAL:
            {str(e)}
            --------------------------------------------------

            DETALLES TÉCNICOS:
            {error_detalle}

            Por favor revisa el servidor o los logs.
            """
            
            try:
                # Usamos el correo configurado en settings.EMAIL_HOST_USER como destinatario
                destinatarios = [settings.EMAIL_HOST_USER] 
                
                send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=destinatarios,
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(">> 📧 Correo de alerta enviado al administrador."))
            except Exception as e_mail:
                self.stdout.write(self.style.ERROR(f">> ❌ No se pudo enviar el correo de alerta: {e_mail}"))