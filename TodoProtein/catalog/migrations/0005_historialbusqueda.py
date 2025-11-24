

import django .db .models .deletion 
from django .conf import settings 
from django .db import migrations ,models 

class Migration (migrations .Migration ):

    dependencies =[
    ('catalog','0004_promocion'),
    migrations .swappable_dependency (settings .AUTH_USER_MODEL ),
    ]

    operations =[
    migrations .CreateModel (
    name ='HistorialBusqueda',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('termino',models .CharField (max_length =100 )),
    ('fecha',models .DateTimeField (auto_now_add =True )),
    ('usuario',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,to =settings .AUTH_USER_MODEL )),
    ],
    ),
    ]
