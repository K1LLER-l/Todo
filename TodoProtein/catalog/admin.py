from django.contrib import admin
from .models import Producto, Categoria, Tienda, Oferta, PrecioHistorico # <--- Agregamos PrecioHistorico

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

# Registros simples
admin.site.register(Categoria)
admin.site.register(Tienda)
admin.site.register(Oferta)