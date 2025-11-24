

from django .db import migrations ,models 

class Migration (migrations .Migration ):

    dependencies =[
    ('catalog','0003_tienda_container_class_tienda_container_tag_and_more'),
    ]

    operations =[
    migrations .CreateModel (
    name ='Promocion',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('titulo',models .CharField (max_length =100 ,verbose_name ='Título del Evento')),
    ('descripcion',models .TextField (verbose_name ='Descripción')),
    ('activa',models .BooleanField (default =False ,verbose_name ='¿Está activa?')),
    ('descuento_minimo',models .IntegerField (default =20 ,verbose_name ='Descuento Mínimo (%) para mostrar')),
    ('fecha_inicio',models .DateTimeField (auto_now_add =True )),
    ],
    ),
    ]
