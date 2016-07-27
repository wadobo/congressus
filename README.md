# Aplicación para venta de entradas y registro en congresos

Esta aplicación ofrece una forma sencilla para montar un formulario de
venta de entradas para eventos y congresos, con cobro a través de un TPV.

## Despliegue

Es una aplicación django, por lo que el despliegue se puede hacer siguiendo
las instrucciones del framework:

 https://docs.djangoproject.com/en/1.8/howto/deployment/

Las dependencias django están en el fichero requirements.txt.

## Entorno de desarrollo

Creación de la base de datos:

```
python manage.py migrate
```

Servidor de pruebas:

```
python manage.py runserver
```

## Generar traducciones

Al ser una aplicación django, podemos ver toda la información de traducciones en el siguiente enlace:

 https://docs.djangoproject.com/en/1.8/topics/i18n/translation/


## Instrucciones detalladas para un despliegue:

1. Crear un usuario específico para la aplicación y descargar el código

```
# adduser congressus
# su - congressus
~ $ git clone https://github.com/wadobo/congressus.git
```

1. Crear un virtualenv e instalar las dependencias

```
~ $ cd congressus
congressus $ virtualenv3 env
congressus $ ./env/bin/activate
(env)congressus $ pip install -r requirements.txt
(env)congressus $ pip install psycopg2
(env)congressus $ pip install uwsgi
```

1. Creamos la base de datos postgresql

```
# su - postgres
postgres $ createuser -P congressus
Enter password for new role: congressus
Enter it again: congressus
postgres $ createdb congressus -O congressus
```

1. Creamos el fichero local\_settings.py con la configuración local

```
# su - congressus
~ $ cd congressus/congressus
congressus $ cat > local_settings.py
DEBUG = False

# tpv config
TPV_MERCHANT = 'XXXXXXX'
TPV_TERMINAL = 'XXXX'
TPV_KEY = "XXXXXX"
TPV_URL = "https://sis.redsys.es/sis/realizarPago"

# url config
SITE_URL = "http://mydomain.com"
TPV_MERCHANT_URL = SITE_URL + '/ticket/confirm/'

# email config
FROM_EMAIL = 'congressus@mydomain.com'
EMAIL_HOST = 'smtp.mydomain.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'congressus@mydomain.com'
EMAIL_HOST_PASSWORD = '1234'

# db configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'congressus',
        'USER': 'congressus',
        'PASSWORD': 'congressus',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

1. Creamos las tablas de la base de datos y el usuario administrador

```
congressus $ python manage.py migrate
congressus $ python manage.py createsuperuser
```

1. Fichero uwsgi

Fichero /home/congressus/uwsgi.ini

```
# uwsgi.ini
[uwsgi]
chdir=/home/congressus/congressus/congressus/
module=congressus.wsgi:application
master=True
pidfile=/tmp/congressus-master.pid
vacuum=True
max-requests=5000
http-socket=:8080
```

Para lanzarlo:

```
congressus $ uwsgi --ini uwsgi.ini
```

1. Añadir un script systemd para que se lance automáticamente al inicio

Fichero /etc/systemd/system/congressus.service

```
[Unit]
Description=congressus

[Service]
User=congressus
ExecStart=/home/congressus/congressus/env/bin/uwsgi --ini /home/congressus/uwsgi.ini
Restart=always
KillSignal=SIGQUIT
Type=simple

[Install]
WantedBy=multi-user.target
```

Y habilitamos el servicio

```
# systemctl enable congressus
# systemctl start congressus
```

Con esto ya tendremos la aplicación ejecutandose en
http://mydomain.com:8080, y podemos hacer un simple proxy html desde apache
o nginx.


## Generar UML de modelos django

Instalar django-extensions y pygraphviz.

```
sudo apt-get install graphviz-dev
pip install django-extensions pygraphviz
```

Añadir django_extensions en INSTALLED_APPS:

```
    'django_extensions',
```

Generar png:

```
# Normal
./manage.py graph_models -a -o testg.png
# Agrupado por app
./manage.py graph_models -a -g -o testg.png
```

Si obtenemos el error "CommandError: Neither pygraphviz nor pydot could be found to generate the image"

```
pip uninstall pygraphviz
pip install pygraphviz --install-option="--include-path=/usr/include/graphviz" --install-option="--library-path=/usr/lib/graphviz/"
```

## Problema al añadir maintenance-mode

Si nos da error de que no existen las relaciones, es porque hay que añadir algunas tablas:

```
./manage.py migrate
./manage.py migrate --run-syncdb
```
 
