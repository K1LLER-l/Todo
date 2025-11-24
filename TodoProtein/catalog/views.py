from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q, Max, Min, Avg, Count
import json
import openpyxl
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

# Importación de Modelos y Formularios
from .models import Producto, Categoria, Oferta, Favorito, PrecioHistorico, Promocion
from .forms import RegistroUsuarioForm, EditarPerfilForm

# =========================================
# 1. VISTA PRINCIPAL (HOME + RANKING + FILTROS)
# =========================================
def home(request):
    # Obtener parámetros GET
    search_query = request.GET.get('q', '')
    category_filter = request.GET.get('category', 'all')
    sort_by = request.GET.get('sort', 'default')
    max_price_filter = request.GET.get('max_price')
    promocion_activa = Promocion.objects.filter(activa=True).last()
    productos_en_oferta = []

    # Configuración base con anotaciones (Precio Mínimo y Conteo de Likes)
    products = Producto.objects.annotate(
        precio_minimo=Min('ofertas__price'),
        num_likes=Count('favorited_by')
    )

    # --- LOGICA HU03: RECUPERAR LOS DESTACADOS ---
    # Filtramos los que tienen likes y ordenamos por popularidad
    destacados = Producto.objects.annotate(
        precio_minimo=Min('ofertas__price'),
        num_likes=Count('favorited_by')
    ).filter(num_likes__gt=0).order_by('-num_likes')[:3]

    # Filtros
    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(brand__icontains=search_query))

    if category_filter != 'all':
        products = products.filter(categoria__name=category_filter)

    if max_price_filter:
        products = products.filter(precio_minimo__lte=max_price_filter)

    # Ordenamiento
    if sort_by == 'price-asc':
        products = products.order_by('precio_minimo')
    elif sort_by == 'price-desc':
        products = products.order_by('-precio_minimo')

    # Datos para el sidebar
    max_price_db = Oferta.objects.aggregate(Max('price'))['price__max']
    if not max_price_db: max_price_db = 100000
    categories = Categoria.objects.all()

    
    if promocion_activa:
        # Buscamos productos que tengan un descuento real comparado con su promedio
        # Esta es una lógica simplificada: Buscamos productos cuyo precio actual sea X% menor que su promedio histórico
        
        # Obtenemos todos los productos con ofertas
        all_prods = Producto.objects.annotate(precio_actual=Min('ofertas__price')).filter(precio_actual__gt=0)
        
        for prod in all_prods:
            # Calculamos promedio histórico
            avg_price = prod.historial.aggregate(Avg('price'))['price__avg']
            
            if avg_price and avg_price > 0:
                descuento = 100 - ((prod.precio_actual * 100) / avg_price)
                
                if descuento >= promocion_activa.descuento_minimo:
                    # Agregamos el atributo "descuento" al objeto temporalmente para usarlo en el template
                    prod.porcentaje_descuento = int(descuento)
                    productos_en_oferta.append(prod)
        
        # Ordenamos por mayor descuento y limitamos a 4
        productos_en_oferta.sort(key=lambda x: x.porcentaje_descuento, reverse=True)
        productos_en_oferta = productos_en_oferta[:4]

    context = {
        'products': products,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
        'max_price_db': max_price_db, 
        'current_max_price': max_price_filter,
        'destacados': destacados, 
        'promocion_activa': promocion_activa,     # <--- NUEVO
        'productos_en_oferta': productos_en_oferta,
    }
    return render(request, 'home.html', context)

# =========================================
# 2. DETALLE DE PRODUCTO (HU04, HU05, HU06, HU07, HU08, HU15)
# =========================================
def product_detail(request, product_id):
    producto = get_object_or_404(Producto, pk=product_id)
    
    # HU04: Comparación de Precios (Ofertas actuales)
    opciones_compra = producto.ofertas.all().order_by('price')

    # HU05: Precio Promedio
    promedio_precio = opciones_compra.aggregate(Avg('price'))['price__avg']

    # HU06: Gráfico de Historial
    historial = producto.historial.all().order_by('fecha')
    fechas = [h.fecha.strftime("%Y-%m-%d %H:%M") for h in historial]
    precios = [h.price for h in historial]

    # HU07 & HU08: Verificar si es favorito y obtener precio deseado
    es_favorito = False
    precio_deseado = 0 
    if request.user.is_authenticated:
        # Recuperamos el objeto Favorito para obtener el precio deseado
        fav_obj = Favorito.objects.filter(usuario=request.user, producto=producto).first()
        if fav_obj:
            es_favorito = True
            precio_deseado = fav_obj.precio_minimo_deseado

    # --- HU15: Lógica de Alternativas Inteligentes ---
    # Buscamos productos con igual/más proteína pero MENOR precio
    productos_similares = []
    mejor_precio_actual = opciones_compra.first().price if opciones_compra.exists() else 0
    tipo_recomendacion = "Similares" # Titulo por defecto

    if mejor_precio_actual > 0:
        # 1. Intentamos buscar "Alternativas Mejores" (Más baratas + Más Proteína)
        alternativas = Producto.objects.filter(
            categoria=producto.categoria,
            protein_grams__gte=producto.protein_grams, # Igual o más proteína
            ofertas__price__lt=mejor_precio_actual,    # Estrictamente más barato
            ofertas__price__gt=0
        ).exclude(id=producto.id).annotate(
            min_price=Min('ofertas__price') # Anotamos el precio mínimo para ordenar
        ).order_by('min_price').distinct()[:3]

        if alternativas.exists():
            productos_similares = alternativas
            tipo_recomendacion = "Mejores Opciones (Ahorra Dinero)"
        else:
            # 2. Si no hay alternativas mejores, usamos la lógica "Estándar" (Rango de precio)
            min_p = mejor_precio_actual * 0.7
            max_p = mejor_precio_actual * 1.3
            productos_similares = Producto.objects.filter(
                categoria=producto.categoria,
                ofertas__price__range=(min_p, max_p)
            ).exclude(id=producto.id).annotate(
                min_price=Min('ofertas__price')
            ).distinct()[:3]
            tipo_recomendacion = "Productos Similares"

    context = {
        'producto': producto,
        'opciones': opciones_compra,
        'productos_similares': productos_similares,
        'tipo_recomendacion': tipo_recomendacion, # Para el título en el HTML
        'precio_referencia': mejor_precio_actual, # Para calcular el ahorro en el HTML
        'chart_fechas': fechas,
        'chart_precios': precios,
        'es_favorito': es_favorito,
        'promedio_precio': promedio_precio,
        'precio_deseado': precio_deseado,
    }
    return render(request, 'product_detail.html', context)

