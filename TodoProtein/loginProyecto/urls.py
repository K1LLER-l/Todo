from django.contrib import admin
from django.urls import path, include
from catalog import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('producto/<int:product_id>/', views.product_detail, name='product_detail'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('registro/', views.registro, name='registro'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'), 
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('favorito/<int:product_id>/', views.toggle_favorito, name='toggle_favorito'),
    
    # NUEVA URL para HU08: Configurar Precio Mínimo Deseado
    path('favorito/set_price/<int:product_id>/', views.set_precio_deseado, name='set_precio_deseado'),
    
    path('favoritos/', views.lista_favoritos, name='lista_favoritos'),
    path('favoritos/exportar/', views.exportar_favoritos_excel, name='exportar_favoritos'),
    path('comparar/', views.comparar_productos, name='comparar_productos'),
    path('cambiar-moneda/', views.cambiar_moneda, name='cambiar_moneda'),
    
    # Rutas duplicadas (mantengo las que tenías al final)
    path('accounts/', include('django.contrib.auth.urls')),
    path('registro/', views.registro, name='registro'),
    path('accounts/', include('allauth.urls')),
]