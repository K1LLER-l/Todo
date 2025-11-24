from django import template 

register =template .Library ()

@register .simple_tag (takes_context =True )
def precio (context ,valor ):

    if not valor :
        return "$0"

    request =context ['request']
    moneda =request .session .get ('moneda','CLP')

    try :
        valor_int =int (valor )

        if moneda =='USD':

            nuevo_valor =valor_int /980 
            return f"US${nuevo_valor :.2f}"
        else :

            return f"${valor_int :,}".replace (",",".")

    except (ValueError ,TypeError ):
        return str (valor )

    except (ValueError ,TypeError ):
        return str (valor )

@register .filter 
def redondear (valor ):
    try :
        return f"{float (valor ):.2f}"
    except (ValueError ,TypeError ):
        return valor 