# =========================================
# 3. GESTIÓN DE FAVORITOS (HU07, HU09, HU22, HU08)
# =========================================
@login_required
def toggle_favorito(request, product_id):
    producto = get_object_or_404(Producto, pk=product_id)
    fav = Favorito.objects.filter(usuario=request.user, producto=producto)
    
    if fav.exists():
        fav.delete()
    else:
        # Al crear un favorito, el precio deseado por defecto es 0
        Favorito.objects.create(usuario=request.user, producto=producto)
    
    return redirect('product_detail', product_id=product_id)

@login_required
def set_precio_deseado(request, product_id): # HU08
    producto = get_object_or_404(Producto, pk=product_id)
    
    if request.method == 'POST':
        # Buscamos el favorito existente
        fav = Favorito.objects.filter(usuario=request.user, producto=producto).first()
        
        # Solo actualizamos si el producto es un favorito activo
        if fav:
            try:
                # El campo del formulario se llamará 'precio_minimo'
                new_price = int(request.POST.get('precio_minimo', 0)) 
                
                if new_price < 0:
                    new_price = 0
                
                fav.precio_minimo_deseado = new_price
                fav.save()
            except ValueError:
                pass 

    return redirect('product_detail', product_id=product_id)

@login_required
def lista_favoritos(request):
    # HU09: Resumen de favoritos optimizado
    favoritos_qs = Favorito.objects.filter(usuario=request.user).select_related('producto', 'producto__categoria')
    
    favoritos_data = []
    
    for fav in favoritos_qs:
        mejor_oferta = fav.producto.ofertas.order_by('price').first()
        
        favoritos_data.append({
            'favorito_obj': fav,
            'producto': fav.producto,
            'mejor_precio': mejor_oferta.price if mejor_oferta else None,
            'mejor_tienda': mejor_oferta.tienda.name if mejor_oferta else "Sin stock",
            'url_compra': mejor_oferta.url_compra if mejor_oferta else "#",
            'precio_objetivo': fav.precio_minimo_deseado
        })

    return render(request, 'favorites.html', {'favoritos_data': favoritos_data})

@login_required
def exportar_favoritos_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mis Favoritos"
    ws.append(["Producto", "Marca", "Categoría", "Mejor Precio", "Tienda", "Link"])

    favoritos = Favorito.objects.filter(usuario=request.user).select_related('producto', 'producto__categoria')
    for item in favoritos:
        oferta = item.producto.ofertas.order_by('price').first()
        
        precio = oferta.price if oferta else "Sin Stock"
        tienda = oferta.tienda.name if oferta else "N/A"
        link = oferta.url_compra if oferta else ""
        
        ws.append([item.producto.name, item.producto.brand, item.producto.categoria.name, precio, tienda, link])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Mis_Favoritos.xlsx"'
    
    wb.save(response)
    return response

# =========================================
# 4. COMPARADOR LADO A LADO (HU14)
# =========================================
def comparar_productos(request):
    ids_string = request.GET.get('ids', '')
    productos = []
    if ids_string:
        try:
            lista_ids = [int(x) for x in ids_string.split(',') if x.isdigit()]
            products_qs = Producto.objects.filter(id__in=lista_ids).annotate(precio_minimo=Min('ofertas__price'))
            productos = [p for p in products_qs if p.id in lista_ids]
        except ValueError:
            pass
    return render(request, 'comparison.html', {'productos': productos})

# =========================================
# 5. REGISTRO DE USUARIOS (HU16)
# =========================================
def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            
            # HU16 (Envío de Correo)
            try:
                asunto = "¡Bienvenido a Todo Protein!"
                html_message = render_to_string('emails/bienvenida.html', {'user': user})
                plain_message = strip_tags(html_message)
                
                send_mail(
                    asunto,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error enviando correo de bienvenida: {e}")

            login(request, user)
            return redirect('home')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registration/registro.html', {'form': form})


def cambiar_moneda(request):
    actual = request.session.get('moneda', 'CLP')
    if actual == 'CLP':
        request.session['moneda'] = 'USD'
    else:
        request.session['moneda'] = 'CLP'
        
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)

@login_required
def perfil_usuario(request):
    return render(request, 'registration/perfil.html', {'user': request.user})

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('perfil_usuario')
    else:
        form = EditarPerfilForm(instance=request.user)
    
    return render(request, 'registration/editar_perfil.html', {'form': form})