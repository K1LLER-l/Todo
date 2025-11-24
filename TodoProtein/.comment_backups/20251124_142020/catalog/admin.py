from django.contrib import admin
from .models import Producto, Categoria, Tienda, Oferta, PrecioHistorico, Promocion

# Configuración para ver las Ofertas DENTRO de la pantalla del Producto
class OfertaInline(admin.TabularInline):
    model = Oferta
    extra = 1

# Configuración para ver el Historial DENTRO de la pantalla del Producto (Opcional, muy útil)
class HistorialInline(admin.TabularInline):
    model = PrecioHistorico
    extra = 0 # No mostrar filas vacías, solo lo que existe
    readonly_fields = ('fecha', 'price', 'tienda') # Para que no se edite accidentalmente
    can_delete = False
    ordering = ('-fecha',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'categoria', 'ver_mejor_precio')
    list_filter = ('brand', 'categoria')
    search_fields = ('name', 'brand')
    
    # Ahora verás las Ofertas actuales Y el Historial al entrar a un producto
    inlines = [OfertaInline, HistorialInline]

    def ver_mejor_precio(self, obj):
        precio = obj.get_best_price()
        return f"${precio}" if precio > 0 else "Sin stock"
    ver_mejor_precio.short_description = "Mejor Precio"

# Configuración para ver la tabla de Historial por separado
@admin.register(PrecioHistorico)
class PrecioHistoricoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'producto', 'tienda', 'price')
    list_filter = ('fecha', 'tienda')
    search_fields = ('producto__name',)
    ordering = ('-fecha',)

# Configuración Mejorada de TIENDA (HU10)
@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = ('name', 'url_busqueda')
    search_fields = ('name',)
    
    # Organizamos los campos en secciones para que se vea profesional
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'logo')
        }),
        ('Configuración del Scraper', {
            'fields': ('url_busqueda', 'container_tag', 'container_class', 'titulo_selector', 'precio_selector', 'imagen_selector'),
            'description': 'Define aquí los selectores CSS para que el robot sepa cómo leer esta tienda.',
        }),
    )

@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'activa', 'descuento_minimo', 'fecha_inicio')
    list_editable = ('activa',)

# Registros simples
admin.site.register(Categoria)
admin.site.register(Oferta)