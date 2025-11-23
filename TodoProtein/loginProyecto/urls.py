from django.contrib import admin
from django.urls import path, include
from catalog import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('producto/<int:product_id>/', views.product_detail, name='product_detail'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('registro/', views.registro, name='registro'),
    path('favorito/<int:product_id>/', views.toggle_favorito, name='toggle_favorito'),
    path('favoritos/', views.lista_favoritos, name='lista_favoritos'),
    path('favoritos/exportar/', views.exportar_favoritos_excel, name='exportar_favoritos'),
    path('comparar/', views.comparar_productos, name='comparar_productos'),
    path('cambiar-moneda/', views.cambiar_moneda, name='cambiar_moneda'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('registro/', views.registro, name='registro'),
    path('accounts/', include('allauth.urls')),
]