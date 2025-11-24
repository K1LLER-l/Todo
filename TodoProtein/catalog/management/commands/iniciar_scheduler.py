import time 
import schedule 
from django .core .management .base import BaseCommand 
from django .core .management import call_command 
from django .utils import timezone 

class Command (BaseCommand ):
    help ='Ejecuta el ciclo completo: Scaner (Shopify) + Selenium + Alertas automáticamente.'

    def job_scraping (self ):
        self .stdout .write (self .style .WARNING (f"\n[{timezone .now ()}] --- INICIANDO CICLO DE ACTUALIZACIÓN ---"))
        try :

            self .stdout .write (self .style .SUCCESS (">>> Paso 1: Ejecutando Scanner Shopify..."))
            call_command ('scaner')

            self .stdout .write (self .style .SUCCESS (f"[{timezone .now ()}] --- ACTUALIZACIÓN DE PRECIOS FINALIZADA ---"))

            self .job_alertas ()

        except Exception as e :
            self .stdout .write (self .style .ERROR (f" [X] Error crítico en el ciclo de actualización: {e }"))

    def job_alertas (self ):
        self .stdout .write (self .style .SUCCESS (f"[{timezone .now ()}] >>> Paso 3: Verificando alertas de precio para usuarios..."))
        try :
            call_command ('enviar_alerta')
        except Exception as e :
            self .stdout .write (self .style .ERROR (f"Error enviando alertas: {e }"))

    def job_resumen_semanal (self ):

        self .stdout .write (self .style .SUCCESS (f"[{timezone .now ()}] Enviando resúmenes semanales..."))

        pass 

    def handle (self ,*args ,**kwargs ):
        self .stdout .write ("--- Iniciando Scheduler Maestro de Todo Protein ---")
        self .stdout .write ("   > Tareas programadas: Scaner + Selenium + Alertas")
        self .stdout .write ("   > Ejecución: Cada 12 horas")
        self .stdout .write ("El sistema se ejecutará en segundo plano. Presiona Ctrl+C para detener.\n")

        schedule .every (2 ).minutes .do (self .job_scraping )

        schedule .every (12 ).hours .do (self .job_scraping )

        schedule .every ().monday .at ("09:00").do (self .job_resumen_semanal )

        self .job_scraping ()

        while True :
            schedule .run_pending ()
            time .sleep (1 )