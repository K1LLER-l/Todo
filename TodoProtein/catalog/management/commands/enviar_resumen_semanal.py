from django .core .management .base import BaseCommand 
from django .core .mail import EmailMultiAlternatives 
from django .template .loader import render_to_string 
from django .utils .html import strip_tags 
from django .conf import settings 
from django .utils import timezone 
from datetime import timedelta 
from django .contrib .auth .models import User 
from catalog .models import Favorito ,PrecioHistorico 

class Command (BaseCommand ):
    help ='Envía un resumen semanal de precios a los usuarios suscritos.'

    def handle (self ,*args ,**kwargs ):
        self .stdout .write ("Iniciando generación de resúmenes semanales...")

        users =User .objects .filter (favoritos__isnull =False ).distinct ()

        correos_enviados =0 
        fecha_hoy =timezone .now ()
        fecha_semana_pasada =fecha_hoy -timedelta (days =7 )

        for user in users :
            reporte_productos =[]

            for fav in user .favoritos .select_related ('producto'):
                producto =fav .producto 

                oferta_actual =producto .ofertas .order_by ('price').first ()
                if not oferta_actual :
                    continue 

                precio_hoy =oferta_actual .price 

                historico =PrecioHistorico .objects .filter (
                producto =producto ,
                fecha__lte =fecha_semana_pasada 
                ).order_by ('-fecha').first ()

                precio_antes =historico .price if historico else precio_hoy 

                diferencia =precio_hoy -precio_antes 

                if diferencia <0 :
                    estado ="BAJÓ"
                    color ="green"
                    icono ="📉"
                elif diferencia >0 :
                    estado ="SUBIÓ"
                    color ="red"
                    icono ="📈"
                else :
                    estado ="IGUAL"
                    color ="gray"
                    icono ="="

                reporte_productos .append ({
                'nombre':producto .name ,
                'imagen':producto .image_url ,
                'precio_hoy':precio_hoy ,
                'precio_antes':precio_antes ,
                'diferencia':abs (diferencia ),
                'estado':estado ,
                'color_estado':color ,
                'icono':icono ,
                'link':f"http://127.0.0.1:8000/producto/{producto .id }/"
                })

            if reporte_productos :
                self .enviar_correo (user ,reporte_productos )
                correos_enviados +=1 

        self .stdout .write (self .style .SUCCESS (f"¡Listo! Se enviaron {correos_enviados } resúmenes semanales."))

    def enviar_correo (self ,user ,reporte ):
        asunto =f"📊 Tu Resumen Semanal de Precios - Todo Protein"
        context ={
        'user':user ,
        'reporte':reporte ,
        }

        html_content =render_to_string ('emails/resumen_semanal.html',context )
        text_content =strip_tags (html_content )

        try :
            msg =EmailMultiAlternatives (
            subject =asunto ,
            body =text_content ,
            from_email =settings .DEFAULT_FROM_EMAIL ,
            to =[user .email ]
            )
            msg .attach_alternative (html_content ,"text/html")
            msg .send ()
            self .stdout .write (f" -> Correo enviado a {user .email }")
        except Exception as e :
            self .stdout .write (self .style .ERROR (f" -> Error enviando a {user .email }: {e }"))