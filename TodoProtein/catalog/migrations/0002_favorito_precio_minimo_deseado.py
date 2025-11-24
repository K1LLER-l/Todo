

from django .db import migrations ,models 

class Migration (migrations .Migration ):

    dependencies =[
    ('catalog','0001_initial'),
    ]

    operations =[
    migrations .AddField (
    model_name ='favorito',
    name ='precio_minimo_deseado',
    field =models .IntegerField (default =0 ,verbose_name ='Precio Mínimo Deseado'),
    ),
    ]
