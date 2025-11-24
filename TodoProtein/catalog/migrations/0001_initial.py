

import django .db .models .deletion 
from django .conf import settings 
from django .db import migrations ,models 

class Migration (migrations .Migration ):

    initial =True 

    dependencies =[
    migrations .swappable_dependency (settings .AUTH_USER_MODEL ),
    ]

    operations =[
    migrations .CreateModel (
    name ='Categoria',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('name',models .CharField (max_length =100 )),
    ],
    ),
    migrations .CreateModel (
    name ='Tienda',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('name',models .CharField (max_length =100 ,unique =True )),
    ('logo',models .URLField (blank =True ,null =True )),
    ],
    ),
    migrations .CreateModel (
    name ='Producto',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('name',models .CharField (max_length =200 )),
    ('brand',models .CharField (max_length =100 )),
    ('image_url',models .URLField (max_length =500 )),
    ('protein_grams',models .FloatField (default =0 ,verbose_name ='Proteínas (g)')),
    ('calories',models .FloatField (default =0 ,verbose_name ='Calorías (kcal)')),
    ('fat_grams',models .FloatField (default =0 ,verbose_name ='Grasas (g)')),
    ('carbs_grams',models .FloatField (default =0 ,verbose_name ='Carbohidratos (g)')),
    ('categoria',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,to ='catalog.categoria')),
    ],
    ),
    migrations .CreateModel (
    name ='PrecioHistorico',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('price',models .IntegerField ()),
    ('fecha',models .DateTimeField (auto_now_add =True )),
    ('producto',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,related_name ='historial',to ='catalog.producto')),
    ('tienda',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,to ='catalog.tienda')),
    ],
    ),
    migrations .CreateModel (
    name ='Favorito',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('fecha_agregado',models .DateTimeField (auto_now_add =True )),
    ('usuario',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,related_name ='favoritos',to =settings .AUTH_USER_MODEL )),
    ('producto',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,related_name ='favorited_by',to ='catalog.producto')),
    ],
    options ={
    'unique_together':{('usuario','producto')},
    },
    ),
    migrations .CreateModel (
    name ='Oferta',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('price',models .IntegerField ()),
    ('url_compra',models .URLField (max_length =800 )),
    ('fecha_actualizacion',models .DateTimeField (auto_now =True )),
    ('producto',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,related_name ='ofertas',to ='catalog.producto')),
    ('tienda',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,to ='catalog.tienda')),
    ],
    options ={
    'ordering':['price'],
    'unique_together':{('producto','tienda')},
    },
    ),
    ]
