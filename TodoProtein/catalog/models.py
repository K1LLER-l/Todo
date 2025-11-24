from django .db import models 
from django .contrib .auth .models import User 

class Tienda (models .Model ):
    name =models .CharField (max_length =100 ,unique =True )
    logo =models .URLField (blank =True ,null =True )

    url_busqueda =models .URLField (blank =True ,null =True ,verbose_name ="URL de Búsqueda/Categoría")

    container_tag =models .CharField (max_length =50 ,blank =True ,default ="div",verbose_name ="Tag del Contenedor (ej: div, article)")
    container_class =models .CharField (max_length =100 ,blank =True ,null =True ,verbose_name ="Clase del Contenedor")

    titulo_selector =models .CharField (max_length =100 ,blank =True ,null =True ,verbose_name ="Selector Título (CSS)")
    precio_selector =models .CharField (max_length =100 ,blank =True ,null =True ,verbose_name ="Selector Precio (CSS)")
    imagen_selector =models .CharField (max_length =100 ,blank =True ,null =True ,verbose_name ="Selector Imagen (CSS)")

    def __str__ (self ):
        return self .name 

class Categoria (models .Model ):
    name =models .CharField (max_length =100 )
    def __str__ (self ):return self .name 

class Producto (models .Model ):
    name =models .CharField (max_length =200 )
    brand =models .CharField (max_length =100 )
    categoria =models .ForeignKey (Categoria ,on_delete =models .CASCADE )
    image_url =models .URLField (max_length =500 )
    protein_grams =models .FloatField (default =0 ,verbose_name ="Proteínas (g)")
    calories =models .FloatField (default =0 ,verbose_name ="Calorías (kcal)")
    fat_grams =models .FloatField (default =0 ,verbose_name ="Grasas (g)")
    carbs_grams =models .FloatField (default =0 ,verbose_name ="Carbohidratos (g)")

    def __str__ (self ):
        return f"{self .brand } - {self .name }"

    def get_best_price (self ):
        ofertas =self .ofertas .order_by ('price')
        if ofertas .exists ():
            return ofertas .first ().price 
        return 0 

class Oferta (models .Model ):
    producto =models .ForeignKey (Producto ,on_delete =models .CASCADE ,related_name ='ofertas')
    tienda =models .ForeignKey (Tienda ,on_delete =models .CASCADE )
    price =models .IntegerField ()
    url_compra =models .URLField (max_length =800 )
    fecha_actualizacion =models .DateTimeField (auto_now =True )

    class Meta :
        unique_together =('producto','tienda')
        ordering =['price']

    def __str__ (self ):
        return f"{self .producto .name } en {self .tienda .name }: ${self .price }"

class PrecioHistorico (models .Model ):
    producto =models .ForeignKey (Producto ,on_delete =models .CASCADE ,related_name ='historial')
    tienda =models .ForeignKey (Tienda ,on_delete =models .CASCADE )
    price =models .IntegerField ()
    fecha =models .DateTimeField (auto_now_add =True )

    def __str__ (self ):
        return f"{self .fecha .date ()} - {self .producto .name } (${self .price })"

class Favorito (models .Model ):
    usuario =models .ForeignKey (User ,on_delete =models .CASCADE ,related_name ='favoritos')
    producto =models .ForeignKey (Producto ,on_delete =models .CASCADE ,related_name ='favorited_by')
    fecha_agregado =models .DateTimeField (auto_now_add =True )

    precio_minimo_deseado =models .IntegerField (
    default =0 ,
    verbose_name ="Precio Mínimo Deseado"
    )

    class Meta :
        unique_together =('usuario','producto')

    def __str__ (self ):
        return f"{self .usuario .username } -> {self .producto .name }"

class Promocion (models .Model ):
    titulo =models .CharField (max_length =100 ,verbose_name ="Título del Evento")
    descripcion =models .TextField (verbose_name ="Descripción")
    activa =models .BooleanField (default =False ,verbose_name ="¿Está activa?")
    descuento_minimo =models .IntegerField (default =20 ,verbose_name ="Descuento Mínimo (%) para mostrar")
    fecha_inicio =models .DateTimeField (auto_now_add =True )

    def __str__ (self ):
        return f"{self .titulo } ({'Activa'if self .activa else 'Inactiva'})"

class HistorialBusqueda (models .Model ):
    usuario =models .ForeignKey (User ,on_delete =models .CASCADE )
    termino =models .CharField (max_length =100 )
    fecha =models .DateTimeField (auto_now_add =True )

    def __str__ (self ):
        return f"{self .usuario .username } busco '{self .termino }'"