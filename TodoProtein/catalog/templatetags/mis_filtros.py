from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def precio(context, valor):
    """
    Convierte el precio a CLP o USD según la sesión del usuario.
    Uso en HTML: {% precio producto.price %}
    """
    if not valor:
        return "$0"
    
    # Obtenemos la moneda de la sesión (por defecto CLP)
    request = context['request']
    moneda = request.session.get('moneda', 'CLP')
    
    try:
        valor_int = int(valor)
        
        if moneda == 'USD':
            # Tasa de cambio fija para el ejemplo (1 USD = 980 CLP)
            nuevo_valor = valor_int / 980
            return f"US${nuevo_valor:.2f}"
        else:
            # Formato chileno: $10.000 (con puntos)
            return f"${valor_int:,}".replace(",", ".")
            
    except (ValueError, TypeError):
        return str(valor)