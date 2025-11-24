from django .core .management .base import BaseCommand 
from django .core .mail import EmailMultiAlternatives 
from django .template .loader import render_to_string 
from django .utils .html import strip_tags 
from django .conf import settings 
from catalog .models import Favorito ,PrecioHistorico 
from django .contrib .auth .models import User 
from django .db .models import Prefetch 

class Command (BaseCommand ):
    help ='Revisa favoritos y envía un correo DIGEST HTML con todas las bajadas'

    def handle (self ,*args ,**kwargs ):
        self .stdout .write ("Iniciando revisión de precios y compilación de digests...")

        favorites_prefetch =Prefetch ('favoritos',queryset =Favorito .objects .filter (precio_minimo_deseado__gt =0 ))

        users_with_alerts =User .objects .filter (
        favoritos__precio_minimo_deseado__gt =0 
        ).prefetch_related (favorites_prefetch ,'favoritos__producto','favoritos__producto__ofertas','favoritos__producto__historial').distinct ()

        correos_enviados =0 

        for user in users_with_alerts :
            alerts_detected =[]

            for fav in user .favoritos .all ():
                prod =fav .producto 

                oferta_actual =prod .ofertas .order_by ('price').first ()
                if not oferta_actual or not oferta_actual .price :
                    continue 

                precio_ahora =oferta_actual .price 
                precio_minimo_deseado =fav .precio_minimo_deseado 

                historial =prod .historial .order_by ('-fecha')
                precio_anterior =historial .first ().price if historial .exists ()else precio_ahora 

                if precio_minimo_deseado >0 and precio_ahora <precio_minimo_deseado :

                    ahorro_potencial =precio_anterior -precio_ahora 

                    alerts_detected .append ({
                    'product_name':prod .name ,
                    'tienda':oferta_actual .tienda .name ,
                    'precio_nuevo':f"{precio_ahora :,}".replace (",","."),
                    'precio_anterior':f"{precio_anterior :,}".replace (",","."),
                    'ahorro':f"{ahorro_potencial :,}".replace (",","."),
                    'link_compra':oferta_actual .url_compra ,
                    'imagen_url':prod .image_url ,
                    })

            if alerts_detected :
                asunto =f"🔥 ¡Ahorra en {len (alerts_detected )} productos favoritos!"

                context ={
                'usuario':user .first_name or user .username ,
                'alerts':alerts_detected ,
                }

                try :
                    html_content =render_to_string ('emails/alerta_digest.html',context )
                    text_content =strip_tags (html_content )

                    msg =EmailMultiAlternatives (
                    subject =asunto ,
                    body =text_content ,
                    from_email =settings .DEFAULT_FROM_EMAIL ,
                    to =[user .email ]
                    )
                    msg .attach_alternative (html_content ,"text/html")
                    msg .send ()

                    self .stdout .write (self .style .SUCCESS (f" [V] Digest enviado a {user .email } con {len (alerts_detected )} alertas."))
                    correos_enviados +=1 
                except Exception as e :
                    self .stdout .write (self .style .ERROR (f" [X] Error enviando digest a {user .email }: {e }"))

        self .stdout .write (self .style .SUCCESS (f"\nProceso terminado. Total digests enviados: {correos_enviados }"))