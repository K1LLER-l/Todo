from django .core .exceptions import ValidationError 
import re 

class ValidarMayusculaNumero :
    def validate (self ,password ,user =None ):

        if not re .search (r'[A-Z]',password ):
            raise ValidationError (
            "La contraseña debe contener al menos una letra mayúscula.",
            code ='password_no_upper',
            )

        if not re .search (r'[0-9]',password ):
            raise ValidationError (
            "La contraseña debe contener al menos un número.",
            code ='password_no_number',
            )

    def get_help_text (self ):
        return "Tu contraseña debe contener al menos una letra mayúscula y un número."

class ValidarLongitudMinima :
    def __init__ (self ,min_length =8 ):
        self .min_length =min_length 

    def validate (self ,password ,user =None ):
        if len (password )<self .min_length :
            raise ValidationError (
            f"La contraseña es muy corta. Debe tener al menos {self .min_length } caracteres.",
            code ='password_too_short',
            )

    def get_help_text (self ):
        return f"Tu contraseña debe tener al menos {self .min_length } caracteres."