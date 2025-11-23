from django.db import models
from django.contrib.auth.models import User

# 1. MODELO DE LA TIENDA (Para no repetir nombres)
class Tienda(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.URLField(blank=True, null=True) # Opcional: Logo de la tienda
    
    def __str__(self):
        return self.name

# 2. MODELO DEL PRODUCTO (Solo la ficha técnica)
class Categoria(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class Producto(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    image_url = models.URLField(max_length=500)
    
    # --- INFORMACIÓN NUTRICIONAL (HU14) ---
    protein_grams = models.FloatField(default=0, verbose_name="Proteínas (g)")
    calories = models.FloatField(default=0, verbose_name="Calorías (kcal)")
    fat_grams = models.FloatField(default=0, verbose_name="Grasas (g)")
    carbs_grams = models.FloatField(default=0, verbose_name="Carbohidratos (g)")

    def __str__(self):
        return f"{self.brand} - {self.name}"

    def get_best_price(self):
        ofertas = self.ofertas.order_by('price')
        if ofertas.exists():
            return ofertas.first().price
        return 0

# 3. MODELO DE OFERTA (La conexión Producto <-> Tienda)
class Oferta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ofertas')
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    price = models.IntegerField()
    url_compra = models.URLField(max_length=800)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        # Evita que se repita la misma tienda para el mismo producto
        unique_together = ('producto', 'tienda') 
        ordering = ['price'] # Siempre ordenado por precio

    def __str__(self):
        return f"{self.producto.name} en {self.tienda.name}: ${self.price}"
    

class PrecioHistorico(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='historial')
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    price = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.fecha.date()} - {self.producto.name} (${self.price})"
    
class Favorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='favorited_by')
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    # ⭐ NUEVO CAMPO PARA HU08: PRECIO MÍNIMO DESEADO ⭐
    precio_minimo_deseado = models.IntegerField(
        default=0, 
        verbose_name="Precio Mínimo Deseado"
    )

    class Meta:
        unique_together = ('usuario', 'producto') # Un usuario no puede tener 2 veces el mismo favorito

    def __str__(self):
        return f"{self.usuario.username} -> {self.producto.name}"