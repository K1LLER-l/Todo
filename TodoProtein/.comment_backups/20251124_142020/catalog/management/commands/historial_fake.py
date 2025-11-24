from django.core.management.base import BaseCommand
from catalog.models import Producto, PrecioHistorico, Tienda, Oferta
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Genera historial falso para pruebas de gráficos'

    def handle(self, *args, **kwargs):
        productos = Producto.objects.all()
        
        if not productos.exists():
            self.stdout.write("No hay productos. Ejecuta el scraper primero.")
            return

        self.stdout.write("Generando historial de prueba...")

        for prod in productos:
            # Buscamos si tiene alguna oferta para saber qué tienda usar
            oferta_base = prod.ofertas.first()
            if not oferta_base:
                continue
                
            tienda = oferta_base.tienda
            precio_actual = oferta_base.price
            
            # Generar datos para los últimos 10 días
            for i in range(1, 11):
                # Fecha hacia atrás
                fecha_atras = timezone.now() - timedelta(days=i)
                
                # Variación de precio simulada (+/- 5% a 15%)
                variacion = random.uniform(0.85, 1.15) 
                precio_falso = int(precio_actual * variacion)
                
                # Crear el registro histórico
                # Usamos get_or_create para no duplicar si lo corres varias veces
                hist, created = PrecioHistorico.objects.get_or_create(
                    producto=prod,
                    tienda=tienda,
                    price=precio_falso,
                )
                # Forzamos la fecha antigua (porque auto_now_add pone la fecha de hoy)
                hist.fecha = fecha_atras
                hist.save()

        self.stdout.write(self.style.SUCCESS("¡Historial falso generado! Revisa tu gráfico."))