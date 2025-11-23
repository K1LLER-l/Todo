from django.core.management.base import BaseCommand
from catalog.models import Producto, PrecioHistorico
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Genera historial falso de 10 días para probar gráficos'

    def handle(self, *args, **kwargs):
        productos = Producto.objects.all()
        self.stdout.write("Generando datos históricos simulados...")

        for prod in productos:
            # Buscamos si tiene alguna oferta base
            oferta = prod.ofertas.first()
            if not oferta: continue
            
            precio_base = oferta.price
            tienda = oferta.tienda

            # Crear 10 puntos de historia hacia atrás
            for dias in range(1, 11):
                fecha_atras = timezone.now() - timedelta(days=dias)
                # Variamos el precio un poco (+/- 10%)
                factor = random.uniform(0.9, 1.1)
                precio_falso = int(precio_base * factor)

                # Guardamos el historial
                hist, created = PrecioHistorico.objects.get_or_create(
                    producto=prod,
                    tienda=tienda,
                    price=precio_falso,
                )
                # Forzamos la fecha antigua
                hist.fecha = fecha_atras
                hist.save()

        self.stdout.write(self.style.SUCCESS("¡Listo! Historial generado. Refresca tu página."))