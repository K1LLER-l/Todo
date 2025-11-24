from django import forms 
from django .contrib .auth .forms import UserCreationForm 
from django .contrib .auth .models import User 
from django .contrib .auth .forms import UserChangeForm 

class RegistroUsuarioForm (UserCreationForm ):

    first_name =forms .CharField (max_length =30 ,required =True ,label ="Nombre")
    email =forms .EmailField (required =True ,label ="Correo Electrónico")

    class Meta :
        model =User 

        fields =['username','first_name','email']

class EditarPerfilForm (UserChangeForm ):
    password =None 

    class Meta :
        model =User 
        fields =['first_name','last_name','email']
        labels ={
        'first_name':'Nombre',
        'last_name':'Apellido',
        'email':'Correo Electrónico',
        }
        help_texts ={
        'email':'Requerido. Usar una dirección válida.',
        }