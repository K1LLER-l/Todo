from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q, Max, Min, Avg, Count
import json
import openpyxl

# Importación de Modelos y Formularios
from .models import Producto, Categoria, Oferta, Favorito, PrecioHistorico
from .forms import RegistroUsuarioForm

# =========================================
# 1. VISTA PRINCIPAL (HOME + RANKING + FILTROS)
# =========================================
def home(request):
    # Obtener parámetros GET
    search_query = request.GET.get('q', '')
    category_filter = request.GET.get('category', 'all')
    sort_by = request.GET.get('sort', 'default')
    max_price_filter = request.GET.get('max_price')

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

    context = {
        'products': products,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
        'max_price_db': max_price_db, 
        'current_max_price': max_price_filter,
        'destacados': destacados, # <--- IMPORTANTE: Enviar esto al HTML
    }
    return render(request, 'home.html', context)

# =========================================
# 2. DETALLE DE PRODUCTO (HU04, HU05, HU06, HU07)
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

    # HU07: Verificar si es favorito del usuario actual
    es_favorito = False
    if request.user.is_authenticated:
        es_favorito = Favorito.objects.filter(usuario=request.user, producto=producto).exists()

    # Lógica de Productos Similares (HU15 / HU20)
    productos_similares = []
    mejor_precio = opciones_compra.first().price if opciones_compra.exists() else 0
    
    if mejor_precio > 0:
        min_p = mejor_precio * 0.7
        max_p = mejor_precio * 1.3
        productos_similares = Producto.objects.filter(
            categoria=producto.categoria,
            ofertas__price__range=(min_p, max_p)
        ).exclude(id=producto.id).distinct()[:3]

    context = {
        'producto': producto,
        'opciones': opciones_compra,
        'productos_similares': productos_similares,
        'chart_fechas': fechas,
        'chart_precios': precios,
        'es_favorito': es_favorito,
        'promedio_precio': promedio_precio,
    }
    return render(request, 'product_detail.html', context)

# =========================================
# 3. GESTIÓN DE FAVORITOS (HU07, HU09, HU22)
# =========================================
@login_required
def toggle_favorito(request, product_id):
    producto = get_object_or_404(Producto, pk=product_id)
    fav = Favorito.objects.filter(usuario=request.user, producto=producto)
    
    if fav.exists():
        fav.delete()
    else:
        Favorito.objects.create(usuario=request.user, producto=producto)
    
    return redirect('product_detail', product_id=product_id)

@login_required
def lista_favoritos(request):
    favoritos = Favorito.objects.filter(usuario=request.user).select_related('producto')
    return render(request, 'favorites.html', {'favoritos': favoritos})

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
            # Mantener orden de selección (opcional)
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
            login(request, user)
            return redirect('home')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registration/registro.html', {'form': form})


def cambiar_moneda(request):
    # 1. Obtener la moneda actual
    actual = request.session.get('moneda', 'CLP')
    
    # 2. Cambiarla (Toggle)
    if actual == 'CLP':
        request.session['moneda'] = 'USD'
    else:
        request.session['moneda'] = 'CLP'
        
    # 3. Volver a la página anterior (o al home si no se sabe)
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)