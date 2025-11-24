import time
import schedule # Necesitarás instalar esto: pip install schedule
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

class Command(BaseCommand):
    help = 'Ejecuta el ciclo de scraping y alertas automáticamente cada cierto tiempo.'

    def job_scraping(self):
        self.stdout.write(self.style.WARNING(f"[{timezone.now()}]  Iniciando Scraping Automático..."))
        try:
            # 1. Ejecutar el scraper de categorías (o el que uses principal)
            call_command('scrape_category_pages') 
            
            # 2. (Opcional) Ejecutar el actualizador de precios si es un script separado
            # call_command('update_prices')
            
            self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}]  Scraping finalizado correctamente."))
            
            # 3. Verificar alertas de bajada de precio inmediatamente después
            self.job_alertas()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f" Error en el ciclo de scraping: {e}"))
            # Aquí podrías integrar la HU12 (Alerta de fallo) enviando un correo al admin

    def job_alertas(self):
        self.stdout.write(self.style.MIGRATE(f"[{timezone.now()}]  Verificando alertas de precio..."))
        call_command('enviar_alerta')

    def job_resumen_semanal(self):
        # Este se ejecutaría una vez a la semana
        self.stdout.write(self.style.MIGRATE(f"[{timezone.now()}]  Enviando resúmenes semanales..."))
        call_command('enviar_resumen_semanal')

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Iniciando Scheduler de Todo Protein ---")
        self.stdout.write("El sistema se ejecutará en segundo plano. Presiona Ctrl+C para detener.")

        # --- CONFIGURACIÓN DEL HORARIO ---
        
        # Opción A: Para pruebas rápidas (cada 2 minutos)
        # schedule.every(2).minutes.do(self.job_scraping)
        
        # Opción B: Realista (cada 12 horas)
        schedule.every(12).hours.do(self.job_scraping)
        
        # Opción C: Resumen semanal (Todos los lunes a las 9:00)
        schedule.every().monday.at("09:00").do(self.job_resumen_semanal)

        # Ejecutar una vez al inicio para no esperar 12 horas la primera vez
        self.job_scraping()

        while True:
            schedule.run_pending()
            time.sleep(1)