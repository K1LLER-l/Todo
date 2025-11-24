import os 
from pathlib import Path 
import pymysql 

pymysql .install_as_MySQLdb ()

BASE_DIR =Path (__file__ ).resolve ().parent .parent 
SECRET_KEY ='django-insecure-clave-secreta-para-desarrollo'
DEBUG =True 
ALLOWED_HOSTS =[]

INSTALLED_APPS =[
'django.contrib.admin',
'django.contrib.auth',
'django.contrib.contenttypes',
'django.contrib.sessions',
'django.contrib.messages',
'django.contrib.staticfiles',

'django.contrib.sites',

'catalog',

'allauth',
'allauth.account',
'allauth.socialaccount',
'allauth.socialaccount.providers.google',
'allauth.socialaccount.providers.facebook',
]

MIDDLEWARE =[
'django.middleware.security.SecurityMiddleware',
'django.contrib.sessions.middleware.SessionMiddleware',
'django.middleware.common.CommonMiddleware',
'django.middleware.csrf.CsrfViewMiddleware',
'django.contrib.auth.middleware.AuthenticationMiddleware',
'django.contrib.messages.middleware.MessageMiddleware',
'django.middleware.clickjacking.XFrameOptionsMiddleware',
'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF ='loginProyecto.urls'

TEMPLATES =[
{
'BACKEND':'django.template.backends.django.DjangoTemplates',
'DIRS':[BASE_DIR /'templates'],
'APP_DIRS':True ,
'OPTIONS':{
'context_processors':[
'django.template.context_processors.debug',
'django.template.context_processors.request',
'django.contrib.auth.context_processors.auth',
'django.contrib.messages.context_processors.messages',
],
},
},
]

WSGI_APPLICATION ='loginProyecto.wsgi.application'

DATABASES ={
'default':{
'ENGINE':'django.db.backends.mysql',
'NAME':'todoprotein_db',
'USER':'root',
'PASSWORD':'133911',
'HOST':'localhost',
'PORT':'3306',
}
}

AUTH_PASSWORD_VALIDATORS =[{
'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
},

{
'NAME':'catalog.validador.ValidarLongitudMinima',
'OPTIONS':{
'min_length':8 ,
}
},

{
'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator',
},

{
'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator',
},

{
'NAME':'catalog.validador.ValidarMayusculaNumero',
},]
LANGUAGE_CODE ='es-cl'
TIME_ZONE ='America/Santiago'
USE_I18N =True 
USE_TZ =True 

STATIC_URL ='static/'
STATICFILES_DIRS =[BASE_DIR /'static']

DEFAULT_AUTO_FIELD ='django.db.models.BigAutoField'

LOGIN_REDIRECT_URL ='home'
LOGOUT_REDIRECT_URL ='home'

SITE_ID =1 

EMAIL_BACKEND ='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST ='smtp.gmail.com'
EMAIL_PORT =587 
EMAIL_USE_TLS =True 
EMAIL_HOST_USER ='cerveran043@gmail.com'
EMAIL_HOST_PASSWORD ='luyt nchy gpud hlnz'
DEFAULT_FROM_EMAIL ='Todo Protein <noreply@todoprotein.cl>'

AUTHENTICATION_BACKENDS =[
'django.contrib.auth.backends.ModelBackend',
'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL ='home'
LOGOUT_REDIRECT_URL ='home'

SOCIALACCOUNT_PROVIDERS ={
'google':{
'SCOPE':['profile','email'],
'AUTH_PARAMS':{'access_type':'online'}
},

'facebook':{
'METHOD':'oauth2',
'SCOPE':['email','public_profile'],
'FIELDS':['id','email','name','first_name','last_name'],
'VERIFIED_EMAIL':True 
}
}

SOCIALACCOUNT_LOGIN_ON_GET =True 

SESSION_COOKIE_SECURE =False 
CSRF_COOKIE_SECURE =False 