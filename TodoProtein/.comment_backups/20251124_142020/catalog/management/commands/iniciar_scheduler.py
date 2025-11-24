import time
import schedule # Asegúrate de instalarlo: pip install schedule
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

class Command(BaseCommand):
    help = 'Ejecuta el ciclo completo: Scaner (Shopify) + Selenium + Alertas automáticamente.'

    def job_scraping(self):
        self.stdout.write(self.style.WARNING(f"\n[{timezone.now()}] --- INICIANDO CICLO DE ACTUALIZACIÓN ---"))
        try:
            # 1. EJECUTAR SCANER (El masivo de Shopify)
            # Este es el más importante porque crea productos nuevos y actualiza 12 tiendas rápido.
            self.stdout.write(self.style.SUCCESS(">>> Paso 1: Ejecutando Scanner Shopify..."))
            call_command('scaner') 
            
            # 2. EJECUTAR SCRAPER MANUAL (Selenium)
            # Este busca precios en tiendas difíciles (Suples.cl, Supletech, etc.) para los productos existentes.
            #self.stdout.write(self.style.SUCCESS(">>> Paso 2: Ejecutando Scraper Selenium (Tiendas Difíciles)..."))
            #call_command('scrape_category_pages')
            
            self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] --- ACTUALIZACIÓN DE PRECIOS FINALIZADA ---"))
            
            # 3. VERIFICAR ALERTAS
            # Una vez actualizados los precios, revisamos si bajó algún favorito.
            self.job_alertas()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f" [X] Error crítico en el ciclo de actualización: {e}"))
            # Aquí podrías agregar lógica para enviar un mail de aviso al admin (HU12)

    def job_alertas(self):
        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] >>> Paso 3: Verificando alertas de precio para usuarios..."))
        try:
            call_command('enviar_alerta')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error enviando alertas: {e}"))

    def job_resumen_semanal(self):
        # Este se ejecutaría una vez a la semana (ej. Lunes)
        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Enviando resúmenes semanales..."))
        # Asegúrate de tener este comando creado o coméntalo si no existe aún
        # call_command('enviar_resumen_semanal') 
        pass

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Iniciando Scheduler Maestro de Todo Protein ---")
        self.stdout.write("   > Tareas programadas: Scaner + Selenium + Alertas")
        self.stdout.write("   > Ejecución: Cada 12 horas")
        self.stdout.write("El sistema se ejecutará en segundo plano. Presiona Ctrl+C para detener.\n")

        # --- CONFIGURACIÓN DEL HORARIO ---
        
        # Opción A: Pruebas (ejecutar cada 10 minutos para ver si funciona)
        schedule.every(2).minutes.do(self.job_scraping)
        
        # Opción B: Producción (cada 12 horas, ej: 9 AM y 9 PM)
        schedule.every(12).hours.do(self.job_scraping)
        
        # Opción C: Resumen semanal (Lunes 9:00 AM)
        schedule.every().monday.at("09:00").do(self.job_resumen_semanal)

        # Ejecutamos una vez al inicio para no esperar 12 horas
        self.job_scraping()

        # Bucle infinito
        while True:
            schedule.run_pending()
            time.sleep(1)