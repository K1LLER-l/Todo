from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegistroUsuarioForm(UserCreationForm):
    # Agregamos campos extra y los hacemos obligatorios
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    email = forms.EmailField(required=True, label="Correo Electrónico")

    class Meta:
        model = User
        # Definimos el orden en que aparecerán en la pantalla
        fields = ['username', 'first_name', 'email']